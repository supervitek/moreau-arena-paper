#!/usr/bin/env python3
"""Season patch generator for Moreau Arena.

Reads tournament results, computes per-animal win-rate EMA,
and proposes proc_rate adjustments to rebalance outliers.

Usage:
    python seasons/patch_generator.py --input data/tournament_002/results.jsonl --dry-run
    python seasons/patch_generator.py --input data/tournament_002/results.jsonl --output seasons/season_1_patch.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------- constants ----------

ALPHA = 0.15          # EMA smoothing factor
BETA = 0.03           # max proc-rate change per season
TARGET_WR = 0.50      # ideal win rate
UPPER_BOUND = 0.55    # animals above this are nerfed
LOWER_BOUND = 0.45    # animals below this are buffed
PROC_FLOOR = 0.025    # minimum allowed proc rate
PROC_CEILING = 0.055  # maximum allowed proc rate

BASE_CONFIG_PATH = Path(__file__).resolve().parent / "season_0_base.json"


# ---------- helpers ----------

def load_base_config() -> dict:
    """Load the frozen base config (season 0)."""
    with open(BASE_CONFIG_PATH) as f:
        return json.load(f)


def parse_results(results_path: Path) -> list[dict]:
    """Parse JSONL results into a list of series dicts."""
    series_list: list[dict] = []
    with open(results_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            series_list.append(json.loads(line))
    return series_list


def compute_raw_win_rates(series_list: list[dict]) -> dict[str, float]:
    """Compute raw per-animal win rate from game-level results.

    Each game contributes one win and one loss to the relevant animals.
    """
    wins: dict[str, int] = defaultdict(int)
    games: dict[str, int] = defaultdict(int)

    for series in series_list:
        agent_a = series["agent_a"]
        agent_b = series["agent_b"]

        for game in series.get("games", []):
            animal_a = game["build_a"]["animal"].lower()
            animal_b = game["build_b"]["animal"].lower()

            games[animal_a] += 1
            games[animal_b] += 1

            winner = game["winner"]
            if winner == agent_a:
                wins[animal_a] += 1
            elif winner == agent_b:
                wins[animal_b] += 1

    rates: dict[str, float] = {}
    for animal in sorted(games):
        if games[animal] > 0:
            rates[animal] = wins[animal] / games[animal]
    return rates


def apply_ema(
    raw_rates: dict[str, float],
    alpha: float = ALPHA,
) -> dict[str, float]:
    """Apply EMA smoothing to raw win rates.

    EMA = alpha * observed + (1 - alpha) * prior
    Prior defaults to TARGET_WR (0.50) for the first observation.
    """
    smoothed: dict[str, float] = {}
    for animal, observed in raw_rates.items():
        prior = TARGET_WR
        smoothed[animal] = alpha * observed + (1.0 - alpha) * prior
    return smoothed


def propose_proc_rate_adjustments(
    ema_rates: dict[str, float],
    base_config: dict,
    beta: float = BETA,
) -> dict[str, dict]:
    """Propose proc_rate adjustments for outlier animals.

    - WR > 0.55: decrease proc rates by beta (not below PROC_FLOOR)
    - WR < 0.45: increase proc rates by beta (not above PROC_CEILING)
    - Animals within [0.45, 0.55] are untouched.

    Returns a patch dict containing only modified proc rates:
        {animal_name: {ability_name: new_proc_rate, ...}, ...}
    """
    animals_cfg = base_config.get("animals", {})
    patch: dict[str, dict] = {}

    for animal_name, ema_wr in ema_rates.items():
        animal_cfg = animals_cfg.get(animal_name)
        if animal_cfg is None:
            continue

        if ema_wr > UPPER_BOUND:
            delta = -beta
        elif ema_wr < LOWER_BOUND:
            delta = +beta
        else:
            continue

        ability_changes: dict[str, float] = {}
        for ability in animal_cfg.get("abilities", []):
            old_rate = ability["proc_chance"]
            new_rate = old_rate + delta
            new_rate = max(PROC_FLOOR, min(PROC_CEILING, new_rate))
            if new_rate != old_rate:
                ability_changes[ability["name"]] = round(new_rate, 4)

        if ability_changes:
            patch[animal_name] = {
                "ema_win_rate": round(ema_wr, 4),
                "proc_rate_changes": ability_changes,
            }

    return patch


def build_season_patch(
    adjustments: dict[str, dict],
    base_config: dict,
) -> dict:
    """Build a season patch JSON containing only the changed proc rates.

    The patch is a minimal dict that can be overlaid onto the base config.
    """
    patch: dict = {
        "meta": {
            "description": "Season patch -- proc_rate adjustments only",
            "base_version": base_config["meta"]["version"],
            "parameters": {
                "ema_alpha": ALPHA,
                "adjustment_beta": BETA,
                "upper_bound": UPPER_BOUND,
                "lower_bound": LOWER_BOUND,
                "proc_rate_floor": PROC_FLOOR,
                "proc_rate_ceiling": PROC_CEILING,
            },
        },
        "animals": {},
    }

    for animal_name, adj in sorted(adjustments.items()):
        abilities: list[dict] = []
        for ability_name, new_rate in adj["proc_rate_changes"].items():
            abilities.append({
                "name": ability_name,
                "proc_chance": new_rate,
            })
        patch["animals"][animal_name] = {
            "ema_win_rate": adj["ema_win_rate"],
            "abilities": abilities,
        }

    return patch


# ---------- main ----------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate season balance patch from tournament results",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to JSONL results file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposed adjustments without writing a patch file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for season patch JSON (required unless --dry-run)",
    )
    args = parser.parse_args(argv)

    if not args.dry_run and args.output is None:
        parser.error("--output is required when not using --dry-run")

    # Load base config
    base_config = load_base_config()

    # Parse results and compute win rates
    series_list = parse_results(args.input)
    raw_rates = compute_raw_win_rates(series_list)
    ema_rates = apply_ema(raw_rates, alpha=ALPHA)

    # Propose adjustments
    adjustments = propose_proc_rate_adjustments(ema_rates, base_config, beta=BETA)

    # Display results
    print("=== Per-Animal Win Rates (EMA smoothed) ===")
    for animal, wr in sorted(ema_rates.items(), key=lambda x: -x[1]):
        if wr > UPPER_BOUND:
            marker = "NERF"
        elif wr < LOWER_BOUND:
            marker = "BUFF"
        else:
            marker = "OK"
        print(f"  {animal:12s}  WR={wr:.4f}  [{marker}]")

    print()
    print("=== Proposed Proc Rate Adjustments ===")
    if not adjustments:
        print("  (no adjustments needed -- all animals within bounds)")
    for animal_name, adj in sorted(adjustments.items()):
        print(f"  {animal_name}  (EMA WR={adj['ema_win_rate']:.4f}):")
        for ability_name, new_rate in adj["proc_rate_changes"].items():
            print(f"    {ability_name}: -> {new_rate:.4f}")

    if args.dry_run:
        print("\n[dry-run] No patch file written.")
        return

    # Write patch
    patch = build_season_patch(adjustments, base_config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(patch, f, indent=2)
        f.write("\n")
    print(f"\nPatch written to {args.output}")


if __name__ == "__main__":
    main()
