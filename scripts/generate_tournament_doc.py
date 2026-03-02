#!/usr/bin/env python3
"""Generate a tournament documentation skeleton from JSONL + prompt files.

Usage:
    python scripts/generate_tournament_doc.py \
        --tournament-id T001 \
        --track "A — Fixed Strategy" \
        --data data/tournament_001/results.jsonl \
        --prompt prompts/t001_prompt.txt \
        --output docs/tournaments/T001.md

All numbers are computed from raw data files. Nothing is hard-coded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Add project root to path for analysis imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.bt_ranking import compute_bt_scores

BASELINES = {"SmartAgent", "HighVarianceAgent", "ConservativeAgent", "GreedyAgent", "RandomAgent"}

CONFIG_HASH = "b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_data(data_path: Path) -> dict:
    """Parse JSONL and return tournament statistics."""
    records = []
    agents = set()
    total_games = 0
    errors = 0
    draws = 0
    adapted = 0
    games_per_series = []
    win_loss: dict[str, dict[str, int]] = {}

    with open(data_path) as f:
        for line in f:
            r = json.loads(line)
            records.append(r)
            agents.add(r["agent_a"])
            agents.add(r["agent_b"])
            games = r.get("games", [])
            games_per_series.append(len(games))
            total_games += len(games)

            for g in games:
                if g.get("error"):
                    errors += 1
                if g.get("winner") == "draw":
                    draws += 1
                if g.get("adapted"):
                    adapted += 1

                w = g.get("winner")
                if w and w != "draw" and not g.get("error"):
                    loser = r["agent_b"] if w == r["agent_a"] else r["agent_a"]
                    win_loss.setdefault(w, {"wins": 0, "losses": 0})["wins"] += 1
                    win_loss.setdefault(loser, {"wins": 0, "losses": 0})["losses"] += 1

    # Compute BT rankings
    pairs = []
    for r in records:
        for g in r.get("games", []):
            w = g.get("winner")
            if w and w != "draw" and not g.get("error"):
                loser = r["agent_b"] if w == r["agent_a"] else r["agent_a"]
                pairs.append((w, loser))

    bt_results = compute_bt_scores(pairs, n_bootstrap=1000, bootstrap_seed=42)

    # Compute win rates
    win_rates = {}
    for agent in agents:
        wl = win_loss.get(agent, {"wins": 0, "losses": 0})
        total = wl["wins"] + wl["losses"]
        win_rates[agent] = wl["wins"] / total * 100 if total > 0 else 0.0

    # LLM vs baseline averages
    llm_rates = [win_rates[a] for a in agents if a not in BASELINES]
    baseline_rates = [win_rates[a] for a in agents if a in BASELINES]
    llm_avg = sum(llm_rates) / len(llm_rates) if llm_rates else 0
    baseline_avg = sum(baseline_rates) / len(baseline_rates) if baseline_rates else 0

    gps = games_per_series if games_per_series else [0]

    return {
        "records": records,
        "agents": sorted(agents),
        "n_agents": len(agents),
        "n_llm": len([a for a in agents if a not in BASELINES]),
        "n_baseline": len([a for a in agents if a in BASELINES]),
        "total_series": len(records),
        "total_games": total_games,
        "errors": errors,
        "draws": draws,
        "adapted": adapted,
        "gps_mean": sum(gps) / len(gps),
        "gps_min": min(gps),
        "gps_max": max(gps),
        "bt_results": bt_results,
        "win_rates": win_rates,
        "llm_avg_wr": llm_avg,
        "baseline_avg_wr": baseline_avg,
    }


def generate_doc(
    tournament_id: str,
    track: str,
    data_path: Path,
    prompt_path: Path,
    stats: dict,
) -> str:
    """Generate markdown document from tournament data."""
    prompt_hash = sha256_file(prompt_path)
    prompt_text = prompt_path.read_text(encoding="utf-8").rstrip()

    lines = []

    # Title
    lines.append(f"# {tournament_id} — {track}")
    lines.append("")

    # Section 1: IDENTITY
    lines.append("## 1. IDENTITY")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| **Tournament ID** | `{tournament_id}` |")
    lines.append(f"| **Track** | {track} |")
    lines.append("| **Status** | `complete` |")
    lines.append(f"| **Data file** | `{data_path}` |")
    lines.append(f"| **Prompt file** | `{prompt_path}` |")
    lines.append(f"| **Prompt SHA-256** | `{prompt_hash}` |")
    lines.append(f"| **Config SHA-256** | `{CONFIG_HASH}` |")
    lines.append("")

    # Section 2: DESIGN
    lines.append("## 2. DESIGN")
    lines.append("")
    lines.append("<!-- TODO: Describe the tournament design, prompt strategy, and mechanics -->")
    lines.append("")

    # Section 3: AGENTS
    lines.append("## 3. AGENTS")
    lines.append("")
    lines.append(f"{stats['n_agents']} agents ({stats['n_llm']} LLMs + {stats['n_baseline']} baselines):")
    lines.append("")
    lines.append("| Agent | Type |")
    lines.append("|-------|------|")
    for agent in stats["agents"]:
        agent_type = "baseline" if agent in BASELINES else "llm"
        lines.append(f"| {agent} | `{agent_type}` |")
    lines.append("")

    # Section 4: RESULTS
    lines.append("## 4. RESULTS — BRADLEY-TERRY RANKINGS")
    lines.append("")
    lines.append("BT scores computed with N_bootstrap=1000, seed=42:")
    lines.append("")
    lines.append("| Rank | Agent | Type | BT Score | 95% CI | Win Rate |")
    lines.append("|------|-------|------|----------|--------|----------|")
    for i, r in enumerate(stats["bt_results"]):
        agent_type = "baseline" if r.name in BASELINES else "llm"
        wr = stats["win_rates"].get(r.name, 0)
        lines.append(
            f"| {i + 1} | {r.name} | {agent_type} | {r.score:.4f} "
            f"| [{r.ci_lower:.4f}, {r.ci_upper:.4f}] | {wr:.1f}% |"
        )
    lines.append("")

    # Summary statistics
    lines.append("### Summary Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total series | {stats['total_series']:,} |")
    lines.append(f"| Total games | {stats['total_games']:,} |")
    lines.append(f"| Errors | {stats['errors']} |")
    lines.append(f"| Draws | {stats['draws']} |")
    lines.append(f"| Games/series (mean) | {stats['gps_mean']:.1f} |")
    lines.append(f"| Games/series (min) | {stats['gps_min']} |")
    lines.append(f"| Games/series (max) | {stats['gps_max']} |")
    if stats["adapted"] > 0:
        pct = stats["adapted"] / stats["total_games"] * 100
        lines.append(f"| Adapted games | {stats['adapted']:,} ({pct:.1f}%) |")
    lines.append(f"| LLM avg win rate | {stats['llm_avg_wr']:.1f}% |")
    lines.append(f"| Baseline avg win rate | {stats['baseline_avg_wr']:.1f}% |")
    lines.append("")

    # Section 5: KEY FINDINGS
    lines.append("## 5. KEY FINDINGS")
    lines.append("")
    lines.append("<!-- TODO: Add key findings and analysis -->")
    lines.append("")

    # Section 6: PROMPT
    lines.append("## 6. PROMPT")
    lines.append("")
    lines.append("```")
    lines.append(prompt_text)
    lines.append("```")
    lines.append("")
    lines.append(f"Prompt SHA-256: `{prompt_hash}`")
    lines.append("")

    # Section 7: WHAT CHANGED (placeholder)
    lines.append("## 7. WHAT CHANGED")
    lines.append("")
    lines.append("<!-- TODO: Add comparison with previous tournament (omit for T001) -->")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate tournament documentation skeleton")
    parser.add_argument("--tournament-id", required=True, help="Tournament ID (e.g., T001)")
    parser.add_argument("--track", required=True, help="Track name (e.g., 'A — Fixed Strategy')")
    parser.add_argument("--data", required=True, help="Path to results.jsonl")
    parser.add_argument("--prompt", required=True, help="Path to prompt file")
    parser.add_argument("--output", required=True, help="Output markdown file path")
    args = parser.parse_args()

    data_path = Path(args.data)
    prompt_path = Path(args.prompt)
    output_path = Path(args.output)

    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)
    if not prompt_path.exists():
        print(f"Error: Prompt file not found: {prompt_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {data_path}...")
    stats = parse_data(data_path)

    print(f"Generating documentation for {args.tournament_id}...")
    doc = generate_doc(args.tournament_id, args.track, data_path, prompt_path, stats)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(doc, encoding="utf-8")
    print(f"Written to {output_path}")
    print(f"  {stats['n_agents']} agents, {stats['total_series']} series, {stats['total_games']:,} games")
    print(f"  #1: {stats['bt_results'][0].name} (BT={stats['bt_results'][0].score:.4f})")


if __name__ == "__main__":
    main()
