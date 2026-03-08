#!/usr/bin/env python3
"""Export compact seed+build data from tournament JSONL files.

Reads each tournament's results.jsonl and writes a slimmed-down version
containing only seeds, builds, and per-game winners — enough to replay
every match deterministically.

Output: data/exports/t{NNN}_seeds.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path


TOURNAMENTS = {
    "tournament_001": "t001_seeds.jsonl",
    "tournament_002": "t002_seeds.jsonl",
    "tournament_003": "t003_seeds.jsonl",
}

DATA_DIR = Path(__file__).parent / "data"
EXPORT_DIR = DATA_DIR / "exports"


def export_tournament(tournament: str, output_name: str) -> int:
    """Export one tournament's seed data. Returns number of series exported."""
    input_path = DATA_DIR / tournament / "results.jsonl"
    output_path = EXPORT_DIR / output_name

    if not input_path.exists():
        print(f"  SKIP {input_path} (not found)")
        return 0

    count = 0
    with open(input_path) as fin, open(output_path, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)

            # Tournament 001/002 have top-level build_a/build_b
            # Tournament 003 has per-game builds (adaptive format)
            has_top_level_builds = "build_a" in record and "build_b" in record

            compact_games = []
            for g in record.get("games", []):
                game_entry: dict = {"seed": g.get("seed", g.get("base_seed", 0))}

                # Determine winner for this game
                if "winner" in g and isinstance(g["winner"], str):
                    game_entry["winner"] = g["winner"]
                elif "winner_side" in g:
                    game_entry["winner"] = g["winner_side"]

                # Per-game builds (T003 adaptive format)
                if "build_a" in g:
                    game_entry["build_a"] = g["build_a"]
                if "build_b" in g:
                    game_entry["build_b"] = g["build_b"]

                compact_games.append(game_entry)

            compact: dict = {"series_id": record["series_id"]}
            if has_top_level_builds:
                compact["build_a"] = record["build_a"]
                compact["build_b"] = record["build_b"]
            compact["games"] = compact_games

            fout.write(json.dumps(compact, separators=(",", ":")) + "\n")
            count += 1

    return count


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Exporting seed data to {EXPORT_DIR}/")

    for tournament, output_name in TOURNAMENTS.items():
        count = export_tournament(tournament, output_name)
        if count:
            print(f"  {tournament} -> {output_name} ({count} series)")

    print("Done.")


if __name__ == "__main__":
    main()
