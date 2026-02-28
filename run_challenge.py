#!/usr/bin/env python3
"""Moreau Arena Challenge -- Test your LLM against tournament baselines.

Run your LLM agent against the 5 baseline agents from the paper using
the same best-of-7 series protocol. Results are compared against the
published Tournament 002 Bradley-Terry scores.

Usage:
    # Dry-run (random builds, no API calls):
    python run_challenge.py --dry-run --provider openai --model test --series 3

    # Real run with Anthropic Claude:
    python run_challenge.py --provider anthropic --model claude-sonnet-4-20250514

    # Real run with OpenAI:
    python run_challenge.py --provider openai --model gpt-4o --api-key sk-...

    # Real run with Google Gemini:
    python run_challenge.py --provider google --model gemini-2.0-flash

    # Real run with xAI Grok:
    python run_challenge.py --provider xai --model grok-3 --api-key xai-...

Providers read API keys from environment variables if --api-key is not set:
    anthropic  -> ANTHROPIC_API_KEY
    openai     -> OPENAI_API_KEY
    google     -> GOOGLE_API_KEY
    xai        -> XAI_API_KEY
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.baselines import (
    BaseAgent,
    Build,
    ConservativeAgent,
    GreedyAgent,
    HighVarianceAgent,
    RandomAgent,
    SmartAgent,
)
from agents.llm_agent import LLMAgent
from agents.llm_agent_v2 import (
    BUILD_JSON_SCHEMA,
    LLMAgentV2,
    build_prompt_v2,
    parse_json_response,
)
from analysis.bt_ranking import compute_bt_scores, BTResult
from prompts.meta_extractor import extract_top_builds
from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Position,
    Size,
    StatBlock,
)
from simulator.engine import CombatConfig, CombatEngine, CombatResult
from simulator.grid import Grid
from simulator.seed import seeded_random


# ---------------------------------------------------------------------------
# Paper reference scores (T002, adaptive best-of-7)
# ---------------------------------------------------------------------------

PAPER_BT_T002: dict[str, float] = {
    "GPT-5.2-Codex": 1.000,
    "Gemini Flash": 0.679,
    "Grok-4.1 Fast": 0.650,
    "Cl. Opus 4.6": 0.252,
    "Cl. Sonnet 4.6": 0.252,
    "GPT-5.2": 0.252,
    "Cl. Haiku 4.5": 0.226,
    "Gemini Pro": 0.188,
}

_BASELINES: list[tuple[str, type[BaseAgent]]] = [
    ("RandomAgent", RandomAgent),
    ("GreedyAgent", GreedyAgent),
    ("SmartAgent", SmartAgent),
    ("ConservativeAgent", ConservativeAgent),
    ("HighVarianceAgent", HighVarianceAgent),
]

_ORIGINAL_ANIMALS = [
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
]

_ENV_KEY_MAP: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
}


# ---------------------------------------------------------------------------
# Creature creation
# ---------------------------------------------------------------------------

def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
    """Create a Creature dataclass from a flat Build."""
    hp, atk, spd, wil = build.hp, build.atk, build.spd, build.wil
    animal = build.animal

    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)

    hp_atk = hp + atk
    if hp_atk <= 10:
        size = Size(1, 1)
    elif hp_atk <= 12:
        size = Size(2, 1)
    elif hp_atk <= 17:
        size = Size(2, 2)
    else:
        size = Size(3, 2)

    passive = ANIMAL_PASSIVE.get(animal)
    abilities = ANIMAL_ABILITIES.get(animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)

    return Creature(
        animal=animal,
        stats=StatBlock(hp=hp, atk=atk, spd=spd, wil=wil),
        passive=passive,
        current_hp=max_hp,
        max_hp=max_hp,
        base_dmg=base_dmg,
        armor_flat=0,
        size=size,
        position=position,
        dodge_chance=dodge,
        resist_chance=resist,
        movement_range=movement,
        abilities=abilities,
    )


# ---------------------------------------------------------------------------
# API call helpers (stdlib only -- urllib.request)
# ---------------------------------------------------------------------------

def _make_request(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout: int = 60,
) -> dict[str, Any]:
    """POST JSON to *url* and return parsed JSON response."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for key, val in headers.items():
        req.add_header(key, val)
    req.add_header("Content-Type", "application/json")

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"API request failed ({exc.code}): {error_body}"
        ) from exc


def _api_call_anthropic(
    api_key: str,
    model: str,
    prompt: str,
) -> dict | str:
    """Call Anthropic Messages API with tool_use for structured output."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": 256,
        "tools": [
            {
                "name": "choose_build",
                "description": "Choose a creature build for Moreau Arena.",
                "input_schema": BUILD_JSON_SCHEMA,
            }
        ],
        "tool_choice": {"type": "tool", "name": "choose_build"},
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = _make_request(url, headers, body)
    for block in resp.get("content", []):
        if block.get("type") == "tool_use":
            return block.get("input", {})
    # Fallback: return text content
    for block in resp.get("content", []):
        if block.get("type") == "text":
            return block.get("text", "")
    return ""


def _api_call_openai(
    api_key: str,
    model: str,
    prompt: str,
    base_url: str = "https://api.openai.com/v1",
) -> dict | str:
    """Call OpenAI-compatible API with json_schema response format."""
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": 256,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "moreau_build",
                "strict": True,
                "schema": BUILD_JSON_SCHEMA,
            },
        },
    }

    resp = _make_request(url, headers, body)
    choices = resp.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content
    return ""


def _api_call_google(
    api_key: str,
    model: str,
    prompt: str,
) -> dict | str:
    """Call Google Generative AI API with response_schema."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    headers: dict[str, str] = {}
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": BUILD_JSON_SCHEMA,
            "maxOutputTokens": 256,
            "temperature": 0.7,
        },
    }

    resp = _make_request(url, headers, body)
    candidates = resp.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            text = parts[0].get("text", "")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
    return ""


def _api_call_xai(
    api_key: str,
    model: str,
    prompt: str,
) -> dict | str:
    """Call xAI API (OpenAI-compatible format)."""
    return _api_call_openai(
        api_key, model, prompt, base_url="https://api.x.ai/v1"
    )


def _build_api_callable(
    provider: str,
    model: str,
    api_key: str,
) -> callable:
    """Return an api_call(prompt) -> dict|str callable for the given provider."""
    dispatch = {
        "anthropic": _api_call_anthropic,
        "openai": _api_call_openai,
        "google": _api_call_google,
        "xai": _api_call_xai,
    }
    fn = dispatch[provider]

    def api_call(prompt: str) -> dict | str:
        return fn(api_key, model, prompt)

    return api_call


# ---------------------------------------------------------------------------
# Dry-run random api_call
# ---------------------------------------------------------------------------

def _random_build_dict() -> dict[str, Any]:
    """Generate a random valid build dict."""
    animal = random.choice(_ORIGINAL_ANIMALS)
    remaining = 16  # 20 - 4 minimum
    stats = [1, 1, 1, 1]
    for i in range(3):
        alloc = random.randint(0, remaining)
        stats[i] += alloc
        remaining -= alloc
    stats[3] += remaining
    return {
        "animal": animal.value.upper(),
        "hp": stats[0],
        "atk": stats[1],
        "spd": stats[2],
        "wil": stats[3],
    }


def _dry_run_api_call_v2(prompt: str) -> dict:
    """Return a random valid build as dict (for LLMAgentV2 / T002)."""
    return _random_build_dict()


def _dry_run_api_call_v1(prompt: str) -> str:
    """Return a random valid build as text (for LLMAgent / T001)."""
    b = _random_build_dict()
    return f"{b['animal']} {b['hp']} {b['atk']} {b['spd']} {b['wil']}"


# ---------------------------------------------------------------------------
# Combat: single game
# ---------------------------------------------------------------------------

def _run_single_game(
    build_a: Build,
    build_b: Build,
    match_seed: int,
) -> CombatResult:
    """Run a single combat between two builds."""
    creature_a = _create_creature(build_a, "a", match_seed)
    creature_b = _create_creature(build_b, "b", match_seed)
    engine = CombatEngine()
    return engine.run_combat(creature_a, creature_b, match_seed)


# ---------------------------------------------------------------------------
# Series protocols
# ---------------------------------------------------------------------------

def _run_blind_series(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
) -> tuple[str, list[dict[str, Any]]]:
    """T001 blind-pick best-of-7. Each agent picks once, uses same build all games.

    Returns (winner_name, game_records).
    """
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    build_a = agent_a.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )
    build_b = agent_b.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )

    wins_a, wins_b = 0, 0
    game_records: list[dict[str, Any]] = []

    for g in range(7):
        if wins_a >= 4 or wins_b >= 4:
            break

        match_seed = series_seed + g
        result = _run_single_game(build_a, build_b, match_seed)

        record = {
            "game": g + 1,
            "seed": match_seed,
            "build_a": _build_to_dict(build_a),
            "build_b": _build_to_dict(build_b),
            "winner_side": result.winner,
            "ticks": result.ticks,
            "end_condition": result.end_condition,
        }
        game_records.append(record)

        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1

    if wins_a > wins_b:
        return name_a, game_records
    elif wins_b > wins_a:
        return name_b, game_records
    return "draw", game_records


def _run_adaptive_series(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
) -> tuple[str, list[dict[str, Any]]]:
    """T002 adaptive best-of-7. Loser sees winner's build, can re-pick.

    Returns (winner_name, game_records).
    """
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    # Initial picks -- blind
    build_a = agent_a.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )
    build_b = agent_b.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )

    wins_a, wins_b = 0, 0
    game_records: list[dict[str, Any]] = []

    for g in range(7):
        if wins_a >= 4 or wins_b >= 4:
            break

        match_seed = series_seed + g
        result = _run_single_game(build_a, build_b, match_seed)

        record = {
            "game": g + 1,
            "seed": match_seed,
            "build_a": _build_to_dict(build_a),
            "build_b": _build_to_dict(build_b),
            "winner_side": result.winner,
            "ticks": result.ticks,
            "end_condition": result.end_condition,
        }
        game_records.append(record)

        if result.winner == "a":
            wins_a += 1
            # B lost -- B gets to re-pick with knowledge of A's build
            try:
                build_b = agent_b.choose_build(
                    opponent_animal=build_a.animal,
                    banned=[],
                    opponent_reveal=build_a,
                )
            except Exception:
                pass  # keep existing build on failure
        elif result.winner == "b":
            wins_b += 1
            # A lost -- A gets to re-pick with knowledge of B's build
            try:
                build_a = agent_a.choose_build(
                    opponent_animal=build_b.animal,
                    banned=[],
                    opponent_reveal=build_b,
                )
            except Exception:
                pass
        # draw: both keep their builds

    if wins_a > wins_b:
        return name_a, game_records
    elif wins_b > wins_a:
        return name_b, game_records
    return "draw", game_records


def _build_to_dict(build: Build) -> dict[str, Any]:
    """Convert a Build to a serializable dict."""
    return {
        "animal": build.animal.value.upper(),
        "hp": build.hp,
        "atk": build.atk,
        "spd": build.spd,
        "wil": build.wil,
    }


# ---------------------------------------------------------------------------
# Cost estimate
# ---------------------------------------------------------------------------

_COST_PER_1K_INPUT: dict[str, float] = {
    "anthropic": 3.00,
    "openai": 2.50,
    "google": 0.50,
    "xai": 2.00,
}

_COST_PER_1K_OUTPUT: dict[str, float] = {
    "anthropic": 15.00,
    "openai": 10.00,
    "google": 1.50,
    "xai": 10.00,
}


def _estimate_cost(
    provider: str,
    num_series: int,
    num_baselines: int,
    protocol: str,
) -> str:
    """Estimate API cost. Very rough: ~1K input tokens per call, ~50 output."""
    avg_games = 5.5  # average games in best-of-7
    calls_per_series = avg_games  # re-pick on loss
    if protocol == "t001":
        calls_per_series = 1  # single pick per series

    total_calls = int(num_series * num_baselines * calls_per_series)
    input_cost = (total_calls * 1.0 / 1000) * _COST_PER_1K_INPUT.get(provider, 3.0)
    output_cost = (total_calls * 0.05 / 1000) * _COST_PER_1K_OUTPUT.get(provider, 10.0)
    total = input_cost + output_cost
    return f"~{total_calls} API calls, ~${total:.2f} estimated cost"


# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

def _print_pairwise_results(
    challenger_name: str,
    results_by_baseline: dict[str, dict[str, int]],
) -> None:
    """Print pairwise series results table."""
    print("\n" + "=" * 65)
    print(f"  {'Baseline':<25} {'Series Won':>10} {'Series Lost':>11} {'WR':>8}")
    print("-" * 65)

    total_won = 0
    total_lost = 0
    total_draws = 0

    for baseline_name in [name for name, _ in _BASELINES]:
        counts = results_by_baseline.get(baseline_name, {"won": 0, "lost": 0, "draw": 0})
        won = counts["won"]
        lost = counts["lost"]
        draws = counts["draw"]
        total = won + lost + draws
        wr = won / total if total > 0 else 0.0
        total_won += won
        total_lost += lost
        total_draws += draws

        print(f"  {baseline_name:<25} {won:>10} {lost:>11} {wr:>7.0%}")

    grand_total = total_won + total_lost + total_draws
    grand_wr = total_won / grand_total if grand_total > 0 else 0.0
    print("-" * 65)
    print(f"  {'TOTAL':<25} {total_won:>10} {total_lost:>11} {grand_wr:>7.0%}")
    if total_draws > 0:
        print(f"  Draws: {total_draws}")
    print("=" * 65)


def _print_bt_comparison(
    challenger_name: str,
    bt_results: list[BTResult],
) -> None:
    """Print BT ranking with comparison to paper scores."""
    print("\nBradley-Terry Rankings:")
    print(f"  {'Rank':<5} {'Agent':<25} {'BT Score':<10} {'95% CI':<22}")
    print("  " + "-" * 60)

    for i, r in enumerate(bt_results, 1):
        ci_str = f"[{r.ci_lower:.4f}, {r.ci_upper:.4f}]"
        print(f"  {i:<5} {r.name:<25} {r.score:<10.4f} {ci_str:<22}")

    # Find challenger score
    challenger_bt = None
    for r in bt_results:
        if r.name == challenger_name:
            challenger_bt = r.score
            break

    if challenger_bt is not None:
        print(f"\n  Your model's BT score: {challenger_bt:.4f}")

        # Compare against paper LLMs
        print("\n  Paper reference (T002 LLM BT scores):")
        for name, score in sorted(
            PAPER_BT_T002.items(), key=lambda x: x[1], reverse=True
        ):
            comparison = ""
            if challenger_bt > score:
                comparison = " < YOUR MODEL"
            elif abs(challenger_bt - score) < 0.01:
                comparison = " ~ YOUR MODEL"
            print(f"    {name:<25} {score:.3f}{comparison}")


# ---------------------------------------------------------------------------
# JSONL output
# ---------------------------------------------------------------------------

def _save_results_jsonl(
    output_dir: Path,
    challenger_name: str,
    protocol: str,
    series_records: list[dict[str, Any]],
) -> Path:
    """Save all series results to a JSONL file. Returns the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = challenger_name.replace("/", "_").replace(" ", "_")
    filename = f"challenge_{safe_name}_{protocol}_{timestamp}.jsonl"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        for record in series_records:
            f.write(json.dumps(record, default=str) + "\n")

    return output_path


# ---------------------------------------------------------------------------
# Main challenge runner
# ---------------------------------------------------------------------------

def run_challenge(args: argparse.Namespace) -> None:
    """Execute the full challenge run."""
    provider = args.provider
    model = args.model
    protocol = args.protocol
    num_series = args.series
    dry_run = args.dry_run
    output_dir = Path(args.output_dir)

    # Resolve API key
    api_key = args.api_key or os.environ.get(_ENV_KEY_MAP.get(provider, ""), "")
    if not dry_run and not api_key:
        env_var = _ENV_KEY_MAP.get(provider, "UNKNOWN")
        print(
            f"Error: No API key provided. Use --api-key or set {env_var}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load meta builds for T002 prompt
    meta_builds: list[dict] = []
    t001_results_path = Path(__file__).parent / "data" / "tournament_001" / "results.jsonl"
    if t001_results_path.exists():
        meta_builds = extract_top_builds(t001_results_path, top_n=5)

    # Build the api_call callable
    if dry_run:
        api_call_v1 = _dry_run_api_call_v1
        api_call_v2 = _dry_run_api_call_v2
        challenger_name = f"DryRun-{model}"
    else:
        api_call_v1 = _build_api_callable(provider, model, api_key)
        api_call_v2 = _build_api_callable(provider, model, api_key)
        challenger_name = model

    # Select api_call based on protocol
    api_call = api_call_v1 if protocol == "t001" else api_call_v2

    # Print header
    print("=" * 65)
    print("  MOREAU ARENA CHALLENGE")
    print("=" * 65)
    print(f"  Provider:     {provider}")
    print(f"  Model:        {model}")
    print(f"  Protocol:     {protocol.upper()} ({'adaptive' if protocol == 't002' else 'blind'})")
    print(f"  Series/base:  {num_series}")
    print(f"  Baselines:    {len(_BASELINES)}")
    print(f"  Dry run:      {dry_run}")
    if meta_builds:
        print(f"  Meta builds:  {len(meta_builds)} loaded from T001")
    else:
        print("  Meta builds:  none (T001 results not found)")

    if not dry_run:
        estimate = _estimate_cost(provider, num_series, len(_BASELINES), protocol)
        print(f"  Cost est.:    {estimate}")

    print("=" * 65)
    print()

    # Run series against each baseline
    series_fn = _run_adaptive_series if protocol == "t002" else _run_blind_series
    results_by_baseline: dict[str, dict[str, int]] = {}
    all_bt_pairs: list[tuple[str, str]] = []
    all_series_records: list[dict[str, Any]] = []
    base_seed = 100_000

    total_series = num_series * len(_BASELINES)
    series_idx = 0

    for baseline_name, baseline_cls in _BASELINES:
        counts = {"won": 0, "lost": 0, "draw": 0}

        for s in range(num_series):
            series_idx += 1
            series_seed = base_seed + series_idx * 100

            # Instantiate baseline fresh each series
            if baseline_cls in (RandomAgent, HighVarianceAgent):
                baseline_agent = baseline_cls(seed=series_seed)
            else:
                baseline_agent = baseline_cls()

            # Recreate LLM agent for fresh state each series
            if protocol == "t001":
                challenger_agent: BaseAgent = LLMAgent(
                    name=challenger_name, api_call=api_call_v1
                )
            else:
                challenger_agent = LLMAgentV2(
                    name=challenger_name,
                    api_call=api_call_v2,
                    meta_builds=meta_builds,
                )

            t_start = time.monotonic()
            winner, game_records = series_fn(
                challenger_agent, baseline_agent, series_seed
            )
            elapsed = time.monotonic() - t_start

            # Classify result for challenger
            if winner == challenger_name:
                counts["won"] += 1
                all_bt_pairs.append((challenger_name, baseline_name))
            elif winner == baseline_name:
                counts["lost"] += 1
                all_bt_pairs.append((baseline_name, challenger_name))
            else:
                counts["draw"] += 1

            # Build series record for JSONL
            series_record = {
                "agent_a": challenger_name,
                "agent_b": baseline_name,
                "winner": winner,
                "protocol": protocol,
                "series_seed": series_seed,
                "games": game_records,
                "elapsed_s": round(elapsed, 2),
            }
            all_series_records.append(series_record)

            # Progress indicator
            games_str = f"{len(game_records)} games"
            status = f"[{series_idx}/{total_series}]"
            print(
                f"  {status:>10}  vs {baseline_name:<22} "
                f"-> {winner:<25} ({games_str}, {elapsed:.1f}s)"
            )

        results_by_baseline[baseline_name] = counts

    # Print pairwise results
    _print_pairwise_results(challenger_name, results_by_baseline)

    # Compute and display BT scores
    if all_bt_pairs:
        bt_results = compute_bt_scores(
            all_bt_pairs, n_bootstrap=1000, bootstrap_seed=42
        )
        _print_bt_comparison(challenger_name, bt_results)
    else:
        print("\n  No decisive series results -- cannot compute BT scores.")

    # Save JSONL
    output_path = _save_results_jsonl(
        output_dir, challenger_name, protocol, all_series_records
    )
    print(f"\nResults saved to: {output_path}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        description="Moreau Arena Challenge -- Test your LLM against tournament baselines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python run_challenge.py --dry-run --provider openai --model test --series 3\n'
            '  python run_challenge.py --provider anthropic --model claude-sonnet-4-20250514\n'
            '  python run_challenge.py --provider openai --model gpt-4o --api-key sk-...\n'
            '  python run_challenge.py --provider google --model gemini-2.0-flash\n'
            '  python run_challenge.py --provider xai --model grok-3\n'
        ),
    )

    parser.add_argument(
        "--provider",
        type=str,
        required=True,
        choices=["openai", "anthropic", "google", "xai"],
        help="API provider (openai, anthropic, google, xai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model identifier string (e.g. gpt-4o, claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--protocol",
        type=str,
        default="t002",
        choices=["t001", "t002"],
        help="Tournament protocol: t001 (blind) or t002 (adaptive, default)",
    )
    parser.add_argument(
        "--series",
        type=int,
        default=10,
        help="Number of best-of-7 series per baseline (default: 10)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (or set env var: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use random builds instead of real API calls (for testing)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Directory for output JSONL files (default: results/)",
    )

    return parser


def main() -> None:
    """Entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        run_challenge(args)
    except KeyboardInterrupt:
        print("\nChallenge interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
