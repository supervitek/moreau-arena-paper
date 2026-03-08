#!/usr/bin/env python3
"""Season 1 Tournament Runner — Moreau Arena

All-pairs tournament with 15 agents (10 LLMs + 5 baselines).
Best-of-7 series using the Season 1 engine and animal roster.
6 parallel workers organized by model latency.

Usage:
    python run_s1_tournament.py              # Real tournament
    python run_s1_tournament.py --dry-run    # Random builds, no API calls
    python run_s1_tournament.py --resume     # Resume from existing chunks
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
from pathlib import Path
from typing import Any

from run_challenge import (
    _api_call_anthropic,
    _api_call_openai,
    _api_call_openai_responses,
    _api_call_xai,
    _make_request,
    _OPENAI_RESPONSES_MODELS,
)
from season1.engine_s1 import run_match as s1_run_match

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("data/season1_tournament")
SERIES_PER_PAIR = 1   # one best-of-7 series per pair (can be increased)
NUM_AGENTS = 15
GAMES_TO_WIN = 4      # first to 4 wins takes the series (best-of-7)

S1_ANIMALS = [
    "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
    "porcupine", "scorpion", "vulture", "rhino", "viper",
    "fox", "eagle", "panther",
]

FALLBACK_BUILD = {"animal": "fox", "hp": 5, "atk": 5, "spd": 5, "wil": 5}

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
    {"idx": 10, "name": "RandomAgent_S1",      "provider": None, "model": None, "baseline_cls": "RandomAgent_S1"},
    {"idx": 11, "name": "GreedyAgent_S1",      "provider": None, "model": None, "baseline_cls": "GreedyAgent_S1"},
    {"idx": 12, "name": "SmartAgent_S1",       "provider": None, "model": None, "baseline_cls": "SmartAgent_S1"},
    {"idx": 13, "name": "ConservativeAgent_S1","provider": None, "model": None, "baseline_cls": "ConservativeAgent_S1"},
    {"idx": 14, "name": "HighVarianceAgent_S1","provider": None, "model": None, "baseline_cls": "HighVarianceAgent_S1"},
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
# Gemini rate limiter
# ---------------------------------------------------------------------------

_google_lock = threading.Lock()
_google_last_call: dict[str, float] = {"t": 0.0}
_GOOGLE_CALL_GAP = 3.0  # >= 2.4s for Pro RPM=25


# S1-specific Google schema (strip additionalProperties)
_S1_BUILD_SCHEMA = {
    "type": "object",
    "properties": {
        "animal": {"type": "string"},
        "hp":     {"type": "integer"},
        "atk":    {"type": "integer"},
        "spd":    {"type": "integer"},
        "wil":    {"type": "integer"},
    },
    "required": ["animal", "hp", "atk", "spd", "wil"],
}


def _api_call_google_s1(api_key: str, model: str, prompt: str) -> dict | str:
    """Google Generative AI call with rate limiter and 429 retry."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": _S1_BUILD_SCHEMA,
            "maxOutputTokens": 2048,
            "temperature": 0.7,
        },
    }
    # Rate limiter: serialize Google calls with gap
    with _google_lock:
        elapsed = time.monotonic() - _google_last_call["t"]
        if elapsed < _GOOGLE_CALL_GAP:
            time.sleep(_GOOGLE_CALL_GAP - elapsed)
        _google_last_call["t"] = time.monotonic()

    # 429 retry: wait 60s, up to 3 attempts
    for attempt in range(3):
        try:
            resp = _make_request(url, {}, body, timeout=90)
            break
        except RuntimeError as exc:
            if "429" in str(exc) and attempt < 2:
                print(
                    f"    [RATE] Google 429 — waiting 60s (attempt {attempt + 1}/3)",
                    flush=True,
                )
                time.sleep(60)
                continue
            raise

    candidates = resp.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        # Skip thought signatures; parse first real text part
        for part in parts:
            if "thoughtSignature" in part:
                continue
            text = part.get("text", "").strip()
            if not text:
                continue
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                pass
        # Fallback: concatenate all non-thought text
        all_text = " ".join(
            p.get("text", "") for p in parts if "thoughtSignature" not in p
        ).strip()
        if all_text:
            try:
                return json.loads(all_text)
            except (json.JSONDecodeError, TypeError):
                return all_text
    return ""


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_TEXT: str | None = None
_PROMPT_LOCK = threading.Lock()


def _load_prompt() -> str:
    global _PROMPT_TEXT
    with _PROMPT_LOCK:
        if _PROMPT_TEXT is None:
            prompt_path = Path("prompts/s1_prompt.txt")
            if prompt_path.exists():
                _PROMPT_TEXT = prompt_path.read_text(encoding="utf-8")
            else:
                _PROMPT_TEXT = (
                    "Choose a build for Moreau Arena Season 1. "
                    "Return JSON: {\"animal\": \"fox\", \"hp\": 5, \"atk\": 5, \"spd\": 5, \"wil\": 5}"
                )
        return _PROMPT_TEXT


# ---------------------------------------------------------------------------
# Build validation
# ---------------------------------------------------------------------------

def _validate_build(raw: Any) -> dict[str, Any] | None:
    """Validate and normalise a build dict. Returns None on failure."""
    if not isinstance(raw, dict):
        return None
    animal = str(raw.get("animal", "")).lower().strip()
    if animal not in S1_ANIMALS:
        return None
    try:
        hp  = int(raw["hp"])
        atk = int(raw["atk"])
        spd = int(raw["spd"])
        wil = int(raw["wil"])
    except (KeyError, TypeError, ValueError):
        return None
    if hp < 1 or atk < 1 or spd < 1 or wil < 1:
        return None
    if hp + atk + spd + wil != 20:
        return None
    return {"animal": animal, "hp": hp, "atk": atk, "spd": spd, "wil": wil}


def _random_s1_build(rng: random.Random | None = None) -> dict[str, Any]:
    """Return a random valid S1 build."""
    r = rng or random
    animal = r.choice(S1_ANIMALS)
    remaining = 16  # 20 - 4 minimums
    stats = [1, 1, 1, 1]
    for i in range(3):
        alloc = r.randint(0, remaining)
        stats[i] += alloc
        remaining -= alloc
    stats[3] += remaining
    return {"animal": animal, "hp": stats[0], "atk": stats[1], "spd": stats[2], "wil": stats[3]}


# ---------------------------------------------------------------------------
# API callable cache
# ---------------------------------------------------------------------------

_api_cache: dict[str, Any] = {}
_api_cache_lock = threading.Lock()


def _get_api_callable(provider: str, model: str):
    key = f"{provider}:{model}"
    with _api_cache_lock:
        if key in _api_cache:
            return _api_cache[key]
    api_key = os.environ.get(ENV_KEYS[provider], "")
    if not api_key:
        raise RuntimeError(f"Missing {ENV_KEYS[provider]}")
    if provider == "openai" and model in _OPENAI_RESPONSES_MODELS:
        fn = lambda p, _k=api_key, _m=model: _api_call_openai_responses(_k, _m, p)
    elif provider == "google":
        fn = lambda p, _k=api_key, _m=model: _api_call_google_s1(_k, _m, p)
    else:
        dispatch = {
            "anthropic": _api_call_anthropic,
            "openai": _api_call_openai,
            "xai": _api_call_xai,
        }
        call_fn = dispatch[provider]
        fn = lambda p, _k=api_key, _m=model, _f=call_fn: _f(_k, _m, p)
    with _api_cache_lock:
        _api_cache[key] = fn
    return fn


# ---------------------------------------------------------------------------
# Build choosers
# ---------------------------------------------------------------------------

def _llm_choose_build(
    api_call,
    opponent_animal: str | None,
) -> dict[str, Any]:
    """Call LLM to choose a build. Falls back to fox 5 5 5 5 on failure."""
    prompt = _load_prompt()
    if opponent_animal:
        prompt = prompt + f"\n\nYour opponent previously chose: {opponent_animal}."
    try:
        raw = api_call(prompt)
        build = _validate_build(raw)
        if build is not None:
            return build
    except Exception:
        pass
    return dict(FALLBACK_BUILD)


def _baseline_choose_build(
    baseline_cls_name: str,
    opponent_animal: str | None,
    series_seed: int,
) -> dict[str, Any]:
    """Lazy-import baseline and get a build. Falls back to random on failure."""
    try:
        # Lazy import to avoid module-level import errors
        import importlib
        mod = importlib.import_module("season1.baselines_s1")
        cls = getattr(mod, baseline_cls_name)
        # Instantiate — seeded agents get series_seed, others plain
        try:
            agent = cls(seed=series_seed)
        except TypeError:
            agent = cls()
        result = agent.choose_build(
            opponent_animal=opponent_animal,
            banned=[],
        )
        # result may be a dict or an object with attributes
        if isinstance(result, dict):
            build = _validate_build(result)
            if build is not None:
                return build
        else:
            build = _validate_build({
                "animal": getattr(result, "animal", "fox"),
                "hp":     getattr(result, "hp", 5),
                "atk":    getattr(result, "atk", 5),
                "spd":    getattr(result, "spd", 5),
                "wil":    getattr(result, "wil", 5),
            })
            if build is not None:
                return build
    except Exception:
        pass
    return _random_s1_build()


def _dry_run_choose_build(seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    return _random_s1_build(rng)


# ---------------------------------------------------------------------------
# Series runner
# ---------------------------------------------------------------------------

def _run_s1_series(
    a_def: dict,
    b_def: dict,
    base_seed: int,
    dry_run: bool,
) -> tuple[str, int, int, list[dict]]:
    """Run one best-of-7 S1 series. Returns (winner_name, score_a, score_b, games)."""
    wins_a = 0
    wins_b = 0
    games: list[dict] = []

    # Track last picks so loser can see opponent's previous animal
    prev_animal_a: str | None = None
    prev_animal_b: str | None = None

    game_num = 0

    while wins_a < GAMES_TO_WIN and wins_b < GAMES_TO_WIN and game_num < 7:
        game_seed = base_seed + game_num

        # --- Choose builds ---
        if dry_run:
            build_a = _dry_run_choose_build(game_seed * 31 + 1)
            build_b = _dry_run_choose_build(game_seed * 31 + 2)
        else:
            # LLM or baseline
            if a_def["provider"] is not None:
                api_a = _get_api_callable(a_def["provider"], a_def["model"])
                build_a = _llm_choose_build(api_a, prev_animal_b)
            else:
                build_a = _baseline_choose_build(
                    a_def["baseline_cls"], prev_animal_b, game_seed
                )

            if b_def["provider"] is not None:
                api_b = _get_api_callable(b_def["provider"], b_def["model"])
                build_b = _llm_choose_build(api_b, prev_animal_a)
            else:
                build_b = _baseline_choose_build(
                    b_def["baseline_cls"], prev_animal_a, game_seed
                )

        prev_animal_a = build_a["animal"]
        prev_animal_b = build_b["animal"]

        # --- Run game ---
        stats_a = (build_a["hp"], build_a["atk"], build_a["spd"], build_a["wil"])
        stats_b = (build_b["hp"], build_b["atk"], build_b["spd"], build_b["wil"])

        result = s1_run_match(
            build_a["animal"], stats_a,
            build_b["animal"], stats_b,
            game_seed,
        )

        winner_side = result.get("winner")  # "a", "b", or None
        ticks = result.get("ticks", 0)

        game_record = {
            "game":        game_num + 1,
            "seed":        game_seed,
            "build_a":     dict(build_a),
            "build_b":     dict(build_b),
            "winner_side": winner_side,
            "ticks":       ticks,
        }
        games.append(game_record)

        if winner_side == "a":
            wins_a += 1
        elif winner_side == "b":
            wins_b += 1
        # None = draw — no score change, same builds next game

        game_num += 1

    # Determine series winner
    if wins_a > wins_b:
        series_winner = a_def["name"]
    elif wins_b > wins_a:
        series_winner = b_def["name"]
    else:
        series_winner = "draw"

    return series_winner, wins_a, wins_b, games


# ---------------------------------------------------------------------------
# Worker pair assignment
# ---------------------------------------------------------------------------

def _assign_pairs() -> dict[int, list[tuple[int, int, int]]]:
    all_pairs = list(combinations(range(NUM_AGENTS), 2))
    workers: dict[int, list] = {i: [] for i in range(6)}
    for pair_idx, (a, b) in enumerate(all_pairs):
        if 9 in (a, b):           # grok
            workers[0].append((pair_idx, a, b))
        elif 7 in (a, b):         # gemini-flash
            workers[1].append((pair_idx, a, b))
        elif 8 in (a, b):         # gemini-pro
            workers[2].append((pair_idx, a, b))
        elif 4 in (a, b) or 6 in (a, b):   # codex models
            workers[3].append((pair_idx, a, b))
        elif 0 in (a, b) or 1 in (a, b):   # anthropic flagship
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
_progress: dict[str, Any] = {"done": 0, "total": 0, "errors": 0, "t0": 0.0}


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
                t0 = time.monotonic()
                series_winner, score_a, score_b, game_records = _run_s1_series(
                    a_def, b_def, base_seed, dry_run
                )
                dur = round(time.monotonic() - t0, 2)

                record = {
                    "series_id":    f"{a_def['name']}_vs_{b_def['name']}_s{s:03d}",
                    "pair_index":   pair_idx,
                    "series_index": s,
                    "agent_a":      a_def["name"],
                    "agent_b":      b_def["name"],
                    "is_llm_a":     a_def["provider"] is not None,
                    "is_llm_b":     b_def["provider"] is not None,
                    "winner":       series_winner,
                    "score_a":      score_a,
                    "score_b":      score_b,
                    "games_played": len(game_records),
                    "games":        game_records,
                    "base_seed":    base_seed,
                    "duration_s":   dur,
                    "error":        None,
                    "worker":       wid,
                }
                _tick(
                    wid,
                    f"{a_def['name']} vs {b_def['name']} s{s} "
                    f"-> {series_winner} ({score_a}-{score_b} {len(game_records)}g {dur:.1f}s)",
                )

            except Exception as exc:
                with _lock:
                    _progress["errors"] += 1
                record = {
                    "series_id":    f"{a_def['name']}_vs_{b_def['name']}_s{s:03d}",
                    "pair_index":   pair_idx,
                    "series_index": s,
                    "agent_a":      a_def["name"],
                    "agent_b":      b_def["name"],
                    "is_llm_a":     a_def["provider"] is not None,
                    "is_llm_b":     b_def["provider"] is not None,
                    "winner":       "error",
                    "score_a":      0,
                    "score_b":      0,
                    "games_played": 0,
                    "games":        [],
                    "base_seed":    base_seed,
                    "duration_s":   0,
                    "error":        str(exc),
                    "worker":       wid,
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
# Merge chunks
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


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _print_summary(merged: Path) -> None:
    with open(merged, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    llm_names = {d["name"] for d in AGENT_DEFS if d["provider"] is not None}
    wins: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    errors = 0

    for r in records:
        if r.get("error"):
            errors += 1
            continue
        w, a, b = r["winner"], r["agent_a"], r["agent_b"]
        if w in ("draw", "error"):
            continue
        totals[a] += 1
        totals[b] += 1
        wins[w] += 1

    print("\n  Season 1 Tournament — Win Rates")
    print("  " + "-" * 55)
    print(f"  {'Agent':<30} {'W':>4} {'L':>4} {'WR':>7}")
    print("  " + "-" * 55)

    for d in AGENT_DEFS:
        n = d["name"]
        w, t = wins[n], totals[n]
        wr = w / t * 100 if t > 0 else 0.0
        marker = " *" if d["provider"] is not None else ""
        print(f"  {n:<30} {w:>4} {t - w:>4} {wr:>6.1f}%{marker}")

    print("  " + "-" * 55)
    print(f"  Total series: {len(records)} | Errors: {errors}")
    print(f"  (* = LLM agent)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Season 1 Tournament Runner — Moreau Arena"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip all API calls, use random valid builds")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing chunk files")
    args = parser.parse_args()

    if not args.dry_run:
        missing = [v for k, v in ENV_KEYS.items() if not os.environ.get(v)]
        if missing:
            print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    worker_pairs = _assign_pairs()
    total_pairs = sum(len(p) for p in worker_pairs.values())
    total = sum(len(p) * SERIES_PER_PAIR for p in worker_pairs.values())
    _progress["total"] = total
    _progress["t0"] = time.monotonic()

    # --- Header ---
    print("=" * 70)
    if args.dry_run:
        print("  *** DRY RUN — No API calls, random builds ***")
    print("  MOREAU ARENA — SEASON 1 TOURNAMENT")
    print("=" * 70)
    print(f"  Estimated cost:    $80-120")
    print(f"  Estimated runtime: 4-6 hours")
    print(f"  Series:            {total_pairs} | Games (est): ~{total_pairs * 5} | Agents: {NUM_AGENTS}")
    print()
    print(f"  Agents:     {NUM_AGENTS} (10 LLMs + 5 baselines)")
    print(f"  Pairs:      {total_pairs}")
    print(f"  Total series: {total}")
    print(f"  Series format: Best-of-7 (first to {GAMES_TO_WIN} wins)")
    print(f"  Dry run:    {args.dry_run}")
    print(f"  Resume:     {args.resume}")
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

        time.sleep(0.5)

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

    _print_summary(merged)


if __name__ == "__main__":
    main()
