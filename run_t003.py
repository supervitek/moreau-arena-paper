#!/usr/bin/env python3
"""Tournament 003: Exact-Only Cleanroom (No Meta Context)

All-pairs tournament with 15 agents (10 LLMs + 5 baselines).
6 parallel workers organized by model latency.

Usage:
    python run_t003.py              # Real tournament
    python run_t003.py --dry-run    # Random builds, no API calls
    python run_t003.py --resume     # Resume from existing chunks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
from pathlib import Path
from typing import Any

from agents.baselines import (
    BaseAgent,
    Build,
    ConservativeAgent,
    GreedyAgent,
    HighVarianceAgent,
    RandomAgent,
    SmartAgent,
)
from agents.llm_agent_v2 import LLMAgentV2
from analysis.bt_ranking import compute_bt_scores
from run_challenge import (
    _api_call_anthropic,
    _api_call_google,
    _api_call_openai,
    _api_call_openai_responses,
    _api_call_xai,
    _OPENAI_RESPONSES_MODELS,
    _run_adaptive_series,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("data/tournament_003")
SERIES_PER_PAIR = 10
NUM_AGENTS = 15

AGENT_DEFS: list[dict[str, Any]] = [
    {"idx": 0,  "name": "claude-opus-4-6",          "provider": "anthropic", "model": "claude-opus-4-6"},
    {"idx": 1,  "name": "claude-sonnet-4-6",         "provider": "anthropic", "model": "claude-sonnet-4-6"},
    {"idx": 2,  "name": "claude-haiku-4-5-20251001", "provider": "anthropic", "model": "claude-haiku-4-5-20251001"},
    {"idx": 3,  "name": "gpt-5.2",                   "provider": "openai",    "model": "gpt-5.2"},
    {"idx": 4,  "name": "gpt-5.2-codex",             "provider": "openai",    "model": "gpt-5.2-codex"},
    {"idx": 5,  "name": "gpt-5.4",                   "provider": "openai",    "model": "gpt-5.4"},
    {"idx": 6,  "name": "gpt-5.3-codex",             "provider": "openai",    "model": "gpt-5.3-codex"},
    {"idx": 7,  "name": "gemini-3-flash-preview",    "provider": "google",    "model": "gemini-3-flash-preview"},
    {"idx": 8,  "name": "gemini-3.1-pro-preview",    "provider": "google",    "model": "gemini-3.1-pro-preview"},
    {"idx": 9,  "name": "grok-4-1-fast-reasoning",   "provider": "xai",       "model": "grok-4-1-fast-reasoning"},
    {"idx": 10, "name": "RandomAgent",     "provider": None, "model": None, "cls": RandomAgent},
    {"idx": 11, "name": "GreedyAgent",     "provider": None, "model": None, "cls": GreedyAgent},
    {"idx": 12, "name": "SmartAgent",      "provider": None, "model": None, "cls": SmartAgent},
    {"idx": 13, "name": "ConservativeAgent", "provider": None, "model": None, "cls": ConservativeAgent},
    {"idx": 14, "name": "HighVarianceAgent", "provider": None, "model": None, "cls": HighVarianceAgent},
]

_AGENT_BY_IDX = {d["idx"]: d for d in AGENT_DEFS}

ENV_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
}

WORKER_LABELS = [
    "W0-grok", "W1-flash", "W2-pro",
    "W3-codex", "W4-anthropic", "W5-fast",
]

# ---------------------------------------------------------------------------
# API callable cache
# ---------------------------------------------------------------------------

_api_cache: dict[str, Any] = {}


def _get_api_callable(provider: str, model: str) -> Any:
    key = f"{provider}:{model}"
    if key in _api_cache:
        return _api_cache[key]
    api_key = os.environ.get(ENV_KEYS[provider], "")
    if not api_key:
        raise RuntimeError(f"Missing {ENV_KEYS[provider]}")
    if provider == "openai" and model in _OPENAI_RESPONSES_MODELS:
        fn = lambda p, _k=api_key, _m=model: _api_call_openai_responses(_k, _m, p)
    else:
        dispatch = {
            "anthropic": _api_call_anthropic,
            "openai": _api_call_openai,
            "google": _api_call_google,
            "xai": _api_call_xai,
        }
        call_fn = dispatch[provider]
        fn = lambda p, _k=api_key, _m=model, _f=call_fn: _f(_k, _m, p)
    _api_cache[key] = fn
    return fn


# ---------------------------------------------------------------------------
# Agent creation
# ---------------------------------------------------------------------------

class _DryRunAgent(BaseAgent):
    """Stand-in for LLM agents during dry-run."""

    def __init__(self, name: str, seed: int = 42):
        self._name = name
        self._rng = RandomAgent(seed=seed)

    def choose_build(self, opponent_animal=None, banned=None, opponent_reveal=None):
        return self._rng.choose_build(opponent_animal, banned or [], opponent_reveal)


def _create_agent(agent_def: dict, series_seed: int, dry_run: bool = False) -> BaseAgent:
    provider = agent_def["provider"]
    if provider is None:
        cls = agent_def["cls"]
        return cls(seed=series_seed) if cls in (RandomAgent, HighVarianceAgent) else cls()
    if dry_run:
        return _DryRunAgent(agent_def["name"], seed=series_seed)
    api_call = _get_api_callable(provider, agent_def["model"])
    return LLMAgentV2(name=agent_def["name"], api_call=api_call, meta_builds=[])


# ---------------------------------------------------------------------------
# Worker pair assignment
# ---------------------------------------------------------------------------

def _assign_pairs() -> dict[int, list[tuple[int, int, int]]]:
    all_pairs = list(combinations(range(NUM_AGENTS), 2))
    workers: dict[int, list] = {i: [] for i in range(6)}
    for pair_idx, (a, b) in enumerate(all_pairs):
        if 9 in (a, b):
            workers[0].append((pair_idx, a, b))
        elif 7 in (a, b):
            workers[1].append((pair_idx, a, b))
        elif 8 in (a, b):
            workers[2].append((pair_idx, a, b))
        elif 4 in (a, b) or 6 in (a, b):
            workers[3].append((pair_idx, a, b))
        elif 0 in (a, b) or 1 in (a, b):
            workers[4].append((pair_idx, a, b))
        else:
            workers[5].append((pair_idx, a, b))
    return workers


# ---------------------------------------------------------------------------
# Resume support
# ---------------------------------------------------------------------------

def _get_completed(chunk_path: Path) -> set[tuple[int, int]]:
    done: set[tuple[int, int]] = set()
    if chunk_path.exists():
        with open(chunk_path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    done.add((r["pair_index"], r["series_index"]))
                except (json.JSONDecodeError, KeyError):
                    pass
    return done


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_progress = {"done": 0, "total": 0, "errors": 0, "t0": 0.0}


def _fmt_time(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    if s < 3600:
        return f"{s / 60:.0f}m"
    return f"{s / 3600:.1f}h"


def _tick(wid: int, msg: str) -> None:
    with _lock:
        _progress["done"] += 1
        n, total = _progress["done"], _progress["total"]
        pct = n / total * 100 if total else 0
        elapsed = time.monotonic() - _progress["t0"]
        eta = (elapsed / n * (total - n)) if n > 0 else 0
        err = f" {_progress['errors']}err" if _progress["errors"] else ""
        print(
            f"  [{n}/{total} {pct:.0f}%{err} ETA:{_fmt_time(eta)}] "
            f"W{wid}: {msg}",
            flush=True,
        )


def _tick_skip() -> None:
    with _lock:
        _progress["done"] += 1


# ---------------------------------------------------------------------------
# Worker function
# ---------------------------------------------------------------------------

def _run_worker(
    wid: int,
    pairs: list[tuple[int, int, int]],
    output_path: Path,
    dry_run: bool,
    resume: bool,
) -> list[dict]:
    completed = _get_completed(output_path) if resume else set()
    results: list[dict] = []

    for pair_idx, a_idx, b_idx in pairs:
        a_def = _AGENT_BY_IDX[a_idx]
        b_def = _AGENT_BY_IDX[b_idx]

        for s in range(SERIES_PER_PAIR):
            if (pair_idx, s) in completed:
                _tick_skip()
                continue

            base_seed = pair_idx * 100_000 + s * 1_000

            try:
                agent_a = _create_agent(a_def, base_seed, dry_run)
                agent_b = _create_agent(b_def, base_seed, dry_run)

                t0 = time.monotonic()
                winner, game_records = _run_adaptive_series(
                    agent_a, agent_b, base_seed
                )
                dur = round(time.monotonic() - t0, 2)

                record = {
                    "series_id": f"{a_def['name']}_vs_{b_def['name']}_s{s:03d}",
                    "pair_index": pair_idx,
                    "series_index": s,
                    "agent_a": a_def["name"],
                    "agent_b": b_def["name"],
                    "is_llm_a": a_def["provider"] is not None,
                    "is_llm_b": b_def["provider"] is not None,
                    "winner": winner,
                    "score_a": sum(
                        1 for g in game_records if g.get("winner_side") == "a"
                    ),
                    "score_b": sum(
                        1 for g in game_records if g.get("winner_side") == "b"
                    ),
                    "games_played": len(game_records),
                    "games": game_records,
                    "base_seed": base_seed,
                    "duration_s": dur,
                    "error": None,
                    "worker": wid,
                }
                _tick(
                    wid,
                    f"{a_def['name']} vs {b_def['name']} s{s} "
                    f"-> {winner} ({len(game_records)}g {dur:.1f}s)",
                )

            except Exception as exc:
                with _lock:
                    _progress["errors"] += 1
                record = {
                    "series_id": f"{a_def['name']}_vs_{b_def['name']}_s{s:03d}",
                    "pair_index": pair_idx,
                    "series_index": s,
                    "agent_a": a_def["name"],
                    "agent_b": b_def["name"],
                    "is_llm_a": a_def["provider"] is not None,
                    "is_llm_b": b_def["provider"] is not None,
                    "winner": "error",
                    "score_a": 0,
                    "score_b": 0,
                    "games_played": 0,
                    "games": [],
                    "base_seed": base_seed,
                    "duration_s": 0,
                    "error": str(exc),
                    "worker": wid,
                }
                _tick(
                    wid,
                    f"{a_def['name']} vs {b_def['name']} s{s} "
                    f"-> ERROR: {exc}",
                )

            results.append(record)
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")

    return results


# ---------------------------------------------------------------------------
# Merge and analyze
# ---------------------------------------------------------------------------

def _merge_chunks() -> Path:
    merged = OUTPUT_DIR / "results.jsonl"
    records: list[dict] = []
    for chunk in sorted(OUTPUT_DIR.glob("chunk_W*.jsonl")):
        with open(chunk, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    records.sort(key=lambda r: (r["pair_index"], r["series_index"]))
    with open(merged, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    return merged


def _extract_bt_pairs(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            w, a, b = r.get("winner"), r.get("agent_a"), r.get("agent_b")
            if w == a:
                pairs.append((a, b))
            elif w == b:
                pairs.append((b, a))
    return pairs


def _compute_analysis(t003_path: Path) -> str:
    tournaments = {
        "T001": Path("data/tournament_001/results.jsonl"),
        "T002": Path("data/tournament_002/results.jsonl"),
        "T003": t003_path,
    }

    bt_results: dict[str, dict] = {}
    rankings: dict[str, dict] = {}
    for name, path in tournaments.items():
        if path.exists():
            pairs = _extract_bt_pairs(path)
            if pairs:
                bt = compute_bt_scores(pairs, n_bootstrap=1000, bootstrap_seed=42)
                bt_results[name] = {r.name: r for r in bt}
                sorted_bt = sorted(bt, key=lambda x: -x.score)
                rankings[name] = {r.name: i + 1 for i, r in enumerate(sorted_bt)}

    # T003 summary stats
    with open(t003_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    llm_names = {d["name"] for d in AGENT_DEFS if d["provider"] is not None}
    wins: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    for r in records:
        w, a, b = r["winner"], r["agent_a"], r["agent_b"]
        if w in ("draw", "error"):
            continue
        totals[a] += 1
        totals[b] += 1
        wins[w] += 1

    llm_wrs = [
        wins[n] / totals[n] * 100 for n in llm_names if totals[n] > 0
    ]
    avg_llm_wr = sum(llm_wrs) / len(llm_wrs) if llm_wrs else 0
    errors = sum(1 for r in records if r.get("error"))

    lines = [
        "# T001 vs T002 vs T003 — Bradley-Terry Comparison",
        "",
        "## T003 Summary",
        "",
        f"- Total series: {len(records)}",
        f"- Errors: {errors}",
        f"- LLM average win rate: **{avg_llm_wr:.1f}%**",
        "",
    ]

    # Per-LLM win rates
    lines.append("### Per-LLM Win Rates")
    lines.append("")
    lines.append("| Agent | Win Rate | W | L | Total |")
    lines.append("|-------|----------|---|---|-------|")
    for d in AGENT_DEFS:
        if d["provider"] is None:
            continue
        n = d["name"]
        w, t = wins[n], totals[n]
        wr = w / t * 100 if t > 0 else 0
        lines.append(f"| {n} | {wr:.1f}% | {w} | {t - w} | {t} |")
    lines.append("")

    # BT comparison table
    all_agents: set[str] = set()
    for t_results in bt_results.values():
        all_agents.update(t_results.keys())

    lines.append("## BT Rankings Comparison")
    lines.append("")
    lines.append(
        "| Agent | T001 BT | T001 # | T002 BT | T002 # "
        "| T003 BT | T003 # | T003 95% CI |"
    )
    lines.append(
        "|-------|---------|--------|---------|--------"
        "|---------|--------|-------------|"
    )

    def sort_key(agent: str) -> float:
        if "T003" in bt_results and agent in bt_results["T003"]:
            return -bt_results["T003"][agent].score
        return 0

    for agent in sorted(all_agents, key=sort_key):
        row = f"| {agent} |"
        for t in ["T001", "T002", "T003"]:
            if t in bt_results and agent in bt_results[t]:
                bt = bt_results[t][agent]
                rank = rankings[t].get(agent, "—")
                row += f" {bt.score:.4f} | {rank} |"
            else:
                row += " — | — |"
        if "T003" in bt_results and agent in bt_results["T003"]:
            bt = bt_results["T003"][agent]
            row += f" [{bt.ci_lower:.3f}, {bt.ci_upper:.3f}] |"
        else:
            row += " — |"
        lines.append(row)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tournament 003: Exact-Only Cleanroom"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if not args.dry_run:
        missing = [v for _, v in ENV_KEYS.items() if not os.environ.get(v)]
        if missing:
            print(f"Error: Missing: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    worker_pairs = _assign_pairs()
    total = sum(len(p) * SERIES_PER_PAIR for p in worker_pairs.values())
    _progress["total"] = total
    _progress["t0"] = time.monotonic()

    print("=" * 70)
    print("  TOURNAMENT 003: Exact-Only Cleanroom (No Meta Context)")
    print("=" * 70)
    print(f"  Agents:       {NUM_AGENTS} (10 LLMs + 5 baselines)")
    print(f"  Pairs:        {sum(len(p) for p in worker_pairs.values())}")
    print(f"  Total series: {total}")
    print(f"  Dry run:      {args.dry_run}")
    for wid in range(6):
        n = len(worker_pairs[wid])
        print(f"  {WORKER_LABELS[wid]}: {n} pairs ({n * SERIES_PER_PAIR} series)")
    print("=" * 70)
    print()

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures: dict[Any, int] = {}

        # W0 (grok) starts first
        cp = OUTPUT_DIR / f"chunk_{WORKER_LABELS[0]}.jsonl"
        if not args.resume:
            cp.unlink(missing_ok=True)
        futures[executor.submit(
            _run_worker, 0, worker_pairs[0], cp, args.dry_run, args.resume
        )] = 0
        print(f"  Started {WORKER_LABELS[0]}")

        time.sleep(1)

        # W1-W5
        for wid in range(1, 6):
            cp = OUTPUT_DIR / f"chunk_{WORKER_LABELS[wid]}.jsonl"
            if not args.resume:
                cp.unlink(missing_ok=True)
            futures[executor.submit(
                _run_worker, wid, worker_pairs[wid], cp,
                args.dry_run, args.resume,
            )] = wid
            print(f"  Started {WORKER_LABELS[wid]}")

        print()

        for future in as_completed(futures):
            wid = futures[future]
            try:
                results = future.result()
                errs = sum(1 for r in results if r.get("error"))
                print(
                    f"\n  >>> {WORKER_LABELS[wid]} DONE: "
                    f"{len(results)} series, {errs} errors",
                    flush=True,
                )
            except Exception as exc:
                print(
                    f"\n  >>> {WORKER_LABELS[wid]} CRASHED: {exc}",
                    flush=True,
                )

    elapsed = time.monotonic() - _progress["t0"]
    print(f"\n{'=' * 70}")
    print(
        f"  All workers done. Time: {_fmt_time(elapsed)} "
        f"| Errors: {_progress['errors']}"
    )
    print(f"{'=' * 70}")

    print("\n  Merging chunks...")
    merged = _merge_chunks()
    with open(merged) as f:
        n = sum(1 for _ in f)
    print(f"  -> {n} series -> {merged}")

    print("\n  Computing BT scores and comparison...")
    analysis = _compute_analysis(merged)
    report_path = OUTPUT_DIR / "comparison_t001_t002_t003.md"
    with open(report_path, "w") as f:
        f.write(analysis)
    print(f"\n{analysis}")
    print(f"\n  Report saved: {report_path}")


if __name__ == "__main__":
    main()
