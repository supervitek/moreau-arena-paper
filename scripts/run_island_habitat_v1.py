from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from island_habitat import (
    DEFAULT_CARRY_LIMIT,
    DEFAULT_MAX_CYCLES,
    FreshHeuristicAgent,
    PersistentScoutAgent,
    RandomAgent,
    evaluate_agents,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Island Habitat v1 baseline sweep.")
    parser.add_argument("--cycles", type=int, default=DEFAULT_MAX_CYCLES, help="Max cycles per run")
    parser.add_argument("--carry-limit", type=int, default=DEFAULT_CARRY_LIMIT, help="Carry-forward byte limit")
    parser.add_argument("--seeds", type=int, default=5, help="Number of seeds to sweep from 0..N-1")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results") / "island_habitat_v1",
        help="Directory for logs and summary",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    agents = [
        RandomAgent(seed=101),
        FreshHeuristicAgent(),
        PersistentScoutAgent(),
    ]
    seeds = list(range(args.seeds))
    results = evaluate_agents(
        agents,
        seeds=seeds,
        max_cycles=args.cycles,
        carry_limit=args.carry_limit,
        output_dir=output_dir,
    )

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("Island Habitat v1 baseline sweep")
    print(f"Output: {output_dir}")
    print("")
    for name, metrics in results.items():
        print(
            f"{name:18} "
            f"mean_cycles={metrics['mean_cycles']:>5} "
            f"death_rate={metrics['death_rate']:.2f} "
            f"diversity={metrics['mean_action_diversity']:.3f} "
            f"carry={metrics['mean_carry_bytes']:.1f}"
        )


if __name__ == "__main__":
    main()
