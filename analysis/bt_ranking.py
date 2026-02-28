"""Rating systems: Elo (frontend UX) + Bradley-Terry (paper-grade).

Elo: online, incremental, per-match updates.
Bradley-Terry: offline, pairwise win counts -> MLE scores + bootstrap CIs.

Standalone version for the companion repository.

Usage:
    python analysis/bt_ranking.py data/tournament_002/results.jsonl
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


# -- Elo ----------------------------------------------------------------------


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def update_ratings(
    winner_elo: float,
    loser_elo: float,
    k: float = 32.0,
    draw: bool = False,
) -> tuple[float, float]:
    expected_w = expected_score(winner_elo, loser_elo)
    expected_l = expected_score(loser_elo, winner_elo)

    if draw:
        new_winner = winner_elo + k * (0.5 - expected_w)
        new_loser = loser_elo + k * (0.5 - expected_l)
    else:
        new_winner = winner_elo + k * (1.0 - expected_w)
        new_loser = loser_elo + k * (0.0 - expected_l)

    return new_winner, new_loser


# -- Bradley-Terry ------------------------------------------------------------


@dataclass(frozen=True)
class BTResult:
    """Bradley-Terry score for one agent/build."""

    name: str
    score: float
    ci_lower: float
    ci_upper: float
    sample_size: int


def _build_win_matrix(
    results: list[tuple[str, str]],
) -> tuple[list[str], dict[str, dict[str, int]], dict[str, int]]:
    """Build pairwise win count matrix from (winner, loser) tuples."""
    wins: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    counts: dict[str, int] = defaultdict(int)
    for winner, loser in results:
        wins[winner][loser] += 1
        counts[winner] += 1
        counts[loser] += 1
    names = sorted(counts.keys())
    return names, dict(wins), dict(counts)


def _bt_mle(
    names: list[str],
    wins: dict[str, dict[str, int]],
    max_iterations: int = 200,
    tol: float = 1e-8,
    smoothing: float = 0.5,
) -> dict[str, float]:
    """Maximum likelihood estimation of BT parameters.

    Uses iterative algorithm with Laplace smoothing to handle
    zero win counts (e.g., 100% win rates).
    """
    n = len(names)
    if n == 0:
        return {}

    scores = {name: 1.0 for name in names}

    for _ in range(max_iterations):
        new_scores: dict[str, float] = {}
        max_delta = 0.0

        for i in names:
            numerator = 0.0
            denominator = 0.0

            for j in names:
                if i == j:
                    continue
                w_ij = wins.get(i, {}).get(j, 0) + smoothing
                w_ji = wins.get(j, {}).get(i, 0) + smoothing
                total = w_ij + w_ji
                if total == 0:
                    continue
                numerator += w_ij
                denominator += total / (scores[i] + scores[j])

            if denominator > 0:
                new_scores[i] = numerator / denominator
            else:
                new_scores[i] = scores[i]

            max_delta = max(max_delta, abs(new_scores[i] - scores[i]))

        max_score = max(new_scores.values()) if new_scores else 1.0
        scores = {k: v / max_score for k, v in new_scores.items()}

        if max_delta < tol:
            break

    return scores


def compute_bt_scores(
    results: list[tuple[str, str]],
    n_bootstrap: int = 1000,
    bootstrap_seed: int | None = None,
) -> list[BTResult]:
    """Compute Bradley-Terry scores with bootstrap confidence intervals.

    Args:
        results: List of (winner_name, loser_name) tuples.
        n_bootstrap: Number of bootstrap resamples for CI.
        bootstrap_seed: Seed for reproducible bootstrap (None = random).

    Returns:
        List of BTResult sorted by score descending.
    """
    if not results:
        return []

    names, wins, sample_sizes = _build_win_matrix(results)
    point_scores = _bt_mle(names, wins)

    rng = random.Random(bootstrap_seed)
    bootstrap_scores: dict[str, list[float]] = {name: [] for name in names}

    for _ in range(n_bootstrap):
        resampled = [results[rng.randint(0, len(results) - 1)] for _ in range(len(results))]
        _, boot_wins, _ = _build_win_matrix(resampled)
        boot_scores = _bt_mle(names, boot_wins)
        for name in names:
            bootstrap_scores[name].append(boot_scores.get(name, 0.0))

    bt_results: list[BTResult] = []
    for name in names:
        samples = sorted(bootstrap_scores[name])
        n = len(samples)
        ci_lower = samples[max(0, int(n * 0.025))]
        ci_upper = samples[min(n - 1, int(n * 0.975))]
        bt_results.append(BTResult(
            name=name,
            score=round(point_scores.get(name, 0.0), 6),
            ci_lower=round(ci_lower, 6),
            ci_upper=round(ci_upper, 6),
            sample_size=sample_sizes.get(name, 0),
        ))

    bt_results.sort(key=lambda r: r.score, reverse=True)
    return bt_results


# -- CLI -----------------------------------------------------------------------


def load_results_from_jsonl(path: Path) -> list[tuple[str, str]]:
    """Load (winner, loser) pairs from a tournament JSONL file."""
    results: list[tuple[str, str]] = []
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

            winner_name = record.get("winner")
            agent_a = record.get("agent_a", "")
            agent_b = record.get("agent_b", "")

            if winner_name is None:
                continue
            if winner_name == agent_a:
                results.append((agent_a, agent_b))
            elif winner_name == agent_b:
                results.append((agent_b, agent_a))

    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python bt_ranking.py <results.jsonl>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    results = load_results_from_jsonl(path)
    print(f"Loaded {len(results)} match results from {path}")

    # Bradley-Terry
    bt = compute_bt_scores(results, n_bootstrap=1000, bootstrap_seed=42)
    print(f"\nBradley-Terry Rankings ({len(bt)} agents):")
    print(f"{'Rank':<5} {'Agent':<30} {'BT Score':<10} {'95% CI':<20} {'Games':<8}")
    print("-" * 75)
    for i, r in enumerate(bt, 1):
        ci = f"[{r.ci_lower:.4f}, {r.ci_upper:.4f}]"
        print(f"{i:<5} {r.name:<30} {r.score:<10.4f} {ci:<20} {r.sample_size:<8}")

    # Elo
    elo_ratings: dict[str, float] = defaultdict(lambda: 1500.0)
    for winner, loser in results:
        w_elo = elo_ratings[winner]
        l_elo = elo_ratings[loser]
        new_w, new_l = update_ratings(w_elo, l_elo)
        elo_ratings[winner] = new_w
        elo_ratings[loser] = new_l

    elo_sorted = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
    print(f"\nElo Rankings:")
    print(f"{'Rank':<5} {'Agent':<30} {'Elo':<10}")
    print("-" * 45)
    for i, (name, elo) in enumerate(elo_sorted, 1):
        print(f"{i:<5} {name:<30} {elo:<10.0f}")


if __name__ == "__main__":
    main()
