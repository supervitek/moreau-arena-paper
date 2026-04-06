#!/usr/bin/env python3
"""Minimal dream/consolidation pass for the self system.

This is intentionally lightweight:
- refresh the thinking index
- surface chain closures from state
- list stale hypotheses
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from subprocess import run


ROOT = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
STATE = ROOT / "state.json"
REFLECT_STATE = ROOT / "state_reflect.json"
MIRROR = ROOT / "mirror.md"
DOCS = ROOT / "docs"
REPORT = DOCS / "dream_cycle_report.md"


def stale_hypotheses(mirror_text: str) -> list[str]:
    statuses = []
    current = None
    for line in mirror_text.splitlines():
        if line.startswith("### H"):
            current = line.split(":")[0].replace("### ", "").strip()
        if current and "TTL status" in line and ("STALE" in line or "EXPIRED" in line):
            statuses.append(current)
            current = None
    return statuses


def main() -> None:
    state = json.loads(STATE.read_text())
    state["mode"] = "dream"
    sleep = state.setdefault("sleep", {})
    sleep["state"] = "dream"
    sleep["last_transition_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not sleep.get("last_sleep_start"):
        sleep["last_sleep_start"] = sleep["last_transition_at"]
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run(
        ["python3", str(ROOT / "scripts/index_thinking.py")],
        check=True,
    )
    run(
        ["python3", str(ROOT / "scripts/health_metrics.py")],
        check=True,
    )
    run(
        ["python3", str(ROOT / "scripts/refresh_continuity.py")],
        check=True,
    )
    state = json.loads(STATE.read_text())
    reflect_state = json.loads(REFLECT_STATE.read_text())
    mirror_text = MIRROR.read_text(encoding="utf-8")

    chain_history = state.get("chain_tracking", {}).get("chain_history", [])
    stale = stale_hypotheses(mirror_text)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Dream Cycle Report",
        "",
        f"- Generated: {now}",
        f"- Current chain root: {state.get('chain_tracking', {}).get('current_chain_root', 'null')}",
        f"- Current chain length: {state.get('chain_tracking', {}).get('current_chain_length', 0)}",
        f"- Closed chains recorded: {len(chain_history)}",
        f"- Reflection count: {reflect_state.get('stats', {}).get('total_reflections', 0)}",
        "",
        "## Closed Chains",
    ]
    if chain_history:
        for entry in chain_history[-10:]:
            lines.append(
                f"- {entry.get('root', '?')}: length={entry.get('length', '?')}, "
                f"status={entry.get('status', '?')}, summary={entry.get('summary', '')}"
            )
    else:
        lines.append("- None recorded yet.")

    lines.extend(["", "## Stale Hypotheses"])
    if stale:
        for hypothesis in stale:
            lines.append(f"- {hypothesis}")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Actions Performed",
            "- Refreshed `self/thinking/INDEX.md`.",
            "- Reviewed chain history from `state.json`.",
            "- Reviewed TTL statuses from `mirror.md`.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()
