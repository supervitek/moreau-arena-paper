"""Pairwise win-rate matrix from tournament JSONL data.

Reads tournament results and computes an agent x agent win-rate matrix.

Usage:
    python analysis/pairwise_matrix.py data/tournament_002/results.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def compute_pairwise_matrix(
    jsonl_path: Path,
) -> tuple[list[str], dict[tuple[str, str], float], dict[tuple[str, str], int]]:
    """Compute pairwise win rates from tournament JSONL.

    Returns:
        agents: Sorted list of agent names.
        win_rates: {(agent_a, agent_b): win_rate_of_a_vs_b}
        game_counts: {(agent_a, agent_b): total_games}
    """
    wins: dict[tuple[str, str], int] = defaultdict(int)
    totals: dict[tuple[str, str], int] = defaultdict(int)
    all_agents: set[str] = set()

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

            agent_a = record.get("agent_a", "")
            agent_b = record.get("agent_b", "")
            winner = record.get("winner")

            if not agent_a or not agent_b:
                continue

            all_agents.add(agent_a)
            all_agents.add(agent_b)

            totals[(agent_a, agent_b)] += 1
            totals[(agent_b, agent_a)] += 1

            if winner == agent_a:
                wins[(agent_a, agent_b)] += 1
            elif winner == agent_b:
                wins[(agent_b, agent_a)] += 1

    agents = sorted(all_agents)
    win_rates: dict[tuple[str, str], float] = {}
    game_counts: dict[tuple[str, str], int] = {}

    for a in agents:
        for b in agents:
            if a == b:
                win_rates[(a, b)] = 0.5
                game_counts[(a, b)] = 0
            else:
                total = totals.get((a, b), 0)
                w = wins.get((a, b), 0)
                win_rates[(a, b)] = round(w / total, 4) if total > 0 else 0.0
                game_counts[(a, b)] = total

    return agents, win_rates, game_counts


def print_matrix(
    agents: list[str],
    win_rates: dict[tuple[str, str], float],
    game_counts: dict[tuple[str, str], int],
) -> None:
    """Print pairwise win-rate matrix to stdout."""
    # Truncate long names for display
    max_name = 20
    short = {a: a[:max_name] for a in agents}

    # Header
    header = f"{'Agent':<{max_name}} | " + " | ".join(
        f"{short[b]:>6}" for b in agents
    )
    print(header)
    print("-" * len(header))

    # Rows
    for a in agents:
        cells = []
        for b in agents:
            wr = win_rates.get((a, b), 0.0)
            if a == b:
                cells.append(f"{'--':>6}")
            else:
                cells.append(f"{wr:>6.1%}")
        row = f"{short[a]:<{max_name}} | " + " | ".join(cells)
        print(row)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python pairwise_matrix.py <results.jsonl>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    agents, win_rates, game_counts = compute_pairwise_matrix(path)
    print(f"Pairwise Win-Rate Matrix ({len(agents)} agents)\n")
    print_matrix(agents, win_rates, game_counts)

    # Summary stats
    total_games = sum(game_counts.values()) // 2
    print(f"\nTotal games: {total_games}")


if __name__ == "__main__":
    main()
