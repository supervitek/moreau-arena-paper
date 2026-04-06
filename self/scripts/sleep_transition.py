#!/usr/bin/env python3
"""Compute and record sleep-state transitions for the self-system."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
STATE = ROOT / "state.json"
REFLECT = ROOT / "state_reflect.json"
MIRROR = ROOT / "mirror.md"
PREAMBLE = ROOT / "preamble.md"
CONTINUITY = ROOT / "CONTINUITY.md"
SLEEP_LOG = ROOT / "docs" / "sleep_log.md"

VALID_STATES = {"awake", "tired", "sleep_prep", "dream", "wake", "recovery"}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def continuity_age_hours() -> float:
    modified = datetime.fromtimestamp(CONTINUITY.stat().st_mtime, tz=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - modified).total_seconds() / 3600.0)


def active_stale_hypotheses() -> list[str]:
    text = MIRROR.read_text(encoding="utf-8")
    active_match = re.search(r"## Active Hypotheses\n(.*?)(?:\n## |\Z)", text, flags=re.DOTALL)
    active_text = active_match.group(1) if active_match else ""
    stale: list[str] = []
    current = None
    for line in active_text.splitlines():
        if line.startswith("### H"):
            current = line.split(":", 1)[0].replace("### ", "").strip()
        elif current and "TTL status:" in line and ("STALE" in line or "EXPIRED" in line):
            stale.append(current)
            current = None
    return stale


def strongest_reason(hard: list[str], soft: list[str]) -> str | None:
    if hard:
        return hard[0]
    if soft:
        return soft[0]
    return None


def compute_transition(state: dict, reflect: dict) -> tuple[str, list[str], list[str]]:
    sleep = state["sleep"]
    hard: list[str] = []
    soft: list[str] = []

    reflect_threads = reflect.get("open_threads", [])
    open_thread_count = len(reflect_threads)
    budget = state.get("open_threads_budget", 7)
    chain = state.get("chain_tracking", {})
    chain_length = chain.get("current_chain_length", 0)
    max_chain_length = chain.get("max_chain_length", 999)
    stale = active_stale_hypotheses()
    stale_threshold = sleep.get("stale_hypothesis_threshold", 3)
    continuity_max_age = sleep.get("continuity_max_age_hours", 12)
    preamble_max_chars = sleep.get("preamble_max_chars", 5000)
    preamble_chars = len(PREAMBLE.read_text(encoding="utf-8"))
    continuity_hours = continuity_age_hours()
    no_oxygen_cycles = max(
        int(sleep.get("no_real_oxygen_cycles", 0)),
        int(reflect.get("consecutive_no_oxygen", 0)),
        int(reflect.get("stats", {}).get("consecutive_no_oxygen", 0)),
    )
    refinement_streak = int(state.get("saturation", {}).get("refinement_streak", 0))
    max_refinement_streak = int(state.get("saturation", {}).get("max_refinement_streak", 3))

    if open_thread_count > budget:
        hard.append(f"open_threads_exceeded:{open_thread_count}/{budget}")
    if chain_length >= max_chain_length and max_chain_length > 0:
        hard.append(f"chain_saturated:{chain_length}/{max_chain_length}")
    if len(stale) >= stale_threshold:
        hard.append(f"stale_hypotheses:{len(stale)}/{stale_threshold}")
    if continuity_hours > continuity_max_age:
        hard.append(f"continuity_stale:{continuity_hours:.1f}h>{continuity_max_age}h")
    if preamble_chars > preamble_max_chars:
        hard.append(f"preamble_too_long:{preamble_chars}>{preamble_max_chars}")

    if no_oxygen_cycles >= 3:
        soft.append(f"no_real_oxygen_cycles:{no_oxygen_cycles}")
    if refinement_streak >= max(2, max_refinement_streak - 1):
        soft.append(f"refinement_pressure:{refinement_streak}/{max_refinement_streak}")
    if open_thread_count == budget and budget > 0:
        soft.append(f"thread_budget_full:{open_thread_count}/{budget}")

    if hard:
        return "sleep_prep", hard, soft
    if soft:
        return "tired", hard, soft
    return "awake", hard, soft


def build_sleep_handoff(state: dict, reflect: dict, hard: list[str], soft: list[str]) -> dict:
    reflect_threads = reflect.get("open_threads", [])
    budget = state.get("open_threads_budget", 7)
    overflow = max(0, len(reflect_threads) - budget)
    stale = active_stale_hypotheses()
    chain_history = state.get("chain_tracking", {}).get("chain_history", [])

    must_close = [item.get("id", "?") for item in reflect_threads[:overflow]]
    must_park = stale[:7]
    must_summarize = []
    if chain_history:
        must_summarize.append(chain_history[-1].get("root", "?"))

    reason = strongest_reason(hard, soft)
    wake_with = state.get("next_task") or reflect.get("next_action") or state.get("next_action")
    if reason:
        wake_with = f"{reason} | {wake_with}"

    return {
        "must_close": must_close,
        "must_park": must_park,
        "must_summarize": must_summarize,
        "wake_with": wake_with,
    }


def append_sleep_log(previous: str, current: str, hard: list[str], soft: list[str], forced: bool) -> None:
    if not SLEEP_LOG.exists():
        SLEEP_LOG.write_text(
            "# Sleep Log\n\n"
            "Auto-generated transition log for the self-system.\n"
            "This is an audit trail, not a diary.\n\n",
            encoding="utf-8",
        )

    lines = [
        f"- {now_utc()} | {previous} -> {current}",
        f"  - forced: {'yes' if forced else 'no'}",
        f"  - hard_triggers: {', '.join(hard) if hard else 'none'}",
        f"  - soft_triggers: {', '.join(soft) if soft else 'none'}",
    ]
    with SLEEP_LOG.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute sleep-state transitions.")
    parser.add_argument("--force", choices=sorted(VALID_STATES), help="Force a specific sleep state.")
    parser.add_argument("--dry-run", action="store_true", help="Print the computed transition without writing files.")
    args = parser.parse_args()

    state = load_json(STATE)
    reflect = load_json(REFLECT)
    state.setdefault("sleep", {})
    reflect.setdefault("sleep_handoff", {
        "must_close": [],
        "must_park": [],
        "must_summarize": [],
        "wake_with": None,
    })

    previous = state["sleep"].get("state", "awake")
    if args.force:
        target, hard, soft = args.force, [f"forced:{args.force}"], []
    else:
        target, hard, soft = compute_transition(state, reflect)

    handoff = build_sleep_handoff(state, reflect, hard, soft)

    if args.dry_run:
        print(json.dumps({
            "previous": previous,
            "target": target,
            "hard_triggers": hard,
            "soft_triggers": soft,
            "sleep_handoff": handoff,
        }, ensure_ascii=False, indent=2))
        return

    sleep = state["sleep"]
    sleep["state"] = target
    sleep["sleep_pressure"] = len(hard) * 2 + len(soft)
    sleep["last_sleep_reason"] = strongest_reason(hard, soft)
    sleep["last_transition_at"] = now_utc()
    sleep["no_real_oxygen_cycles"] = max(
        int(sleep.get("no_real_oxygen_cycles", 0)),
        int(reflect.get("consecutive_no_oxygen", 0)),
        int(reflect.get("stats", {}).get("consecutive_no_oxygen", 0)),
    )
    sleep["last_health_status"] = "sleep_required" if hard else ("sleep_recommended" if soft else "ok")
    if target == "sleep_prep" and not sleep.get("last_sleep_start"):
        sleep["last_sleep_start"] = now_utc()

    state["last_updated"] = now_utc()
    state["last_updated_by"] = "sleep_transition"
    reflect["sleep_handoff"] = handoff
    reflect["last_updated"] = now_utc()
    reflect["last_updated_by"] = "sleep_transition"

    save_json(STATE, state)
    save_json(REFLECT, reflect)
    append_sleep_log(previous, target, hard, soft, forced=bool(args.force))

    print(json.dumps({
        "previous": previous,
        "target": target,
        "hard_triggers": hard,
        "soft_triggers": soft,
        "sleep_handoff": handoff,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
