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

        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
