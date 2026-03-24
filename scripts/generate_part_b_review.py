from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from part_b_state import PART_B_SEASON_CURRENT_ID, export_part_b_season_archive, part_b_calibration_report


def build_review(season_id: str) -> str:
    archive = export_part_b_season_archive(season_id)
    calibration = part_b_calibration_report(season_id)
    boards = archive["leaderboards"]
    counts = boards["counts"]
    trace_summary = archive.get("trace_summary") or {}
    lines = [
        "# Part B Weekly Review",
        "",
        f"- Season: `{archive['season']['season_id']}`",
        f"- Name: {archive['season']['name']}",
        f"- Total runs: `{counts['total_runs']}`",
        f"- Eligible runs: `{counts['eligible_runs']}`",
        f"- Watch runs: `{trace_summary.get('watch_runs', 0)}`",
        f"- Completed watches: `{trace_summary.get('completed_watches', 0)}`",
        "",
        "## Top Signals",
    ]
    for family in ("welfare", "combat", "expedition"):
        top = boards["families"].get(family) or []
        if not top:
            lines.extend([f"### {family.title()}", "", "- No eligible runs yet.", ""])
            continue
        leader = top[0]
        lines.extend(
            [
                f"### {family.title()}",
                "",
                f"- Leader: `{leader['subject_pet_name']}`",
                f"- Run class: `{leader['run_class']}`",
                f"- Score: `{leader['scores'][family]}`",
                f"- World tick: `{leader['world_tick']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Guardrails",
            "",
            f"- Composite headline enabled: `{archive['season']['composite_headline_enabled']}`",
            f"- House agent allowed in benchmark: `{archive['season']['house_agent_benchmark_allowed']}`",
            f"- Rule: {archive['season']['house_agent_benchmark_rule']}",
            "",
        ]
    )
    cadence = archive.get("review_cadence") or {}
    if cadence:
        lines.extend(["## Review Cadence", ""])
        for label in ("daily", "midweek", "weekly"):
            items = cadence.get(label) or []
            if not items:
                continue
            lines.extend([f"### {label.title()}", ""])
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
    lines.extend(
        [
            "## Calibration",
            "",
            f"- Warnings: `{', '.join(calibration['warnings']) if calibration['warnings'] else 'none'}`",
            "",
            "## Continue / Pivot / Kill",
            "",
            "- Continue if welfare does not collapse into pure idling and at least one run class produces differentiated family scores.",
            "- Pivot if one family score dominates every top run regardless of action mix.",
            "- Kill if operator fantasy becomes decorative and all interesting results come only from hidden house-agent behavior.",
            "",
        ]
    )
    by_run_class = trace_summary.get("by_run_class") or {}
    if by_run_class:
        lines.extend(["## Operator Traces", ""])
        for run_class in ("manual", "operator-assisted", "agent-only"):
            payload = by_run_class.get(run_class) or {}
            if not payload.get("runs"):
                continue
            means = payload.get("mean_scores") or {}
            lines.append(
                f"- `{run_class}`: runs `{payload.get('runs', 0)}`, welfare `{means.get('welfare', 0)}`, combat `{means.get('combat', 0)}`, expedition `{means.get('expedition', 0)}`, avg tick span `{payload.get('mean_tick_span', 0)}`, avg credits used `{payload.get('mean_credits_used', 0)}`"
            )
            if payload.get("action_digest"):
                lines.append(f"  Top actions: {payload['action_digest']}")
            primary_lanes = payload.get("primary_lanes") or {}
            if primary_lanes:
                lines.append(f"  Primary lanes: {', '.join(f'{k}={v}' for k, v in sorted(primary_lanes.items()))}")
            return_postures = payload.get("return_postures") or {}
            if return_postures:
                lines.append(f"  Return postures: {', '.join(f'{k}={v}' for k, v in sorted(return_postures.items()))}")
        lines.append("")
    recent_traces = trace_summary.get("recent_operator_traces") or []
    if recent_traces:
        lines.extend(["## Recent Highlights", ""])
        for entry in recent_traces[:5]:
            scores = entry.get("scores") or {}
            lines.append(
                f"- `{entry.get('subject_pet_name', 'Unnamed')}` [{entry.get('run_class', 'unknown')}] `{entry.get('priority_profile', 'balanced')}` / `{entry.get('risk_appetite', 'measured')}` -> {entry.get('headline', 'No headline')} Score `{scores.get('welfare', 0)}/{scores.get('combat', 0)}/{scores.get('expedition', 0)}`"
            )
            if entry.get("status_line"):
                lines.append(f"  {entry['status_line']}")
        lines.append("")
    if calibration["policy_summary"]:
        lines.extend(["## Policy Summary", ""])
        for policy, payload in sorted(calibration["policy_summary"].items()):
            means = payload["mean_scores"]
            lines.append(
                f"- `{policy}`: welfare `{means['welfare']}`, combat `{means['combat']}`, expedition `{means['expedition']}`, runs `{payload['runs']}`"
            )
        lines.append("")
    if calibration.get("priority_summary"):
        lines.extend(["## Standing Orders", ""])
        for priority, payload in sorted(calibration["priority_summary"].items()):
            means = payload["mean_scores"]
            lines.append(
                f"- `{priority}`: welfare `{means['welfare']}`, combat `{means['combat']}`, expedition `{means['expedition']}`, avg tick span `{payload['mean_tick_span']}`, avg credits used `{payload['mean_credits_used']}`, runs `{payload['runs']}`"
            )
        lines.append("")
    if calibration.get("risk_summary"):
        lines.extend(["## Risk Calibration", ""])
        for risk, payload in sorted(calibration["risk_summary"].items()):
            means = payload["mean_scores"]
            lines.append(
                f"- `{risk}`: welfare `{means['welfare']}`, combat `{means['combat']}`, expedition `{means['expedition']}`, avg tick span `{payload['mean_tick_span']}`, avg credits used `{payload['mean_credits_used']}`, runs `{payload['runs']}`"
            )
        lines.append("")
    if calibration["run_class_summary"]:
        lines.extend(["## Run Class Summary", ""])
        for run_class, payload in sorted(calibration["run_class_summary"].items()):
            means = payload["mean_scores"]
            lines.append(
                f"- `{run_class}`: welfare `{means['welfare']}`, combat `{means['combat']}`, expedition `{means['expedition']}`, runs `{payload['runs']}`"
            )
        lines.append("")
    if calibration.get("agent_summary"):
        lines.extend(["## Agent Modes", ""])
        for agent_mode, payload in sorted(calibration["agent_summary"].items()):
            means = payload["mean_scores"]
            lines.append(
                f"- `{agent_mode}`: welfare `{means['welfare']}`, combat `{means['combat']}`, expedition `{means['expedition']}`, avg tick span `{payload['mean_tick_span']}`, avg credits used `{payload['mean_credits_used']}`, runs `{payload['runs']}`"
            )
        lines.append("")
    watch_summary = calibration.get("watch_summary") or {}
    if watch_summary.get("runs"):
        means = watch_summary.get("mean_scores") or {}
        lines.extend(
            [
                "## Watch Quality",
                "",
                f"- Watch runs: `{watch_summary.get('runs', 0)}`",
                f"- Mean scores: welfare `{means.get('welfare', 0)}`, combat `{means.get('combat', 0)}`, expedition `{means.get('expedition', 0)}`",
                f"- Avg tick span: `{watch_summary.get('mean_tick_span', 0)}`",
                f"- Avg credits used: `{watch_summary.get('mean_credits_used', 0)}`",
                f"- Dominant action mix: {watch_summary.get('action_digest', 'none')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a concise Part B weekly review packet.")
    parser.add_argument("--season-id", default=PART_B_SEASON_CURRENT_ID)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    text = build_review(args.season_id)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
