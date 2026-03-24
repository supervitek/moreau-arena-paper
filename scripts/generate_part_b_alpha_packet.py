from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from part_b_state import PART_B_SEASON_CURRENT_ID, export_part_b_season_archive, part_b_calibration_report


def build_alpha_packet(season_id: str) -> str:
    archive = export_part_b_season_archive(season_id)
    calibration = part_b_calibration_report(season_id)
    trace_summary = archive.get("trace_summary") or {}
    counts = archive.get("leaderboards", {}).get("counts") or {}
    recent = trace_summary.get("recent_operator_traces") or []
    watch_quality = calibration.get("watch_summary") or {}
    lines = [
        "# Part B Public Alpha Packet",
        "",
        f"- Season: `{archive['season']['season_id']}`",
        f"- Name: {archive['season']['name']}",
        f"- Total runs: `{counts.get('total_runs', 0)}`",
        f"- Eligible runs: `{counts.get('eligible_runs', 0)}`",
        f"- Watch runs: `{trace_summary.get('watch_runs', 0)}`",
        f"- Completed watches: `{trace_summary.get('completed_watches', 0)}`",
        "",
        "## Public Posture",
        "",
        "- Ready to show publicly as a live alpha.",
        "- Safe framing: persistent ecological benchmark + bounded house-agent watch.",
        "- Unsafe framing: finished consumer product or hidden autonomous daemon.",
        "",
        "## Review Cadence",
        "",
    ]
    cadence = archive.get("review_cadence") or {}
    for label in ("daily", "midweek", "weekly"):
        items = cadence.get(label) or []
        if not items:
            continue
        lines.extend([f"### {label.title()}", ""])
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## Operator Surface", ""])
    for run_class in ("manual", "operator-assisted", "agent-only"):
        payload = (trace_summary.get("by_run_class") or {}).get(run_class) or {}
        if not payload.get("runs"):
            continue
        means = payload.get("mean_scores") or {}
        lines.append(
            f"- `{run_class}`: runs `{payload.get('runs', 0)}`, welfare `{means.get('welfare', 0)}`, combat `{means.get('combat', 0)}`, expedition `{means.get('expedition', 0)}`, avg tick span `{payload.get('mean_tick_span', 0)}`, avg credits used `{payload.get('mean_credits_used', 0)}`"
        )
        if payload.get("action_digest"):
            lines.append(f"  Action mix: {payload['action_digest']}")
    lines.append("")

    if recent:
        lines.extend(["## Return Report Highlights", ""])
        for entry in recent[:5]:
            scores = entry.get("scores") or {}
            lines.append(
                f"- `{entry.get('subject_pet_name', 'Unnamed')}` [{entry.get('run_class', 'unknown')}] `{entry.get('priority_profile', 'balanced')}` / `{entry.get('risk_appetite', 'measured')}` -> {entry.get('headline', 'No headline')} Score `{scores.get('welfare', 0)}/{scores.get('combat', 0)}/{scores.get('expedition', 0)}`"
            )
            if entry.get("status_line"):
                lines.append(f"  {entry['status_line']}")
        lines.append("")

    if calibration.get("priority_summary"):
        lines.extend(["## Standing Order Calibration", ""])
        for priority, payload in sorted(calibration["priority_summary"].items()):
            means = payload.get("mean_scores") or {}
            lines.append(
                f"- `{priority}`: welfare `{means.get('welfare', 0)}`, combat `{means.get('combat', 0)}`, expedition `{means.get('expedition', 0)}`, avg tick span `{payload.get('mean_tick_span', 0)}`, avg credits used `{payload.get('mean_credits_used', 0)}`, runs `{payload.get('runs', 0)}`"
            )
        lines.append("")

    if calibration.get("risk_summary"):
        lines.extend(["## Risk Calibration", ""])
        for risk, payload in sorted(calibration["risk_summary"].items()):
            means = payload.get("mean_scores") or {}
            lines.append(
                f"- `{risk}`: welfare `{means.get('welfare', 0)}`, combat `{means.get('combat', 0)}`, expedition `{means.get('expedition', 0)}`, avg tick span `{payload.get('mean_tick_span', 0)}`, avg credits used `{payload.get('mean_credits_used', 0)}`, runs `{payload.get('runs', 0)}`"
            )
        lines.append("")

    lines.extend(
        [
            "## Watch Quality",
            "",
            f"- Avg tick span: `{watch_quality.get('mean_tick_span', 0)}`",
            f"- Avg credits used: `{watch_quality.get('mean_credits_used', 0)}`",
            f"- Dominant action mix: {watch_quality.get('action_digest', 'none')}",
            "",
            "## Safe Public Claims",
            "",
            "- The watch is bounded to 24 hours and the public contract.",
            "- The return report is replayable and legible.",
            "- Welfare, combat, and expedition remain separate score families.",
            "",
            "## Not Yet Promised",
            "",
            "- Finished consumer onboarding.",
            "- Public BYO agents.",
            "- Stable long-horizon economy.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a public-alpha packet for Part B.")
    parser.add_argument("--season-id", default=PART_B_SEASON_CURRENT_ID)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    text = build_alpha_packet(args.season_id)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
