from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from part_b_state import PART_B_BASELINE_POLICIES, PART_B_SEASON_CURRENT_ID, create_part_b_run, part_b_run_report, run_part_b_baseline


def _initial_projection(name: str, animal: str, level: int) -> dict[str, Any]:
    return {
        "name": name,
        "animal": animal,
        "level": level,
        "xp": level * 10,
        "health_pct": 88,
        "morale_pct": 81,
        "happiness_pct": 76,
        "energy_pct": 84,
        "mutation_count": 0,
        "recent_fight_summary": "none",
        "recent_cave_summary": "none",
        "last_action": "START",
        "last_action_outcome": "baseline created",
        "neglect_ticks": 0,
        "days_survived": 0,
        "arena_available": True,
        "arena_tickets": 1,
        "arena_recent_record": "none",
        "arena_reward_preview": 12,
        "arena_loss_streak": 0,
        "cave_available": True,
        "cave_depth_last_run": 0,
        "cave_extract_value_last_run": 0,
        "cave_injury_last_run": 0,
        "cave_reward_preview": 18,
        "in_cave": False,
        "current_cave_depth": 0,
        "current_cave_value": 0,
        "current_cave_risk": 0,
        "idle_ticks": 0,
        "critical_state_ticks": 0,
        "care_like_ticks": 0,
        "total_ticks": 0,
    }


def run_baselines(ticks: int, policies: list[str]) -> dict[str, Any]:
    animals = ["fox", "wolf", "bear", "monkey", "raven"]
    results: list[dict[str, Any]] = []
    for index, policy in enumerate(policies):
        run = create_part_b_run(
            {
                "season_id": PART_B_SEASON_CURRENT_ID,
                "run_class": "agent-only",
                "subject_pet_name": f"{policy.title()} Baseline",
                "subject_pet_animal": animals[index % len(animals)],
                "state_projection": _initial_projection(f"{policy.title()} Baseline", animals[index % len(animals)], index + 1),
                "metadata": {
                    "baseline_policy": policy,
                    "generated_by": "scripts/run_part_b_baselines.py",
                },
            }
        )
        run_part_b_baseline(run["id"], policy, ticks=ticks)
        report = part_b_run_report(run["id"])
        results.append({"run": run, "report": report})
    return {"season_id": PART_B_SEASON_CURRENT_ID, "ticks": ticks, "policies": policies, "results": results}


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Part B Baseline Run",
        "",
        f"- Season: `{payload['season_id']}`",
        f"- Ticks per baseline: `{payload['ticks']}`",
        f"- Policies: `{', '.join(payload['policies'])}`",
        "",
        "| Policy | Welfare | Combat | Expedition | Tick | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in payload["results"]:
        report = item["report"] or {}
        scores = report.get("scores") or {}
        policy = (item["run"].get("metadata") or {}).get("baseline_policy", "unknown")
        lines.append(
            f"| `{policy}` | {scores.get('welfare', 0)} | {scores.get('combat', 0)} | {scores.get('expedition', 0)} | {report.get('world_tick', 0)} | {report.get('status', 'unknown')} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Part B baseline policies for the active ecological season.")
    parser.add_argument("--ticks", type=int, default=12, help="Number of ticks per baseline run.")
    parser.add_argument(
        "--policies",
        default="conservative,greedy,random",
        help="Comma-separated baseline policies to execute.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional output path (.md or .json).")
    args = parser.parse_args()

    policies = [item.strip().lower() for item in args.policies.split(",") if item.strip()]
    invalid = [policy for policy in policies if policy not in PART_B_BASELINE_POLICIES]
    if invalid:
        raise SystemExit(f"Unknown baseline policies: {', '.join(invalid)}")

    payload = run_baselines(args.ticks, policies)
    output_text = render_markdown(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.suffix.lower() == ".json":
            args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
