#!/usr/bin/env python3
"""T003 PSI Validation v2 — Prompt Sensitivity Index for the No-Meta-Context finding.

Runs a MINI tournament using a paraphrased T003 prompt (t003_v2.txt) with
7 agents: 5 LLMs (gemini-flash, gemini-pro, gpt-5.4, claude-opus, claude-sonnet)
+ 2 baselines (SmartAgent, GreedyAgent). 21 pairings, 5 series each = 105 series.

v2 changes vs v1:
  - Grok excluded (intermittent 403 errors)
  - Claude Opus 4.6 + Claude Sonnet 4.6 added
  - Google rate limiter (2s gap between calls)
  - Google 429 retry (60s wait, 3 attempts)
  - No GreedyAgent fallback on API failure (series marked FAILED)
  - Gemini failure abort threshold (>30%)

Usage:
    python run_t003_psi.py                # Real tournament
    python run_t003_psi.py --dry-run      # Random builds, no API calls
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from agents.baselines import (
    BaseAgent,
    Build,
    GreedyAgent,
    SmartAgent,
)
from agents.llm_agent_v2 import parse_json_response
from analysis.bt_ranking import compute_bt_scores, BTResult
from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine, CombatResult
from simulator.grid import Grid

from run_challenge import (
    _api_call_anthropic,
    _api_call_openai,
    _make_request,
)
from agents.llm_agent_v2 import BUILD_JSON_SCHEMA


# ---------------------------------------------------------------------------
# Fixed Google API call (strip additionalProperties from schema)
# ---------------------------------------------------------------------------

_GOOGLE_SCHEMA = {k: v for k, v in BUILD_JSON_SCHEMA.items() if k != "additionalProperties"}


_google_lock = threading.Lock()
_google_last_call = {"t": 0.0}
_GOOGLE_CALL_GAP = 3.0  # Pro RPM=25, need >=2.4s gap


def _api_call_google_fixed(api_key: str, model: str, prompt: str) -> dict | str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": _GOOGLE_SCHEMA,
            "maxOutputTokens": 2048,
            "temperature": 0.7,
        },
    }
    # Rate limiter: serialize Google calls with 2s gap
    with _google_lock:
        elapsed = time.monotonic() - _google_last_call["t"]
        if elapsed < _GOOGLE_CALL_GAP:
            time.sleep(_GOOGLE_CALL_GAP - elapsed)
        _google_last_call["t"] = time.monotonic()
    # 429 retry: wait 60s and retry up to 3 times
    for attempt in range(3):
        try:
            resp = _make_request(url, {}, body, timeout=90)
            break
        except RuntimeError as exc:
            if "429" in str(exc) and attempt < 2:
                print(f"    [RATE] Google 429 — waiting 60s (attempt {attempt + 1}/3)", flush=True)
                time.sleep(60)
                continue
            raise
    candidates = resp.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        # Collect all text parts (skip thought signatures)
        for part in parts:
            text = part.get("text", "").strip()
            if not text or "thoughtSignature" in part:
                continue
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                pass
        # Fallback: concatenate all text
        all_text = " ".join(p.get("text", "") for p in parts if "thoughtSignature" not in p).strip()
        if all_text:
            try:
                return json.loads(all_text)
            except (json.JSONDecodeError, TypeError):
                return all_text
    return ""


def _build_psi_api_callable(provider: str, model: str, api_key: str):
    dispatch = {
        "anthropic": _api_call_anthropic,
        "openai": _api_call_openai,
        "google": _api_call_google_fixed,
    }
    fn = dispatch[provider]
    def api_call(prompt: str) -> dict | str:
        return fn(api_key, model, prompt)
    return api_call


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROMPT_FILE = "prompts/t003_v2.txt"
OUTPUT_DIR = Path("data/t003_psi")
SERIES_PER_PAIR = 5

AGENT_DEFS: list[dict[str, Any]] = [
    # Gemini excluded — structured output quota exhausted on both Flash and Pro
    # {"name": "gemini-3-flash-preview",  "provider": "google",    "model": "gemini-3-flash-preview"},
    # {"name": "gemini-3.1-pro-preview",  "provider": "google",    "model": "gemini-3.1-pro-preview"},
    {"name": "gpt-5.4",                 "provider": "openai",    "model": "gpt-5.4"},
    {"name": "claude-opus-4-6",         "provider": "anthropic", "model": "claude-opus-4-6"},
    {"name": "claude-sonnet-4-6",       "provider": "anthropic", "model": "claude-sonnet-4-6"},
    {"name": "SmartAgent",              "provider": None,        "model": None},
    {"name": "GreedyAgent",             "provider": None,        "model": None},
]

ENV_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
}

# Original T003 results file
T003_RESULTS = Path("data/tournament_003/results.jsonl")

# ---------------------------------------------------------------------------
# Prompt-file LLM agent with adaptation support
# ---------------------------------------------------------------------------

class PromptFileAdaptiveAgent(BaseAgent):
    """LLM agent that uses a verbatim prompt file, with T003-style adaptation."""

    def __init__(self, name: str, prompt_text: str, api_call) -> None:
        self._name = name
        self._prompt_text = prompt_text
        self._api_call = api_call

    @property
    def name(self) -> str:
        return self._name

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        prompt = self._prompt_text

        # Add adaptation context if opponent build is revealed (loser re-pick)
        if isinstance(opponent_reveal, Build):
            adapt_block = (
                f"\nOPPONENT'S WINNING BUILD (you lost last game to this):\n"
                f"  {opponent_reveal.animal.value.upper()} "
                f"{opponent_reveal.hp}/{opponent_reveal.atk}/{opponent_reveal.spd}/{opponent_reveal.wil}\n"
                f"  Adapt your build to counter this specific opponent.\n"
            )
            prompt = prompt + adapt_block

        for attempt in range(3):
            try:
                response = self._api_call(prompt)
                build = parse_json_response(response, banned)
                if build is not None:
                    return build
            except Exception as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                print(f"    [WARN] {self._name} API failed after 3 attempts: {exc}")
        return None  # No fallback — series will be marked FAILED


# ---------------------------------------------------------------------------
# Creature creation + combat (same as run_challenge.py)
# ---------------------------------------------------------------------------

def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
    hp, atk, spd, wil = build.hp, build.atk, build.spd, build.wil
    animal = build.animal
    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)
    hp_atk = hp + atk
    if hp_atk <= 10:
        size = Size(1, 1)
    elif hp_atk <= 12:
        size = Size(2, 1)
    elif hp_atk <= 17:
        size = Size(2, 2)
    else:
        size = Size(3, 2)
    passive = ANIMAL_PASSIVE.get(animal)
    abilities = ANIMAL_ABILITIES.get(animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)
    return Creature(
        animal=animal, stats=StatBlock(hp=hp, atk=atk, spd=spd, wil=wil),
        passive=passive, current_hp=max_hp, max_hp=max_hp, base_dmg=base_dmg,
        armor_flat=0, size=size, position=position, dodge_chance=dodge,
        resist_chance=resist, movement_range=movement, abilities=abilities,
    )


def _run_single_game(build_a: Build, build_b: Build, seed: int) -> CombatResult:
    ca = _create_creature(build_a, "a", seed)
    cb = _create_creature(build_b, "b", seed)
    return CombatEngine().run_combat(ca, cb, seed)


def _build_to_dict(b: Build) -> dict:
    return {"animal": b.animal.value.upper(), "hp": b.hp, "atk": b.atk, "spd": b.spd, "wil": b.wil}


# ---------------------------------------------------------------------------
# Adaptive series (same protocol as T003)
# ---------------------------------------------------------------------------

def _run_adaptive_series(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
) -> tuple[str, list[dict], bool]:
    """Returns (winner_name, game_records, failed).

    failed=True if any agent returned None build (API failure, no fallback).
    """
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    build_a = agent_a.choose_build(opponent_animal=None, banned=[], opponent_reveal=None)
    build_b = agent_b.choose_build(opponent_animal=None, banned=[], opponent_reveal=None)

    if build_a is None or build_b is None:
        failed_name = name_a if build_a is None else name_b
        print(f"    [FAIL] {failed_name} returned None build — series FAILED", flush=True)
        return "error", [], True

    wins_a, wins_b = 0, 0
    records: list[dict] = []

    for g in range(7):
        if wins_a >= 4 or wins_b >= 4:
            break
        seed = series_seed + g
        result = _run_single_game(build_a, build_b, seed)
        records.append({
            "game": g + 1, "seed": seed,
            "build_a": _build_to_dict(build_a), "build_b": _build_to_dict(build_b),
            "winner_side": result.winner, "ticks": result.ticks,
            "end_condition": result.end_condition,
        })
        if result.winner == "a":
            wins_a += 1
            new_b = agent_b.choose_build(
                opponent_animal=build_a.animal, banned=[], opponent_reveal=build_a)
            if new_b is not None:
                build_b = new_b
        elif result.winner == "b":
            wins_b += 1
            new_a = agent_a.choose_build(
                opponent_animal=build_b.animal, banned=[], opponent_reveal=build_b)
            if new_a is not None:
                build_a = new_a

    if wins_a > wins_b:
        return name_a, records, False
    elif wins_b > wins_a:
        return name_b, records, False
    return "draw", records, False


# ---------------------------------------------------------------------------
# Kendall tau (stdlib only)
# ---------------------------------------------------------------------------

def _kendall_tau(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            product = dx * dy
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total else 0.0


# ---------------------------------------------------------------------------
# Extract original T003 rankings for target agents
# ---------------------------------------------------------------------------

def _get_original_t003_rankings(target_names: set[str]) -> dict[str, float]:
    """Compute BT scores from original T003 data, return scores for target agents."""
    if not T003_RESULTS.exists():
        print(f"  WARNING: {T003_RESULTS} not found", file=sys.stderr)
        return {}

    pairs: list[tuple[str, str]] = []
    with open(T003_RESULTS, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            w, a, b = r.get("winner"), r.get("agent_a"), r.get("agent_b")
            if w == a:
                pairs.append((a, b))
            elif w == b:
                pairs.append((b, a))

    bt = compute_bt_scores(pairs, n_bootstrap=1000, bootstrap_seed=42)
    return {r.name: r.score for r in bt if r.name in target_names}


# ---------------------------------------------------------------------------
# Dry-run stub
# ---------------------------------------------------------------------------

_ORIGINAL_ANIMALS = [Animal.BEAR, Animal.BUFFALO, Animal.BOAR, Animal.TIGER, Animal.WOLF, Animal.MONKEY]

def _dry_run_api(prompt: str) -> dict:
    animal = random.choice(_ORIGINAL_ANIMALS)
    remaining = 16
    stats = [1, 1, 1, 1]
    for i in range(3):
        alloc = random.randint(0, remaining)
        stats[i] += alloc
        remaining -= alloc
    stats[3] += remaining
    return {"animal": animal.value.upper(), "hp": stats[0], "atk": stats[1], "spd": stats[2], "wil": stats[3]}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="T003 PSI Validation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prompt", type=str, default=PROMPT_FILE)
    parser.add_argument("--series", type=int, default=SERIES_PER_PAIR)
    args = parser.parse_args()

    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: {prompt_path} not found", file=sys.stderr)
        sys.exit(1)
    prompt_text = prompt_path.read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:12]

    # Resolve API keys
    api_callables: dict[str, Any] = {}
    if not args.dry_run:
        for provider, env_key in ENV_KEYS.items():
            key = os.environ.get(env_key, "")
            if not key:
                print(f"Error: Missing {env_key}", file=sys.stderr)
                sys.exit(1)
            api_callables[provider] = (provider, key)

    # Create agents
    agents: list[tuple[str, BaseAgent]] = []
    for adef in AGENT_DEFS:
        name = adef["name"]
        provider = adef["provider"]
        if provider is None:
            if name == "SmartAgent":
                agents.append((name, SmartAgent()))
            elif name == "GreedyAgent":
                agents.append((name, GreedyAgent()))
        else:
            if args.dry_run:
                agents.append((name, PromptFileAdaptiveAgent(name, prompt_text, _dry_run_api)))
            else:
                prov, key = api_callables[provider]
                api_call = _build_psi_api_callable(prov, adef["model"], key)
                agents.append((name, PromptFileAdaptiveAgent(name, prompt_text, api_call)))

    n_agents = len(agents)
    all_pairs = list(combinations(range(n_agents), 2))
    total_series = len(all_pairs) * args.series

    # Header
    print("=" * 70, flush=True)
    print("  T003 PSI VALIDATION — Prompt Sensitivity Index", flush=True)
    print("=" * 70, flush=True)
    print(f"  Prompt:       {args.prompt}  (sha256: {prompt_hash}...)", flush=True)
    print(f"  Agents:       {n_agents} ({sum(1 for d in AGENT_DEFS if d['provider'])} LLM + {sum(1 for d in AGENT_DEFS if not d['provider'])} baseline)", flush=True)
    print(f"  Pairs:        {len(all_pairs)}", flush=True)
    print(f"  Series/pair:  {args.series}", flush=True)
    print(f"  Total series: {total_series}", flush=True)
    print(f"  Dry run:      {args.dry_run}", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)

    # Run tournament with parallel workers
    from concurrent.futures import ThreadPoolExecutor, as_completed

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_path = OUTPUT_DIR / "psi_series.jsonl"
    results_path.unlink(missing_ok=True)

    bt_pairs: list[tuple[str, str]] = []
    all_records: list[dict] = []
    _lock = threading.Lock()
    _done = {"n": 0}
    _failed = {"n": 0, "gemini": 0, "gemini_total": 0}
    base_seed = 500_000
    t_start_all = time.monotonic()

    # Build work items
    work_items: list[tuple[int, int, int, int]] = []
    idx = 0
    for i, j in all_pairs:
        for s in range(args.series):
            idx += 1
            work_items.append((i, j, s, base_seed + idx * 1000))

    def _run_one(i: int, j: int, s: int, seed: int) -> dict:
        name_a, _ = agents[i]
        name_b, _ = agents[j]
        agent_a = _fresh_agent(agents[i], prompt_text, api_callables if not args.dry_run else None, args.dry_run)
        agent_b = _fresh_agent(agents[j], prompt_text, api_callables if not args.dry_run else None, args.dry_run)
        t0 = time.monotonic()
        winner, game_records, failed = _run_adaptive_series(agent_a, agent_b, seed)
        dur = time.monotonic() - t0
        return {
            "series_id": f"{name_a}_vs_{name_b}_s{s:03d}",
            "agent_a": name_a, "agent_b": name_b,
            "winner": winner,
            "failed": failed,
            "games_played": len(game_records),
            "games": game_records,
            "base_seed": seed,
            "duration_s": round(dur, 2),
        }

    # 4 parallel workers (one per provider, avoids rate limits)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_run_one, *w): w for w in work_items}

        for future in as_completed(futures):
            record = future.result()
            with _lock:
                _done["n"] += 1
                n = _done["n"]
                name_a = record["agent_a"]
                name_b = record["agent_b"]
                winner = record["winner"]

                # Track failures
                if record["failed"]:
                    _failed["n"] += 1
                    if "gemini" in name_a.lower() or "gemini" in name_b.lower():
                        _failed["gemini"] += 1

                if "gemini" in name_a.lower() or "gemini" in name_b.lower():
                    _failed["gemini_total"] += 1

                if winner == name_a:
                    bt_pairs.append((name_a, name_b))
                elif winner == name_b:
                    bt_pairs.append((name_b, name_a))
                all_records.append(record)

                with open(results_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, default=str) + "\n")

                pct = n / total_series * 100
                elapsed = time.monotonic() - t_start_all
                eta = (elapsed / n * (total_series - n)) if n > 0 else 0
                eta_str = f"{eta:.0f}s" if eta < 60 else f"{eta/60:.0f}m"
                status = "FAILED" if record["failed"] else winner
                print(
                    f"  [{n}/{total_series} {pct:.0f}% ETA:{eta_str}] "
                    f"{name_a} vs {name_b} -> {status} "
                    f"({record['games_played']}g {record['duration_s']:.1f}s)",
                    flush=True,
                )

                # Gemini abort threshold: if >30% of Gemini series fail, abort
                if _failed["gemini_total"] >= 10 and _failed["gemini"] / _failed["gemini_total"] > 0.30:
                    print(f"\n  ABORT: Gemini failure rate {_failed['gemini']}/{_failed['gemini_total']} > 30%", flush=True)
                    executor.shutdown(wait=False, cancel_futures=True)
                    sys.exit(1)

    total_time = time.monotonic() - t_start_all
    n_failed = _failed["n"]
    n_valid = len(all_records) - n_failed
    print(f"\n  Tournament done in {total_time:.0f}s", flush=True)
    print(f"  Results saved: {results_path}", flush=True)
    print(f"  Valid series: {n_valid}/{len(all_records)} ({n_failed} failed)", flush=True)

    # Compute BT rankings for PSI run
    if not bt_pairs:
        print("\n  ERROR: No decisive series. Cannot compute rankings.")
        sys.exit(1)

    psi_bt = compute_bt_scores(bt_pairs, n_bootstrap=1000, bootstrap_seed=42)
    psi_scores = {r.name: r.score for r in psi_bt}

    print(f"\n  PSI Tournament BT Rankings (t003_v2):")
    print(f"  {'Rank':<5} {'Agent':<30} {'BT Score':<10} {'95% CI':<22}")
    print("  " + "-" * 65)
    for i, r in enumerate(psi_bt, 1):
        print(f"  {i:<5} {r.name:<30} {r.score:<10.4f} [{r.ci_lower:.4f}, {r.ci_upper:.4f}]")

    # Get original T003 rankings
    target_names = {d["name"] for d in AGENT_DEFS}
    orig_scores = _get_original_t003_rankings(target_names)

    if not orig_scores:
        print("\n  ERROR: Could not load original T003 rankings.")
        sys.exit(1)

    print(f"\n  Original T003 BT Scores (for target agents):")
    for name in sorted(orig_scores, key=lambda n: -orig_scores[n]):
        print(f"    {name:<30} {orig_scores[name]:.4f}")

    # Compute Kendall tau
    common = sorted(set(psi_scores.keys()) & set(orig_scores.keys()))
    if len(common) < 3:
        print(f"\n  ERROR: Only {len(common)} common agents. Need at least 3.")
        sys.exit(1)

    orig_ranks = [orig_scores[a] for a in common]
    psi_ranks = [psi_scores[a] for a in common]
    tau = _kendall_tau(orig_ranks, psi_ranks)

    # Win rate stats
    wins: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    for r in all_records:
        w, a, b = r["winner"], r["agent_a"], r["agent_b"]
        if w in ("draw", "error"):
            continue
        totals[a] += 1
        totals[b] += 1
        wins[w] += 1

    llm_names = {d["name"] for d in AGENT_DEFS if d["provider"] is not None}
    llm_wrs = {n: wins[n] / totals[n] * 100 if totals[n] > 0 else 0 for n in llm_names}
    avg_llm_wr = sum(llm_wrs.values()) / len(llm_wrs) if llm_wrs else 0

    # Verdict
    if tau > 0.85:
        verdict = "PROMPT-ROBUST"
        verdict_detail = "tau > 0.85: T003 finding is robust to prompt paraphrasing."
    elif tau > 0.60:
        verdict = "MODERATE"
        verdict_detail = "0.60 < tau < 0.85: T003 finding shows moderate prompt sensitivity."
    else:
        verdict = "PROMPT-SENSITIVE"
        verdict_detail = "tau < 0.60: T003 finding is NOT robust to prompt paraphrasing."

    print(f"\n{'=' * 70}")
    print(f"  KENDALL TAU: {tau:.4f}")
    print(f"  VERDICT:     {verdict}")
    print(f"  {verdict_detail}")
    print(f"  LLM avg WR:  {avg_llm_wr:.1f}%")
    print(f"{'=' * 70}")

    # Generate docs/T003_PSI.md
    _write_report(
        prompt_path=str(args.prompt),
        prompt_hash=prompt_hash,
        psi_bt=psi_bt,
        orig_scores=orig_scores,
        common=common,
        tau=tau,
        verdict=verdict,
        verdict_detail=verdict_detail,
        llm_wrs=llm_wrs,
        avg_llm_wr=avg_llm_wr,
        wins=wins,
        totals=totals,
        total_series=total_series,
        total_time=total_time,
        dry_run=args.dry_run,
    )


def _fresh_agent(
    agent_tuple: tuple[str, BaseAgent],
    prompt_text: str,
    api_callables: dict | None,
    dry_run: bool,
) -> BaseAgent:
    name, original = agent_tuple
    if isinstance(original, SmartAgent):
        return SmartAgent()
    if isinstance(original, GreedyAgent):
        return GreedyAgent()
    if isinstance(original, PromptFileAdaptiveAgent):
        if dry_run:
            return PromptFileAdaptiveAgent(name, prompt_text, _dry_run_api)
        else:
            # Find the provider for this agent
            for adef in AGENT_DEFS:
                if adef["name"] == name and adef["provider"]:
                    prov, key = api_callables[adef["provider"]]
                    api_call = _build_psi_api_callable(prov, adef["model"], key)
                    return PromptFileAdaptiveAgent(name, prompt_text, api_call)
    return original


def _write_report(
    prompt_path: str,
    prompt_hash: str,
    psi_bt: list[BTResult],
    orig_scores: dict[str, float],
    common: list[str],
    tau: float,
    verdict: str,
    verdict_detail: str,
    llm_wrs: dict[str, float],
    avg_llm_wr: float,
    wins: Counter,
    totals: Counter,
    total_series: int,
    total_time: float,
    dry_run: bool,
) -> None:
    """Write docs/T003_PSI.md report."""
    Path("docs").mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Rank tables
    orig_sorted = sorted(common, key=lambda n: -orig_scores.get(n, 0))
    psi_scores = {r.name: r for r in psi_bt}
    psi_sorted = sorted(common, key=lambda n: -psi_scores[n].score if n in psi_scores else 0)

    orig_rank_map = {name: i + 1 for i, name in enumerate(orig_sorted)}
    psi_rank_map = {name: i + 1 for i, name in enumerate(psi_sorted)}

    lines = [
        "# T003 PSI Validation -- Prompt Sensitivity Index",
        "",
        f"Generated: {timestamp}",
        f"{'**DRY RUN** -- results are random, not meaningful.' if dry_run else ''}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Kendall tau | **{tau:.4f}** |",
        f"| Verdict | **{verdict}** |",
        f"| LLM avg win rate (PSI run) | {avg_llm_wr:.1f}% |",
        f"| Total series | {total_series} |",
        f"| Runtime | {total_time:.0f}s |",
        "",
        f"> {verdict_detail}",
        "",
        "## Method",
        "",
        "Prompt Sensitivity Index (PSI) measures whether tournament rankings are stable",
        "across semantically-equivalent prompt paraphrases. We created `t003_v2.txt` --",
        "a paraphrase of the original T003 prompt with identical game mechanics but",
        "different wording -- and ran a mini tournament with 6 agents (4 LLMs + 2 baselines).",
        "",
        f"- **Original prompt**: `prompts/t003_prompt.txt`",
        f"- **Paraphrased prompt**: `{prompt_path}` (sha256: `{prompt_hash}...`)",
        f"- **Protocol**: Adaptive best-of-7 (same as T003)",
        f"- **Agents**: gemini-flash, gemini-pro, gpt-5.4, claude-opus-4-6, claude-sonnet-4-6, SmartAgent, GreedyAgent",
        f"- **Series per pair**: {SERIES_PER_PAIR}",
        "",
        "## Ranking Comparison",
        "",
        "| Agent | T003 Original Rank | T003 Original BT | PSI (v2) Rank | PSI (v2) BT | Delta |",
        "|-------|--------------------|-------------------|---------------|-------------|-------|",
    ]

    for name in orig_sorted:
        o_rank = orig_rank_map[name]
        o_bt = orig_scores.get(name, 0)
        p_rank = psi_rank_map.get(name, "?")
        p_bt_r = psi_scores.get(name)
        p_bt = p_bt_r.score if p_bt_r else 0
        delta = p_rank - o_rank if isinstance(p_rank, int) else "?"
        delta_str = f"+{delta}" if isinstance(delta, int) and delta > 0 else str(delta)
        lines.append(f"| {name} | {o_rank} | {o_bt:.4f} | {p_rank} | {p_bt:.4f} | {delta_str} |")

    lines.extend([
        "",
        "## Per-Agent Win Rates (PSI Run)",
        "",
        "| Agent | W | L | Total | WR |",
        "|-------|---|---|-------|----|",
    ])

    for d in AGENT_DEFS:
        n = d["name"]
        w, t = wins[n], totals[n]
        wr = w / t * 100 if t > 0 else 0
        lines.append(f"| {n} | {w} | {t - w} | {t} | {wr:.1f}% |")

    lines.extend([
        "",
        "## BT Rankings (PSI Run, full)",
        "",
        "| Rank | Agent | BT Score | 95% CI |",
        "|------|-------|----------|--------|",
    ])

    for i, r in enumerate(psi_bt, 1):
        lines.append(f"| {i} | {r.name} | {r.score:.4f} | [{r.ci_lower:.4f}, {r.ci_upper:.4f}] |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "Kendall tau thresholds:",
        "- tau > 0.85: **prompt-robust** -- rankings are stable across paraphrases",
        "- 0.60 < tau < 0.85: **moderate** -- some sensitivity, investigate further",
        "- tau < 0.60: **prompt-sensitive** -- rankings depend on exact wording",
        "",
        f"Our tau = {tau:.4f} -> **{verdict}**",
        "",
    ])

    report_path = Path("docs/T003_PSI.md")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Report saved: {report_path}")


if __name__ == "__main__":
    main()
