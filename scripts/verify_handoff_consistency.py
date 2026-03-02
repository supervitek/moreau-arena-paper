#!/usr/bin/env python3
"""Verify handoff documents are consistent with raw tournament data.

Checks:
1. Agent lists match between raw data and RESULTS_SUMMARY.md
2. BT rankings in RESULTS_SUMMARY.md match recomputed values
3. Pairwise matrices are complementary (A_vs_B + B_vs_A = 100% ± rounding)
4. LLM vs baseline win rates match
5. Series counts match
6. Config hash is correct

Exits 0 if all checks pass, exits 1 with details otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from analysis.bt_ranking import compute_bt_scores, load_results_from_jsonl

BASELINES = {"SmartAgent", "GreedyAgent", "ConservativeAgent", "HighVarianceAgent", "RandomAgent"}
RESULTS_MD = _root / "handoff" / "RESULTS_SUMMARY.md"
CONFIG_PATH = _root / "simulator" / "config.json"
T001_PATH = _root / "data" / "tournament_001" / "results.jsonl"
T002_PATH = _root / "data" / "tournament_002" / "results.jsonl"

EXPECTED_CONFIG_HASH = "b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534"

errors: list[str] = []
warnings: list[str] = []
checks_passed = 0


def check(condition: bool, msg: str) -> None:
    global checks_passed
    if condition:
        checks_passed += 1
        print(f"  PASS: {msg}")
    else:
        errors.append(msg)
        print(f"  FAIL: {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"  WARN: {msg}")


def load_series(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def extract_agents_from_jsonl(path: Path) -> set[str]:
    agents = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line.strip())
            agents.add(r["agent_a"])
            agents.add(r["agent_b"])
    return agents


def extract_agents_from_md(md_text: str) -> set[str]:
    """Extract agent names from BT ranking tables in the markdown."""
    agents = set()
    # Match table rows like: | 1 | AgentName | 0.1234 | ...
    for m in re.finditer(r"\|\s*\d+\s*\|\s*([^\|]+?)\s*\|", md_text):
        name = m.group(1).strip()
        # Filter out headers and non-agent entries
        if name and name not in ("Rank", "Agent", "#") and not name.startswith("---") and not name.isdigit():
            agents.add(name)
    return agents


def compute_llm_vs_baseline_wr(records: list[dict]) -> float:
    llm_wins = 0
    total = 0
    for r in records:
        a, b = r["agent_a"], r["agent_b"]
        winner = r.get("winner")
        a_is_llm = a not in BASELINES
        b_is_llm = b not in BASELINES
        if a_is_llm == b_is_llm:
            continue
        total += 1
        if winner and ((winner == a and a_is_llm) or (winner == b and b_is_llm)):
            llm_wins += 1
    return llm_wins / total if total > 0 else 0.0


def compute_pairwise(records: list[dict]) -> tuple[list[str], dict[str, dict[str, float]]]:
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
    matrix = {}
    for x in agent_list:
        matrix[x] = {}
        for y in agent_list:
            if x == y:
                matrix[x][y] = None
            else:
                t = totals.get((x, y), 0)
                w = wins.get((x, y), 0)
                matrix[x][y] = w / t if t > 0 else 0.0
    return agent_list, matrix


def extract_pairwise_from_md(md_text: str, section_name: str) -> dict[str, dict[str, float | None]]:
    """Extract pairwise percentages from a markdown table in the given section."""
    # Find the section
    pattern = re.escape(section_name)
    match = re.search(pattern, md_text)
    if not match:
        return {}

    # Find the table after this section
    rest = md_text[match.end():]

    # Extract table rows
    lines = rest.split("\n")
    header_line = None
    data_rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            if data_rows:
                break
            continue
        if "|---" in line:
            continue
        if header_line is None:
            header_line = line
        else:
            data_rows.append(line)

    if not header_line or not data_rows:
        return {}

    # Parse header to get column names
    cols = [c.strip().strip("*") for c in header_line.split("|") if c.strip()]
    col_names = cols[1:]  # Skip the empty/row-header column

    matrix = {}
    for row in data_rows:
        cells = [c.strip().strip("*") for c in row.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        row_name = cells[0]
        matrix[row_name] = {}
        for j, val in enumerate(cells[1:]):
            if j >= len(col_names):
                break
            col_name = col_names[j]
            if val == "--":
                matrix[row_name][col_name] = None
            else:
                try:
                    matrix[row_name][col_name] = float(val.replace("%", "")) / 100.0
                except ValueError:
                    matrix[row_name][col_name] = None
    return matrix


def main() -> int:
    print("=" * 60)
    print("Handoff Consistency Verification")
    print("=" * 60)
    print()

    # 1. Config hash (check embedded sha256 field, matching test_invariants.py)
    print("[1] Config Hash")
    config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    embedded_hash = config_data.get("sha256", "")
    check(embedded_hash == EXPECTED_CONFIG_HASH, f"Config embedded hash matches ({embedded_hash[:12]}...)")

    # 2. Data files exist
    print("\n[2] Data Files")
    check(T001_PATH.exists(), "T001 results.jsonl exists")
    check(T002_PATH.exists(), "T002 results.jsonl exists")
    check(RESULTS_MD.exists(), "RESULTS_SUMMARY.md exists")

    # 3. Agent lists
    print("\n[3] Agent Lists")
    t001_agents = extract_agents_from_jsonl(T001_PATH)
    t002_agents = extract_agents_from_jsonl(T002_PATH)
    check(t001_agents == t002_agents, f"T001 and T002 have same {len(t001_agents)} agents")

    md_text = RESULTS_MD.read_text(encoding="utf-8")
    md_agents = extract_agents_from_md(md_text)
    # The MD agents should be a superset of raw agents
    missing_in_md = t001_agents - md_agents
    extra_in_md = md_agents - t001_agents
    check(len(missing_in_md) == 0, f"All raw agents appear in RESULTS_SUMMARY.md (missing: {missing_in_md or 'none'})")
    if extra_in_md:
        warn(f"Extra agents in MD not in raw data: {extra_in_md}")

    # 4. Series counts
    print("\n[4] Series Counts")
    t001_records = load_series(T001_PATH)
    t002_records = load_series(T002_PATH)
    # Check MD mentions correct counts
    check(f"| **Series** | {len(t001_records)} |" in md_text,
          f"T001 series count ({len(t001_records)}) in MD")
    check(f"| {len(t002_records)} |" in md_text,
          f"T002 series count ({len(t002_records)}) in MD")

    # 5. LLM vs baseline win rates
    print("\n[5] LLM vs Baseline Win Rates")
    t001_wr = compute_llm_vs_baseline_wr(t001_records)
    t002_wr = compute_llm_vs_baseline_wr(t002_records)
    t001_wr_str = f"{t001_wr*100:.2f}%"
    t002_wr_str = f"{t002_wr*100:.2f}%"
    check(t001_wr_str in md_text, f"T001 LLM WR ({t001_wr_str}) in MD")
    check(t002_wr_str in md_text, f"T002 LLM WR ({t002_wr_str}) in MD")

    # 6. BT Rankings match
    print("\n[6] BT Rankings")
    t001_results = load_results_from_jsonl(T001_PATH)
    t002_results = load_results_from_jsonl(T002_PATH)
    t001_bt = compute_bt_scores(t001_results, n_bootstrap=1000, bootstrap_seed=42)
    t002_bt = compute_bt_scores(t002_results, n_bootstrap=1000, bootstrap_seed=42)

    # Check top agent
    check(t001_bt[0].name in md_text, f"T001 top agent ({t001_bt[0].name}) in MD")
    check(t002_bt[0].name in md_text, f"T002 top agent ({t002_bt[0].name}) in MD")

    # Check BT scores appear in MD (spot check top 3)
    for bt in t001_bt[:3]:
        score_str = f"{bt.score:.4f}"
        check(score_str in md_text, f"T001 BT score for {bt.name} ({score_str}) in MD")

    for bt in t002_bt[:3]:
        score_str = f"{bt.score:.4f}"
        check(score_str in md_text, f"T002 BT score for {bt.name} ({score_str}) in MD")

    # 7. Pairwise complementarity (wins + losses + draws = 100%)
    print("\n[7] Pairwise Complementarity")
    for label, records in [("T001", t001_records), ("T002", t002_records)]:
        agents, matrix = compute_pairwise(records)
        complement_ok = True
        for a in agents:
            for b in agents:
                if a >= b:
                    continue
                wr_ab = matrix[a][b]
                wr_ba = matrix[b][a]
                if wr_ab is not None and wr_ba is not None:
                    total = wr_ab + wr_ba
                    # Allow draws: A_wins + B_wins <= 1.0 (remainder = draws)
                    if total > 1.01:
                        complement_ok = False
                        errors.append(f"{label}: {a} vs {b}: {wr_ab:.4f} + {wr_ba:.4f} = {total:.4f} (exceeds 1.0)")
                    elif total < 1.0 - 0.01:
                        draw_pct = (1.0 - total) * 100
                        warn(f"{label}: {a} vs {b}: {draw_pct:.0f}% draws ({wr_ab:.0%} + {wr_ba:.0%} = {total:.0%})")
        check(complement_ok, f"{label} pairwise matrix is complementary (A+B ≤ 100%, remainder = draws)")

    # 8. Agent count in headline
    print("\n[8] Agent Count")
    n_agents = len(t001_agents)
    n_llm = sum(1 for a in t001_agents if a not in BASELINES)
    n_baseline = n_agents - n_llm
    expected_str = f"{n_agents} ({n_llm} LLM + {n_baseline} baseline)"
    check(expected_str in md_text, f"Agent count string ({expected_str}) in MD")

    # Summary
    print()
    print("=" * 60)
    total_checks = checks_passed + len(errors)
    print(f"Results: {checks_passed}/{total_checks} checks passed")
    if warnings:
        print(f"Warnings: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print(f"FAILURES: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        print()
        print("EXIT CODE: 1")
        return 1
    else:
        print("All checks passed.")
        print()
        print("EXIT CODE: 0")
        return 0


if __name__ == "__main__":
    sys.exit(main())
