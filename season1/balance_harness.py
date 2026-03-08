"""
Balance testing harness for Moreau Arena Season 1.

Runs a full round-robin tournament of all 14 animals at 5/5/5/5 stats,
checks quality gates, and produces reports.

Usage:
    python -m season1.balance_harness [--games N] [--workers N]
"""

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Attempt to import the engine
# ---------------------------------------------------------------------------
try:
    from season1.engine_s1 import run_match
except ImportError:
    print("Waiting for engine_s1.py...")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ANIMALS = [
    "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
    "porcupine", "scorpion", "vulture", "rhino", "viper",
    "fox", "eagle", "panther",
]

BALANCED_STATS = (5, 5, 5, 5)

DEFAULT_GAMES = 1000
SEASON1_DIR = os.path.join(os.path.dirname(__file__))

# Gate thresholds
GATE_MAX_WR = 0.58
GATE_MIN_WR = 0.42
GATE_BEATS_THRESHOLD = 0.52
GATE_RNG_SPREAD = 0.25
GATE_COSINE_SIM = 0.95

# ---------------------------------------------------------------------------
# Seed helper
# ---------------------------------------------------------------------------

def make_seed(i: int, j: int, k: int) -> int:
    """Deterministic seed for pair (i, j) game k."""
    raw = hashlib.sha256(f"{i}_{j}_{k}".encode()).hexdigest()
    return int(raw, 16) & 0xFFFFFFFFFFFFFFFF


# ---------------------------------------------------------------------------
# Worker function (top-level so it is picklable)
# ---------------------------------------------------------------------------

def run_pair(args):
    """Run all games for one (i, j) pair. Returns (i, j, results_list)."""
    i, j, n_games, animal_i, animal_j = args
    results = []
    half = n_games // 2

    # First half: animal_i as side A, animal_j as side B
    for k in range(half):
        seed = make_seed(i, j, k)
        res = run_match(animal_i, BALANCED_STATS, animal_j, BALANCED_STATS, seed)
        results.append(res)

    # Second half: swap sides — animal_j as side A, animal_i as side B
    for k in range(half, n_games):
        seed = make_seed(i, j, k)
        res = run_match(animal_j, BALANCED_STATS, animal_i, BALANCED_STATS, seed)
        # Flip winner label so it's still from perspective of i vs j
        if res["winner"] == "a":
            res = {**res, "winner": "b"}
        elif res["winner"] == "b":
            res = {**res, "winner": "a"}
        results.append(res)

    return (i, j, results)


# ---------------------------------------------------------------------------
# Gate checks
# ---------------------------------------------------------------------------

def check_g1(overall_wr: dict) -> tuple:
    """G1: No animal > 58% overall win rate."""
    worst = max(overall_wr.items(), key=lambda x: x[1])
    passed = worst[1] <= GATE_MAX_WR
    return passed, worst

def check_g2(overall_wr: dict) -> tuple:
    """G2: No animal < 42% overall win rate."""
    worst = min(overall_wr.items(), key=lambda x: x[1])
    passed = worst[1] >= GATE_MIN_WR
    return passed, worst

def check_g3(pairwise: dict) -> tuple:
    """G3: Non-transitive cycles exist (A>B>C>A at >52%)."""
    # Build full WR lookup (pairwise only stores one direction)
    full_wr = {}
    for (a, b), wr in pairwise.items():
        full_wr[(a, b)] = wr
        full_wr[(b, a)] = 1.0 - wr

    # Build directed graph of "beats" edges
    beats = defaultdict(set)
    for (a, b), wr in full_wr.items():
        if wr > GATE_BEATS_THRESHOLD:
            beats[a].add(b)

    # Find at least one 3-cycle
    cycles = []
    seen = set()
    for a in ANIMALS:
        for b in beats[a]:
            for c in beats[b]:
                if a in beats[c]:
                    cycle = tuple(sorted([a, b, c]))
                    if cycle not in seen:
                        seen.add(cycle)
                        cycles.append((a, b, c))
                        if len(cycles) >= 5:
                            return True, cycles
    return len(cycles) > 0, cycles

def check_g4(pair_results: dict, n_games: int) -> tuple:
    """G4: RNG variance — split each matchup into 10 batches, check spread."""
    n_batches = 10
    batch_size = n_games // n_batches
    if batch_size == 0:
        return True, {}  # Too few games to test

    flagged = {}
    for (i, j), results in pair_results.items():
        batch_wrs = []
        for b in range(n_batches):
            batch = results[b * batch_size : (b + 1) * batch_size]
            wins = sum(1 for r in batch if r["winner"] == "a")
            batch_wrs.append(wins / len(batch) if batch else 0.5)
        spread = max(batch_wrs) - min(batch_wrs)
        if spread > GATE_RNG_SPREAD:
            flagged[(ANIMALS[i], ANIMALS[j])] = {
                "spread": round(spread, 4),
                "batch_wrs": [round(w, 4) for w in batch_wrs],
            }

    return len(flagged) == 0, flagged

def check_g5(pairwise: dict) -> tuple:
    """G5: Distinct identities — cosine similarity of mean-centered matchup vectors < 0.95.

    Mean-centering ensures we compare matchup *patterns* (who beats whom)
    rather than overall strength. Without centering, all vectors cluster
    near [0.5, 0.5, ...] and have cos sim ~1.0 regardless of matchup structure.
    """
    # Build matchup vectors for each animal
    vectors = {}
    for a in ANIMALS:
        vec = []
        for b in ANIMALS:
            if a == b:
                continue
            key = (a, b) if (a, b) in pairwise else None
            if key:
                vec.append(pairwise[key])
            else:
                # Use 1 - reverse
                vec.append(1.0 - pairwise.get((b, a), 0.5))
        # Mean-center the vector to compare patterns, not absolute strength
        mean = sum(vec) / len(vec) if vec else 0.0
        vectors[a] = [v - mean for v in vec]

    def cosine_sim(v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    similar_pairs = []
    for a, b in itertools.combinations(ANIMALS, 2):
        sim = cosine_sim(vectors[a], vectors[b])
        if sim >= GATE_COSINE_SIM:
            similar_pairs.append((a, b, round(sim, 4)))

    return len(similar_pairs) == 0, similar_pairs


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_pairwise_csv(pairwise: dict, path: str):
    """Write pairwise win-rate matrix to CSV."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([""] + ANIMALS)
        for a in ANIMALS:
            row = [a]
            for b in ANIMALS:
                if a == b:
                    row.append("")
                elif (a, b) in pairwise:
                    row.append(f"{pairwise[(a, b)]:.4f}")
                else:
                    row.append(f"{1.0 - pairwise[(b, a)]:.4f}")
            writer.writerow(row)


def build_balance_json(overall_wr, pairwise, gates):
    """Build the JSON results dict."""
    per_animal = {}
    for a in ANIMALS:
        matchups = {}
        for b in ANIMALS:
            if a == b:
                continue
            if (a, b) in pairwise:
                matchups[b] = round(pairwise[(a, b)], 4)
            else:
                matchups[b] = round(1.0 - pairwise[(b, a)], 4)
        best = max(matchups.items(), key=lambda x: x[1])
        worst = min(matchups.items(), key=lambda x: x[1])
        per_animal[a] = {
            "overall_wr": round(overall_wr[a], 4),
            "best_matchup": {"vs": best[0], "wr": best[1]},
            "worst_matchup": {"vs": worst[0], "wr": worst[1]},
        }

    # Sort by win rate descending
    ranked = sorted(per_animal.items(), key=lambda x: x[1]["overall_wr"], reverse=True)

    return {
        "animals": {k: v for k, v in ranked},
        "gates": gates,
    }


def write_markdown_report(balance_json, pairwise, gates, cycles, path, n_games):
    """Write BALANCE_REPORT.md."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Moreau Arena Season 1 -- Balance Report",
        "",
        f"Generated: {ts}",
        f"Games per pair: {n_games}",
        "",
        "## Rankings by Win Rate",
        "",
        "| Rank | Animal | WR | Best Matchup | Worst Matchup |",
        "|------|--------|----|-------------|---------------|",
    ]

    for rank, (name, data) in enumerate(balance_json["animals"].items(), 1):
        best = f"{data['best_matchup']['vs']} ({data['best_matchup']['wr']:.2%})"
        worst = f"{data['worst_matchup']['vs']} ({data['worst_matchup']['wr']:.2%})"
        lines.append(f"| {rank} | {name} | {data['overall_wr']:.2%} | {best} | {worst} |")

    lines += ["", "## Pairwise Matrix (condensed)", ""]
    # Header
    short = [a[:4] for a in ANIMALS]
    lines.append("| | " + " | ".join(short) + " |")
    lines.append("|---" * (len(ANIMALS) + 1) + "|")
    for a in ANIMALS:
        row_vals = []
        for b in ANIMALS:
            if a == b:
                row_vals.append("--")
            elif (a, b) in pairwise:
                row_vals.append(f"{pairwise[(a, b)]:.0%}")
            else:
                row_vals.append(f"{1.0 - pairwise[(b, a)]:.0%}")
        lines.append(f"| {a[:4]} | " + " | ".join(row_vals) + " |")

    lines += ["", "## Gate Results", ""]
    for gname, gdata in gates.items():
        status = "PASS" if gdata["passed"] else "FAIL"
        lines.append(f"- **{gname}**: {status} -- {gdata['detail']}")

    if cycles:
        lines += ["", "## Non-Transitive Cycles Found", ""]
        for c in cycles[:10]:
            lines.append(f"- {c[0]} > {c[1]} > {c[2]} > {c[0]}")

    lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Moreau Arena Season 1 Balance Harness")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES,
                        help=f"Games per pair (default {DEFAULT_GAMES})")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers (default: cpu_count)")
    args = parser.parse_args()

    n_games = args.games
    n_workers = args.workers or os.cpu_count() or 4

    # Make sure n_games is even for clean side-split
    if n_games % 2 != 0:
        n_games += 1
        print(f"Rounded --games up to {n_games} for even side-split.")

    pairs = list(itertools.combinations(range(len(ANIMALS)), 2))
    total_pairs = len(pairs)
    total_games = total_pairs * n_games

    print(f"Moreau Arena Season 1 -- Balance Harness")
    print(f"Animals: {len(ANIMALS)}, Pairs: {total_pairs}, Games/pair: {n_games}")
    print(f"Total games: {total_games:,}, Workers: {n_workers}")
    print()

    # Build work items
    work = []
    for i, j in pairs:
        work.append((i, j, n_games, ANIMALS[i], ANIMALS[j]))

    # Run round-robin
    pair_results = {}  # (i, j) -> list of result dicts
    completed = 0
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_pair, w): w for w in work}
        for future in as_completed(futures):
            i, j, results = future.result()
            pair_results[(i, j)] = results
            completed += 1
            if completed % 10 == 0 or completed == total_pairs:
                elapsed = time.time() - t0
                print(f"  [{completed}/{total_pairs}] pairs done  ({elapsed:.1f}s)")

    elapsed = time.time() - t0
    print(f"\nAll {total_pairs} pairs completed in {elapsed:.1f}s")
    print()

    # ---------------------------------------------------------------------------
    # Compute pairwise win rates (from perspective of animal i = "a" side)
    # ---------------------------------------------------------------------------
    pairwise = {}  # (animal_name_i, animal_name_j) -> win rate of i
    for (i, j), results in pair_results.items():
        wins_i = sum(1 for r in results if r["winner"] == "a")
        draws = sum(1 for r in results if r["winner"] is None)
        wr = (wins_i + draws * 0.5) / len(results)
        pairwise[(ANIMALS[i], ANIMALS[j])] = round(wr, 6)

    # Overall win rates
    overall_wr = {}
    for a in ANIMALS:
        wrs = []
        for b in ANIMALS:
            if a == b:
                continue
            if (a, b) in pairwise:
                wrs.append(pairwise[(a, b)])
            else:
                wrs.append(1.0 - pairwise[(b, a)])
        overall_wr[a] = sum(wrs) / len(wrs)

    # ---------------------------------------------------------------------------
    # Gate checks
    # ---------------------------------------------------------------------------
    gates = {}

    g1_pass, g1_worst = check_g1(overall_wr)
    gates["G1_max_wr"] = {
        "passed": g1_pass,
        "detail": f"Max WR: {g1_worst[0]} at {g1_worst[1]:.4f} (limit {GATE_MAX_WR})",
    }

    g2_pass, g2_worst = check_g2(overall_wr)
    gates["G2_min_wr"] = {
        "passed": g2_pass,
        "detail": f"Min WR: {g2_worst[0]} at {g2_worst[1]:.4f} (limit {GATE_MIN_WR})",
    }

    g3_pass, g3_cycles = check_g3(pairwise)
    gates["G3_nontransitive"] = {
        "passed": g3_pass,
        "detail": f"Found {len(g3_cycles)} cycle(s)",
    }

    g4_pass, g4_flagged = check_g4(pair_results, n_games)
    gates["G4_rng_variance"] = {
        "passed": g4_pass,
        "detail": f"{len(g4_flagged)} matchup(s) flagged" if g4_flagged else "All matchups within tolerance",
    }

    g5_pass, g5_similar = check_g5(pairwise)
    gates["G5_distinct_identities"] = {
        "passed": g5_pass,
        "detail": f"{len(g5_similar)} similar pair(s)" if g5_similar else "All animals distinct",
    }

    # ---------------------------------------------------------------------------
    # Print results
    # ---------------------------------------------------------------------------
    print("=" * 60)
    print("  BALANCE RESULTS -- Sorted by Win Rate")
    print("=" * 60)
    ranked = sorted(overall_wr.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, wr) in enumerate(ranked, 1):
        # Find best and worst matchup
        matchups = {}
        for b in ANIMALS:
            if name == b:
                continue
            if (name, b) in pairwise:
                matchups[b] = pairwise[(name, b)]
            else:
                matchups[b] = 1.0 - pairwise[(b, name)]
        best = max(matchups.items(), key=lambda x: x[1])
        worst = min(matchups.items(), key=lambda x: x[1])
        print(f"  {rank:2d}. {name:12s}  WR={wr:.4f}  best={best[0]}({best[1]:.2f})  worst={worst[0]}({worst[1]:.2f})")

    print()
    print("=" * 60)
    print("  GATE CHECKS")
    print("=" * 60)
    all_passed = True
    for gname, gdata in gates.items():
        status = "PASS" if gdata["passed"] else "FAIL"
        marker = "  " if gdata["passed"] else ">>"
        if not gdata["passed"]:
            all_passed = False
        print(f"  {marker} {gname}: {status} -- {gdata['detail']}")

    print()
    if all_passed:
        print("  >>> ALL GATES PASSED <<<")
    else:
        print("  >>> SOME GATES FAILED -- see details above <<<")
    print()

    # ---------------------------------------------------------------------------
    # Write outputs
    # ---------------------------------------------------------------------------
    csv_path = os.path.join(SEASON1_DIR, "pairwise_matrix.csv")
    write_pairwise_csv(pairwise, csv_path)
    print(f"Pairwise CSV: {csv_path}")

    balance_json = build_balance_json(overall_wr, pairwise, gates)
    json_path = os.path.join(SEASON1_DIR, "balance_results.json")
    with open(json_path, "w") as f:
        json.dump(balance_json, f, indent=2)
    print(f"JSON results: {json_path}")

    md_path = os.path.join(SEASON1_DIR, "BALANCE_REPORT.md")
    write_markdown_report(balance_json, pairwise, gates, g3_cycles, md_path, n_games)
    print(f"Markdown report: {md_path}")


if __name__ == "__main__":
    main()
