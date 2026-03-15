#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
PORT = 8014

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
]


def fetch(url: str) -> tuple[int, str, str]:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8", errors="ignore")
        return response.status, response.headers.get_content_type(), body


def wait_until_ready(proc: subprocess.Popen[str]) -> None:
    base = f"http://127.0.0.1:{PORT}"
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

    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "web.app:app", "--port", str(PORT), "--log-level", "warning"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        wait_until_ready(proc)
        base = f"http://127.0.0.1:{PORT}"

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

        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
