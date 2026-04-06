#!/usr/bin/env python3
"""Compute per-tier prediction accuracy and write a markdown summary."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


CSV_PATH = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/predictions.csv")
OUTPUT = Path(
    "/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/docs/prediction_accuracy_by_tier.md"
)

TIER_DESCRIPTIONS = {
    "Tier 1": "Structural invariants and durable repository behaviors.",
    "Tier 2": "Conditional/pattern predictions that depend on a specific surface being touched.",
    "Tier 3": "Temporal and regime-sensitive forecasts tracked separately.",
    "Tier 4": "Exploratory predictions; informative, but excluded from main accuracy.",
}


def normalize_tier(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("Tier "):
        return value
    if value.isdigit():
        return f"Tier {value}"
    return "Unspecified"


def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8", newline="")))
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"correct": 0, "wrong": 0, "pending": 0, "total": 0}
    )

    for row in rows:
        tier = normalize_tier(row.get("tier", ""))
        result = (row.get("result") or "").strip()
        totals[tier]["total"] += 1
        if result == "1":
            totals[tier]["correct"] += 1
        elif result == "0":
            totals[tier]["wrong"] += 1
        else:
            totals[tier]["pending"] += 1

    main_correct = totals["Tier 1"]["correct"] + totals["Tier 2"]["correct"]
    main_scored = (
        totals["Tier 1"]["correct"]
        + totals["Tier 1"]["wrong"]
        + totals["Tier 2"]["correct"]
        + totals["Tier 2"]["wrong"]
    )
    main_accuracy = (main_correct / main_scored * 100.0) if main_scored else 0.0

    lines = [
        "# Prediction Accuracy by Tier",
        "",
        f"Generated from `{CSV_PATH.name}`.",
        "",
        f"Main accuracy (Tier 1 + Tier 2 only): **{main_accuracy:.1f}%** "
        f"({main_correct}/{main_scored})",
        "",
        "| Tier | Meaning | Correct | Wrong | Pending | Accuracy |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for tier in ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Unspecified"]:
        if tier not in totals:
            continue
        scored = totals[tier]["correct"] + totals[tier]["wrong"]
        accuracy = (totals[tier]["correct"] / scored * 100.0) if scored else 0.0
        lines.append(
            f"| {tier} | {TIER_DESCRIPTIONS.get(tier, 'Needs classification.')} | "
            f"{totals[tier]['correct']} | {totals[tier]['wrong']} | {totals[tier]['pending']} | "
            f"{accuracy:.1f}% |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "- Tier 1 and Tier 2 count toward the main accuracy headline.",
            "- Tier 3 predictions are tracked separately because regime shifts distort raw hit-rate.",
            "- Tier 4 predictions are exploratory and should not drive calibration decisions.",
            "",
        ]
    )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
