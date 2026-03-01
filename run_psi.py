#!/usr/bin/env python3
"""Prompt Sensitivity Index (PSI) — measure ranking stability across prompt paraphrases.

Runs the same set of agents on N paraphrased prompts (same information, different
wording). Computes Bradley-Terry rankings for each prompt, then reports Kendall τ
between every pair of rankings.

    PSI < 0.15  → "prompt-robust"
    0.15–0.30   → "moderate"
    > 0.30      → "prompt-sensitive"

Usage:
    # Dry-run with default 3 prompts:
    python run_psi.py --dry-run

    # Explicit prompt files:
    python run_psi.py --prompts prompts/t002_prompt.txt prompts/t002_v2.txt prompts/t002_v3.txt --dry-run

    # Real run:
    python run_psi.py --provider anthropic --model claude-sonnet-4-20250514
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scipy.stats import kendalltau

from agents.baselines import (
    BaseAgent,
    Build,
    GreedyAgent,
    RandomAgent,
    SmartAgent,
)
from agents.llm_agent import parse_response
from analysis.bt_ranking import compute_bt_scores, BTResult
from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine, CombatResult
from simulator.grid import Grid


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_PROMPTS = [
    "prompts/t002_prompt.txt",
    "prompts/t002_v2.txt",
    "prompts/t002_v3.txt",
]

_ORIGINAL_ANIMALS = [
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
]

_BASELINES: list[tuple[str, type[BaseAgent]]] = [
    ("RandomAgent", RandomAgent),
    ("SmartAgent", SmartAgent),
]

_LLM_AGENT_NAMES = [
    "LLM-PSI-1",
    "LLM-PSI-2",
    "LLM-PSI-3",
]


# ---------------------------------------------------------------------------
# Prompt-driven LLM agent
# ---------------------------------------------------------------------------

class PromptFileAgent(BaseAgent):
    """LLM agent that sends a verbatim prompt file to the API."""

    def __init__(self, name: str, prompt_text: str, api_call) -> None:
        self._name = name
        self._prompt_text = prompt_text
        self._api_call = api_call

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        response = self._api_call(self._prompt_text)
        build = _parse_json_or_text(response, banned)
        if build is not None:
            return build
        return GreedyAgent().choose_build(opponent_animal, banned)


def _parse_json_or_text(response: str, banned: list[Animal]) -> Build | None:
    """Try JSON parsing first, then fall back to text parsing."""
    # Try JSON
    try:
        data = json.loads(response.strip())
        animal_str = data.get("animal", "").upper()
        animal_map = {a.value.upper(): a for a in _ORIGINAL_ANIMALS}
        animal = animal_map.get(animal_str)
        if animal and animal not in banned:
            return Build(
                animal=animal,
                hp=int(data["hp"]),
                atk=int(data["atk"]),
                spd=int(data["spd"]),
                wil=int(data["wil"]),
            )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        pass
    # Fall back to text format
    return parse_response(response, banned)


# ---------------------------------------------------------------------------
# Creature creation (shared with run_ablation.py)
# ---------------------------------------------------------------------------

def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
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


def _run_single_game(build_a: Build, build_b: Build, match_seed: int) -> CombatResult:
    creature_a = _create_creature(build_a, "a", match_seed)
    creature_b = _create_creature(build_b, "b", match_seed)
    engine = CombatEngine()
    return engine.run_combat(creature_a, creature_b, match_seed)


def _build_to_dict(build: Build) -> dict[str, Any]:
    return {
        "animal": build.animal.value.upper(),
        "hp": build.hp,
        "atk": build.atk,
        "spd": build.spd,
        "wil": build.wil,
    }


# ---------------------------------------------------------------------------
# Blind-pick series (same as run_ablation.py)
# ---------------------------------------------------------------------------

def _run_blind_series(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
) -> tuple[str, list[dict[str, Any]]]:
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    build_a = agent_a.choose_build(opponent_animal=None, banned=[], opponent_reveal=None)
    build_b = agent_b.choose_build(opponent_animal=None, banned=[], opponent_reveal=None)

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


# ---------------------------------------------------------------------------
# Dry-run API call
# ---------------------------------------------------------------------------

def _random_build_json() -> str:
    animal = random.choice(_ORIGINAL_ANIMALS)
    remaining = 16
    stats = [1, 1, 1, 1]
    for i in range(3):
        alloc = random.randint(0, remaining)
        stats[i] += alloc
        remaining -= alloc
    stats[3] += remaining
    return json.dumps({
        "animal": animal.value.upper(),
        "hp": stats[0],
        "atk": stats[1],
        "spd": stats[2],
        "wil": stats[3],
    })


def _dry_run_api_call(prompt: str) -> str:
    return _random_build_json()


# ---------------------------------------------------------------------------
# Run one prompt variant
# ---------------------------------------------------------------------------

def _run_prompt_tournament(
    prompt_path: str,
    prompt_text: str,
    api_call,
    num_series: int,
) -> tuple[list[BTResult], list[dict[str, Any]]]:
    """Run a mini round-robin for a single prompt variant. Return BT rankings and records."""
    agents: list[tuple[str, BaseAgent]] = []
    for name in _LLM_AGENT_NAMES:
        agents.append((name, PromptFileAgent(name, prompt_text, api_call)))
    for baseline_name, baseline_cls in _BASELINES:
        if baseline_cls is RandomAgent:
            agents.append((baseline_name, baseline_cls(seed=42)))
        else:
            agents.append((baseline_name, baseline_cls()))

    pairs = [(i, j) for i in range(len(agents)) for j in range(i + 1, len(agents))]
    total_series = len(pairs) * num_series
    series_idx = 0
    base_seed = 300_000

    bt_pairs: list[tuple[str, str]] = []
    all_records: list[dict[str, Any]] = []

    prompt_label = Path(prompt_path).stem
    print(f"\n--- Prompt: {prompt_label} ({prompt_path}) ---")
    print(f"  Agents: {', '.join(n for n, _ in agents)}")
    print(f"  Series per pair: {num_series}, Total: {total_series}")
    print()

    for i, j in pairs:
        name_a, _ = agents[i]
        name_b, _ = agents[j]

        for s in range(num_series):
            series_idx += 1
            series_seed = base_seed + series_idx * 100

            # Fresh agents per series
            agent_a = _fresh_agent(agents[i], prompt_text, api_call, series_seed)
            agent_b = _fresh_agent(agents[j], prompt_text, api_call, series_seed)

            t_start = time.monotonic()
            winner, game_records = _run_blind_series(agent_a, agent_b, series_seed)
            elapsed = time.monotonic() - t_start

            if winner == name_a:
                bt_pairs.append((name_a, name_b))
            elif winner == name_b:
                bt_pairs.append((name_b, name_a))

            series_record = {
                "prompt": prompt_path,
                "agent_a": name_a,
                "agent_b": name_b,
                "winner": winner,
                "series_seed": series_seed,
                "games": game_records,
                "elapsed_s": round(elapsed, 2),
            }
            all_records.append(series_record)

            status = f"[{series_idx}/{total_series}]"
            print(
                f"  {status:>10}  {name_a:<22} vs {name_b:<22} "
                f"-> {winner:<25} ({len(game_records)} games, {elapsed:.1f}s)"
            )

    bt_results = compute_bt_scores(bt_pairs, n_bootstrap=1000, bootstrap_seed=42) if bt_pairs else []
    return bt_results, all_records


def _fresh_agent(
    agent_tuple: tuple[str, BaseAgent],
    prompt_text: str,
    api_call,
    seed: int,
) -> BaseAgent:
    name, original = agent_tuple
    if isinstance(original, RandomAgent):
        return RandomAgent(seed=seed)
    if isinstance(original, SmartAgent):
        return SmartAgent()
    if isinstance(original, PromptFileAgent):
        return PromptFileAgent(name, prompt_text, api_call)
    return original


# ---------------------------------------------------------------------------
# Kendall tau computation
# ---------------------------------------------------------------------------

def _compute_psi(
    rankings: dict[str, list[BTResult]],
) -> dict[str, Any]:
    """Compute pairwise Kendall τ between BT rankings from different prompts."""
    prompt_names = list(rankings.keys())
    if len(prompt_names) < 2:
        return {"error": "Need at least 2 prompt variants"}

    # Build agent → rank mapping for each prompt
    rank_maps: dict[str, dict[str, int]] = {}
    for pname, bt_list in rankings.items():
        rank_maps[pname] = {r.name: i for i, r in enumerate(bt_list)}

    # All agents across all prompts
    all_agents = sorted(set().union(*(rm.keys() for rm in rank_maps.values())))

    pairwise_taus: list[dict[str, Any]] = []
    tau_values: list[float] = []

    for i in range(len(prompt_names)):
        for j in range(i + 1, len(prompt_names)):
            p1, p2 = prompt_names[i], prompt_names[j]
            rm1, rm2 = rank_maps[p1], rank_maps[p2]

            # Align ranks for agents present in both
            common = [a for a in all_agents if a in rm1 and a in rm2]
            if len(common) < 2:
                continue

            ranks_1 = [rm1[a] for a in common]
            ranks_2 = [rm2[a] for a in common]

            tau, p_value = kendalltau(ranks_1, ranks_2)

            pairwise_taus.append({
                "prompt_a": p1,
                "prompt_b": p2,
                "kendall_tau": round(tau, 6),
                "p_value": round(p_value, 6),
                "n_agents": len(common),
            })
            tau_values.append(tau)

    mean_tau = sum(tau_values) / len(tau_values) if tau_values else 0.0
    # PSI = 1 - mean_tau (high tau = stable rankings = low PSI)
    psi = round(1.0 - mean_tau, 6)

    if psi < 0.15:
        label = "prompt-robust"
    elif psi <= 0.30:
        label = "moderate"
    else:
        label = "prompt-sensitive"

    return {
        "psi": psi,
        "label": label,
        "mean_kendall_tau": round(mean_tau, 6),
        "pairwise": pairwise_taus,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_psi(args: argparse.Namespace) -> None:
    prompt_paths = args.prompts
    num_series = args.series
    output_dir = Path(args.output_dir)
    dry_run = args.dry_run

    # Validate prompt files exist
    for p in prompt_paths:
        if not Path(p).exists():
            print(f"Error: prompt file not found: {p}", file=sys.stderr)
            sys.exit(1)

    # Resolve API call
    if dry_run:
        api_call = _dry_run_api_call
    else:
        provider = args.provider
        model = args.model
        env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "xai": "XAI_API_KEY",
        }
        api_key = args.api_key or os.environ.get(env_map.get(provider, ""), "")
        if not api_key:
            print(f"Error: No API key. Use --api-key or set {env_map.get(provider, 'UNKNOWN')}.", file=sys.stderr)
            sys.exit(1)
        from run_challenge import _build_api_callable
        api_call = _build_api_callable(provider, model, api_key)

    # Print header
    print("=" * 65)
    print("  MOREAU ARENA — PROMPT SENSITIVITY INDEX (PSI)")
    print("=" * 65)
    print(f"  Prompts:      {len(prompt_paths)}")
    for p in prompt_paths:
        h = hashlib.sha256(Path(p).read_bytes()).hexdigest()[:12]
        print(f"                {p}  (sha256: {h}…)")
    print(f"  Dry run:      {dry_run}")
    print(f"  Series/pair:  {num_series}")
    print(f"  Agents:       5 per prompt (3 LLM + 2 baseline)")
    print(f"  Output dir:   {output_dir}")
    print("=" * 65)

    # Run tournament for each prompt
    rankings: dict[str, list[BTResult]] = {}
    all_records: list[dict[str, Any]] = []

    for prompt_path in prompt_paths:
        prompt_text = Path(prompt_path).read_text(encoding="utf-8")
        label = Path(prompt_path).stem
        bt_results, records = _run_prompt_tournament(prompt_path, prompt_text, api_call, num_series)
        rankings[label] = bt_results
        all_records.extend(records)

        # Print per-prompt rankings
        if bt_results:
            print(f"\n  BT Rankings for {label}:")
            print(f"  {'Rank':<5} {'Agent':<25} {'BT Score':<10}")
            print("  " + "-" * 40)
            for i, r in enumerate(bt_results, 1):
                print(f"  {i:<5} {r.name:<25} {r.score:<10.4f}")

    # Compute PSI
    psi_result = _compute_psi(rankings)

    print(f"\n{'=' * 65}")
    print("  PSI RESULTS")
    print(f"{'=' * 65}")
    print(f"  PSI score:    {psi_result.get('psi', 'N/A')}")
    print(f"  Label:        {psi_result.get('label', 'N/A')}")
    print(f"  Mean τ:       {psi_result.get('mean_kendall_tau', 'N/A')}")
    for pw in psi_result.get("pairwise", []):
        print(f"  {pw['prompt_a']} ↔ {pw['prompt_b']}: τ={pw['kendall_tau']}, p={pw['p_value']}")
    print(f"{'=' * 65}")

    # Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"psi_{timestamp}.json"

    output_data = {
        "timestamp": timestamp,
        "dry_run": dry_run,
        "prompts": prompt_paths,
        "prompt_hashes": {
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in prompt_paths
        },
        "series_per_pair": num_series,
        "rankings": {
            label: [
                {"name": r.name, "score": r.score, "ci_lower": r.ci_lower, "ci_upper": r.ci_upper}
                for r in bt_list
            ]
            for label, bt_list in rankings.items()
        },
        "psi": psi_result,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  Results saved to: {output_path}")

    # Also save raw series data as JSONL
    jsonl_path = output_dir / f"psi_series_{timestamp}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, default=str) + "\n")
    print(f"  Series data:  {jsonl_path}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prompt Sensitivity Index — Kendall τ across paraphrased prompts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "PSI thresholds:\n"
            "  < 0.15   prompt-robust\n"
            "  0.15–0.30  moderate\n"
            "  > 0.30   prompt-sensitive\n"
            "\n"
            "Examples:\n"
            "  python run_psi.py --dry-run\n"
            "  python run_psi.py --prompts prompts/t002_prompt.txt prompts/t002_v2.txt prompts/t002_v3.txt --dry-run\n"
        ),
    )
    parser.add_argument(
        "--prompts",
        nargs="+",
        default=_DEFAULT_PROMPTS,
        help="Prompt files to compare (default: 3 T002 variants)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "google", "xai"],
        help="API provider (default: openai, only for real runs)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="test",
        help="Model identifier (default: test)",
    )
    parser.add_argument(
        "--series",
        type=int,
        default=10,
        help="Series per pair per prompt (default: 10)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (or set env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use random builds instead of real API calls",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Output directory (default: results/)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        run_psi(args)
    except KeyboardInterrupt:
        print("\nPSI interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
