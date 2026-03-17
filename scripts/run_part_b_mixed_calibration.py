from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from part_b_state import (
    PART_B_SEASON_CURRENT_ID,
    append_part_b_event,
    create_part_b_run,
    enqueue_part_b_action,
    part_b_calibration_report,
    part_b_leaderboards,
    part_b_run_report,
    process_part_b_ticks,
    run_part_b_baseline,
)


def _projection(name: str, animal: str) -> dict:
    return {
        "name": name,
        "animal": animal,
        "health_pct": 88,
        "morale_pct": 82,
        "happiness_pct": 78,
        "energy_pct": 84,
        "mutation_count": 0,
        "arena_available": True,
        "cave_available": True,
        "arena_recent_record": "none",
        "recent_fight_summary": "none",
        "recent_cave_summary": "none",
    }


def seed_manual_run() -> str:
    run = create_part_b_run(
        {
            "season_id": PART_B_SEASON_CURRENT_ID,
            "run_class": "manual",
            "subject_pet_name": "Manual Trace",
            "subject_pet_animal": "fox",
            "state_projection": _projection("Manual Trace", "fox"),
            "metadata": {"generated_by": "run_part_b_mixed_calibration.py", "trace_kind": "manual-seed"},
        }
    )
    append_part_b_event(
        run["id"],
        {
            "actor_type": "manual",
            "event_type": "action_applied",
            "action_verb": "CARE",
            "zone": "arena",
            "world_tick": 1,
            "expected_state_revision": 0,
            "outcome": {"welfare_delta": 10},
            "state_after": {"health_pct": 96, "morale_pct": 90, "happiness_pct": 89, "energy_pct": 88},
        },
    )
    append_part_b_event(
        run["id"],
        {
            "actor_type": "manual",
            "event_type": "action_applied",
            "action_verb": "ENTER_ARENA",
            "zone": "arena",
            "world_tick": 2,
            "expected_state_revision": 1,
            "outcome": {"result": "win", "reward": 12, "xp_gain": 20},
            "state_after": {"health_pct": 88, "morale_pct": 96, "happiness_pct": 92, "energy_pct": 72, "arena_recent_record": "W"},
        },
    )
    return run["id"]


def seed_operator_assisted_run() -> str:
    run = create_part_b_run(
        {
            "season_id": PART_B_SEASON_CURRENT_ID,
            "run_class": "operator-assisted",
            "subject_pet_name": "Operator Trace",
            "subject_pet_animal": "wolf",
            "state_projection": _projection("Operator Trace", "wolf"),
            "metadata": {"generated_by": "run_part_b_mixed_calibration.py", "trace_kind": "operator-seed"},
        }
    )
    enqueue_part_b_action(run["id"], {"action_verb": "CARE", "actor_type": "operator"})
    enqueue_part_b_action(run["id"], {"action_verb": "ENTER_CAVE", "actor_type": "operator"})
    enqueue_part_b_action(run["id"], {"action_verb": "EXTRACT", "actor_type": "operator"})
    process_part_b_ticks(run["id"], count=3)
    return run["id"]


def seed_agent_only_run() -> str:
    run = create_part_b_run(
        {
            "season_id": PART_B_SEASON_CURRENT_ID,
            "run_class": "agent-only",
            "subject_pet_name": "Agent Trace",
            "subject_pet_animal": "panther",
            "state_projection": _projection("Agent Trace", "panther"),
            "metadata": {"generated_by": "run_part_b_mixed_calibration.py", "trace_kind": "agent-seed"},
        }
    )
    run_part_b_baseline(run["id"], "expedition-max", ticks=6)
    return run["id"]


def build_payload() -> dict:
    run_ids = [seed_manual_run(), seed_operator_assisted_run(), seed_agent_only_run()]
    return {
        "season_id": PART_B_SEASON_CURRENT_ID,
        "run_ids": run_ids,
        "reports": {run_id: part_b_run_report(run_id) for run_id in run_ids},
        "leaderboards": part_b_leaderboards(PART_B_SEASON_CURRENT_ID, limit=5),
        "calibration": part_b_calibration_report(PART_B_SEASON_CURRENT_ID),
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Part B Mixed Calibration",
        "",
        f"- Season: `{payload['season_id']}`",
        f"- Runs seeded: `{len(payload['run_ids'])}`",
        "",
        "## Run Classes",
        "",
    ]
    for run_id, report in payload["reports"].items():
        lines.extend(
            [
                f"- `{report['run_class']}` · `{report['state_projection'].get('name', run_id[:8])}` · welfare `{report['scores']['welfare']}` · combat `{report['scores']['combat']}` · expedition `{report['scores']['expedition']}`",
            ]
        )
    lines.extend(["", "## Calibration Warnings", "", f"- `{', '.join(payload['calibration']['warnings']) if payload['calibration']['warnings'] else 'none'}`", ""])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed mixed run-class Part B traces for live-like calibration.")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
