from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from part_b_state import part_b_storage_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify local Part B readiness for Supabase productionization.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = {
        "storage_status": part_b_storage_status(),
        "env": {
            "SUPABASE_URL": bool(os.environ.get("SUPABASE_URL", "").strip()),
            "SUPABASE_SERVICE_ROLE_KEY": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()),
        },
        "schema_path": str(ROOT / "sql" / "PART_B_STATE_MIGRATION_B1_5.sql"),
        "schema_exists": (ROOT / "sql" / "PART_B_STATE_MIGRATION_B1_5.sql").exists(),
        "next_manual_steps": [
            "Apply sql/PART_B_STATE_MIGRATION_B1_5.sql to production Supabase",
            "Set SUPABASE_URL",
            "Set SUPABASE_SERVICE_ROLE_KEY",
            "Verify /api/v1/island/part-b/storage-status returns backend=supabase",
        ],
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
