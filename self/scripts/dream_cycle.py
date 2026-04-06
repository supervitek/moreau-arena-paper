#!/usr/bin/env python3
"""Bounded dream/consolidation pass for the self system."""

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
SLEEP_LOG = DOCS / "sleep_log.md"


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


def append_sleep_log(previous: str, current: str, wake_with: str) -> None:
    if not SLEEP_LOG.exists():
        SLEEP_LOG.write_text(
            "# Sleep Log\n\nAuto-generated transition log for the self-system.\nThis is an audit trail, not a diary.\n\n",
            encoding="utf-8",
        )
    with SLEEP_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            f"- {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} | {previous} -> {current}\n"
            "  - forced: no\n"
            "  - hard_triggers: none\n"
            "  - soft_triggers: bounded_dream_run\n"
            f"  - wake_with: {wake_with}\n"
        )


def choose_wake_with(state: dict, reflect_state: dict, stale: list[str]) -> str:
    handoff = reflect_state.get("sleep_handoff", {})
    must_close = handoff.get("must_close") or []
    must_park = handoff.get("must_park") or []
    must_summarize = handoff.get("must_summarize") or []

    if must_close:
        return f"Close or merge one active thread first: {must_close[0]}"
    if must_park:
        return f"Park or reactivate deliberately, not both: {must_park[0]}"
    if stale:
        return f"Triage one stale hypothesis before new expansion: {stale[0]}"
    if must_summarize:
        return f"Use the last closed chain as the first wake anchor: {must_summarize[0]}"
    return state.get("next_task") or reflect_state.get("next_action") or "Wake quietly and prefer one closure over new opening."


def main() -> None:
    state = json.loads(STATE.read_text())
    reflect_state = json.loads(REFLECT_STATE.read_text())
    previous_sleep_state = state.get("sleep", {}).get("state", "awake")
    if previous_sleep_state not in {"sleep_prep", "dream"}:
        raise SystemExit(
            f"dream_cycle.py may only run from sleep_prep or dream; current sleep.state={previous_sleep_state}"
        )

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
    wake_with = choose_wake_with(state, reflect_state, stale)

    sleep = state.setdefault("sleep", {})
    sleep["dream_cycles_completed"] = int(sleep.get("dream_cycles_completed", 0)) + 1
    sleep["last_transition_at"] = now
    sleep["last_health_status"] = "ok"
    reflect_state.setdefault("sleep_handoff", {})
    reflect_state["sleep_handoff"] = {
        "must_close": reflect_state["sleep_handoff"].get("must_close", []),
        "must_park": reflect_state["sleep_handoff"].get("must_park", []),
        "must_summarize": reflect_state["sleep_handoff"].get("must_summarize", []),
        "wake_with": wake_with,
    }
    reflect_state["last_updated"] = now
    reflect_state["last_updated_by"] = "dream_cycle"
    state["last_updated"] = now
    state["last_updated_by"] = "dream_cycle"
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REFLECT_STATE.write_text(json.dumps(reflect_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Dream Cycle Report",
        "",
        f"- Generated: {now}",
        f"- Entered from sleep state: {previous_sleep_state}",
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
            "- Refreshed `self/docs/health_baseline.md`.",
            "- Refreshed `self/CONTINUITY.md`.",
            "- Reviewed chain history from `state.json`.",
            "- Reviewed TTL statuses from `mirror.md`.",
            "",
            "## Wake With",
            f"- {wake_with}",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    append_sleep_log(previous_sleep_state, "dream", wake_with)
    print(REPORT)


if __name__ == "__main__":
    main()
