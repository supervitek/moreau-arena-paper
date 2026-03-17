from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from part_b_state import PART_B_SEASON_CURRENT_ID, export_part_b_season_archive


def archive_markdown(payload: dict) -> str:
    lines = [
        "# Part B Season Archive",
        "",
        f"- Season: `{payload['season']['season_id']}`",
        f"- Name: {payload['season']['name']}",
        f"- Headline note: {payload['leaderboards']['headline_note']}",
        f"- Runs archived: `{len(payload['runs'])}`",
        "",
        "## Leaderboards",
        "",
    ]
    for family, entries in payload["leaderboards"]["families"].items():
        lines.append(f"### {family.title()}")
        lines.append("")
        if not entries:
            lines.append("- No eligible runs.")
        else:
            for index, entry in enumerate(entries, start=1):
                lines.append(
                    f"{index}. `{entry['subject_pet_name']}` · `{entry['run_class']}` · score `{entry['scores'][family]}` · tick `{entry['world_tick']}`"
                )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a complete Part B season archive.")
    parser.add_argument("--season-id", default=PART_B_SEASON_CURRENT_ID)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()

    payload = export_part_b_season_archive(args.season_id)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_output.write_text(archive_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
