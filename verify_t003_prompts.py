#!/usr/bin/env python3
"""T003 Integrity — Script A: Prompt hash verification + meta-hint scan.

Confirms:
1. SHA-256 of t003_prompt.txt matches the canonical hash.
2. Zero forbidden meta-hint phrases appear in any T003 JSONL data.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PROMPT_PATH = PROJECT_ROOT / "prompts" / "t003_prompt.txt"
DATA_DIR = PROJECT_ROOT / "data" / "tournament_003"
INTEGRITY_DOC = PROJECT_ROOT / "docs" / "T003_INTEGRITY.md"

CANONICAL_HASH = "a599ca7dacb21a59ebeda1ed434463c6ddcf3fdcba280e4ff2e9afc5335e524b"

FORBIDDEN_PHRASES = [
    "META CONTEXT",
    "top builds",
    "win rate",
    "ATK is important",
    "starting point",
    "100% win rate",
    "ranked by win rate",
]


def verify_prompt_hash() -> bool:
    """Verify SHA-256 of t003_prompt.txt."""
    data = PROMPT_PATH.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    ok = actual == CANONICAL_HASH
    print(f"Prompt hash: {actual}")
    print(f"Expected:    {CANONICAL_HASH}")
    print(f"Match: {'YES' if ok else 'NO — MISMATCH!'}")
    return ok


def scan_for_meta_hints() -> tuple[int, int, list[str]]:
    """Scan all JSONL files in T003 data for forbidden meta-hint phrases.

    Returns (files_checked, records_scanned, violations).
    """
    jsonl_files = sorted(DATA_DIR.glob("*.jsonl"))
    files_checked = 0
    records_scanned = 0
    violations: list[str] = []

    for path in jsonl_files:
        files_checked += 1
        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                records_scanned += 1

                # Serialize the entire record to a string and search
                record_str = json.dumps(record, ensure_ascii=False)
                for phrase in FORBIDDEN_PHRASES:
                    if phrase.lower() in record_str.lower():
                        violations.append(
                            f"{path.name}:{line_num} contains '{phrase}'"
                        )

    return files_checked, records_scanned, violations


def main() -> None:
    print("=" * 60)
    print("T003 INTEGRITY — Script A: Prompt & Meta-Hint Verification")
    print("=" * 60)

    print("\n--- 1. Prompt Hash Verification ---")
    hash_ok = verify_prompt_hash()

    print("\n--- 2. Meta-Hint Scan ---")
    files_checked, records_scanned, violations = scan_for_meta_hints()
    print(f"Files checked:   {files_checked}")
    print(f"Records scanned: {records_scanned}")
    print(f"Violations:      {len(violations)}")
    if violations:
        for v in violations:
            print(f"  VIOLATION: {v}")
    else:
        print("  No meta-hint phrases found in any T003 data.")

    # Append to integrity doc
    section = []
    section.append("\n## 1. Prompt Integrity\n")
    section.append(f"- T003 prompt SHA-256: `{CANONICAL_HASH}`")
    section.append(f"- Hash verified: **{'PASS' if hash_ok else 'FAIL'}**")
    section.append(f"- See `docs/T003_PROMPT_DIFF.md` for exact diff from T002")
    section.append("")
    section.append("## 2. Meta-Hint Scan\n")
    section.append(f"- Files checked: {files_checked}")
    section.append(f"- Records scanned: {records_scanned}")
    section.append(f"- Forbidden phrases searched: {len(FORBIDDEN_PHRASES)}")
    for p in FORBIDDEN_PHRASES:
        section.append(f'  - `"{p}"`')
    section.append(f"- Violations found: **{len(violations)}**")
    if not violations:
        section.append("- Result: **PASS** — zero meta-hints in T003 data")
    section.append("")

    _append_to_integrity_doc("\n".join(section))

    if not hash_ok or violations:
        print("\nRESULT: FAIL")
        sys.exit(1)
    else:
        print("\nRESULT: PASS")


def _append_to_integrity_doc(text: str) -> None:
    """Append text to the integrity document."""
    with open(INTEGRITY_DOC, "a", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
