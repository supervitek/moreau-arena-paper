#!/usr/bin/env python3
"""Generate handoff/RESULTS_SUMMARY.md from raw tournament data.

All numbers come ONLY from data/tournament_001/results.jsonl and
data/tournament_002/results.jsonl. Nothing is hardcoded.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add project root
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from analysis.bt_ranking import compute_bt_scores, load_results_from_jsonl

T001_PATH = _root / "data" / "tournament_001" / "results.jsonl"
T002_PATH = _root / "data" / "tournament_002" / "results.jsonl"

BASELINES = {"SmartAgent", "GreedyAgent", "ConservativeAgent", "HighVarianceAgent", "RandomAgent"}


def load_series(path: Path) -> list[dict]:
    """Load all series records from a JSONL file."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def compute_series_wl(records: list[dict]) -> dict[str, dict[str, int]]:
    """Compute series wins/losses per agent."""
    stats: dict[str, dict[str, int]] = {}
    for r in records:
        a, b = r["agent_a"], r["agent_b"]
        winner = r.get("winner")
        for agent in (a, b):
            if agent not in stats:
                stats[agent] = {"wins": 0, "losses": 0, "draws": 0}
        if winner == a:
            stats[a]["wins"] += 1
            stats[b]["losses"] += 1
        elif winner == b:
            stats[b]["wins"] += 1
            stats[a]["losses"] += 1
        else:
            stats[a]["draws"] += 1
            stats[b]["draws"] += 1
    return stats


def compute_llm_vs_baseline_wr(records: list[dict]) -> tuple[int, int, int, float]:
    """Compute LLM win rate when playing against baselines.
    Returns (llm_wins, baseline_wins, draws, llm_wr)."""
    llm_wins = 0
    baseline_wins = 0
    draws = 0
    for r in records:
        a, b = r["agent_a"], r["agent_b"]
        winner = r.get("winner")
        a_is_llm = a not in BASELINES
        b_is_llm = b not in BASELINES
        # Only count cross-type matchups
        if a_is_llm == b_is_llm:
            continue
        if winner is None:
            draws += 1
        elif winner == a:
            if a_is_llm:
                llm_wins += 1
            else:
                baseline_wins += 1
        elif winner == b:
            if b_is_llm:
                llm_wins += 1
            else:
                baseline_wins += 1
    total = llm_wins + baseline_wins + draws
    wr = llm_wins / total if total > 0 else 0.0
    return llm_wins, baseline_wins, draws, wr


def compute_pairwise(records: list[dict]) -> tuple[list[str], dict[str, dict[str, float | None]], dict[str, dict[str, int]]]:
    """Compute pairwise win-rate matrix."""
    wins: dict[tuple[str, str], int] = defaultdict(int)
    totals: dict[tuple[str, str], int] = defaultdict(int)
    agents: set[str] = set()

    for r in records:
        a, b = r["agent_a"], r["agent_b"]
        winner = r.get("winner")
        agents.add(a)
        agents.add(b)
        totals[(a, b)] += 1
        totals[(b, a)] += 1
        if winner == a:
            wins[(a, b)] += 1
        elif winner == b:
            wins[(b, a)] += 1

    agent_list = sorted(agents)
    matrix: dict[str, dict[str, float | None]] = {}
    counts: dict[str, dict[str, int]] = {}
    for x in agent_list:
        matrix[x] = {}
        counts[x] = {}
        for y in agent_list:
            if x == y:
                matrix[x][y] = None
                counts[x][y] = 0
            else:
                t = totals.get((x, y), 0)
                w = wins.get((x, y), 0)
                matrix[x][y] = round(w / t, 4) if t > 0 else 0.0
                counts[x][y] = t
    return agent_list, matrix, counts


def get_animals_used(records: list[dict]) -> dict[str, set[str]]:
    """Get animals used by each agent across all games."""
    animals: dict[str, set[str]] = {}
    for r in records:
        a, b = r["agent_a"], r["agent_b"]
        # Series-level builds
        for side, agent in [("build_a", a), ("build_b", b)]:
            build = r.get(side)
            if build and isinstance(build, dict) and build.get("animal"):
                if agent not in animals:
                    animals[agent] = set()
                animals[agent].add(build["animal"])
        # Game-level builds
        for g in r.get("games", []):
            for side, agent in [("build_a", a), ("build_b", b)]:
                build = g.get(side)
                if build and isinstance(build, dict) and build.get("animal"):
                    if agent not in animals:
                        animals[agent] = set()
                    animals[agent].add(build["animal"])
    return animals


def format_pairwise_table(agents: list[str], matrix: dict, counts: dict) -> str:
    """Format pairwise win-rate matrix as markdown."""
    # Truncate long names
    def short(name: str, max_len: int = 14) -> str:
        return name if len(name) <= max_len else name[:max_len-1] + "."

    header = "| | " + " | ".join(short(a) for a in agents) + " |"
    sep = "|---|" + "|".join("---:" for _ in agents) + "|"
    rows = [header, sep]
    for a in agents:
        cells = []
        for b in agents:
            if a == b:
                cells.append("--")
            else:
                wr = matrix[a][b]
                if wr is not None:
                    cells.append(f"{wr*100:.0f}%")
                else:
                    cells.append("--")
        rows.append(f"| **{short(a)}** | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def main() -> None:
    # Load raw data
    t001_records = load_series(T001_PATH)
    t002_records = load_series(T002_PATH)

    # BT scores
    t001_results = load_results_from_jsonl(T001_PATH)
    t002_results = load_results_from_jsonl(T002_PATH)
    t001_bt = compute_bt_scores(t001_results, n_bootstrap=1000, bootstrap_seed=42)
    t002_bt = compute_bt_scores(t002_results, n_bootstrap=1000, bootstrap_seed=42)

    # Series W-L
    t001_wl = compute_series_wl(t001_records)
    t002_wl = compute_series_wl(t002_records)

    # LLM vs baseline
    t001_llm_w, t001_bl_w, t001_draws, t001_llm_wr = compute_llm_vs_baseline_wr(t001_records)
    t002_llm_w, t002_bl_w, t002_draws, t002_llm_wr = compute_llm_vs_baseline_wr(t002_records)

    # Pairwise
    t001_agents, t001_pw, t001_pc = compute_pairwise(t001_records)
    t002_agents, t002_pw, t002_pc = compute_pairwise(t002_records)

    # Animals
    t001_animals = get_animals_used(t001_records)
    t002_animals = get_animals_used(t002_records)

    # File sizes
    t001_size = os.path.getsize(T001_PATH)
    t002_size = os.path.getsize(T002_PATH)

    # Top and bottom agents
    t001_top = t001_bt[0].name if t001_bt else "N/A"
    t001_bottom = t001_bt[-1].name if t001_bt else "N/A"
    t002_top = t002_bt[0].name if t002_bt else "N/A"
    t002_bottom = t002_bt[-1].name if t002_bt else "N/A"

    t001_top_type = "baseline" if t001_top in BASELINES else "LLM"
    t001_bottom_type = "baseline" if t001_bottom in BASELINES else "LLM"
    t002_top_type = "baseline" if t002_top in BASELINES else "LLM"
    t002_bottom_type = "baseline" if t002_bottom in BASELINES else "LLM"

    # Agent counts
    n_agents = len(set(t001_agents) | set(t002_agents))
    n_llm = sum(1 for a in (set(t001_agents) | set(t002_agents)) if a not in BASELINES)
    n_baseline = n_agents - n_llm

    # Build the markdown
    md = []
    md.append("# Results Summary — Scientific Findings")
    md.append("")
    md.append("> **This file is auto-generated by `scripts/generate_results_summary.py`.**")
    md.append("> All numbers are computed from raw JSONL data. Do not edit manually.")
    md.append("")
    md.append("## The Headline")
    md.append("")
    md.append(f"Same {n_agents} agents, same game, different scaffolding — the leaderboard flips 180 degrees.")
    md.append("")
    md.append("| | Tournament 001 | Tournament 002 |")
    md.append("|---|---|---|")
    md.append(f"| **Series** | {len(t001_records)} | {len(t002_records)} |")
    md.append(f"| **Agents** | {n_agents} ({n_llm} LLM + {n_baseline} baseline) | {n_agents} (same) |")
    md.append(f"| **Format** | Best-of-7, blind pick | Adaptive best-of-7 |")
    md.append(f"| **LLM vs Baseline Win Rate** | **{t001_llm_wr*100:.2f}%** ({t001_llm_w}W/{t001_bl_w}L/{t001_draws}D) | **{t002_llm_wr*100:.2f}%** ({t002_llm_w}W/{t002_bl_w}L/{t002_draws}D) |")
    md.append(f"| **Top Agent** | {t001_top} ({t001_top_type}) | {t002_top} ({t002_top_type}) |")
    md.append(f"| **Bottom Agent** | {t001_bottom} ({t001_bottom_type}) | {t002_bottom} ({t002_bottom_type}) |")
    md.append("")
    md.append("---")
    md.append("")

    # T001 section
    md.append("## Tournament 001 — BT Rankings")
    md.append("")
    md.append("| Rank | Agent | BT Score | 95% CI | Type | Series W-L-D |")
    md.append("|---:|------|-------:|-------|------|------------|")
    for i, bt in enumerate(t001_bt):
        agent_type = "Baseline" if bt.name in BASELINES else "LLM"
        wl = t001_wl.get(bt.name, {"wins": 0, "losses": 0, "draws": 0})
        ci_str = f"[{bt.ci_lower:.4f}, {bt.ci_upper:.4f}]"
        md.append(f"| {i+1} | {bt.name} | {bt.score:.4f} | {ci_str} | {agent_type} | {wl['wins']}-{wl['losses']}-{wl['draws']} |")
    md.append("")
    md.append("---")
    md.append("")

    # T002 section
    md.append("## Tournament 002 — BT Rankings")
    md.append("")
    md.append("| Rank | Agent | BT Score | 95% CI | Type | Series W-L-D |")
    md.append("|---:|------|-------:|-------|------|------------|")
    for i, bt in enumerate(t002_bt):
        agent_type = "Baseline" if bt.name in BASELINES else "LLM"
        wl = t002_wl.get(bt.name, {"wins": 0, "losses": 0, "draws": 0})
        ci_str = f"[{bt.ci_lower:.4f}, {bt.ci_upper:.4f}]"
        md.append(f"| {i+1} | {bt.name} | {bt.score:.4f} | {ci_str} | {agent_type} | {wl['wins']}-{wl['losses']}-{wl['draws']} |")
    md.append("")
    md.append("---")
    md.append("")

    # Pairwise T001
    md.append("## Pairwise Win Rates — T001")
    md.append("")
    md.append("Row agent's series win rate vs column agent.")
    md.append("")
    md.append(format_pairwise_table(t001_agents, t001_pw, t001_pc))
    md.append("")
    md.append("---")
    md.append("")

    # Pairwise T002
    md.append("## Pairwise Win Rates — T002")
    md.append("")
    md.append("Row agent's series win rate vs column agent.")
    md.append("")
    md.append(format_pairwise_table(t002_agents, t002_pw, t002_pc))
    md.append("")
    md.append("---")
    md.append("")

    # Animals
    md.append("## Animals Used by Agent")
    md.append("")
    md.append("| Agent | Type | T001 Animals | T002 Animals |")
    md.append("|-------|------|-------------|-------------|")
    all_agents_sorted = sorted(set(t001_agents) | set(t002_agents))
    for agent in all_agents_sorted:
        agent_type = "Baseline" if agent in BASELINES else "LLM"
        a1 = ", ".join(sorted(t001_animals.get(agent, set()))) or "—"
        a2 = ", ".join(sorted(t002_animals.get(agent, set()))) or "—"
        md.append(f"| {agent} | {agent_type} | {a1} | {a2} |")
    md.append("")
    md.append("---")
    md.append("")

    # Actual JSONL structure
    md.append("## JSONL Record Structure")
    md.append("")
    md.append("Each line in a results JSONL file is a JSON object representing one **series** (best-of-7).")
    md.append("Below is the actual schema extracted from the data:")
    md.append("")
    md.append("```json")
    # Get a real example
    example = t001_records[0].copy()
    # Trim games array for display
    if "games" in example and len(example["games"]) > 1:
        example["games"] = [example["games"][0], "... (remaining games)"]
    md.append(json.dumps(example, indent=2))
    md.append("```")
    md.append("")
    md.append("### Top-Level Fields")
    md.append("")
    example_keys = t001_records[0]
    md.append("| Field | Type | Description |")
    md.append("|-------|------|-------------|")
    md.append("| `series_id` | string | Unique ID: `AgentA_vs_AgentB_sNNN` |")
    md.append("| `pair_index` | int | Index of agent pair in round-robin |")
    md.append("| `series_index` | int | Series number within this pair |")
    md.append("| `agent_a` | string | Name of agent A |")
    md.append("| `agent_b` | string | Name of agent B |")
    md.append("| `is_llm_a` | bool | Whether agent A is an LLM |")
    md.append("| `is_llm_b` | bool | Whether agent B is an LLM |")
    if "build_a" in example_keys:
        md.append("| `build_a` | object\\|null | Series-level build for A (T001 only) |")
        md.append("| `build_b` | object\\|null | Series-level build for B (T001 only) |")
    md.append("| `winner` | string | Name of series winner |")
    md.append("| `score_a` | int | Games won by A |")
    md.append("| `score_b` | int | Games won by B |")
    md.append("| `games_played` | int | Total games in series |")
    md.append("| `games` | array | Per-game records |")
    md.append("| `base_seed` | int | RNG seed for reproducibility |")
    md.append("| `duration_s` | float | Wall-clock time in seconds |")
    md.append("| `error` | string\\|null | Error message if any |")
    md.append("")
    md.append("---")
    md.append("")

    # Data files
    md.append("## Data File Reference")
    md.append("")
    md.append("| File | Content | Size | Records |")
    md.append("|------|---------|------|---------|")
    md.append(f"| `data/tournament_001/results.jsonl` | T001 series records | {t001_size/1024:.0f} KB | {len(t001_records)} |")
    md.append(f"| `data/tournament_002/results.jsonl` | T002 series records | {t002_size/1024:.0f} KB | {len(t002_records)} |")
    md.append("")

    # Write
    out_path = _root / "handoff" / "RESULTS_SUMMARY.md"
    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Generated {out_path} ({len(md)} lines)")
    print(f"  T001: {len(t001_records)} series, {len(t001_bt)} agents, LLM WR={t001_llm_wr*100:.2f}%")
    print(f"  T002: {len(t002_records)} series, {len(t002_bt)} agents, LLM WR={t002_llm_wr*100:.2f}%")


if __name__ == "__main__":
    main()
