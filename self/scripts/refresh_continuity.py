#!/usr/bin/env python3
"""Refresh the compact continuity surface for the next wave."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
STATE = ROOT / "state.json"
REFLECT = ROOT / "state_reflect.json"
MIRROR = ROOT / "mirror.md"
OUTPUT = ROOT / "CONTINUITY.md"


def stale_hypotheses(text: str) -> list[str]:
    found: list[str] = []
    current = None
    for line in text.splitlines():
        if line.startswith("### H"):
            current = line.split(":", 1)[0].replace("### ", "").strip()
        elif current and "TTL status:" in line and ("STALE" in line or "EXPIRED" in line):
            found.append(current)
            current = None
    return found


def main() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    reflect = json.loads(REFLECT.read_text(encoding="utf-8"))
    mirror_text = MIRROR.read_text(encoding="utf-8")

    stale = stale_hypotheses(mirror_text)
    open_threads = state.get("open_threads", [])
    reflect_threads = reflect.get("open_threads", [])
    budget = state.get("open_threads_budget", 7)
    chain = state.get("chain_tracking", {})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    urgent = []
    if stale:
        urgent.append(f"STALE hypotheses need triage: {', '.join(stale[:7])}")
    if state.get("next_action"):
        urgent.append(state["next_action"])
    if chain.get("current_chain_length", 0) >= chain.get("max_chain_length", 999):
        urgent.append("Current chain is saturated and must pivot before another extension.")
    if len(reflect_threads) > budget:
        urgent.append(
            f"Open thread budget exceeded: {len(reflect_threads)}/{budget}. Close or merge before opening new work."
        )

    tension_lines = []
    if chain.get("chain_history"):
        last = chain["chain_history"][-1]
        tension_lines.append(
            f"Last closed chain: {last.get('root', '?')} -> {last.get('end_question', '?')} "
            f"(status={last.get('status', '?')})"
        )
    tension_lines.append(f"Open threads in shared state: {len(open_threads)}")
    tension_lines.append(f"Open threads in reflection state: {len(reflect_threads)} / budget {budget}")
    if state.get("mode"):
        tension_lines.append(f"Current mode: {state['mode']}")

    next_wave = reflect.get("next_action") or state.get("next_task") or "No explicit handoff."

    lines = [
        "# CONTINUITY",
        "",
        "> Auto-generated. If stale, rebuild with `python3 self/scripts/refresh_continuity.py`.",
        "",
        f"- Generated: {now}",
        "",
        "## Where I am",
        f"- Mode: {state.get('mode', 'unknown')}",
        f"- Current question: {state.get('current_question', 'null')}",
        f"- Last cycle type: {state.get('last_cycle_type', 'null')}",
        f"- Last reflection hint: {reflect.get('stats', {}).get('last_type', 'null')}",
        "",
        "## What's urgent",
    ]
    if urgent:
        lines.extend([f"- {item}" for item in urgent[:5]])
    else:
        lines.append("- No urgent drift detected.")

    lines.extend(["", "## Open tensions"])
    lines.extend([f"- {item}" for item in tension_lines])

    lines.extend(
        [
            "",
            "## For next wave",
            next_wave,
            "",
        ]
    )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
