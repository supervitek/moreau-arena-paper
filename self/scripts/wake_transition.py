#!/usr/bin/env python3
"""Finalize a wake transition after sleep or recovery."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
STATE = ROOT / "state.json"
REFLECT = ROOT / "state_reflect.json"
CONTINUITY = ROOT / "CONTINUITY.md"
SLEEP_LOG = ROOT / "docs" / "sleep_log.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_sleep_log(previous: str, current: str) -> None:
    if not SLEEP_LOG.exists():
        SLEEP_LOG.write_text("# Sleep Log\n\nAuto-generated transition log.\n\n", encoding="utf-8")
    with SLEEP_LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            f"- {now_utc()} | {previous} -> {current}\n"
            f"  - forced: no\n"
            f"  - hard_triggers: none\n"
            f"  - soft_triggers: none\n"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Move the self-system into wake or awake.")
    parser.add_argument("--finalize-awake", action="store_true", help="Move directly to awake instead of wake.")
    args = parser.parse_args()

    state = load_json(STATE)
    reflect = load_json(REFLECT)
    state.setdefault("sleep", {})
    reflect.setdefault("sleep_handoff", {})

    previous = state["sleep"].get("state", "awake")
    target = "awake" if args.finalize_awake else "wake"

    sleep = state["sleep"]
    sleep["state"] = target
    sleep["sleep_pressure"] = 0
    sleep["last_sleep_end"] = now_utc()
    sleep["last_transition_at"] = now_utc()
    sleep["last_health_status"] = "ok" if target == "awake" else sleep.get("last_health_status", "ok")
    state["mode"] = "quiet" if target == "awake" else "wake"
    sleep["last_sleep_reason"] = None if target == "awake" else sleep.get("last_sleep_reason")
    if target == "awake":
        sleep["sleep_pressure"] = 0

    wake_with = reflect.get("sleep_handoff", {}).get("wake_with")
    if wake_with and not wake_with.startswith("forced:"):
        state["next_task"] = wake_with

    reflect["sleep_handoff"] = {
        "must_close": [],
        "must_park": [],
        "must_summarize": [],
        "wake_with": None if (wake_with and wake_with.startswith("forced:")) else wake_with,
    }

    state["last_updated"] = now_utc()
    state["last_updated_by"] = "wake_transition"
    reflect["last_updated"] = now_utc()
    reflect["last_updated_by"] = "wake_transition"

    if CONTINUITY.exists():
        lines = CONTINUITY.read_text(encoding="utf-8").splitlines()
        updated = []
        replaced = False
        wake_inserted = False
        for line in lines:
            if line.startswith("- Mode: "):
                updated.append(f"- Mode: {state.get('mode', 'unknown')} | sleep: {target}")
                replaced = True
            elif line == "## For next wave" and wake_with:
                updated.extend(["## Wake note", f"- {wake_with}", ""])
                updated.append(line)
                wake_inserted = True
            else:
                updated.append(line)
        if not replaced:
            updated.extend(["", "## Wake note", f"- sleep state: {target}"])
        elif wake_with and not wake_inserted:
            updated.extend(["", "## Wake note", f"- {wake_with}"])
        CONTINUITY.write_text("\n".join(updated) + "\n", encoding="utf-8")

    save_json(STATE, state)
    save_json(REFLECT, reflect)
    append_sleep_log(previous, target)
    print(json.dumps({"previous": previous, "target": target, "wake_with": wake_with}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
