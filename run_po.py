#!/usr/bin/env python3
"""Moreau Arena -- Partial Observability Suite (Task 3.2).

Runs an adaptive best-of-7 series with configurable fog levels that
control how much information the loser receives about the winner's build
when re-picking:

  fog=0.0  Full info   -- opponent's animal + full stat allocation (standard T002)
  fog=0.5  Partial     -- opponent's animal name only, no stats
  fog=1.0  No info     -- nothing revealed about the opponent

Usage:
    # Dry-run (random builds, no API calls):
    python run_po.py --fog 0.5 --series 3 --dry-run

    # All fog levels:
    python run_po.py --fog 0.0 --series 10 --dry-run
    python run_po.py --fog 0.5 --series 10 --dry-run
    python run_po.py --fog 1.0 --series 10 --dry-run

    # Real run:
    python run_po.py --fog 0.5 --series 10 --provider anthropic --model claude-sonnet-4-20250514
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
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
from agents.llm_agent_v2 import LLMAgentV2
from analysis.bt_ranking import BTResult, compute_bt_scores
from prompts.meta_extractor import extract_top_builds
from run_challenge import (
    _build_api_callable,
    _build_to_dict,
    _create_creature,
    _dry_run_api_call_v2,
    _random_build_dict,
    _run_single_game,
    _BASELINES,
    _ENV_KEY_MAP,
    _ORIGINAL_ANIMALS,
    PAPER_BT_T002,
)
from simulator.engine import CombatResult


# ---------------------------------------------------------------------------
# Fog-aware adaptive series
# ---------------------------------------------------------------------------

def _run_adaptive_series_fog(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
    fog: float,
) -> tuple[str, list[dict[str, Any]]]:
    """Adaptive best-of-7 with fog-filtered opponent information.

    The fog level controls what the loser sees when re-picking:
      fog=0.0: opponent_animal is set, opponent_reveal = full build (standard)
      fog=0.5: opponent_animal is set, opponent_reveal = None
      fog=1.0: opponent_animal = None, opponent_reveal = None
    """
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    # Initial picks -- blind (no info either way)
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
            # B lost -- B gets to re-pick with fog-filtered info about A
            opp_animal, opp_reveal = _apply_fog(build_a, fog)
            try:
                build_b = agent_b.choose_build(
                    opponent_animal=opp_animal,
                    banned=[],
                    opponent_reveal=opp_reveal,
                )
            except Exception:
                pass  # keep existing build on failure
        elif result.winner == "b":
            wins_b += 1
            # A lost -- A gets to re-pick with fog-filtered info about B
            opp_animal, opp_reveal = _apply_fog(build_b, fog)
            try:
                build_a = agent_a.choose_build(
                    opponent_animal=opp_animal,
                    banned=[],
                    opponent_reveal=opp_reveal,
                )
            except Exception:
                pass
        # draw: both keep their builds

    if wins_a > wins_b:
        return name_a, game_records
    elif wins_b > wins_a:
        return name_b, game_records
    return "draw", game_records


def _apply_fog(
    winner_build: Build,
    fog: float,
) -> tuple[Any, Build | None]:
    """Apply fog filtering to the winner's build before revealing to the loser.

    Returns (opponent_animal, opponent_reveal) tuple.
    """
    if fog <= 0.0:
        # Full info: animal + full stats
        return winner_build.animal, winner_build
    elif fog < 1.0:
        # Partial: animal only, no stats
        return winner_build.animal, None
    else:
        # No info at all
        return None, None


# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

def _print_pairwise_results(
    challenger_name: str,
    results_by_baseline: dict[str, dict[str, int]],
    fog: float,
) -> None:
    """Print pairwise series results table."""
    print("\n" + "=" * 65)
    print(f"  Partial Observability Results  (fog={fog})")
    print("=" * 65)
    print(f"  {'Baseline':<25} {'Series Won':>10} {'Series Lost':>11} {'WR':>8}")
    print("-" * 65)

    total_won = 0
    total_lost = 0
    total_draws = 0

    for baseline_name in [name for name, _ in _BASELINES]:
        counts = results_by_baseline.get(
            baseline_name, {"won": 0, "lost": 0, "draw": 0}
        )
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


def _print_bt_results(
    challenger_name: str,
    bt_results: list[BTResult],
) -> None:
    """Print BT ranking."""
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


# ---------------------------------------------------------------------------
# JSONL output
# ---------------------------------------------------------------------------

def _save_results_jsonl(
    output_dir: Path,
    challenger_name: str,
    fog: float,
    series_records: list[dict[str, Any]],
) -> Path:
    """Save all series results to a JSONL file. Returns the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = challenger_name.replace("/", "_").replace(" ", "_")
    fog_str = f"{fog:.1f}".replace(".", "")
    filename = f"po_fog{fog_str}_{safe_name}_{timestamp}.jsonl"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        for record in series_records:
            f.write(json.dumps(record, default=str) + "\n")

    return output_path


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_po(args: argparse.Namespace) -> None:
    """Execute the partial observability challenge run."""
    provider = args.provider
    model = args.model
    fog = args.fog
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

    # Load meta builds for prompt
    meta_builds: list[dict] = []
    t001_results_path = Path(__file__).parent / "data" / "tournament_001" / "results.jsonl"
    if t001_results_path.exists():
        meta_builds = extract_top_builds(t001_results_path, top_n=5)

    # Build the api_call callable
    if dry_run:
        api_call = _dry_run_api_call_v2
        challenger_name = f"DryRun-{model or 'test'}"
    else:
        api_call = _build_api_callable(provider, model, api_key)
        challenger_name = model

    # Fog level description
    fog_labels = {0.0: "Full info (standard T002)", 0.5: "Partial (animal only)", 1.0: "No info (blind)"}
    fog_label = fog_labels.get(fog, f"Custom fog={fog}")

    # Print header
    print("=" * 65)
    print("  MOREAU ARENA -- PARTIAL OBSERVABILITY SUITE")
    print("=" * 65)
    if not dry_run:
        print(f"  Provider:     {provider}")
        print(f"  Model:        {model}")
    else:
        print(f"  Mode:         Dry Run (random builds)")
    print(f"  Fog level:    {fog} -- {fog_label}")
    print(f"  Series/base:  {num_series}")
    print(f"  Baselines:    {len(_BASELINES)}")
    if meta_builds:
        print(f"  Meta builds:  {len(meta_builds)} loaded from T001")
    print("=" * 65)
    print()

    # Run series against each baseline
    results_by_baseline: dict[str, dict[str, int]] = {}
    all_bt_pairs: list[tuple[str, str]] = []
    all_series_records: list[dict[str, Any]] = []
    base_seed = 200_000  # different seed range from run_challenge
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

            # Create LLM agent fresh each series
            challenger_agent: BaseAgent = LLMAgentV2(
                name=challenger_name,
                api_call=api_call,
                meta_builds=meta_builds,
            )

            t_start = time.monotonic()
            winner, game_records = _run_adaptive_series_fog(
                challenger_agent, baseline_agent, series_seed, fog
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
                "protocol": "t002-po",
                "fog": fog,
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
    _print_pairwise_results(challenger_name, results_by_baseline, fog)

    # Compute and display BT scores
    if all_bt_pairs:
        bt_results = compute_bt_scores(
            all_bt_pairs, n_bootstrap=1000, bootstrap_seed=42
        )
        _print_bt_results(challenger_name, bt_results)
    else:
        print("\n  No decisive series results -- cannot compute BT scores.")

    # Save JSONL
    output_path = _save_results_jsonl(
        output_dir, challenger_name, fog, all_series_records
    )
    print(f"\nResults saved to: {output_path}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        description="Moreau Arena -- Partial Observability Suite (fog levels).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_po.py --fog 0.0 --series 3 --dry-run\n"
            "  python run_po.py --fog 0.5 --series 3 --dry-run\n"
            "  python run_po.py --fog 1.0 --series 3 --dry-run\n"
            "  python run_po.py --fog 0.5 --series 10 --provider anthropic "
            "--model claude-sonnet-4-20250514\n"
        ),
    )

    parser.add_argument(
        "--fog",
        type=float,
        required=True,
        help="Fog level: 0.0 (full info), 0.5 (animal only), 1.0 (no info)",
    )
    parser.add_argument(
        "--series",
        type=int,
        default=10,
        help="Number of best-of-7 series per baseline (default: 10)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "google", "xai"],
        help="API provider (default: openai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model identifier string (e.g. gpt-4o, claude-sonnet-4-20250514)",
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

    # Validate: non-dry-run requires model
    if not args.dry_run and not args.model:
        parser.error("--model is required when not using --dry-run")

    try:
        run_po(args)
    except KeyboardInterrupt:
        print("\nRun interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
