#!/usr/bin/env python3
"""Verify the frozen simulator config hash."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent.parent / "simulator" / "config.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    embedded = config.get("sha256")
    payload = {k: v for k, v in config.items() if k != "sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    derived = hashlib.sha256(canonical).hexdigest()

    print(f"config_path={CONFIG_PATH}")
    print(f"embedded_sha256={embedded}")
    print(f"derived_sha256={derived}")

    if embedded != derived:
        print("status=FAIL")
        return 1

    print("status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
