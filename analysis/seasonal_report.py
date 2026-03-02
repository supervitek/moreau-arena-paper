"""Seasonal Meta Report Generator for Moreau Arena.

Generates a Markdown report (+ optional PNG heatmap) from tournament JSONL data.

Usage:
    python -m analysis.seasonal_report --data data/tournament_002/results.jsonl [--season N] [--prev data/tournament_001/results.jsonl]

Outputs:
    reports/season_{N}_report.md   — Full Markdown report
    reports/season_{N}_heatmap.png — Pairwise win-rate heatmap (if matplotlib available)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from analysis.bt_ranking import (
    compute_bt_scores,
    load_results_from_jsonl,
    update_ratings,
)
from analysis.pairwise_matrix import compute_pairwise_matrix

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAS_MATPLOTLIB = False
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    HAS_MATPLOTLIB = True
except ImportError:
    pass


def _load_records(jsonl_path: Path) -> list[dict]:
    """Load all non-error records from a JSONL file."""
    records: list[dict] = []
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
            records.append(record)
    return records


# ---------------------------------------------------------------------------
# Section 1: Leaderboard (BT + Elo)
# ---------------------------------------------------------------------------


def _build_leaderboard(
    results: list[tuple[str, str]],
) -> tuple[list[dict], list[tuple[str, float]]]:
    """Return (bt_rows, elo_sorted).

    bt_rows: list of dicts with keys name, bt_score, ci_lower, ci_upper, games.
    elo_sorted: list of (name, elo) sorted descending.
    """
    bt = compute_bt_scores(results, n_bootstrap=1000, bootstrap_seed=42)
    bt_rows = [
        {
            "name": r.name,
            "bt_score": r.score,
            "ci_lower": r.ci_lower,
            "ci_upper": r.ci_upper,
            "games": r.sample_size,
        }
        for r in bt
    ]

    elo_ratings: dict[str, float] = defaultdict(lambda: 1500.0)
    for winner, loser in results:
        w_elo = elo_ratings[winner]
        l_elo = elo_ratings[loser]
        new_w, new_l = update_ratings(w_elo, l_elo)
        elo_ratings[winner] = new_w
        elo_ratings[loser] = new_l

    elo_sorted = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
    return bt_rows, elo_sorted


def _format_leaderboard_md(
    bt_rows: list[dict], elo_sorted: list[tuple[str, float]]
) -> str:
    """Format the leaderboard as Markdown tables."""
    elo_map = {name: elo for name, elo in elo_sorted}

    lines = ["## Leaderboard", ""]
    lines.append(
        "| Rank | Agent | BT Score | 95% CI | Elo | Games |"
    )
    lines.append(
        "|------|-------|----------|--------|-----|-------|"
    )
    for i, row in enumerate(bt_rows, 1):
        ci = f"[{row['ci_lower']:.4f}, {row['ci_upper']:.4f}]"
        elo = elo_map.get(row["name"], 1500.0)
        lines.append(
            f"| {i} | {row['name']} | {row['bt_score']:.4f} | {ci} | {elo:.0f} | {row['games']} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 2: Pairwise heatmap
# ---------------------------------------------------------------------------


def _generate_heatmap_png(
    agents: list[str],
    win_rates: dict[tuple[str, str], float],
    output_path: Path,
) -> bool:
    """Generate a pairwise heatmap PNG. Returns True on success."""
    if not HAS_MATPLOTLIB:
        return False

    n = len(agents)
    matrix = np.zeros((n, n))
    for i, a in enumerate(agents):
        for j, b in enumerate(agents):
            matrix[i][j] = win_rates.get((a, b), 0.5)

    fig, ax = plt.subplots(figsize=(max(8, n * 0.8), max(7, n * 0.7)))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")

    # Truncate long names for display
    max_label = 18
    labels = [a[:max_label] for a in agents]

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = matrix[i][j]
            if i == j:
                text = "--"
            else:
                text = f"{val:.0%}"
            color = "black" if 0.3 < val < 0.7 else "white"
            ax.text(j, i, text, ha="center", va="center", fontsize=7, color=color)

    ax.set_title("Pairwise Win Rates (row vs column)")
    fig.colorbar(im, ax=ax, label="Win Rate", shrink=0.8)
    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)
    return True


def _format_pairwise_text(
    agents: list[str],
    win_rates: dict[tuple[str, str], float],
) -> str:
    """Format pairwise win rates as a Markdown table."""
    max_name = 20
    short = {a: a[:max_name] for a in agents}

    header_cells = " | ".join(f"{short[b]}" for b in agents)
    lines = [
        "## Pairwise Win Rates",
        "",
        f"| Agent | {header_cells} |",
        "|" + "---|" * (len(agents) + 1),
    ]
    for a in agents:
        cells = []
        for b in agents:
            if a == b:
                cells.append("--")
            else:
                wr = win_rates.get((a, b), 0.0)
                cells.append(f"{wr:.0%}")
        row = f"| {short[a]} | " + " | ".join(cells) + " |"
        lines.append(row)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 3: 3-cycle detection (A > B > C > A)
# ---------------------------------------------------------------------------


def _find_3_cycles(
    agents: list[str],
    win_rates: dict[tuple[str, str], float],
) -> list[tuple[str, str, str]]:
    """Find all A>B>C>A cycles where each win rate > 0.5."""
    cycles: list[tuple[str, str, str]] = []
    for a, b, c in combinations(agents, 3):
        # Check all 2 possible rotation directions for (a,b,c)
        # Direction 1: a>b>c>a
        if (
            win_rates.get((a, b), 0.0) > 0.5
            and win_rates.get((b, c), 0.0) > 0.5
            and win_rates.get((c, a), 0.0) > 0.5
        ):
            cycles.append((a, b, c))
        # Direction 2: a>c>b>a
        if (
            win_rates.get((a, c), 0.0) > 0.5
            and win_rates.get((c, b), 0.0) > 0.5
            and win_rates.get((b, a), 0.0) > 0.5
        ):
            cycles.append((a, c, b))
    return cycles


def _format_cycles_md(cycles: list[tuple[str, str, str]]) -> str:
    lines = ["## Non-Transitive Cycles (A > B > C > A)", ""]
    if not cycles:
        lines.append("No 3-cycles detected. The ranking is fully transitive.")
    else:
        lines.append(f"**{len(cycles)} cycle(s) detected:**\n")
        # Show up to 20 cycles to keep the report readable
        for i, (a, b, c) in enumerate(cycles[:20], 1):
            lines.append(f"{i}. {a} > {b} > {c} > {a}")
        if len(cycles) > 20:
            lines.append(f"\n... and {len(cycles) - 20} more.")
        lines.append("")

        # Summarize which agents appear in cycles
        involved: set[str] = set()
        for a, b, c in cycles:
            involved.update([a, b, c])
        lines.append(f"**Agents involved in cycles:** {', '.join(sorted(involved))}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 4: Signature builds per agent
# ---------------------------------------------------------------------------


def _extract_signature_builds(records: list[dict]) -> dict[str, dict]:
    """Find the most-used build per agent from JSONL records.

    Returns {agent_name: {"animal": str, "hp": int, ...., "count": int, "total": int}}.
    Handles both T001 (builds at series level) and T002 (builds per game).
    """
    build_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    game_totals: dict[str, int] = defaultdict(int)

    for record in records:
        agent_a = record.get("agent_a", "")
        agent_b = record.get("agent_b", "")
        games = record.get("games", [])

        # T002 format: builds per game inside games[]
        if games and "build_a" in games[0]:
            for game in games:
                ba = game.get("build_a", {})
                bb = game.get("build_b", {})
                if ba and agent_a:
                    key_a = f"{ba.get('animal','?')}|{ba.get('hp',0)}|{ba.get('atk',0)}|{ba.get('spd',0)}|{ba.get('wil',0)}"
                    build_counts[agent_a][key_a] += 1
                    game_totals[agent_a] += 1
                if bb and agent_b:
                    key_b = f"{bb.get('animal','?')}|{bb.get('hp',0)}|{bb.get('atk',0)}|{bb.get('spd',0)}|{bb.get('wil',0)}"
                    build_counts[agent_b][key_b] += 1
                    game_totals[agent_b] += 1
        else:
            # T001 format: builds at series level
            ba = record.get("build_a", {})
            bb = record.get("build_b", {})
            n_games = len(games) if games else record.get("games_played", 1)
            if ba and agent_a:
                key_a = f"{ba.get('animal','?')}|{ba.get('hp',0)}|{ba.get('atk',0)}|{ba.get('spd',0)}|{ba.get('wil',0)}"
                build_counts[agent_a][key_a] += n_games
                game_totals[agent_a] += n_games
            if bb and agent_b:
                key_b = f"{bb.get('animal','?')}|{bb.get('hp',0)}|{bb.get('atk',0)}|{bb.get('spd',0)}|{bb.get('wil',0)}"
                build_counts[agent_b][key_b] += n_games
                game_totals[agent_b] += n_games

    result: dict[str, dict] = {}
    for agent, counts in sorted(build_counts.items()):
        if not counts:
            continue
        top_key = max(counts, key=counts.get)  # type: ignore[arg-type]
        parts = top_key.split("|")
        total = game_totals[agent]
        result[agent] = {
            "animal": parts[0],
            "hp": int(parts[1]),
            "atk": int(parts[2]),
            "spd": int(parts[3]),
            "wil": int(parts[4]),
            "count": counts[top_key],
            "total": total,
        }
    return result


def _format_signature_builds_md(builds: dict[str, dict]) -> str:
    lines = ["## Signature Builds", ""]
    lines.append(
        "| Agent | Top Build | HP | ATK | SPD | WIL | Usage |"
    )
    lines.append(
        "|-------|-----------|----|----|-----|-----|-------|"
    )
    for agent, b in builds.items():
        pct = b["count"] / b["total"] * 100 if b["total"] > 0 else 0
        lines.append(
            f"| {agent} | {b['animal']} | {b['hp']} | {b['atk']} | {b['spd']} | {b['wil']} | {b['count']}/{b['total']} ({pct:.0f}%) |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 5: Balance assessment
# ---------------------------------------------------------------------------


def _assess_balance(results: list[tuple[str, str]]) -> list[tuple[str, float]]:
    """Return agents with >70% overall win rate (potentially overpowered)."""
    wins: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    for winner, loser in results:
        wins[winner] += 1
        total[winner] += 1
        total[loser] += 1

    flagged: list[tuple[str, float]] = []
    for agent in sorted(total.keys()):
        if total[agent] == 0:
            continue
        wr = wins.get(agent, 0) / total[agent]
        if wr > 0.70:
            flagged.append((agent, wr))
    flagged.sort(key=lambda x: x[1], reverse=True)
    return flagged


def _format_balance_md(flagged: list[tuple[str, float]]) -> str:
    lines = ["## Balance Assessment", ""]
    if not flagged:
        lines.append("No agents exceed the 70% overall win rate threshold. The meta appears balanced.")
    else:
        lines.append(
            f"**{len(flagged)} agent(s) exceed 70% overall win rate (potentially overpowered):**\n"
        )
        lines.append("| Agent | Overall Win Rate |")
        lines.append("|-------|-----------------|")
        for agent, wr in flagged:
            lines.append(f"| {agent} | {wr:.1%} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 6: Season comparison
# ---------------------------------------------------------------------------


def _format_comparison_md(
    bt_rows: list[dict],
    prev_bt_rows: list[dict],
    prev_season: int,
    curr_season: int,
) -> str:
    """Compare BT scores between two seasons."""
    prev_map = {r["name"]: r["bt_score"] for r in prev_bt_rows}
    curr_map = {r["name"]: r["bt_score"] for r in bt_rows}
    all_agents = sorted(set(prev_map.keys()) | set(curr_map.keys()))

    lines = [
        f"## Season Comparison (S{prev_season} vs S{curr_season})",
        "",
        "| Agent | S{prev} BT | S{curr} BT | Delta |".format(
            prev=prev_season, curr=curr_season
        ),
        "|-------|----------|----------|-------|",
    ]
    for agent in all_agents:
        prev_score = prev_map.get(agent)
        curr_score = curr_map.get(agent)
        prev_str = f"{prev_score:.4f}" if prev_score is not None else "N/A"
        curr_str = f"{curr_score:.4f}" if curr_score is not None else "N/A"
        if prev_score is not None and curr_score is not None:
            delta = curr_score - prev_score
            sign = "+" if delta > 0 else ""
            delta_str = f"{sign}{delta:.4f}"
        else:
            delta_str = "NEW" if curr_score is not None else "DROPPED"
        lines.append(f"| {agent} | {prev_str} | {curr_str} | {delta_str} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 7: Adaptation analysis (Track B — if available)
# ---------------------------------------------------------------------------


def _compute_adaptation_metrics(records: list[dict]) -> dict[str, dict] | None:
    """Compute adaptation metrics from T002-style data (per-game builds).

    Returns {agent: {unique_builds: int, adapted_games: int, recovery_rate: float}}
    or None if the data lacks per-game builds.
    """
    # Check if data has per-game builds
    if not records:
        return None
    sample_games = records[0].get("games", [])
    if not sample_games or "build_a" not in sample_games[0]:
        return None

    unique_builds: dict[str, set[str]] = defaultdict(set)
    adapted_games: dict[str, int] = defaultdict(int)
    recovery_attempts: dict[str, int] = defaultdict(int)
    recovery_successes: dict[str, int] = defaultdict(int)

    for record in records:
        agent_a = record.get("agent_a", "")
        agent_b = record.get("agent_b", "")
        games = record.get("games", [])

        prev_winner = None
        for game in games:
            ba = game.get("build_a", {})
            bb = game.get("build_b", {})

            if ba:
                key_a = f"{ba.get('animal','?')}|{ba.get('hp',0)}|{ba.get('atk',0)}|{ba.get('spd',0)}|{ba.get('wil',0)}"
                unique_builds[agent_a].add(key_a)
            if bb:
                key_b = f"{bb.get('animal','?')}|{bb.get('hp',0)}|{bb.get('atk',0)}|{bb.get('spd',0)}|{bb.get('wil',0)}"
                unique_builds[agent_b].add(key_b)

            if game.get("adapted"):
                adapted_games[agent_a] += 1
                adapted_games[agent_b] += 1

            game_winner = game.get("winner", "")
            # Track recovery: after losing, did the agent win the next game?
            if prev_winner is not None:
                if prev_winner == agent_a:
                    # agent_b lost previous game
                    recovery_attempts[agent_b] += 1
                    if game_winner == agent_b:
                        recovery_successes[agent_b] += 1
                elif prev_winner == agent_b:
                    # agent_a lost previous game
                    recovery_attempts[agent_a] += 1
                    if game_winner == agent_a:
                        recovery_successes[agent_a] += 1

            prev_winner = game_winner

    all_agents = sorted(set(unique_builds.keys()))
    result: dict[str, dict] = {}
    for agent in all_agents:
        attempts = recovery_attempts.get(agent, 0)
        successes = recovery_successes.get(agent, 0)
        result[agent] = {
            "unique_builds": len(unique_builds[agent]),
            "adapted_games": adapted_games.get(agent, 0),
            "recovery_rate": successes / attempts if attempts > 0 else 0.0,
            "recovery_attempts": attempts,
            "recovery_successes": successes,
        }
    return result


def _format_adaptation_md(metrics: dict[str, dict]) -> str:
    lines = ["## Adaptation Metrics", ""]
    lines.append(
        "| Agent | Unique Builds | Adapted Games | Recovery Rate |"
    )
    lines.append(
        "|-------|--------------|---------------|---------------|"
    )
    for agent, m in sorted(metrics.items(), key=lambda x: x[1]["unique_builds"], reverse=True):
        rr = m["recovery_rate"]
        attempts = m["recovery_attempts"]
        rr_str = f"{rr:.0%} ({m['recovery_successes']}/{attempts})" if attempts > 0 else "N/A"
        lines.append(
            f"| {agent} | {m['unique_builds']} | {m['adapted_games']} | {rr_str} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def _count_series_and_agents(records: list[dict]) -> tuple[int, int, int]:
    """Return (n_series, n_agents, n_errors)."""
    agents: set[str] = set()
    errors = 0
    for r in records:
        agents.add(r.get("agent_a", ""))
        agents.add(r.get("agent_b", ""))
    agents.discard("")
    return len(records), len(agents), errors


def generate_report(
    data_path: Path,
    season: int,
    prev_path: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Generate a full seasonal meta report.

    Args:
        data_path: Path to the current season's results.jsonl.
        season: Season number.
        prev_path: Path to the previous season's results.jsonl (optional).
        output_dir: Directory for output files. Default: reports/.

    Returns:
        Path to the generated Markdown report.
    """
    if output_dir is None:
        output_dir = Path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    records = _load_records(data_path)
    results = load_results_from_jsonl(data_path)
    n_series, n_agents, n_errors = _count_series_and_agents(records)

    # Section 1: Leaderboard
    bt_rows, elo_sorted = _build_leaderboard(results)

    # Section 2: Pairwise matrix
    agents, win_rates, game_counts = compute_pairwise_matrix(data_path)

    # Section 3: 3-cycles
    cycles = _find_3_cycles(agents, win_rates)

    # Section 4: Signature builds
    builds = _extract_signature_builds(records)

    # Section 5: Balance assessment
    flagged = _assess_balance(results)

    # Section 6: Adaptation metrics (if applicable)
    adaptation = _compute_adaptation_metrics(records)

    # Section 7: Season comparison (if --prev provided)
    prev_bt_rows = None
    if prev_path is not None:
        prev_results = load_results_from_jsonl(prev_path)
        prev_bt, _ = _build_leaderboard(prev_results)
        prev_bt_rows = prev_bt

    # -- Assemble Markdown report --

    md_parts: list[str] = []

    # Header
    md_parts.append(f"# Season {season} Meta Report")
    md_parts.append("")
    md_parts.append(f"**Data:** `{data_path}`")
    md_parts.append(f"**Agents:** {n_agents}")
    md_parts.append(f"**Series:** {n_series}")
    total_games = sum(game_counts.values()) // 2
    md_parts.append(f"**Total games:** {total_games}")
    md_parts.append("")

    # S1: Leaderboard
    md_parts.append(_format_leaderboard_md(bt_rows, elo_sorted))

    # S2: Pairwise heatmap
    heatmap_path = output_dir / f"season_{season}_heatmap.png"
    heatmap_ok = _generate_heatmap_png(agents, win_rates, heatmap_path)
    if heatmap_ok:
        md_parts.append("## Pairwise Win-Rate Heatmap")
        md_parts.append("")
        md_parts.append(f"![Pairwise Heatmap](season_{season}_heatmap.png)")
        md_parts.append("")
    # Always include text table as well
    md_parts.append(_format_pairwise_text(agents, win_rates))

    # S3: Cycles
    md_parts.append(_format_cycles_md(cycles))

    # S4: Signature builds
    md_parts.append(_format_signature_builds_md(builds))

    # S5: Balance
    md_parts.append(_format_balance_md(flagged))

    # S6: Adaptation (if available)
    if adaptation is not None:
        md_parts.append(_format_adaptation_md(adaptation))

    # S7: Season comparison
    if prev_bt_rows is not None:
        prev_season = season - 1 if season > 1 else 0
        md_parts.append(_format_comparison_md(bt_rows, prev_bt_rows, prev_season, season))

    # Write report
    report_path = output_dir / f"season_{season}_report.md"
    report_path.write_text("\n".join(md_parts), encoding="utf-8")

    return report_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a seasonal meta report from Moreau Arena JSONL data."
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to the current season's results.jsonl.",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=1,
        help="Season number (default: 1).",
    )
    parser.add_argument(
        "--prev",
        type=Path,
        default=None,
        help="Path to the previous season's results.jsonl for comparison.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: reports/).",
    )
    args = parser.parse_args()

    if not args.data.exists():
        print(f"Error: data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    if args.prev is not None and not args.prev.exists():
        print(f"Error: previous season file not found: {args.prev}", file=sys.stderr)
        sys.exit(1)

    report_path = generate_report(
        data_path=args.data,
        season=args.season,
        prev_path=args.prev,
        output_dir=args.output_dir,
    )

    print(f"Report generated: {report_path}")
    if HAS_MATPLOTLIB:
        heatmap_path = report_path.parent / f"season_{args.season}_heatmap.png"
        if heatmap_path.exists():
            print(f"Heatmap generated: {heatmap_path}")
    else:
        print("Note: matplotlib not available; heatmap PNG skipped (text table included).")


if __name__ == "__main__":
    main()
