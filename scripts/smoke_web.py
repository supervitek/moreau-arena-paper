#!/usr/bin/env python3
"""Lightweight smoke test for the live-facing Moreau Arena web app.

Starts a local Uvicorn server, checks a handful of critical HTML routes,
API routes, and static assets, then exits non-zero on the first failure.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "http://127.0.0.1:8765"
PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"


CHECKS: list[tuple[str, str]] = [
    ("/", "text/html"),
    ("/leaderboard", "text/html"),
    ("/leaderboard?track=C", "text/html"),
    ("/s1-leaderboard", "text/html"),
    ("/s1-fighters", "text/html"),
    ("/s1-matchups", "text/html"),
    ("/pets", "text/html"),
    ("/pets/home", "text/html"),
    ("/pets/train", "text/html"),
    ("/island/home", "text/html"),
    ("/moreddit", "text/html"),
    ("/api/v1/leaderboard/bt?track=C", "application/json"),
    ("/api/v1/s1/tournament", "application/json"),
    ("/static/og-image.png", "image/png"),
]

BODY_MUST_CONTAIN: dict[str, str] = {
    "/s1-fighters": "Meet the Fighters",
    "/s1-matchups": "Matchup Explorer",
    "/pets/home": 'property="og:image"',
    "/pets/train": "Training Grounds",
    "/island/home": 'property="og:image"',
}

BODY_MUST_NOT_CONTAIN: dict[str, str] = {
    "/s1-fighters": "(Preview)",
    "/s1-matchups": "(Preview)",
}


def fetch(path: str) -> tuple[int, str, bytes]:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_until_ready() -> None:
    deadline = time.time() + 60
    last_error = "server did not start"
    while time.time() < deadline:
        try:
            status, _, _ = fetch("/")
            if status == 200:
                return
        except Exception as exc:  # pragma: no cover - startup polling
            last_error = str(exc)
        time.sleep(0.4)
    raise RuntimeError(last_error)


def main() -> int:
    global BASE_URL
    port = pick_port()
    BASE_URL = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [
            str(PYTHON_BIN if PYTHON_BIN.exists() else Path(sys.executable)),
            "-m",
            "uvicorn",
            "web.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_until_ready()

        for path, expected_content_type in CHECKS:
            status, content_type, body = fetch(path)
            if status != 200:
                raise RuntimeError(f"{path} returned {status}")
            if expected_content_type not in content_type:
                raise RuntimeError(
                    f"{path} returned unexpected content type {content_type!r}"
                )
            if path.endswith(".json") or "application/json" in expected_content_type:
                json.loads(body.decode("utf-8"))
            else:
                text = body.decode("utf-8", errors="ignore")
                required = BODY_MUST_CONTAIN.get(path)
                forbidden = BODY_MUST_NOT_CONTAIN.get(path)
                if required and required not in text:
                    raise RuntimeError(f"{path} missing expected marker {required!r}")
                if forbidden and forbidden in text:
                    raise RuntimeError(f"{path} still contains forbidden marker {forbidden!r}")
            print(f"OK {path} [{content_type}]")

        return 0
    except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"SMOKE FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
