#!/usr/bin/env python3
"""Observability baseline for the self/OpenClaw system.

Keeps the baseline intentionally small:
- preamble readability / size
- mirror freshness coverage
- prompt drift against shared invariants
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re


ROOT = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
PREAMBLE = ROOT / "preamble.md"
MIRROR = ROOT / "mirror.md"
STATE = ROOT / "state.json"
DOCS = ROOT / "docs"
OUTPUT = DOCS / "health_baseline.md"

PROMPT_RULES = {
    "prompt.md": {
        "path": ROOT / "prompt.md",
        "needs": {
            "tier_required": "Do not add predictions without a tier",
            "index_read": "self/thinking/INDEX.md",
        },
    },
    "prompt_quiet.md": {
        "path": ROOT / "prompt_quiet.md",
        "needs": {
            "tier_required": "Do not add predictions without a tier",
            "index_read": "self/thinking/INDEX.md",
        },
    },
    "prompt_reflect.md": {
        "path": ROOT / "prompt_reflect.md",
        "needs": {
            "classification_block": "## Classification",
            "index_read": "self/thinking/INDEX.md",
        },
    },
}


def parse_date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def mirror_freshness() -> tuple[int, int, list[str]]:
    text = MIRROR.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc)
    total = 0
    fresh = 0
    stale_ids: list[str] = []

    active_match = re.search(
        r"## Active Hypotheses\n(.*?)(?:\n## |\Z)", text, flags=re.DOTALL
    )
    active_text = active_match.group(1) if active_match else ""

    chunks = re.split(r"(?=^### H\d+:)", active_text, flags=re.MULTILINE)
    for chunk in chunks:
        if not chunk.startswith("### H"):
            continue
        if "**PROMOTED**" in chunk:
            continue
        total += 1
        hyp_id = chunk.split(":", 1)[0].replace("### ", "").strip()
        status_match = re.search(r"TTL status:\s*(.+)", chunk)
        if status_match and any(flag in status_match.group(1) for flag in ("STALE", "EXPIRED")):
            stale_ids.append(hyp_id)
            continue
        date_match = re.search(r"Last evidence:\s*([0-9TZ:\-]+)", chunk)
        if date_match:
            dt = parse_date(date_match.group(1))
            if dt and (now - dt) <= timedelta(days=14):
                fresh += 1
            else:
                stale_ids.append(hyp_id)
        else:
            stale_ids.append(hyp_id)
    return fresh, total, stale_ids


def prompt_drift() -> tuple[list[str], dict[str, list[str]]]:
    missing_by_prompt: dict[str, list[str]] = {}
    overall: list[str] = []
    for name, config in PROMPT_RULES.items():
        text = config["path"].read_text(encoding="utf-8")
        missing = [
            label for label, needle in config["needs"].items() if needle not in text
        ]
        if missing:
            missing_by_prompt[name] = missing
            overall.extend([f"{name}:{item}" for item in missing])
    return overall, missing_by_prompt


def main() -> None:
    preamble_text = PREAMBLE.read_text(encoding="utf-8")
    preamble_chars = len(preamble_text)
    preamble_status = "OK" if preamble_chars <= 5000 else "TOO_LONG"

    fresh, total, stale_ids = mirror_freshness()
    coverage = (fresh / total * 100.0) if total else 100.0

    overall_drift, missing_by_prompt = prompt_drift()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Health Baseline",
        "",
        f"- Generated: {now}",
        f"- Current mode: {state.get('mode', 'unknown')}",
        "",
        "## Baseline Metrics",
        f"- Preamble readability: **{preamble_status}** ({preamble_chars} chars, target < 5000)",
        f"- Mirror freshness coverage: **{fresh}/{total} = {coverage:.1f}%** with `Last evidence` < 14 days",
        f"- Prompt drift alerts: **{len(overall_drift)}**",
        "",
        "## Details",
        "",
        "### Preamble",
        "- Signal: can a new wave read the preamble fast enough to orient itself?",
        "",
        "### Mirror coverage",
        f"- Fresh hypotheses: {fresh}",
        f"- Total active hypotheses: {total}",
    ]
    if stale_ids:
        lines.append(f"- Stale or uncovered hypotheses: {', '.join(stale_ids)}")
    else:
        lines.append("- Stale or uncovered hypotheses: none")

    lines.extend(["", "### Prompt drift"])
    if missing_by_prompt:
        for prompt_name, missing in missing_by_prompt.items():
            lines.append(f"- {prompt_name}: missing {', '.join(missing)}")
    else:
        lines.append("- No drift detected across current shared invariants.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- This file is the observability baseline for future self-system changes.",
            "- If CONTINUITY or POLICY changes do not improve these metrics, the added structure is probably noise.",
            "",
        ]
    )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
