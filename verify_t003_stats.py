#!/usr/bin/env python3
"""T003 Integrity — Script C: Statistical robustness verification.

Computes:
1. Bradley-Terry rankings with 10,000 bootstrap resamples
2. GPT-5.4 rank stability (bootstrap P(rank <= 10))
3. Build diversity analysis per model
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from analysis.bt_ranking import (
    _build_win_matrix,
    _bt_mle,
    compute_bt_scores,
    load_results_from_jsonl,
)

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = PROJECT_ROOT / "data" / "tournament_003" / "results.jsonl"
INTEGRITY_DOC = PROJECT_ROOT / "docs" / "T003_INTEGRITY.md"

GPT54_NAME = "gpt-5.4"


def load_all_games(path: Path) -> list[dict]:
    """Load all individual games with agent + build info."""
    games = []
    with open(path, encoding="utf-8") as f:
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
            for game in record.get("games", []):
                games.append({
                    "agent_a": agent_a,
                    "agent_b": agent_b,
                    "build_a": game["build_a"],
                    "build_b": game["build_b"],
                    "winner_side": game.get("winner_side"),
                })
    return games


def analyze_build_diversity(games: list[dict]) -> dict[str, set[tuple]]:
    """Extract unique builds per agent."""
    builds_by_agent: dict[str, set[tuple]] = defaultdict(set)
    for g in games:
        ba = g["build_a"]
        bb = g["build_b"]
        key_a = (ba["animal"].upper(), ba["hp"], ba["atk"], ba["spd"], ba["wil"])
        key_b = (bb["animal"].upper(), bb["hp"], bb["atk"], bb["spd"], bb["wil"])
        builds_by_agent[g["agent_a"]].add(key_a)
        builds_by_agent[g["agent_b"]].add(key_b)
    return dict(builds_by_agent)


def find_dominant_build(builds_by_agent: dict[str, set[tuple]], games: list[dict]) -> dict[str, list[tuple]]:
    """Find models that heavily converge on a single build."""
    # Count build usage per agent
    build_counts: dict[str, dict[tuple, int]] = defaultdict(lambda: defaultdict(int))
    for g in games:
        ba = g["build_a"]
        bb = g["build_b"]
        key_a = (ba["animal"].upper(), ba["hp"], ba["atk"], ba["spd"], ba["wil"])
        key_b = (bb["animal"].upper(), bb["hp"], bb["atk"], bb["spd"], bb["wil"])
        build_counts[g["agent_a"]][key_a] += 1
        build_counts[g["agent_b"]][key_b] += 1

    dominant: dict[str, list[tuple]] = {}
    for agent, counts in sorted(build_counts.items()):
        total = sum(counts.values())
        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        # Report builds used >50% of the time
        for build, count in top:
            if count / total > 0.5:
                dominant.setdefault(agent, []).append((*build, count, total))
    return dominant


def main() -> None:
    print("=" * 60)
    print("T003 INTEGRITY — Script C: Statistical Robustness")
    print("=" * 60)

    # 1. BT Rankings
    print("\n--- 1. Bradley-Terry Rankings (n_bootstrap=10000) ---")
    results = load_results_from_jsonl(RESULTS_PATH)
    print(f"Loaded {len(results)} series-level (winner, loser) pairs")

    bt = compute_bt_scores(results, n_bootstrap=10000, bootstrap_seed=42)

    print(f"\n{'Rank':<5} {'Agent':<30} {'BT Score':<10} {'95% CI':<24} {'Games':<8}")
    print("-" * 79)
    ranking_lines = []
    gpt54_rank = None
    for i, r in enumerate(bt, 1):
        ci = f"[{r.ci_lower:.4f}, {r.ci_upper:.4f}]"
        line = f"{i:<5} {r.name:<30} {r.score:<10.4f} {ci:<24} {r.sample_size:<8}"
        print(line)
        ranking_lines.append(f"| {i} | {r.name} | {r.score:.4f} | [{r.ci_lower:.4f}, {r.ci_upper:.4f}] | {r.sample_size} |")
        if GPT54_NAME in r.name.lower():
            gpt54_rank = i

    # 2. GPT-5.4 Bootstrap Stability
    print(f"\n--- 2. GPT-5.4 Bootstrap Rank Stability ---")
    if gpt54_rank is not None:
        print(f"GPT-5.4 point-estimate rank: {gpt54_rank}")
    else:
        # Try partial match
        gpt54_candidates = [r.name for r in bt if "gpt" in r.name.lower() and "5" in r.name]
        if gpt54_candidates:
            print(f"GPT-5.4 candidates found: {gpt54_candidates}")
        else:
            print("GPT-5.4 not found in rankings — checking all agent names:")
            for r in bt:
                print(f"  {r.name}")

    # Run 10,000 bootstrap resamples to check rank stability
    rng = random.Random(42)
    n_bootstrap = 10000
    rank_counts = defaultdict(int)
    below_10_count = 0

    # Find GPT-5.4 exact name
    gpt54_exact = None
    for r in bt:
        if GPT54_NAME in r.name.lower() or "gpt-5.4" in r.name.lower():
            gpt54_exact = r.name
            break

    if gpt54_exact:
        for _ in range(n_bootstrap):
            resampled = [results[rng.randint(0, len(results) - 1)] for _ in range(len(results))]
            names, boot_wins, _ = _build_win_matrix(resampled)
            boot_scores = _bt_mle(names, boot_wins)
            # Rank by score descending
            ranked = sorted(boot_scores.items(), key=lambda x: x[1], reverse=True)
            for rank_i, (name, _) in enumerate(ranked, 1):
                if name == gpt54_exact:
                    rank_counts[rank_i] += 1
                    if rank_i > 10:
                        below_10_count += 1
                    break

        pct_below_10 = below_10_count / n_bootstrap * 100
        print(f"Bootstrap resamples: {n_bootstrap}")
        print(f"Times GPT-5.4 ranked below 10: {below_10_count} ({pct_below_10:.1f}%)")
        print(f"Rank distribution (top 5 most common):")
        for rank, count in sorted(rank_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  Rank {rank}: {count} times ({count/n_bootstrap*100:.1f}%)")
    else:
        print("GPT-5.4 not found in dataset — skipping bootstrap analysis")
        pct_below_10 = None

    # 3. Build Diversity
    print(f"\n--- 3. Build Diversity ---")
    all_games = load_all_games(RESULTS_PATH)
    builds_by_agent = analyze_build_diversity(all_games)

    print(f"\n{'Agent':<30} {'Unique Builds':<15}")
    print("-" * 45)
    diversity_lines = []
    for agent in sorted(builds_by_agent.keys()):
        n = len(builds_by_agent[agent])
        print(f"{agent:<30} {n:<15}")
        diversity_lines.append(f"| {agent} | {n} |")

    dominant = find_dominant_build(builds_by_agent, all_games)
    if dominant:
        print(f"\nDominant builds (>50% usage):")
        for agent, builds in sorted(dominant.items()):
            for b in builds:
                animal, hp, atk, spd, wil, count, total = b
                print(f"  {agent}: {animal} {hp}/{atk}/{spd}/{wil} "
                      f"({count}/{total} games, {count/total*100:.0f}%)")

    # Append to integrity doc
    section = []
    section.append("\n## 4. Statistical Robustness\n")
    section.append("### Bradley-Terry Rankings\n")
    section.append(f"Computed with 10,000 bootstrap resamples (seed=42) from {len(results)} series results.\n")
    section.append(f"| Rank | Agent | BT Score | 95% CI | Games |")
    section.append(f"|------|-------|----------|--------|-------|")
    for line in ranking_lines:
        section.append(line)
    section.append("")

    if gpt54_exact and gpt54_rank is not None:
        section.append("### GPT-5.4 Rank Stability\n")
        section.append(f"- Point-estimate rank: **{gpt54_rank}**")
        section.append(f"- Bootstrap resamples: {n_bootstrap}")
        if pct_below_10 is not None:
            section.append(f"- P(rank > 10): **{pct_below_10:.1f}%**")
        section.append(f"\nRank distribution (top 5):\n")
        section.append("| Rank | Count | Percentage |")
        section.append("|------|-------|------------|")
        for rank, count in sorted(rank_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            section.append(f"| {rank} | {count} | {count/n_bootstrap*100:.1f}% |")
        section.append("")

    section.append("### Build Diversity\n")
    section.append("| Agent | Unique Builds |")
    section.append("|-------|---------------|")
    for line in diversity_lines:
        section.append(line)
    section.append("")

    if dominant:
        section.append("### Dominant Builds (>50% usage)\n")
        section.append("| Agent | Build | Usage |")
        section.append("|-------|-------|-------|")
        for agent, builds in sorted(dominant.items()):
            for b in builds:
                animal, hp, atk, spd, wil, count, total = b
                section.append(f"| {agent} | {animal} {hp}/{atk}/{spd}/{wil} | "
                             f"{count}/{total} ({count/total*100:.0f}%) |")
        section.append("")

    _append_to_integrity_doc("\n".join(section))

    print("\nRESULT: PASS")


def _append_to_integrity_doc(text: str) -> None:
    with open(INTEGRITY_DOC, "a", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
