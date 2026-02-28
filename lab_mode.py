"""Laboratory Mode: iteration efficiency curve experiment.

Gives an LLM unlimited local simulation access and measures how its
proposed builds improve over successive rounds of feedback.

Usage:
    # Dry run (no API key needed)
    python lab_mode.py --dry-run --provider openai --model test --rounds 3 \\
        --builds-per-round 5 --games-per-pair 10

    # Real run with an LLM
    python lab_mode.py --provider anthropic --model claude-sonnet-4-5 --rounds 10
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine
from simulator.grid import Grid
from simulator.seed import seeded_random

from agents.baselines import Build
from agents.llm_agent_v2 import _STATIC_RULES


# ---------------------------------------------------------------------------
# Available animals for lab mode (original 6 only)
# ---------------------------------------------------------------------------

_LAB_ANIMALS = (
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
)
_ANIMAL_NAMES = frozenset(a.value.upper() for a in _LAB_ANIMALS)
_ANIMAL_LOOKUP: dict[str, Animal] = {a.value.upper(): a for a in _LAB_ANIMALS}


# ---------------------------------------------------------------------------
# Creature creation (from a Build)
# ---------------------------------------------------------------------------

def _compute_derived(hp: int, atk: int, spd: int, wil: int) -> dict[str, Any]:
    """Compute derived combat stats from raw stat allocation."""
    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)
    return {
        "max_hp": max_hp,
        "base_dmg": base_dmg,
        "dodge": dodge,
        "resist": resist,
    }


def _compute_size(hp: int, atk: int) -> Size:
    """Compute creature size from HP + ATK sum."""
    total = hp + atk
    if total <= 10:
        return Size(1, 1)
    elif total <= 12:
        return Size(2, 1)
    elif total <= 17:
        return Size(2, 2)
    else:
        return Size(3, 2)


def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
    """Create a Creature instance from a Build for one side of the arena."""
    hp, atk, spd, wil = build.hp, build.atk, build.spd, build.wil
    derived = _compute_derived(hp, atk, spd, wil)
    size = _compute_size(hp, atk)
    passive = ANIMAL_PASSIVE.get(build.animal)
    abilities = ANIMAL_ABILITIES.get(build.animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)

    return Creature(
        animal=build.animal,
        stats=StatBlock(hp=hp, atk=atk, spd=spd, wil=wil),
        passive=passive,
        current_hp=derived["max_hp"],
        max_hp=derived["max_hp"],
        base_dmg=derived["base_dmg"],
        armor_flat=0,
        size=size,
        position=position,
        dodge_chance=derived["dodge"],
        resist_chance=derived["resist"],
        movement_range=movement,
        abilities=abilities,
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _run_games(build_a: Build, build_b: Build, num_games: int,
               base_seed: int) -> dict[str, int]:
    """Run N games between two builds and return win/loss/draw counts."""
    engine = CombatEngine()
    wins_a = 0
    wins_b = 0
    draws = 0

    for i in range(num_games):
        match_seed = base_seed + i
        creature_a = _create_creature(build_a, "a", match_seed)
        creature_b = _create_creature(build_b, "b", match_seed)
        result = engine.run_combat(creature_a, creature_b, match_seed)

        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1
        else:
            draws += 1

    return {"wins_a": wins_a, "wins_b": wins_b, "draws": draws}


def _run_round_robin(
    builds: list[Build],
    games_per_pair: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    """Run a full round-robin among builds, returning per-build results.

    Returns a list of dicts (one per build), each containing:
        build, total_wins, total_games, win_rate, pairwise (dict of opponent -> wr)
    """
    n = len(builds)
    total_wins = [0] * n
    total_games = [0] * n
    pairwise: list[dict[int, float]] = [{} for _ in range(n)]
    seed_offset = base_seed

    for i in range(n):
        for j in range(i + 1, n):
            res = _run_games(builds[i], builds[j], games_per_pair, seed_offset)
            seed_offset += games_per_pair

            total_wins[i] += res["wins_a"]
            total_wins[j] += res["wins_b"]
            total_games[i] += games_per_pair
            total_games[j] += games_per_pair

            wr_i = res["wins_a"] / games_per_pair if games_per_pair > 0 else 0.0
            wr_j = res["wins_b"] / games_per_pair if games_per_pair > 0 else 0.0
            pairwise[i][j] = wr_i
            pairwise[j][i] = wr_j

    results = []
    for i in range(n):
        wr = total_wins[i] / total_games[i] if total_games[i] > 0 else 0.0
        results.append({
            "build": builds[i],
            "total_wins": total_wins[i],
            "total_games": total_games[i],
            "win_rate": wr,
            "pairwise": pairwise[i],
        })
    return results


# ---------------------------------------------------------------------------
# Build formatting
# ---------------------------------------------------------------------------

def _format_build(build: Build) -> str:
    """Format a Build as 'animal hp/atk/spd/wil'."""
    return f"{build.animal.value} {build.hp}/{build.atk}/{build.spd}/{build.wil}"


def _build_to_dict(build: Build) -> dict[str, Any]:
    """Serialize a Build to a JSON-friendly dict."""
    return {
        "animal": build.animal.value.upper(),
        "hp": build.hp,
        "atk": build.atk,
        "spd": build.spd,
        "wil": build.wil,
    }


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_round1_prompt(builds_per_round: int) -> str:
    """Build the prompt for round 1 (no previous results)."""
    return (
        f"{_STATIC_RULES}\n\n"
        f"LABORATORY MODE\n"
        f"You have access to unlimited local simulation. "
        f"Your task: propose {builds_per_round} different builds to test.\n"
        f"Each build is an animal + stat allocation (HP+ATK+SPD+WIL=20, each >= 1).\n"
        f"Animals: BEAR, BUFFALO, BOAR, TIGER, WOLF, MONKEY\n\n"
        f"Try to explore diverse strategies. You want to find the strongest possible build.\n\n"
        f'Respond with ONLY a JSON array of {builds_per_round} builds (no other text):\n'
        f'[{{"animal":"BEAR","hp":3,"atk":14,"spd":2,"wil":1}}, ...]\n'
    )


def _build_round_n_prompt(
    round_num: int,
    prev_rankings: list[dict[str, Any]],
    pairwise_summary: str,
    builds_per_round: int,
) -> str:
    """Build the prompt for round 2+ with previous results."""
    ranking_lines = []
    for i, entry in enumerate(prev_rankings, 1):
        b = entry["build"]
        wr = entry["win_rate"]
        ranking_lines.append(
            f"  {i}. {b.animal.value.upper()} "
            f"{b.hp}/{b.atk}/{b.spd}/{b.wil} "
            f"-- {wr:.1%} win rate"
        )
    ranking_text = "\n".join(ranking_lines)

    return (
        f"{_STATIC_RULES}\n\n"
        f"LABORATORY MODE — Round {round_num}\n\n"
        f"Results from round {round_num - 1}:\n\n"
        f"Build Rankings (by avg win rate vs field):\n"
        f"{ranking_text}\n\n"
        f"Pairwise matrix (selected matchups):\n"
        f"{pairwise_summary}\n\n"
        f"Now propose {builds_per_round} new builds for the next round.\n"
        f"You may keep good builds from before and replace weak ones.\n"
        f"Your goal: find the single strongest build possible.\n\n"
        f'Respond with ONLY a JSON array of {builds_per_round} builds (no other text):\n'
        f'[{{"animal":"BEAR","hp":3,"atk":14,"spd":2,"wil":1}}, ...]\n'
    )


def _build_pairwise_summary(
    builds: list[Build],
    round_results: list[dict[str, Any]],
    max_rows: int = 10,
) -> str:
    """Build a compact text representation of the pairwise win-rate matrix."""
    n = min(len(builds), max_rows)
    sorted_results = sorted(round_results, key=lambda r: r["win_rate"], reverse=True)
    top_indices = []
    build_to_idx: dict[int, int] = {}
    for entry in sorted_results[:n]:
        idx = round_results.index(entry)
        top_indices.append(idx)
        build_to_idx[idx] = len(top_indices) - 1

    labels = []
    for idx in top_indices:
        b = builds[idx]
        labels.append(f"{b.animal.value[:3].upper()}{b.hp}/{b.atk}")

    header = f"{'':>12}" + "".join(f"{lbl:>10}" for lbl in labels)
    lines = [header]

    for row_idx in top_indices:
        row_pw = round_results[row_idx]["pairwise"]
        row_label = labels[build_to_idx[row_idx]]
        row = f"{row_label:>12}"
        for col_idx in top_indices:
            if row_idx == col_idx:
                row += f"{'--':>10}"
            else:
                wr = row_pw.get(col_idx, 0.0)
                row += f"{wr:.0%}".rjust(10)

        lines.append(row)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

_JSON_ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")
_JSON_OBJECT_PATTERN = re.compile(r"\{[^}]+\}")


def _parse_builds_response(
    response_text: str,
    expected_count: int,
) -> list[Build]:
    """Parse an LLM response into a list of Build objects.

    Tries JSON array first, then falls back to extracting individual
    JSON objects from the text.
    """
    builds: list[Build] = []

    array_match = _JSON_ARRAY_PATTERN.search(response_text)
    if array_match:
        try:
            items = json.loads(array_match.group(0))
            if isinstance(items, list):
                for item in items:
                    build = _validate_build_dict(item)
                    if build is not None:
                        builds.append(build)
                if builds:
                    return builds[:expected_count]
        except (json.JSONDecodeError, TypeError):
            pass

    for obj_match in _JSON_OBJECT_PATTERN.finditer(response_text):
        try:
            data = json.loads(obj_match.group(0))
            build = _validate_build_dict(data)
            if build is not None:
                builds.append(build)
        except (json.JSONDecodeError, TypeError):
            continue

    return builds[:expected_count]


def _validate_build_dict(data: dict) -> Build | None:
    """Validate a parsed dict into a Build, returning None on failure."""
    try:
        animal_str = str(data.get("animal", "")).upper()
        animal = _ANIMAL_LOOKUP.get(animal_str)
        if animal is None:
            return None

        hp = int(data["hp"])
        atk = int(data["atk"])
        spd = int(data["spd"])
        wil = int(data["wil"])

        if hp < 1 or atk < 1 or spd < 1 or wil < 1:
            return None
        if hp + atk + spd + wil != 20:
            return None

        return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
    except (ValueError, TypeError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Dry-run build generator
# ---------------------------------------------------------------------------

def _generate_dry_run_builds(
    count: int,
    round_num: int,
    seed: int,
) -> list[Build]:
    """Generate deterministic pseudo-random builds for --dry-run mode."""
    animals = list(_LAB_ANIMALS)
    builds: list[Build] = []

    for i in range(count):
        build_seed = seed + round_num * 1000 + i
        animal_idx = int(seeded_random(build_seed, 0, len(animals) - 0.001))
        animal = animals[animal_idx]

        remaining = 16  # 20 - 4 (min 1 each)
        values = [1, 1, 1, 1]
        for s in range(4):
            sub_seed_val = build_seed * 31 + s * 7919
            sub_seed_val = sub_seed_val & 0xFFFFFFFF
            if s == 3:
                values[s] += remaining
            else:
                max_alloc = min(remaining, 14)
                if max_alloc > 0:
                    alloc = int(seeded_random(sub_seed_val, 0, max_alloc + 0.999))
                    alloc = max(0, min(alloc, remaining))
                    values[s] += alloc
                    remaining -= alloc

        try:
            builds.append(Build(
                animal=animal,
                hp=values[0],
                atk=values[1],
                spd=values[2],
                wil=values[3],
            ))
        except ValueError:
            builds.append(Build(animal=animal, hp=5, atk=5, spd=5, wil=5))

    return builds


# ---------------------------------------------------------------------------
# API call helpers (urllib only)
# ---------------------------------------------------------------------------

def _get_api_key(provider: str, cli_key: str | None) -> str:
    """Resolve the API key from CLI arg or environment variable."""
    if cli_key:
        return cli_key

    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "xai": "XAI_API_KEY",
    }

    keys = env_map.get(provider, provider.upper() + "_API_KEY")
    if isinstance(keys, list):
        for k in keys:
            val = os.environ.get(k)
            if val:
                return val
        raise ValueError(
            f"No API key found. Set one of: {', '.join(keys)} "
            f"or pass --api-key"
        )

    val = os.environ.get(keys)
    if not val:
        raise ValueError(
            f"No API key found. Set {keys} or pass --api-key"
        )
    return val


def _create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context for HTTPS requests."""
    ctx = ssl.create_default_context()
    return ctx


def _call_anthropic(
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Call Anthropic Messages API and return the text response."""
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = _create_ssl_context()

    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    for block in body.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""


def _call_openai(
    api_key: str,
    model: str,
    prompt: str,
    base_url: str = "https://api.openai.com/v1/chat/completions",
) -> str:
    """Call OpenAI-compatible chat completions API and return the text response."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.7,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    ctx = _create_ssl_context()

    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    choices = body.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _call_google(
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Call Google Generative Language API and return the text response."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 4096,
            "temperature": 0.7,
        },
    }
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = _create_ssl_context()

    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    candidates = body.get("candidates", [])
    if candidates:
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if parts:
            return parts[0].get("text", "")
    return ""


def _call_xai(
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Call xAI API (OpenAI-compatible) and return the text response."""
    return _call_openai(
        api_key, model, prompt,
        base_url="https://api.x.ai/v1/chat/completions",
    )


_PROVIDER_CALLERS = {
    "anthropic": _call_anthropic,
    "openai": _call_openai,
    "google": _call_google,
    "xai": _call_xai,
}


def _call_llm(
    provider: str,
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Route an LLM call to the appropriate provider."""
    caller = _PROVIDER_CALLERS.get(provider)
    if caller is None:
        raise ValueError(f"Unknown provider: {provider}")
    return caller(api_key, model, prompt)


# ---------------------------------------------------------------------------
# Main lab loop
# ---------------------------------------------------------------------------

def run_lab(
    provider: str,
    model: str,
    api_key: str,
    builds_per_round: int,
    games_per_pair: int,
    rounds: int,
    seed: int,
    dry_run: bool,
    output_dir: str,
) -> dict[str, Any]:
    """Execute the laboratory mode experiment and return full results.

    Returns a dict with model info, iteration curve, and totals.
    """
    curve: list[dict[str, Any]] = []
    total_simulations = 0
    total_api_calls = 0
    round_seed = seed

    print(f"\n{'=' * 60}")
    print("MOREAU ARENA -- LABORATORY MODE")
    print(f"{'=' * 60}")
    print(f"Model: {model} ({provider})")
    print(f"Rounds: {rounds} | Builds/round: {builds_per_round} | Games/pair: {games_per_pair}")
    if dry_run:
        print("Mode: DRY RUN (random builds, no API calls)")
    print()

    sims_per_round = builds_per_round * (builds_per_round - 1) // 2 * games_per_pair
    est_total = sims_per_round * rounds
    print(f"Estimated simulations per round: {sims_per_round:,}")
    print(f"Estimated total simulations: {est_total:,}")
    print()

    prev_rankings: list[dict[str, Any]] | None = None
    prev_builds: list[Build] | None = None

    for r in range(1, rounds + 1):
        round_start = time.time()
        print(f"--- Round {r}/{rounds} ---")

        # 1. Get builds from LLM (or dry-run generator)
        if dry_run:
            builds = _generate_dry_run_builds(builds_per_round, r, seed)
        else:
            if r == 1:
                prompt = _build_round1_prompt(builds_per_round)
            else:
                pairwise_summary = _build_pairwise_summary(
                    prev_builds, prev_rankings,
                )
                sorted_prev = sorted(
                    prev_rankings, key=lambda x: x["win_rate"], reverse=True,
                )
                prompt = _build_round_n_prompt(
                    r, sorted_prev, pairwise_summary, builds_per_round,
                )

            try:
                response_text = _call_llm(provider, api_key, model, prompt)
                total_api_calls += 1
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                print(f"  API error: {exc}")
                print("  Falling back to dry-run builds for this round.")
                builds = _generate_dry_run_builds(builds_per_round, r, seed)
                response_text = None

            if not dry_run and response_text is not None:
                builds = _parse_builds_response(response_text, builds_per_round)
                if not builds:
                    print(f"  Warning: could not parse any builds from LLM response.")
                    print(f"  Response preview: {response_text[:200]}")
                    builds = _generate_dry_run_builds(builds_per_round, r, seed)

        # Deduplicate builds (keep first occurrence)
        seen: set[tuple] = set()
        unique_builds: list[Build] = []
        for b in builds:
            key = (b.animal, b.hp, b.atk, b.spd, b.wil)
            if key not in seen:
                seen.add(key)
                unique_builds.append(b)
        builds = unique_builds

        if len(builds) < 2:
            print(f"  Warning: only {len(builds)} unique build(s), adding fallback.")
            fallback = Build(animal=Animal.BEAR, hp=5, atk=5, spd=5, wil=5)
            if len(builds) == 0:
                builds = [
                    fallback,
                    Build(animal=Animal.BOAR, hp=8, atk=8, spd=3, wil=1),
                ]
            else:
                builds.append(fallback)

        print(f"  Builds submitted: {len(builds)}")

        # 2. Run round-robin simulation
        actual_sims = len(builds) * (len(builds) - 1) // 2 * games_per_pair
        total_simulations += actual_sims

        round_results = _run_round_robin(builds, games_per_pair, round_seed)
        round_seed += actual_sims

        # 3. Sort by win rate
        sorted_results = sorted(
            round_results, key=lambda x: x["win_rate"], reverse=True,
        )

        best_entry = sorted_results[0]
        best_build = best_entry["build"]
        best_wr = best_entry["win_rate"]

        print(f"  Best: {_format_build(best_build)} ({best_wr:.1%})")
        elapsed = time.time() - round_start
        print(f"  Simulations: {actual_sims:,} | Time: {elapsed:.1f}s")
        print()

        # Record curve entry
        all_builds_data = []
        for entry in sorted_results:
            b = entry["build"]
            all_builds_data.append({
                "animal": b.animal.value.upper(),
                "hp": b.hp,
                "atk": b.atk,
                "spd": b.spd,
                "wil": b.wil,
                "win_rate": round(entry["win_rate"], 4),
            })

        curve.append({
            "round": r,
            "best_build": _format_build(best_build),
            "best_wr": round(best_wr, 4),
            "all_builds": all_builds_data,
        })

        prev_rankings = round_results
        prev_builds = builds

    # -----------------------------------------------------------------------
    # Final analysis
    # -----------------------------------------------------------------------

    # Find overall best build across all rounds
    overall_best_wr = 0.0
    overall_best_build: Build | None = None
    overall_best_round = 0

    for entry in curve:
        if entry["best_wr"] > overall_best_wr:
            overall_best_wr = entry["best_wr"]
            overall_best_build = _find_build_from_curve_entry(entry)
            overall_best_round = entry["round"]

    if overall_best_build is None:
        overall_best_build = Build(animal=Animal.BEAR, hp=5, atk=5, spd=5, wil=5)

    # Convergence: first round where improvement < 1pp
    convergence_round = rounds
    for i in range(1, len(curve)):
        improvement = curve[i]["best_wr"] - curve[i - 1]["best_wr"]
        if improvement < 0.01:
            convergence_round = curve[i]["round"]
            break

    # SmartAgent comparison: run 100 games vs bear 3/14/2/1
    smart_build = Build(animal=Animal.BEAR, hp=3, atk=14, spd=2, wil=1)
    comparison_res = _run_games(overall_best_build, smart_build, 100, seed + 999999)
    vs_smart_wr = comparison_res["wins_a"] / 100.0

    # Print final results
    derived = _compute_derived(
        overall_best_build.hp, overall_best_build.atk,
        overall_best_build.spd, overall_best_build.wil,
    )

    first_wr = curve[0]["best_wr"]
    last_wr = curve[-1]["best_wr"]
    improvement_pp = (last_wr - first_wr) * 100

    print(f"\n{'=' * 60}")
    print("=== LABORATORY MODE RESULTS ===")
    print(f"{'=' * 60}")
    print()
    print(f"Model: {model}")
    print(
        f"Rounds: {rounds} | Builds/round: {builds_per_round} | "
        f"Games/pair: {games_per_pair}"
    )
    print(f"Total simulations: {total_simulations:,}")
    print(f"Total API calls: {total_api_calls}")
    print()
    print("Iteration Curve:")
    for entry in curve:
        marker = ""
        if entry["round"] == overall_best_round:
            marker = "  [peak]"
        if entry["round"] > 1:
            prev_wr = curve[entry["round"] - 2]["best_wr"]
            if entry["best_wr"] - prev_wr < 0.01 and entry["round"] == convergence_round:
                marker = "  [converged]"
        print(
            f"  Round {entry['round']:2d}: best = {entry['best_build']}  "
            f"({entry['best_wr']:.1%}){marker}"
        )

    print()
    print(
        f"Improvement: {first_wr:.1%} -> {last_wr:.1%} "
        f"({'+' if improvement_pp >= 0 else ''}{improvement_pp:.1f}pp over {rounds} rounds)"
    )
    print(
        f"Convergence: round {convergence_round} "
        f"(first round with <1pp improvement)"
    )
    print()
    print(f"Best build found: {_format_build(overall_best_build)}")
    print(
        f"  max_hp={derived['max_hp']}, base_dmg={derived['base_dmg']}, "
        f"dodge={derived['dodge']:.1%}, resist={derived['resist']:.1%}"
    )
    print(
        f"  Win rate vs SmartAgent's bear 3/14/2/1: {vs_smart_wr:.1%}"
    )

    # Build output dict
    output = {
        "model": model,
        "provider": provider,
        "rounds": rounds,
        "builds_per_round": builds_per_round,
        "games_per_pair": games_per_pair,
        "seed": seed,
        "dry_run": dry_run,
        "curve": curve,
        "total_simulations": total_simulations,
        "total_api_calls": total_api_calls,
        "best_build": _build_to_dict(overall_best_build),
        "best_build_wr": round(overall_best_wr, 4),
        "best_build_round": overall_best_round,
        "convergence_round": convergence_round,
        "vs_smart_agent_wr": round(vs_smart_wr, 4),
        "improvement_pp": round(improvement_pp, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Save results
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_model = re.sub(r"[^a-zA-Z0-9_.-]", "_", model)
    filename = f"lab_{safe_model}_{ts}.json"
    filepath = out_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {filepath}")

    return output


def _find_build_from_curve_entry(entry: dict[str, Any]) -> Build | None:
    """Extract the best Build from a curve entry's all_builds list."""
    if not entry.get("all_builds"):
        return None
    best = entry["all_builds"][0]
    animal = _ANIMAL_LOOKUP.get(best["animal"].upper())
    if animal is None:
        return None
    try:
        return Build(
            animal=animal,
            hp=best["hp"],
            atk=best["atk"],
            spd=best["spd"],
            wil=best["wil"],
        )
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Moreau Arena -- Laboratory Mode (iteration efficiency curve)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Dry run (no API key needed)\n"
            '  python lab_mode.py --dry-run --provider openai --model test '
            "--rounds 3 --builds-per-round 5 --games-per-pair 10\n\n"
            "  # Real run\n"
            "  python lab_mode.py --provider anthropic "
            "--model claude-sonnet-4-5 --rounds 10\n"
        ),
    )

    parser.add_argument(
        "--provider",
        type=str,
        required=True,
        choices=["openai", "anthropic", "google", "xai"],
        help="LLM provider (openai, anthropic, google, xai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model identifier (e.g. claude-sonnet-4-5, gpt-4o)",
    )
    parser.add_argument(
        "--builds-per-round",
        type=int,
        default=20,
        help="Number of builds the LLM proposes each round (default: 20)",
    )
    parser.add_argument(
        "--games-per-pair",
        type=int,
        default=50,
        help="Number of simulation games per build pair (default: 50)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="Number of iteration rounds (default: 10)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (or set via env: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate random builds instead of calling LLM API",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Directory for output files (default: results/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for laboratory mode."""
    args = _parse_args(argv)

    if not args.dry_run:
        try:
            api_key = _get_api_key(args.provider, args.api_key)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        api_key = "dry-run"

    try:
        run_lab(
            provider=args.provider,
            model=args.model,
            api_key=api_key,
            builds_per_round=args.builds_per_round,
            games_per_pair=args.games_per_pair,
            rounds=args.rounds,
            seed=args.seed,
            dry_run=args.dry_run,
            output_dir=args.output_dir,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
