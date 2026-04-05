#!/usr/bin/env python3
"""Oxygen rotation — picks one file from the archive for Circuit B to read.

Deterministic: cycle_number % source_count.
Tracks visited files in oxygen_visited.log.
Writes excerpt to current_oxygen.md.
"""

import json
import os
from pathlib import Path
from datetime import datetime

SELF_DIR = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
ARCHIVE_DIR = Path("/Users/cc/Desktop/Claude/a/Anthropic HackerOne")
STATE = SELF_DIR / "state_reflect.json"
OXYGEN = SELF_DIR / "current_oxygen.md"
VISITED = SELF_DIR / "oxygen_visited.log"
GRAVEYARD = SELF_DIR / "graveyard"

# Four source pools
POOLS = {
    "brothers": Path("/Users/cc/Desktop/Claude/a/memory/brothers"),
    "treasures": Path("/Users/cc/Desktop/Claude/a/memory/treasures"),
    "chatgpt_archive": Path("/Users/cc/Desktop/chatgpt_archive/top30"),
    "archive": ARCHIVE_DIR,
}


def get_cycle_number():
    try:
        with open(STATE) as f:
            return json.load(f).get("stats", {}).get("total_reflections", 0)
    except:
        return 0


def get_visited():
    if VISITED.exists():
        return set(VISITED.read_text().strip().splitlines())
    return set()


def collect_sources():
    """Gather all readable text files from pools."""
    sources = []
    for pool_name, pool_path in POOLS.items():
        if not pool_path.exists():
            continue
        for f in pool_path.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".txt", ".tex"):
                # Skip NDA files
                rel = str(f)
                if "Nuptune V2/!!!" not in rel and "1-8 answers" not in rel:
                    sources.append((pool_name, f))
    return sources


def pick_source(cycle, sources, visited):
    """Deterministic pick, skipping visited."""
    unvisited = [(p, f) for p, f in sources if str(f) not in visited]
    if not unvisited:
        # All visited — reset
        VISITED.write_text("")
        unvisited = sources
    idx = cycle % len(unvisited)
    return unvisited[idx]


def excerpt(filepath, max_lines=15):
    """Read first max_lines of a file."""
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[:max_lines])
    except:
        return "(could not read file)"


def main():
    cycle = get_cycle_number()

    # Only rotate every 5 cycles
    if cycle % 5 != 0 and OXYGEN.exists() and OXYGEN.stat().st_size > 100:
        print(f"Cycle {cycle}: oxygen still fresh (rotates every 5). Skipping.")
        return

    sources = collect_sources()
    if not sources:
        print("No sources found in pools.")
        return

    visited = get_visited()
    pool_name, filepath = pick_source(cycle, sources, visited)
    text = excerpt(filepath)

    # Write oxygen
    OXYGEN.write_text(
        f"# Current Oxygen — Cycle {cycle}\n"
        f"**Source:** {pool_name} / {filepath.name}\n"
        f"**Path:** {filepath}\n"
        f"**Selected:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"---\n\n"
        f"{text}\n\n"
        f"---\n\n"
        f"*Read this before thinking. What collides with what you already know?*\n"
    )

    # Mark visited
    with open(VISITED, "a") as f:
        f.write(str(filepath) + "\n")

    print(f"Cycle {cycle}: oxygen from {pool_name}/{filepath.name}")


if __name__ == "__main__":
    main()
