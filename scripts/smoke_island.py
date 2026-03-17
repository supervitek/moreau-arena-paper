#!/usr/bin/env python3
from __future__ import annotations

import socket
import subprocess
import sys
import time
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

ROUTES = [
    ("/island/home", "Island"),
    ("/island/ecology", "Cave of Catharsis"),
    ("/island/train", "Training"),
    ("/island/pit", "Pit"),
    ("/island/menagerie", "Menagerie"),
    ("/island/kennel", "Kennel"),
    ("/island/rivals", "Rivals"),
    ("/island/breeding", "Breeding"),
    ("/island/pact", "Pact"),
    ("/island/tides", "Tide"),
    ("/island/deep-tide", "Deep Tide"),
    ("/island/dreams", "Dream"),
    ("/island/prophecy", "Oracle"),
    ("/island/achievements", "Achievement"),
    ("/island/graveyard", "Graveyard"),
    ("/island/genesis", "Genesis"),
    ("/island/succession", "Bloodline"),
    ("/island/cosmetics", "Cosmetic"),
    ("/island/black-market", "Black Market"),
    ("/island/confessions", "Confession"),
]

STATIC_ASSETS = [
    "/static/island/storage.js",
    "/static/island/island-time.js",
    "/static/island/ui.js",
    "/static/island/chronicler.js",
]


def fetch(url: str) -> tuple[int, str, str]:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status, response.headers.get_content_type(), body


def post_json(url: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status, json.loads(body)


def delete_json(url: str) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status, json.loads(body)


def pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_until_ready(proc: subprocess.Popen[str], port: int) -> None:
    base = f"http://127.0.0.1:{port}"
    for _ in range(40):
        if proc.poll() is not None:
            raise RuntimeError("uvicorn exited before island smoke checks began")
        try:
            status, _, _ = fetch(base + "/island")
            if status == 200:
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("timed out waiting for island app to start")


def main() -> int:
    if not VENV_PYTHON.exists():
        print("Missing .venv Python at", VENV_PYTHON, file=sys.stderr)
        return 1

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

        for route, marker in ROUTES:
            status, content_type, body = fetch(base + route)
            if status != 200:
                raise RuntimeError(f"{route} returned {status}")
            if marker.lower() not in body.lower():
                raise RuntimeError(f"{route} missing marker {marker!r}")
            print(f"OK {route} [{content_type}]")

        for asset in STATIC_ASSETS:
            status, content_type, _ = fetch(base + asset)
            if status != 200:
                raise RuntimeError(f"{asset} returned {status}")
            print(f"OK {asset} [{content_type}]")

        status, payload = post_json(
            base + "/api/v1/island/chronicler",
            {
                "session_id": "smoke-island",
                "active_pet": {
                    "name": "Smoke",
                    "animal": "fox",
                    "level": 5,
                    "mood": "philosophical",
                    "corruption": 0,
                    "instability": 0,
                    "mutations": [],
                },
                "dream_unread": 1,
                "recent_dream": "A lantern swings above black water.",
                "available_actions": ["dreams", "train", "profile"],
            },
        )
        required_fields = ["trace_id", "observation", "prompt", "uncertainty", "suggested_action", "mode"]
        if status != 200 or any(payload.get(field) in (None, "") for field in required_fields):
            raise RuntimeError("/api/v1/island/chronicler returned invalid payload")
        if payload.get("suggested_action") not in {
            "none", "train", "caretaker", "lab", "dreams", "prophecy", "pact",
            "rivals", "tides", "deep_tide", "profile", "menagerie"
        }:
            raise RuntimeError("/api/v1/island/chronicler returned invalid suggested_action")
        print("OK /api/v1/island/chronicler [application/json]")

        status, content_type, summary_body = fetch(base + "/api/v1/island/chronicler/summary")
        if status != 200 or content_type != "application/json":
            raise RuntimeError("/api/v1/island/chronicler/summary returned invalid response")
        if '"runs"' not in summary_body or '"events"' not in summary_body:
            raise RuntimeError("/api/v1/island/chronicler/summary missing core sections")
        print("OK /api/v1/island/chronicler/summary [application/json]")

        status, payload = post_json(
            base + "/api/v1/island/part-b/runs",
            {
                "run_class": "operator-assisted",
                "subject_pet_name": "Smoke",
                "subject_pet_animal": "fox",
                "state_projection": {"health_pct": 82, "morale_pct": 75, "happiness_pct": 74, "energy_pct": 81},
            },
        )
        if status != 200 or not payload.get("id"):
            raise RuntimeError("/api/v1/island/part-b/runs did not create a run")
        run_id = str(payload["id"])
        print("OK /api/v1/island/part-b/runs [application/json]")

        status, content_type, body = fetch(base + "/api/v1/island/part-b/season")
        if status != 200 or content_type != "application/json" or '"season_id"' not in body:
            raise RuntimeError("Part B season endpoint invalid")
        print("OK /api/v1/island/part-b/season [application/json]")

        status, payload = post_json(
            base + f"/api/v1/island/part-b/runs/{run_id}/queue",
            {"action_verb": "CARE", "actor_type": "operator", "source": "smoke"},
        )
        if status != 200 or not payload.get("queued_item"):
            raise RuntimeError("Part B queue enqueue failed")
        queued_item_id = str(payload["queued_item"]["id"])
        print("OK /api/v1/island/part-b/runs/{id}/queue [application/json]")

        status, payload = post_json(base + f"/api/v1/island/part-b/runs/{run_id}/tick", {"count": 1})
        processed = payload.get("processed") or []
        if status != 200 or not processed or processed[0].get("action_verb") != "CARE":
            raise RuntimeError("Part B tick processing did not execute queued CARE action")
        print("OK /api/v1/island/part-b/runs/{id}/tick [application/json]")

        status, payload = delete_json(base + f"/api/v1/island/part-b/runs/{run_id}/queue/{queued_item_id}")
        if status != 200 or payload.get("removed") not in {False, True}:
            raise RuntimeError("Part B queue delete returned invalid payload")
        print("OK /api/v1/island/part-b/runs/{id}/queue/{item} [application/json]")

        status, content_type, body = fetch(base + "/api/v1/island/part-b/leaderboards?run_class=operator-assisted&limit=5")
        if status != 200 or content_type != "application/json" or '"welfare"' not in body:
            raise RuntimeError("Part B leaderboards endpoint invalid")
        print("OK /api/v1/island/part-b/leaderboards [application/json]")

        status, content_type, body = fetch(base + "/api/v1/island/part-b/calibration")
        if status != 200 or content_type != "application/json" or '"warnings"' not in body:
            raise RuntimeError("Part B calibration endpoint invalid")
        print("OK /api/v1/island/part-b/calibration [application/json]")

        status, content_type, body = fetch(base + f"/api/v1/island/part-b/runs/{run_id}/baseline/preview?policy=conservative")
        if status != 200 or content_type != "application/json" or '"action_verb"' not in body:
            raise RuntimeError("Part B baseline preview invalid")
        print("OK /api/v1/island/part-b/runs/{id}/baseline/preview [application/json]")

        status, payload = post_json(base + f"/api/v1/island/part-b/runs/{run_id}/baseline", {"policy": "conservative", "ticks": 1})
        if status != 200 or not payload.get("processed"):
            raise RuntimeError("Part B baseline execution failed")
        print("OK /api/v1/island/part-b/runs/{id}/baseline [application/json]")

        status, content_type, body = fetch(base + "/api/v1/island/part-b/season/archive?limit=25")
        if status != 200 or content_type != "application/json" or '"leaderboards"' not in body:
            raise RuntimeError("Part B season archive endpoint invalid")
        print("OK /api/v1/island/part-b/season/archive [application/json]")

        status, payload = post_json(
            base + "/api/v1/island/part-b/runs",
            {
                "run_class": "agent-only",
                "subject_pet_name": "Smoke Agent",
                "subject_pet_animal": "panther",
                "house_agent_enabled": True,
                "inference_budget_remaining": 1,
                "inference_budget_daily": 1,
                "state_projection": {"health_pct": 44, "morale_pct": 61, "happiness_pct": 42, "energy_pct": 31},
            },
        )
        if status != 200 or not payload.get("id"):
            raise RuntimeError("Part B agent-only run creation failed")
        agent_run_id = str(payload["id"])

        status, content_type, preview_body = fetch(base + f"/api/v1/island/part-b/runs/{agent_run_id}/house-agent/preview")
        if status != 200 or content_type != "application/json" or '"action_verb"' not in preview_body:
            raise RuntimeError("Part B house-agent preview invalid")
        print("OK /api/v1/island/part-b/runs/{id}/house-agent/preview [application/json]")

        status, payload = post_json(base + f"/api/v1/island/part-b/runs/{agent_run_id}/tick", {"count": 2})
        if status != 200 or not payload.get("processed"):
            raise RuntimeError("Part B house-agent ticks failed")
        if payload["processed"][0].get("source") != "house-agent":
            raise RuntimeError("Part B house-agent did not produce a house-agent action")
        print("OK /api/v1/island/part-b/runs/{id}/tick house-agent [application/json]")

        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
