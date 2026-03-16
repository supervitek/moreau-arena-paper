#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_until_ready(proc: subprocess.Popen[str], port: int) -> None:
    base = f"http://127.0.0.1:{port}"
    for _ in range(40):
        if proc.poll() is not None:
            raise RuntimeError("uvicorn exited before chronicler report could start")
        try:
            payload = fetch_json(base + "/api/v1/island/chronicler/summary")
            if isinstance(payload, dict) and "runs" in payload:
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("timed out waiting for chronicler summary endpoint")


def build_markdown(summary: dict, recent: dict) -> str:
    kill = summary.get("kill_signals", {})
    events = summary.get("events", {})
    runs = summary.get("runs", {})
    cost = summary.get("cost", {})

    lines = [
        "# Chronicler Report",
        "",
        "## Cost",
        f"- Date: `{cost.get('date', 'unknown')}`",
        f"- Spent: `${cost.get('usd_spent', 0.0)}` / `${cost.get('usd_cap', 0.0)}`",
        "",
        "## Runs",
        f"- Count: `{runs.get('count', 0)}`",
        f"- Modes: `{json.dumps(runs.get('mode_counts', {}), sort_keys=True)}`",
        f"- Suggested actions: `{json.dumps(runs.get('suggested_action_counts', {}), sort_keys=True)}`",
        "",
        "## Event Summary",
        f"- Event count: `{events.get('count', 0)}`",
        f"- Event types: `{json.dumps(events.get('event_counts', {}), sort_keys=True)}`",
        f"- Follow: `{events.get('follow', 0)}`",
        f"- Override: `{events.get('override', 0)}`",
        f"- Neutral: `{events.get('neutral', 0)}`",
        f"- Follow rate: `{events.get('follow_rate')}`",
        f"- Override rate: `{events.get('override_rate')}`",
        f"- Bounce rate: `{events.get('bounce_rate')}`",
        "",
        "## Kill Signals",
        f"- Follow rate > 30%: `{kill.get('follow_rate_gt_30pct')}`",
        f"- Override rate < 50%: `{kill.get('override_rate_lt_50pct')}`",
        f"- Bounce rate > 5%: `{kill.get('bounce_rate_gt_5pct')}`",
        f"- Cost > cap: `{kill.get('cost_gt_cap')}`",
        "",
        "## Recent Runs",
    ]

    for run in recent.get("runs", [])[-5:]:
        response = run.get("response", {})
        lines.append(
            f"- `{run.get('trace_id')}` `{run.get('pet_name')}` `{response.get('mode')}` "
            f"`{response.get('suggested_action')}` — {response.get('observation')}"
        )

    lines.extend(["", "## Recent Events"])
    for event in recent.get("events", [])[-10:]:
        lines.append(
            f"- `{event.get('event_type')}` trace=`{event.get('trace_id')}` "
            f"relation=`{event.get('relation')}` action=`{event.get('action_id')}` details=`{event.get('details')}`"
        )

    lines.extend(
        [
            "",
            "## Decision Stub",
            "- Continue / Pivot / Kill: `TBD`",
            "- Reviewer notes:",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local Chronicler review report from in-memory endpoints.")
    parser.add_argument("--output", default=str(ROOT / "reports" / "chronicler_report.md"))
    args = parser.parse_args()

    if not VENV_PYTHON.exists():
        print("Missing .venv Python at", VENV_PYTHON, file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    port = pick_port()
    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "web.app:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        wait_until_ready(proc, port)
        base = f"http://127.0.0.1:{port}"
        summary = fetch_json(base + "/api/v1/island/chronicler/summary")
        recent = fetch_json(base + "/api/v1/island/chronicler/recent?limit=20")
        output.write_text(build_markdown(summary, recent), encoding="utf-8")
        print(output)
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
