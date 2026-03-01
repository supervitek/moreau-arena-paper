"""Season patch generator for Moreau Arena.

Reads tournament JSONL results, computes per-animal win-rate EMA (alpha=0.15),
and proposes beta=0.03 proc-rate adjustments for the next season patch.

Usage:
    python -m seasons.patch_generator \
        --results data/tournament_002/results.jsonl \
        --base seasons/season_0_base.json \
        --out seasons/season_1_patch.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_ALPHA = 0.15
DEFAULT_BETA = 0.03
TARGET_WR = 0.50
PROC_FLOOR = 0.025
PROC_CEILING = 0.055


def compute_win_rates(results_path: Path) -> dict[str, float]:
    """Compute per-animal win rate from JSONL tournament results."""
    wins: dict[str, int] = defaultdict(int)
    games: dict[str, int] = defaultdict(int)

    with open(results_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            series = json.loads(line)
            for game in series.get("games", []):
                animal_a = game["build_a"]["animal"].lower()
                animal_b = game["build_b"]["animal"].lower()
                winner = game["winner"]

                games[animal_a] += 1
                games[animal_b] += 1

                if winner == series["agent_a"]:
                    wins[animal_a] += 1
                elif winner == series["agent_b"]:
                    wins[animal_b] += 1

    rates: dict[str, float] = {}
    for animal in games:
        if games[animal] > 0:
            rates[animal] = wins[animal] / games[animal]
    return rates


def ema_smooth(
    raw_rates: dict[str, float],
    prior: dict[str, float] | None = None,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, float]:
    """Apply EMA smoothing to win rates.

    EMA_new = alpha * observed + (1 - alpha) * prior
    If no prior exists, uses TARGET_WR (0.50) as initial value.
    """
    smoothed: dict[str, float] = {}
    for animal, observed in raw_rates.items():
        prev = prior.get(animal, TARGET_WR) if prior else TARGET_WR
        smoothed[animal] = alpha * observed + (1.0 - alpha) * prev
    return smoothed


def propose_adjustments(
    ema_rates: dict[str, float],
    base_config: dict,
    beta: float = DEFAULT_BETA,
) -> dict[str, dict]:
    """Propose proc-rate adjustments based on EMA win rates.

    Animals above TARGET_WR get proc rates reduced by beta.
    Animals below TARGET_WR get proc rates increased by beta.
    Adjustments are clamped to [PROC_FLOOR, PROC_CEILING].

    Returns dict of {animal: {ability_name: new_proc_rate, ...}}.
    """
    animals = base_config.get("animals", {})
    adjustments: dict[str, dict] = {}

    for animal_name, ema_wr in ema_rates.items():
        animal_cfg = animals.get(animal_name)
        if animal_cfg is None:
            continue

        deviation = ema_wr - TARGET_WR
        if abs(deviation) < 0.01:
            continue

        direction = -1.0 if deviation > 0 else 1.0
        delta = direction * beta

        ability_changes: dict[str, float] = {}
        for ability in animal_cfg.get("abilities", []):
            old_rate = ability["proc_chance"]
            new_rate = max(PROC_FLOOR, min(PROC_CEILING, old_rate + delta))
            if new_rate != old_rate:
                ability_changes[ability["name"]] = round(new_rate, 4)

        if ability_changes:
            adjustments[animal_name] = {
                "ema_wr": round(ema_wr, 4),
                "deviation": round(deviation, 4),
                "ability_adjustments": ability_changes,
            }

    return adjustments


def generate_patch(
    base_config: dict,
    adjustments: dict[str, dict],
    season: int,
) -> dict:
    """Apply adjustments to base config, producing a season patch config."""
    patch = copy.deepcopy(base_config)

    patch["meta"]["version"] = f"MOREAU_SEASON_{season}"
    patch["meta"]["description"] = (
        f"Season {season} balance patch — proc-rate adjustments from EMA win rates"
    )
    patch["meta"]["base_version"] = "MOREAU_CORE_v1"
    patch["meta"]["season"] = season

    for animal_name, adj in adjustments.items():
        animal_cfg = patch["animals"].get(animal_name)
        if animal_cfg is None:
            continue
        for ability in animal_cfg["abilities"]:
            new_rate = adj["ability_adjustments"].get(ability["name"])
            if new_rate is not None:
                ability["proc_chance"] = new_rate

    # Recalculate hash for patched config
    patch.pop("sha256", None)

    return patch


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate season balance patch")
    parser.add_argument(
        "--results", required=True, type=Path, help="Path to JSONL results file"
    )
    parser.add_argument(
        "--base", required=True, type=Path, help="Path to base config (season_0_base.json)"
    )
    parser.add_argument(
        "--out", required=True, type=Path, help="Output path for patch config"
    )
    parser.add_argument(
        "--alpha", type=float, default=DEFAULT_ALPHA, help="EMA smoothing factor"
    )
    parser.add_argument(
        "--beta", type=float, default=DEFAULT_BETA, help="Max proc-rate adjustment"
    )
    parser.add_argument(
        "--season", type=int, default=1, help="Season number for the patch"
    )
    args = parser.parse_args(argv)

    with open(args.base) as f:
        base_config = json.load(f)

    raw_rates = compute_win_rates(args.results)
    ema_rates = ema_smooth(raw_rates, alpha=args.alpha)
    adjustments = propose_adjustments(ema_rates, base_config, beta=args.beta)

    print("=== Win Rate EMA ===")
    for animal, wr in sorted(ema_rates.items(), key=lambda x: -x[1]):
        marker = "▲" if wr > TARGET_WR + 0.01 else ("▼" if wr < TARGET_WR - 0.01 else "=")
        print(f"  {animal:12s}  {wr:.3f}  {marker}")

    print("\n=== Proposed Adjustments ===")
    if not adjustments:
        print("  (none — all animals within tolerance)")
    for animal, adj in sorted(adjustments.items()):
        print(f"  {animal}: deviation={adj['deviation']:+.3f}")
        for ability, new_rate in adj["ability_adjustments"].items():
            print(f"    {ability}: -> {new_rate}")

    patch = generate_patch(base_config, adjustments, args.season)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(patch, f, indent=2)
    print(f"\nPatch written to {args.out}")


if __name__ == "__main__":
    main()
