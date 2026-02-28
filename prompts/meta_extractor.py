"""Extract top-N builds from tournament JSONL data.

Reads tournament results and ranks builds by win rate.
Used to inject meta context into LLMAgentV2 prompts.

Standalone version for the companion repository.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def extract_top_builds(jsonl_path: Path, top_n: int = 5) -> list[dict]:
    """Extract the top-N builds by win rate from tournament JSONL.

    Args:
        jsonl_path: Path to results.jsonl from a tournament run.
        top_n: Number of top builds to return.

    Returns:
        List of dicts sorted by win_rate descending:
        [{"animal": "BEAR", "hp": 3, "atk": 14, "spd": 2, "wil": 1,
          "win_rate": 0.90, "games": 100}, ...]
    """
    wins: dict[str, int] = defaultdict(int)
    losses: dict[str, int] = defaultdict(int)

    if not jsonl_path.exists():
        return []

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            if record.get("error") is not None:
                continue
            if record.get("winner") is None:
                continue

            build_a = record.get("build_a")
            build_b = record.get("build_b")
            if build_a is None or build_b is None:
                continue

            # Skip RandomAgent and HighVarianceAgent entries (noise)
            agent_a = record.get("agent_a", "")
            agent_b = record.get("agent_b", "")
            skip_agents = {"RandomAgent", "HighVarianceAgent"}

            key_a = _build_key(build_a)
            key_b = _build_key(build_b)

            winner = record["winner"]
            if agent_a not in skip_agents:
                if winner == agent_a:
                    wins[key_a] += 1
                else:
                    losses[key_a] += 1

            if agent_b not in skip_agents:
                if winner == agent_b:
                    wins[key_b] += 1
                else:
                    losses[key_b] += 1

    all_keys = set(wins.keys()) | set(losses.keys())
    if not all_keys:
        return []

    ranked: list[dict] = []
    for key in all_keys:
        w = wins[key]
        total = w + losses[key]
        if total == 0:
            continue
        animal, hp, atk, spd, wil = _parse_key(key)
        ranked.append({
            "animal": animal,
            "hp": hp,
            "atk": atk,
            "spd": spd,
            "wil": wil,
            "win_rate": round(w / total, 4),
            "games": total,
        })

    ranked.sort(key=lambda x: (-x["win_rate"], -x["games"]))
    return ranked[:top_n]


def _build_key(build: dict) -> str:
    """Create a canonical string key for a build dict."""
    animal = build.get("animal", "unknown").upper()
    hp = build.get("hp", 0)
    atk = build.get("atk", 0)
    spd = build.get("spd", 0)
    wil = build.get("wil", 0)
    return f"{animal}/{hp}/{atk}/{spd}/{wil}"


def _parse_key(key: str) -> tuple[str, int, int, int, int]:
    """Parse a build key back into components."""
    parts = key.split("/")
    return parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python meta_extractor.py <results.jsonl> [top_n]")
        sys.exit(1)

    path = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    builds = extract_top_builds(path, n)
    for i, b in enumerate(builds, 1):
        wr = b["win_rate"]
        print(f"  {i}. {b['animal']} {b['hp']}/{b['atk']}/{b['spd']}/{b['wil']} "
              f"-- {wr:.0%} win rate ({b['games']} games)")
