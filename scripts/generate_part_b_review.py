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
    lines = [
        "# Part B Weekly Review",
        "",
        f"- Season: `{archive['season']['season_id']}`",
        f"- Name: {archive['season']['name']}",
        f"- Total runs: `{counts['total_runs']}`",
        f"- Eligible runs: `{counts['eligible_runs']}`",
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
    if calibration["policy_summary"]:
        lines.extend(["## Policy Summary", ""])
        for policy, payload in sorted(calibration["policy_summary"].items()):
            means = payload["mean_scores"]
            lines.append(
                f"- `{policy}`: welfare `{means['welfare']}`, combat `{means['combat']}`, expedition `{means['expedition']}`, runs `{payload['runs']}`"
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
