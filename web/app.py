"""Moreau Arena — FastAPI Web UI.

Provides a web interface for running fights between creature builds,
viewing leaderboard data from tournament results, and exploring
the benchmark methodology.
"""

from __future__ import annotations

import json
import logging
import math
import sys
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from itertools import combinations
from pathlib import Path
from typing import Any

import os
import random
import re
import time

from fastapi import APIRouter, FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# Add parent directory to sys.path so we can import the simulator package
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from analysis.bt_ranking import (
    compute_bt_scores,
    load_results_from_jsonl,
    update_ratings,
)
from simulator.__main__ import _create_creature, _parse_build, _run_games
from simulator.engine import CombatEngine
from season1.engine_s1 import run_match as s1_run_match
from pets.soul import generate_soul_response, calculate_mood as pet_calculate_mood

logger = logging.getLogger("moreau-arena")

# -- Startup cache for BT scores / pairwise / cycles -------------------------

_cache: dict[str, dict[str, Any]] = {}

STATIC_DIR = Path(__file__).resolve().parent / "static"
RESULTS_DIR = _project_root / "results"
SUBMISSIONS_DIR = RESULTS_DIR / "submissions"
DATA_DIR = _project_root / "data"
SEASON1_DIR = _project_root / "season1"

VALID_ANIMALS = [
    "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
    "crocodile", "eagle", "snake", "raven", "shark", "owl", "fox", "scorpion",
]

S1_ANIMALS = [
    "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
    "porcupine", "scorpion", "vulture", "rhino", "viper", "fox", "eagle", "panther",
]

# Tournament track mapping
TRACK_PATHS: dict[str, list[Path]] = {
    "A": [DATA_DIR / "tournament_001" / "results.jsonl"],
    "B": [DATA_DIR / "tournament_002" / "results.jsonl"],
    "C": [DATA_DIR / "tournament_003" / "results.jsonl"],
    "all": [
        DATA_DIR / "tournament_001" / "results.jsonl",
        DATA_DIR / "tournament_002" / "results.jsonl",
        DATA_DIR / "tournament_003" / "results.jsonl",
    ],
}

# Reference builds for the /challenge endpoint
REFERENCE_BUILDS = [
    "bear 5 5 5 5",
    "tiger 3 8 6 3",
    "buffalo 8 6 4 2",
    "wolf 4 6 7 3",
    "scorpion 5 5 5 5",
]


BASELINES = {"SmartAgent", "GreedyAgent", "ConservativeAgent", "HighVarianceAgent", "RandomAgent"}


def _compute_agent_cards() -> dict[str, dict[str, Any]]:
    """Parse JSONL tournament data and compute per-agent card data."""
    # Structures: per track, per agent
    # track_key -> agent_name -> list of (animal, hp, atk, spd, wil, won_game:bool)
    _tracks = ["A", "B", "C"]
    agent_builds: dict[str, dict[str, list[dict[str, Any]]]] = {t: defaultdict(list) for t in _tracks}
    # track_key -> agent_name -> {opponent -> {"wins": int, "losses": int}}
    agent_pairwise: dict[str, dict[str, dict[str, dict[str, int]]]] = {
        t: defaultdict(lambda: defaultdict(lambda: {"wins": 0, "losses": 0})) for t in _tracks
    }
    # track_key -> agent_name -> {"series_wins": int, "series_losses": int, "series_draws": int}
    agent_records: dict[str, dict[str, dict[str, int]]] = {
        t: defaultdict(lambda: {"series_wins": 0, "series_losses": 0, "series_draws": 0}) for t in _tracks
    }
    # track_key -> agent_name -> list of series build history dicts
    agent_series_history: dict[str, dict[str, list[dict[str, Any]]]] = {t: defaultdict(list) for t in _tracks}

    track_map = {
        "A": DATA_DIR / "tournament_001" / "results.jsonl",
        "B": DATA_DIR / "tournament_002" / "results.jsonl",
        "C": DATA_DIR / "tournament_003" / "results.jsonl",
    }

    for track_key, jsonl_path in track_map.items():
        if not jsonl_path.exists():
            continue
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                agent_a = record.get("agent_a", "unknown")
                agent_b = record.get("agent_b", "unknown")
                winner = record.get("winner")
                games = record.get("games", [])

                # Series record
                if winner == agent_a:
                    agent_records[track_key][agent_a]["series_wins"] += 1
                    agent_records[track_key][agent_b]["series_losses"] += 1
                elif winner == agent_b:
                    agent_records[track_key][agent_b]["series_wins"] += 1
                    agent_records[track_key][agent_a]["series_losses"] += 1
                else:
                    agent_records[track_key][agent_a]["series_draws"] += 1
                    agent_records[track_key][agent_b]["series_draws"] += 1

                # Pairwise series wins
                if winner == agent_a:
                    agent_pairwise[track_key][agent_a][agent_b]["wins"] += 1
                    agent_pairwise[track_key][agent_b][agent_a]["losses"] += 1
                elif winner == agent_b:
                    agent_pairwise[track_key][agent_b][agent_a]["wins"] += 1
                    agent_pairwise[track_key][agent_a][agent_b]["losses"] += 1

                # Extract builds per game
                # T001: builds at top level
                # T002: builds inside each game object
                top_build_a = record.get("build_a")
                top_build_b = record.get("build_b")

                series_builds_a: list[dict[str, Any]] = []
                series_builds_b: list[dict[str, Any]] = []

                for game in games:
                    game_winner = game.get("winner")
                    # Determine build for this game
                    if track_key == "A":
                        ba = top_build_a
                        bb = top_build_b
                    else:
                        ba = game.get("build_a") or top_build_a
                        bb = game.get("build_b") or top_build_b

                    if ba:
                        agent_builds[track_key][agent_a].append({
                            "animal": ba.get("animal", "unknown"),
                            "hp": ba.get("hp", 0),
                            "atk": ba.get("atk", 0),
                            "spd": ba.get("spd", 0),
                            "wil": ba.get("wil", 0),
                            "won": game_winner == agent_a,
                        })
                        series_builds_a.append({
                            "game": game.get("game_number", 0),
                            "animal": ba.get("animal", "unknown"),
                            "hp": ba.get("hp", 0),
                            "atk": ba.get("atk", 0),
                            "spd": ba.get("spd", 0),
                            "wil": ba.get("wil", 0),
                            "won": game_winner == agent_a,
                        })

                    if bb:
                        agent_builds[track_key][agent_b].append({
                            "animal": bb.get("animal", "unknown"),
                            "hp": bb.get("hp", 0),
                            "atk": bb.get("atk", 0),
                            "spd": bb.get("spd", 0),
                            "wil": bb.get("wil", 0),
                            "won": game_winner == agent_b,
                        })
                        series_builds_b.append({
                            "game": game.get("game_number", 0),
                            "animal": bb.get("animal", "unknown"),
                            "hp": bb.get("hp", 0),
                            "atk": bb.get("atk", 0),
                            "spd": bb.get("spd", 0),
                            "wil": bb.get("wil", 0),
                            "won": game_winner == agent_b,
                        })

                # Store series history
                series_info_a = {
                    "opponent": agent_b,
                    "series_id": record.get("series_id", ""),
                    "result": "win" if winner == agent_a else ("loss" if winner == agent_b else "draw"),
                    "score": f"{record.get('score_a', 0)}-{record.get('score_b', 0)}",
                    "builds": series_builds_a,
                }
                series_info_b = {
                    "opponent": agent_a,
                    "series_id": record.get("series_id", ""),
                    "result": "win" if winner == agent_b else ("loss" if winner == agent_a else "draw"),
                    "score": f"{record.get('score_b', 0)}-{record.get('score_a', 0)}",
                    "builds": series_builds_b,
                }
                agent_series_history[track_key][agent_a].append(series_info_a)
                agent_series_history[track_key][agent_b].append(series_info_b)

    # Gather all agent names
    all_agents: set[str] = set()
    for track_key in ("A", "B", "C"):
        all_agents.update(agent_records[track_key].keys())

    # Build BT score lookup from cache
    bt_lookup: dict[str, dict[str, dict[str, Any]]] = {"A": {}, "B": {}, "C": {}}
    for track_key in ("A", "B", "C"):
        if track_key in _cache and "bt" in _cache[track_key]:
            for i, entry in enumerate(_cache[track_key]["bt"]["bt_scores"]):
                bt_lookup[track_key][entry["name"]] = {
                    "rank": i + 1,
                    "bt_score": entry["bt_score"],
                    "ci_lower": entry["ci_lower"],
                    "ci_upper": entry["ci_upper"],
                }

    # Assemble per-agent cards
    cards: dict[str, dict[str, Any]] = {}
    for agent_name in sorted(all_agents):
        agent_type = "Baseline" if agent_name in BASELINES else "LLM"

        tracks_data: dict[str, dict[str, Any]] = {}
        animals_used: dict[str, dict[str, int]] = {}
        favorite_animal: dict[str, str] = {}
        avg_stats: dict[str, dict[str, float]] = {}
        pairwise_rates: dict[str, dict[str, float | None]] = {}

        for track_key in ("A", "B", "C"):
            rec = agent_records[track_key].get(agent_name)
            if not rec:
                continue

            bt_info = bt_lookup[track_key].get(agent_name, {})
            total_games_won = 0
            total_games_lost = 0
            # Count game-level wins/losses from builds
            builds = agent_builds[track_key].get(agent_name, [])
            total_games_won = sum(1 for b in builds if b["won"])
            total_games_lost = len(builds) - total_games_won

            tracks_data[track_key] = {
                "rank": bt_info.get("rank", 0),
                "bt_score": round(bt_info.get("bt_score", 0.0), 4),
                "ci": [round(bt_info.get("ci_lower", 0.0), 4), round(bt_info.get("ci_upper", 0.0), 4)],
                "wins": rec["series_wins"],
                "losses": rec["series_losses"],
                "draws": rec["series_draws"],
                "game_wins": total_games_won,
                "game_losses": total_games_lost,
            }

            # Animal usage
            animal_counts: dict[str, int] = defaultdict(int)
            for b in builds:
                animal_counts[b["animal"]] += 1
            animals_used[track_key] = dict(sorted(animal_counts.items(), key=lambda x: -x[1]))
            if animal_counts:
                favorite_animal[track_key] = max(animal_counts, key=animal_counts.get)  # type: ignore[arg-type]
            else:
                favorite_animal[track_key] = "N/A"

            # Average stats
            if builds:
                n = len(builds)
                avg_stats[track_key] = {
                    "hp": round(sum(b["hp"] for b in builds) / n, 2),
                    "atk": round(sum(b["atk"] for b in builds) / n, 2),
                    "spd": round(sum(b["spd"] for b in builds) / n, 2),
                    "wil": round(sum(b["wil"] for b in builds) / n, 2),
                }
            else:
                avg_stats[track_key] = {"hp": 0, "atk": 0, "spd": 0, "wil": 0}

            # Pairwise win rates (series-level)
            pw: dict[str, float | None] = {}
            for opp in sorted(all_agents):
                if opp == agent_name:
                    pw[opp] = None
                    continue
                opp_data = agent_pairwise[track_key][agent_name].get(opp, {"wins": 0, "losses": 0})
                total = opp_data["wins"] + opp_data["losses"]
                if total > 0:
                    pw[opp] = round(opp_data["wins"] / total, 4)
                else:
                    pw[opp] = None
            pairwise_rates[track_key] = pw

        # Rank shift
        rank_a = tracks_data.get("A", {}).get("rank", 0)
        rank_b = tracks_data.get("B", {}).get("rank", 0)
        if rank_a and rank_b:
            shift = rank_a - rank_b  # positive means improved in B
            rank_shift = f"+{shift}" if shift > 0 else str(shift)
        else:
            rank_shift = "N/A"

        # Total record across both tracks
        total_w = sum(t.get("wins", 0) for t in tracks_data.values())
        total_l = sum(t.get("losses", 0) for t in tracks_data.values())
        total_d = sum(t.get("draws", 0) for t in tracks_data.values())

        # Limit series history to avoid massive payloads - keep last 20 per track
        history: dict[str, list[dict[str, Any]]] = {}
        for track_key in ("A", "B", "C"):
            h = agent_series_history[track_key].get(agent_name, [])
            history[track_key] = h[-20:] if len(h) > 20 else h

        cards[agent_name] = {
            "name": agent_name,
            "type": agent_type,
            "tracks": tracks_data,
            "rank_shift": rank_shift,
            "animals_used": animals_used,
            "favorite_animal": favorite_animal,
            "avg_stats": avg_stats,
            "pairwise": pairwise_rates,
            "total_record": {"wins": total_w, "losses": total_l, "draws": total_d},
            "series_history": history,
        }

    return cards


def _compute_agent_builds() -> dict[str, dict[str, Any]]:
    """Extract the most common build per agent from JSONL tournament data.

    For T001, builds are at the series level (record["build_a"], record["build_b"]).
    For T002, builds are per game (record["games"][i]["build_a"], record["games"][i]["build_b"]).

    Returns a dict mapping agent_name -> {"animal": str, "hp": int, "atk": int, "spd": int, "wil": int}.
    """
    agent_build_counts: dict[str, Counter] = defaultdict(Counter)

    track_map = {
        "A": DATA_DIR / "tournament_001" / "results.jsonl",
        "B": DATA_DIR / "tournament_002" / "results.jsonl",
        "C": DATA_DIR / "tournament_003" / "results.jsonl",
    }

    for track_key, jsonl_path in track_map.items():
        if not jsonl_path.exists():
            continue
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                agent_a = record.get("agent_a", "unknown")
                agent_b = record.get("agent_b", "unknown")
                games = record.get("games", [])
                top_build_a = record.get("build_a")
                top_build_b = record.get("build_b")

                for game in games:
                    if track_key == "A":
                        ba = top_build_a
                        bb = top_build_b
                    else:
                        ba = game.get("build_a") or top_build_a
                        bb = game.get("build_b") or top_build_b

                    if ba:
                        key_a = (ba["animal"], ba["hp"], ba["atk"], ba["spd"], ba["wil"])
                        agent_build_counts[agent_a][key_a] += 1
                    if bb:
                        key_b = (bb["animal"], bb["hp"], bb["atk"], bb["spd"], bb["wil"])
                        agent_build_counts[agent_b][key_b] += 1

    result: dict[str, dict[str, Any]] = {}
    for agent, counter in agent_build_counts.items():
        if not counter:
            continue
        top_build = counter.most_common(1)[0][0]
        result[agent] = {
            "animal": top_build[0],
            "hp": top_build[1],
            "atk": top_build[2],
            "spd": top_build[3],
            "wil": top_build[4],
        }

    return result


# -- Strategy parsing -----------------------------------------------------------

# Maps keyword patterns to builds
_STRATEGY_RULES: list[tuple[list[str], dict[str, Any]]] = [
    (
        ["fastest", "speed", "quick"],
        {"animal": "wolf", "hp": 1, "atk": 5, "spd": 13, "wil": 1},
    ),
    (
        ["tankiest", "tank", "survive"],
        {"animal": "buffalo", "hp": 14, "atk": 3, "spd": 2, "wil": 1},
    ),
    (
        ["glass cannon", "damage", "attack", "dps"],
        {"animal": "tiger", "hp": 1, "atk": 16, "spd": 2, "wil": 1},
    ),
    (
        ["willpower", "magic", "abilities", "proc"],
        {"animal": "monkey", "hp": 1, "atk": 2, "spd": 1, "wil": 16},
    ),
    (
        ["balanced", "all-around"],
        {"animal": "bear", "hp": 5, "atk": 5, "spd": 5, "wil": 5},
    ),
]

# "hp" keyword handled specially — matches "hp" as a word but not inside other words
_HP_PATTERN = re.compile(r"\bhp\b", re.IGNORECASE)

_DEFAULT_BUILD: dict[str, Any] = {"animal": "bear", "hp": 5, "atk": 5, "spd": 5, "wil": 5}


def _parse_strategy(text: str) -> tuple[dict[str, Any], str]:
    """Parse a natural language strategy into a build dict.

    Returns (build_dict, strategy_label).
    """
    lower = text.lower().strip()

    # Check for "meta" / "optimal" / "best" / "win" first
    meta_keywords = ["meta", "optimal", "best", "win"]
    for kw in meta_keywords:
        if kw in lower:
            # Use the top T002 winning build from cached agent_builds
            agent_builds = _cache.get("agent_builds", {})
            if agent_builds:
                # Find the overall most common winning build across all agents
                # The top build from T002 data analysis is bear 8/10/1/1
                # But we derive it dynamically from the cached builds
                build_counter: Counter = Counter()
                for agent, build in agent_builds.items():
                    key = (build["animal"], build["hp"], build["atk"], build["spd"], build["wil"])
                    build_counter[key] += 1
                top = build_counter.most_common(1)[0][0]
                return {
                    "animal": top[0], "hp": top[1], "atk": top[2],
                    "spd": top[3], "wil": top[4],
                }, "meta (most popular tournament build)"
            # Fallback if no cached data
            return {"animal": "bear", "hp": 8, "atk": 10, "spd": 1, "wil": 1}, "meta"

    # Check for "hp" keyword specifically (tank variant)
    if _HP_PATTERN.search(lower):
        return {"animal": "buffalo", "hp": 14, "atk": 3, "spd": 2, "wil": 1}, "maximize HP"

    # Check other rules
    for keywords, build in _STRATEGY_RULES:
        for kw in keywords:
            if kw in lower:
                label = kw if len(kw) > 3 else keywords[0]
                return dict(build), label

    return dict(_DEFAULT_BUILD), "balanced (default)"


def _strategy_logic(strategy_text: str, games_per_opponent: int) -> dict[str, Any]:
    """Parse strategy text, run against all tournament agents, return results."""
    build, label = _parse_strategy(strategy_text)
    build_str = f"{build['animal']} {build['hp']} {build['atk']} {build['spd']} {build['wil']}"

    agent_builds = _cache.get("agent_builds", {})
    if not agent_builds:
        raise HTTPException(
            status_code=503,
            detail="Tournament data not yet loaded. Try again shortly.",
        )

    try:
        animal_p, hp_p, atk_p, spd_p, wil_p = _parse_build(build_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parsed build: {e}")

    per_opponent: list[dict[str, Any]] = []
    total_wins = 0
    total_games = 0

    for agent_name in sorted(agent_builds.keys()):
        ab = agent_builds[agent_name]
        opp_str = f"{ab['animal']} {ab['hp']} {ab['atk']} {ab['spd']} {ab['wil']}"
        try:
            animal_o, hp_o, atk_o, spd_o, wil_o = _parse_build(opp_str)
        except ValueError:
            continue

        res = _run_games(
            animal_p, hp_p, atk_p, spd_p, wil_p,
            animal_o, hp_o, atk_o, spd_o, wil_o,
            games_per_opponent, base_seed=42,
        )

        wins = res["wins_a"]
        losses = res["wins_b"]
        draws = res["draws"]
        wr = wins / games_per_opponent if games_per_opponent > 0 else 0.0
        total_wins += wins
        total_games += games_per_opponent

        per_opponent.append({
            "agent": agent_name,
            "agent_build": opp_str,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round(wr, 4),
        })

    overall_wr = total_wins / total_games if total_games > 0 else 0.0

    # Compute rank: count how many agents the user beats (win_rate > 0.5)
    agents_beaten = sum(1 for r in per_opponent if r["win_rate"] > 0.5)
    rank = len(per_opponent) + 1 - agents_beaten  # rank 1 = beat all, rank 14 = beat none

    return {
        "strategy": strategy_text,
        "strategy_label": label,
        "build": build,
        "build_string": build_str,
        "results": per_opponent,
        "overall_win_rate": round(overall_wr, 4),
        "agents_beaten": agents_beaten,
        "rank": rank,
        "total_agents": len(per_opponent),
    }


def _load_raw_records(track: str) -> list[dict[str, Any]]:
    """Load raw JSONL records for a given track."""
    paths = _resolve_track(track)
    records: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def _compute_match_log_pairs(track: str) -> dict[str, Any]:
    """Compute per-pair W-L summaries from raw JSONL records."""
    records = _load_raw_records(track)
    pair_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for rec in records:
        agent_a = rec.get("agent_a", "")
        agent_b = rec.get("agent_b", "")
        key = (min(agent_a, agent_b), max(agent_a, agent_b))
        pair_map[key].append(rec)

    pairs: list[dict[str, Any]] = []
    for (a, b), recs in sorted(pair_map.items()):
        wins_a = sum(1 for r in recs if r.get("winner") == a)
        wins_b = sum(1 for r in recs if r.get("winner") == b)
        draws = len(recs) - wins_a - wins_b
        pairs.append({
            "agent_a": a,
            "agent_b": b,
            "wins_a": wins_a,
            "wins_b": wins_b,
            "draws": draws,
            "total_series": len(recs),
        })
    return {"track": track, "pairs": pairs}


def _compute_match_log_detail(
    track: str, agent_a: str, agent_b: str,
) -> dict[str, Any]:
    """Return all series between two agents with per-game details."""
    records = _load_raw_records(track)
    series_list: list[dict[str, Any]] = []

    for rec in records:
        ra = rec.get("agent_a", "")
        rb = rec.get("agent_b", "")
        if not ({ra, rb} == {agent_a, agent_b}):
            continue
        flipped = (ra != agent_a)
        if flipped:
            sa, sb = rec.get("score_b", 0), rec.get("score_a", 0)
        else:
            sa, sb = rec.get("score_a", 0), rec.get("score_b", 0)
        winner = rec.get("winner")

        games_raw = rec.get("games", [])
        games_out: list[dict[str, Any]] = []
        has_per_game_builds = len(games_raw) > 0 and "build_a" in games_raw[0]

        for g in games_raw:
            game_entry: dict[str, Any] = {
                "game_number": g.get("game_number"),
                "winner": g.get("winner"),
                "seed": g.get("seed"),
                "ticks": g.get("ticks"),
            }
            if has_per_game_builds:
                if flipped:
                    game_entry["build_a"] = g.get("build_b")
                    game_entry["build_b"] = g.get("build_a")
                else:
                    game_entry["build_a"] = g.get("build_a")
                    game_entry["build_b"] = g.get("build_b")
                game_entry["adapted"] = g.get("adapted", False)
            else:
                if flipped:
                    game_entry["build_a"] = rec.get("build_b")
                    game_entry["build_b"] = rec.get("build_a")
                else:
                    game_entry["build_a"] = rec.get("build_a")
                    game_entry["build_b"] = rec.get("build_b")

            games_out.append(game_entry)

        series_entry: dict[str, Any] = {
            "series_id": rec.get("series_id", ""),
            "agent_a": agent_a,
            "agent_b": agent_b,
            "score_a": sa,
            "score_b": sb,
            "winner": winner,
            "games": games_out,
        }
        if not has_per_game_builds:
            if flipped:
                series_entry["build_a"] = rec.get("build_b")
                series_entry["build_b"] = rec.get("build_a")
            else:
                series_entry["build_a"] = rec.get("build_a")
                series_entry["build_b"] = rec.get("build_b")

        series_list.append(series_entry)

    wins_a = sum(1 for s in series_list if s["winner"] == agent_a)
    wins_b = sum(1 for s in series_list if s["winner"] == agent_b)
    return {
        "track": track,
        "agent_a": agent_a,
        "agent_b": agent_b,
        "total_series": len(series_list),
        "wins_a": wins_a,
        "wins_b": wins_b,
        "series": series_list,
    }


def _compute_variance_decomposition() -> dict[str, Any]:
    """Compute variance decomposition: RNG vs strategy."""
    result: dict[str, Any] = {}
    for track_key in ("A", "B", "C"):
        records = _load_raw_records(track_key)
        all_outcomes: list[float] = []
        series_variances: list[float] = []
        series_sizes: list[int] = []

        for rec in records:
            agent_a = rec.get("agent_a", "")
            games = rec.get("games", [])
            if len(games) < 2:
                continue
            outcomes: list[float] = []
            for g in games:
                w = g.get("winner")
                outcomes.append(1.0 if w == agent_a else 0.0)
            all_outcomes.extend(outcomes)
            n = len(outcomes)
            mean = sum(outcomes) / n
            var = sum((x - mean) ** 2 for x in outcomes) / n
            series_variances.append(var)
            series_sizes.append(n)

        if not all_outcomes or not series_variances:
            result[track_key] = {
                "rng_variance": 0, "total_variance": 0,
                "rng_fraction": 0, "strategy_fraction": 1,
                "n_series": 0, "n_games": 0,
            }
            continue

        total_weight = sum(series_sizes)
        within_var = sum(
            v * n for v, n in zip(series_variances, series_sizes)
        ) / total_weight

        grand_mean = sum(all_outcomes) / len(all_outcomes)
        total_var = sum(
            (x - grand_mean) ** 2 for x in all_outcomes
        ) / len(all_outcomes)

        rng_fraction = within_var / total_var if total_var > 0 else 0.0
        strategy_fraction = 1.0 - rng_fraction

        result[track_key] = {
            "rng_variance": round(within_var, 6),
            "total_variance": round(total_var, 6),
            "rng_fraction": round(rng_fraction, 4),
            "strategy_fraction": round(strategy_fraction, 4),
            "n_series": len(series_variances),
            "n_games": len(all_outcomes),
        }

    return result


def _compute_random_baseline() -> dict[str, Any]:
    """Compute RandomAgent statistics from actual tournament data."""
    result: dict[str, Any] = {}
    for track_key in ("A", "B", "C"):
        records = _load_raw_records(track_key)
        random_series = 0
        random_wins = 0
        random_losses = 0
        opponents: dict[str, dict[str, int]] = {}

        for rec in records:
            agent_a = rec.get("agent_a", "")
            agent_b = rec.get("agent_b", "")
            winner = rec.get("winner")

            if agent_a == "RandomAgent":
                opponent = agent_b
            elif agent_b == "RandomAgent":
                opponent = agent_a
            else:
                continue

            random_series += 1
            if winner == "RandomAgent":
                random_wins += 1
            else:
                random_losses += 1
            if opponent not in opponents:
                opponents[opponent] = {"wins": 0, "losses": 0}
            if winner == "RandomAgent":
                opponents[opponent]["wins"] += 1
            else:
                opponents[opponent]["losses"] += 1

        result[track_key] = {
            "total_series": random_series,
            "wins": random_wins,
            "losses": random_losses,
            "win_rate": round(random_wins / random_series, 4) if random_series > 0 else 0.0,
            "opponents": dict(sorted(opponents.items())),
        }

    return result


def _precompute_cache() -> None:
    """Precompute BT scores, pairwise matrices, 3-cycles, match logs, and methodology data."""
    for track_key in ("A", "B", "C", "all"):
        results = _load_track_results(track_key)
        if not results:
            _cache[track_key] = {
                "bt": {"track": track_key, "bt_scores": [], "total_matches": 0},
                "pairwise": {"track": track_key, "agents": [], "win_rates": {}, "game_counts": {}},
                "cycles": {"track": track_key, "cycles": [], "total_cycles": 0},
            }
            continue

        # BT scores + Elo
        bt_scores = compute_bt_scores(results, n_bootstrap=1000, bootstrap_seed=42)
        elo_ratings = _compute_elo_ratings(results)
        bt_list = [
            {
                "name": r.name,
                "bt_score": r.score,
                "ci_lower": r.ci_lower,
                "ci_upper": r.ci_upper,
                "sample_size": r.sample_size,
                "elo": round(elo_ratings.get(r.name, 1500.0)),
            }
            for r in bt_scores
        ]

        # Pairwise
        pairwise = _compute_pairwise_from_results(results)

        # 3-cycles
        cycles = _detect_3_cycles(pairwise["agents"], pairwise["win_rates"])

        _cache[track_key] = {
            "bt": {
                "track": track_key,
                "bt_scores": bt_list,
                "total_matches": len(results),
            },
            "pairwise": {"track": track_key, **pairwise},
            "cycles": {
                "track": track_key,
                "cycles": cycles,
                "total_cycles": len(cycles),
            },
        }

    # Agent builds (most common build per agent from JSONL data)
    _cache["agent_builds"] = _compute_agent_builds()

    # Agent cards
    _cache["agents"] = _compute_agent_cards()

    # Match log pair summaries
    for track_key in ("A", "B", "C"):
        _cache[f"match_log_pairs_{track_key}"] = _compute_match_log_pairs(track_key)

    # Methodology data
    _cache["variance_decomposition"] = _compute_variance_decomposition()
    _cache["random_baseline"] = _compute_random_baseline()

    logger.info("Cache precomputed for tracks: %s", list(_cache.keys()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Precompute leaderboard data at startup."""
    _precompute_cache()
    yield


app = FastAPI(title="Moreau Arena", version="2.0.0", lifespan=lifespan)

# CORS middleware — allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FightRequest(BaseModel):
    build1: str = Field(..., description='Build string, e.g. "bear 3 14 2 1"')
    build2: str = Field(..., description='Build string, e.g. "buffalo 8 6 4 2"')
    games: int = Field(default=100, ge=1, le=10000)

    @field_validator("build1", "build2")
    @classmethod
    def validate_build_string(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Build string cannot be empty")
        return v


class FightResponse(BaseModel):
    build1_wins: int
    build2_wins: int
    draws: int
    avg_ticks: float


class ChallengeRequest(BaseModel):
    build: str = Field(..., description='Build string, e.g. "bear 3 14 2 1"')
    games: int = Field(default=100, ge=1, le=10000)

    @field_validator("build")
    @classmethod
    def validate_build_string(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Build string cannot be empty")
        return v


class ChallengeResult(BaseModel):
    opponent: str
    wins: int
    losses: int
    draws: int
    win_rate: float


class ChallengeResponse(BaseModel):
    build: str
    results: list[ChallengeResult]
    overall_win_rate: float


class PlayRequest(BaseModel):
    animal: str = Field(..., description="Animal type, e.g. 'bear'")
    hp: int = Field(..., ge=1, le=17)
    atk: int = Field(..., ge=1, le=17)
    spd: int = Field(..., ge=1, le=17)
    wil: int = Field(..., ge=1, le=17)

    @field_validator("animal")
    @classmethod
    def validate_animal(cls, v: str) -> str:
        v = v.strip().lower()
        all_animals = set(VALID_ANIMALS) | set(S1_ANIMALS)
        if v not in all_animals:
            raise ValueError(
                f"Invalid animal '{v}'. Valid: {', '.join(sorted(all_animals))}"
            )
        return v


class PlayGameResult(BaseModel):
    game: int
    winner: str
    ticks: int


class PlayResponse(BaseModel):
    player_wins: int
    opponent_wins: int
    games: list[PlayGameResult]


class LeaderboardEntry(BaseModel):
    agent: str
    series_wins: int
    series_losses: int
    series_draws: int
    win_rate: float


class StrategyRequest(BaseModel):
    strategy: str = Field(..., description='Natural language strategy, e.g. "fastest" or "glass cannon"')
    games: int = Field(default=100, ge=1, le=1000)

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Strategy text cannot be empty")
        if len(v) > 500:
            raise ValueError("Strategy text too long (max 500 characters)")
        return v


class StrategyOpponentResult(BaseModel):
    agent: str
    agent_build: str
    wins: int
    losses: int
    draws: int
    win_rate: float


class StrategyResponse(BaseModel):
    strategy: str
    strategy_label: str
    build: dict[str, Any]
    build_string: str
    results: list[StrategyOpponentResult]
    overall_win_rate: float
    agents_beaten: int
    rank: int
    total_agents: int


# -- Shared logic ----------------------------------------------------------------


def _fight_logic(build1: str, build2: str, games: int) -> FightResponse:
    try:
        animal_a, hp_a, atk_a, spd_a, wil_a = _parse_build(build1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build1: {e}")

    try:
        animal_b, hp_b, atk_b, spd_b, wil_b = _parse_build(build2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build2: {e}")

    try:
        result = _run_games(
            animal_a, hp_a, atk_a, spd_a, wil_a,
            animal_b, hp_b, atk_b, spd_b, wil_b,
            games, base_seed=42,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")

    return FightResponse(
        build1_wins=result["wins_a"],
        build2_wins=result["wins_b"],
        draws=result["draws"],
        avg_ticks=round(result["avg_ticks"], 2),
    )


def _load_leaderboard() -> list[dict[str, Any]]:
    """Read all JSONL files in results/ and aggregate series wins per agent."""
    if not RESULTS_DIR.exists():
        return []

    agent_stats: dict[str, dict[str, int]] = {}

    for jsonl_path in RESULTS_DIR.glob("*.jsonl"):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                agent_a = record.get("agent_a", "unknown")
                agent_b = record.get("agent_b", "unknown")
                winner = record.get("winner")

                for agent in (agent_a, agent_b):
                    if agent not in agent_stats:
                        agent_stats[agent] = {
                            "series_wins": 0,
                            "series_losses": 0,
                            "series_draws": 0,
                        }

                if winner == agent_a:
                    agent_stats[agent_a]["series_wins"] += 1
                    agent_stats[agent_b]["series_losses"] += 1
                elif winner == agent_b:
                    agent_stats[agent_b]["series_wins"] += 1
                    agent_stats[agent_a]["series_losses"] += 1
                else:
                    agent_stats[agent_a]["series_draws"] += 1
                    agent_stats[agent_b]["series_draws"] += 1

    entries = []
    for agent, stats in sorted(agent_stats.items()):
        total = stats["series_wins"] + stats["series_losses"] + stats["series_draws"]
        win_rate = stats["series_wins"] / total if total > 0 else 0.0
        entries.append({
            "agent": agent,
            "series_wins": stats["series_wins"],
            "series_losses": stats["series_losses"],
            "series_draws": stats["series_draws"],
            "win_rate": round(win_rate, 4),
        })

    entries.sort(key=lambda e: e["win_rate"], reverse=True)
    return entries


def _resolve_track(track: str) -> list[Path]:
    """Resolve track parameter to list of JSONL file paths."""
    key = track.upper() if track.upper() in ("A", "B", "C") else "all"
    return TRACK_PATHS.get(key, TRACK_PATHS["all"])


def _load_track_results(track: str) -> list[tuple[str, str]]:
    """Load (winner, loser) pairs for a given track."""
    paths = _resolve_track(track)
    all_results: list[tuple[str, str]] = []
    for path in paths:
        if path.exists():
            all_results.extend(load_results_from_jsonl(path))
    return all_results


def _compute_elo_ratings(results: list[tuple[str, str]]) -> dict[str, float]:
    """Compute Elo ratings from (winner, loser) pairs."""
    elo_ratings: dict[str, float] = defaultdict(lambda: 1500.0)
    for winner, loser in results:
        w_elo = elo_ratings[winner]
        l_elo = elo_ratings[loser]
        new_w, new_l = update_ratings(w_elo, l_elo)
        elo_ratings[winner] = new_w
        elo_ratings[loser] = new_l
    return dict(elo_ratings)


def _compute_pairwise_from_results(
    results: list[tuple[str, str]],
) -> dict[str, Any]:
    """Compute pairwise win-rate matrix from (winner, loser) pairs."""
    wins: dict[tuple[str, str], int] = defaultdict(int)
    totals: dict[tuple[str, str], int] = defaultdict(int)
    all_agents: set[str] = set()

    for winner, loser in results:
        all_agents.add(winner)
        all_agents.add(loser)
        wins[(winner, loser)] += 1
        totals[(winner, loser)] += 1
        totals[(loser, winner)] += 1

    agents = sorted(all_agents)
    matrix: dict[str, dict[str, float | None]] = {}
    counts: dict[str, dict[str, int]] = {}

    for a in agents:
        matrix[a] = {}
        counts[a] = {}
        for b in agents:
            if a == b:
                matrix[a][b] = None
                counts[a][b] = 0
            else:
                total = totals.get((a, b), 0)
                w = wins.get((a, b), 0)
                matrix[a][b] = round(w / total, 4) if total > 0 else 0.0
                counts[a][b] = total

    return {
        "agents": agents,
        "win_rates": matrix,
        "game_counts": counts,
    }


def _detect_3_cycles(
    agents: list[str],
    win_rates: dict[str, dict[str, float | None]],
) -> list[dict[str, Any]]:
    """Detect 3-cycles: sets of (A, B, C) where A>B>50%, B>C>50%, C>A>50%."""
    cycles: list[dict[str, Any]] = []
    for a, b, c in combinations(agents, 3):
        # Check all 6 possible orderings of (a, b, c)
        for x, y, z in [
            (a, b, c), (a, c, b), (b, a, c),
            (b, c, a), (c, a, b), (c, b, a),
        ]:
            wr_xy = win_rates.get(x, {}).get(y)
            wr_yz = win_rates.get(y, {}).get(z)
            wr_zx = win_rates.get(z, {}).get(x)
            if (
                wr_xy is not None and wr_yz is not None and wr_zx is not None
                and wr_xy > 0.5 and wr_yz > 0.5 and wr_zx > 0.5
            ):
                cycles.append({
                    "cycle": [x, y, z],
                    "win_rates": [
                        round(wr_xy, 4),
                        round(wr_yz, 4),
                        round(wr_zx, 4),
                    ],
                    "description": (
                        f"{x} beats {y} ({wr_xy:.1%}), "
                        f"{y} beats {z} ({wr_yz:.1%}), "
                        f"{z} beats {x} ({wr_zx:.1%})"
                    ),
                })
                break  # Only report one orientation per (a, b, c) triple

    return cycles


def _challenge_logic(build: str, games: int) -> ChallengeResponse:
    try:
        animal_c, hp_c, atk_c, spd_c, wil_c = _parse_build(build)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build: {e}")

    results = []
    total_wins = 0
    total_games = 0

    for ref_build in REFERENCE_BUILDS:
        animal_r, hp_r, atk_r, spd_r, wil_r = _parse_build(ref_build)
        res = _run_games(
            animal_c, hp_c, atk_c, spd_c, wil_c,
            animal_r, hp_r, atk_r, spd_r, wil_r,
            games, base_seed=42,
        )
        wins = res["wins_a"]
        losses = res["wins_b"]
        draws = res["draws"]
        wr = wins / games if games > 0 else 0.0
        total_wins += wins
        total_games += games
        results.append(ChallengeResult(
            opponent=ref_build,
            wins=wins,
            losses=losses,
            draws=draws,
            win_rate=round(wr, 4),
        ))

    overall = total_wins / total_games if total_games > 0 else 0.0
    return ChallengeResponse(
        build=build,
        results=results,
        overall_win_rate=round(overall, 4),
    )


# -- Page routes ----------------------------------------------------------------


@app.get("/")
def index() -> HTMLResponse:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    # Server-side render top-5 leaderboard rankings to avoid "Loading..." flash
    for track_key in ("A", "B", "C"):
        bt_data = _cache.get(track_key, {}).get("bt", {})
        scores = bt_data.get("bt_scores", [])[:6]
        if scores:
            items = []
            for i, s in enumerate(scores):
                name = s["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                items.append(
                    f'<li><span class="rank-num">{i+1}.</span>'
                    f'<span class="agent-name">{name}</span>'
                    f'<span class="bt-score">{s["bt_score"]:.3f}</span></li>'
                )
            rendered = "\n                        ".join(items)
        else:
            rendered = '<li class="muted small">No data</li>'
        placeholder = f'<ul class="mini-ranking" id="track{track_key}-ranking">\n                        <li class="loading">Loading...</li>\n                    </ul>'
        replacement = f'<ul class="mini-ranking" id="track{track_key}-ranking">\n                        {rendered}\n                    </ul>'
        html = html.replace(placeholder, replacement)
    return HTMLResponse(html)


@app.get("/about")
def about_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "about.html")


@app.get("/tournaments")
def tournaments_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "tournaments.html")


@app.get("/leaderboard")
def leaderboard_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "leaderboard.html")


@app.get("/paper")
def paper_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "paper.html")


@app.get("/api-docs")
def api_docs_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "api.html")


@app.get("/play")
def play_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "play.html")


@app.get("/research")
def research_page() -> FileResponse:
    """Legacy route — redirect to paper page."""
    return FileResponse(STATIC_DIR / "paper.html")


@app.get("/match-log")
def match_log_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "match-log.html")


@app.get("/methodology")
def methodology_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "methodology.html")


@app.get("/compare")
def compare_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "compare.html")


@app.get("/s1-leaderboard")
def s1_leaderboard_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "s1-leaderboard.html")


@app.get("/s1-fighters")
def s1_fighters_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "s1-fighters.html")


@app.get("/s1-matchups")
def s1_matchups_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "s1-matchups.html")


@app.get("/s1-compare")
def s1_compare_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "s1-compare.html")


@app.get("/fighters/{animal}")
def fighter_page(animal: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "fighters" / f"{animal}.html")


@app.get("/moreddit")
def moreddit_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "moreddit.html")


# -- Island routes -------------------------------------------------------------

@app.get("/island")
def island_landing_page() -> FileResponse:
    """Serve the Island landing page."""
    return FileResponse(STATIC_DIR / "island" / "index.html")


@app.get("/api/v1/island/config")
def island_config():
    """Return Supabase configuration for the frontend."""
    return {
        "supabase_url": os.environ.get("SUPABASE_URL", ""),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
    }


@app.get("/island/{page}")
def island_page(page: str) -> FileResponse:
    allowed = {"index", "home", "create", "kennel", "train", "lab", "pit", "graveyard", "profile", "leaderboard", "achievements", "onboarding", "dreams", "crimson", "rivals", "prophecy", "shrine", "artifacts", "menagerie", "succession", "deep-tide", "black-market"}
    if page not in allowed:
        raise HTTPException(404, f"Unknown island page: {page}")
    return FileResponse(STATIC_DIR / "island" / f"{page}.html")


# -- Pets routes ---------------------------------------------------------------

@app.get("/pets")
def pets_landing_page() -> FileResponse:
    """Serve the hub page; JS handles redirect to creation if no pets exist."""
    return FileResponse(STATIC_DIR / "pets" / "hub.html")


@app.get("/pets/{page}")
def pets_page(page: str) -> FileResponse:
    allowed = {"index", "create", "hub", "home", "train", "mutate", "profile", "pvp", "forbidden-lab"}
    if page not in allowed:
        raise HTTPException(404, f"Unknown pets page: {page}")
    # "create" is served from index.html (the creation wizard)
    filename = "index.html" if page == "create" else f"{page}.html"
    return FileResponse(STATIC_DIR / "pets" / filename)


@app.post("/api/v1/pets/soul")
def pets_soul(req: dict) -> dict:
    """Generate an AI soul response for a pet."""
    pet = req.get("pet", {})
    context = req.get("context", "idle")
    kwargs = {k: v for k, v in req.items() if k not in ("pet", "context")}
    mood = pet_calculate_mood(pet)
    pet["mood"] = mood
    response = generate_soul_response(pet, context=context, **kwargs)
    return {"response": response, "mood": mood}


@app.post("/fight", response_model=FightResponse)
def fight(req: FightRequest) -> FightResponse:
    return _fight_logic(req.build1, req.build2, req.games)


def _parse_s1_build(build_str: str) -> tuple[str, int, int, int, int]:
    """Parse a build string like 'bear 5 5 5 5' into (animal, hp, atk, spd, wil)."""
    parts = build_str.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 'animal hp atk spd wil', got: {build_str!r}")
    animal = parts[0].lower()
    if animal not in S1_ANIMALS:
        raise ValueError(f"Invalid S1 animal '{animal}'. Valid: {', '.join(S1_ANIMALS)}")
    hp, atk, spd, wil = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
    total = hp + atk + spd + wil
    if total < 4 or total > 24:
        raise ValueError(f"Stats must sum to 4-24, got {total}")
    if any(s < 1 for s in (hp, atk, spd, wil)):
        raise ValueError("Each stat must be >= 1")
    return animal, hp, atk, spd, wil


def _fight_s1_logic(build1: str, build2: str, games: int) -> FightResponse:
    """Run a Season 1 fight series using the S1 engine."""
    try:
        animal_a, hp_a, atk_a, spd_a, wil_a = _parse_s1_build(build1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build1: {e}")

    try:
        animal_b, hp_b, atk_b, spd_b, wil_b = _parse_s1_build(build2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build2: {e}")

    wins_a = 0
    wins_b = 0
    draws = 0
    total_ticks = 0

    for i in range(games):
        seed = 42 + i
        result = s1_run_match(
            animal_a, (hp_a, atk_a, spd_a, wil_a),
            animal_b, (hp_b, atk_b, spd_b, wil_b),
            seed,
        )
        total_ticks += result["ticks"]
        if result["winner"] == "a":
            wins_a += 1
        elif result["winner"] == "b":
            wins_b += 1
        else:
            draws += 1

    return FightResponse(
        build1_wins=wins_a,
        build2_wins=wins_b,
        draws=draws,
        avg_ticks=round(total_ticks / games, 2) if games else 0,
    )


@app.post("/fight/s1", response_model=FightResponse)
def fight_s1(req: FightRequest) -> FightResponse:
    return _fight_s1_logic(req.build1, req.build2, req.games)


# -- API v1 router ---------------------------------------------------------------

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.post("/fight", response_model=FightResponse)
def api_fight(req: FightRequest) -> FightResponse:
    return _fight_logic(req.build1, req.build2, req.games)


@api_v1.post("/fight/s1", response_model=FightResponse)
def api_fight_s1(req: FightRequest) -> FightResponse:
    return _fight_s1_logic(req.build1, req.build2, req.games)


@api_v1.get("/leaderboard")
def api_leaderboard() -> list[dict[str, Any]]:
    return _load_leaderboard()


@api_v1.post("/challenge", response_model=ChallengeResponse)
def api_challenge(req: ChallengeRequest) -> ChallengeResponse:
    return _challenge_logic(req.build, req.games)


@api_v1.get("/leaderboard/bt")
def api_leaderboard_bt(
    track: str = Query(default="all", pattern="^(A|B|C|all)$"),
) -> dict[str, Any]:
    """Return cached BT scores + Elo ratings for the given track."""
    key = track.upper() if track.upper() in ("A", "B", "C") else "all"
    if key in _cache:
        return _cache[key]["bt"]

    # Fallback: compute on the fly if cache miss
    results = _load_track_results(track)
    if not results:
        return {"track": track, "bt_scores": [], "total_matches": 0}

    bt_scores = compute_bt_scores(results, n_bootstrap=1000, bootstrap_seed=42)
    elo_ratings = _compute_elo_ratings(results)

    bt_list = [
        {
            "name": r.name,
            "bt_score": r.score,
            "ci_lower": r.ci_lower,
            "ci_upper": r.ci_upper,
            "sample_size": r.sample_size,
            "elo": round(elo_ratings.get(r.name, 1500.0)),
        }
        for r in bt_scores
    ]

    return {
        "track": track,
        "bt_scores": bt_list,
        "total_matches": len(results),
    }


@api_v1.get("/leaderboard/pairwise")
def api_leaderboard_pairwise(
    track: str = Query(default="all", pattern="^(A|B|C|all)$"),
) -> dict[str, Any]:
    """Return cached pairwise win-rate matrix for the given track."""
    key = track.upper() if track.upper() in ("A", "B", "C") else "all"
    if key in _cache:
        return _cache[key]["pairwise"]

    results = _load_track_results(track)
    if not results:
        return {"track": track, "agents": [], "win_rates": {}, "game_counts": {}}

    pairwise = _compute_pairwise_from_results(results)
    return {"track": track, **pairwise}


@api_v1.get("/leaderboard/cycles")
def api_leaderboard_cycles(
    track: str = Query(default="all", pattern="^(A|B|C|all)$"),
) -> dict[str, Any]:
    """Return cached 3-cycles for the given track."""
    key = track.upper() if track.upper() in ("A", "B", "C") else "all"
    if key in _cache:
        return _cache[key]["cycles"]

    results = _load_track_results(track)
    if not results:
        return {"track": track, "cycles": []}

    pairwise = _compute_pairwise_from_results(results)
    cycles = _detect_3_cycles(pairwise["agents"], pairwise["win_rates"])
    return {
        "track": track,
        "cycles": cycles,
        "total_cycles": len(cycles),
    }


@api_v1.get("/s1/leaderboard")
def api_s1_leaderboard() -> dict[str, Any]:
    """Return Season 1 balance results (animal win rates, gates, pairwise)."""
    balance_file = SEASON1_DIR / "balance_results.json"
    if not balance_file.exists():
        raise HTTPException(status_code=404, detail="Season 1 balance data not found")
    data = json.loads(balance_file.read_text(encoding="utf-8"))

    # Include pairwise matrix from CSV
    pairwise_file = SEASON1_DIR / "pairwise_matrix.csv"
    if pairwise_file.exists():
        import csv as _csv
        import io as _io

        text = pairwise_file.read_text(encoding="utf-8")
        reader = _csv.reader(_io.StringIO(text))
        headers = next(reader)[1:]  # skip first empty column
        pairwise: dict[str, dict[str, float | None]] = {}
        for row in reader:
            name = row[0]
            pairwise[name] = {}
            for j, val in enumerate(row[1:]):
                pairwise[name][headers[j]] = float(val) if val else None
        data["pairwise"] = pairwise

    return data


@api_v1.get("/s1/tournament")
def api_s1_tournament() -> dict[str, Any]:
    """Return Season 1 tournament results (BT rankings + series stats)."""
    bt_file = DATA_DIR / "season1_tournament" / "bt_rankings.json"
    if not bt_file.exists():
        raise HTTPException(status_code=404, detail="Season 1 tournament data not found")
    rankings = json.loads(bt_file.read_text(encoding="utf-8"))

    # Compute head-to-head from results.jsonl
    results_file = DATA_DIR / "season1_tournament" / "results.jsonl"
    h2h: dict[str, dict[str, dict[str, int]]] = {}
    if results_file.exists():
        for line in results_file.read_text(encoding="utf-8").strip().split("\n"):
            rec = json.loads(line)
            a1, a2 = rec["agent_a"], rec["agent_b"]
            w = rec.get("winner", "")
            for x, y in [(a1, a2), (a2, a1)]:
                h2h.setdefault(x, {}).setdefault(y, {"w": 0, "l": 0})
            if w == a1:
                h2h[a1][a2]["w"] += 1
                h2h[a2][a1]["l"] += 1
            elif w == a2:
                h2h[a2][a1]["w"] += 1
                h2h[a1][a2]["l"] += 1

    return {
        "rankings": rankings,
        "head_to_head": h2h,
        "meta": {
            "format": "Best-of-7, adaptive",
            "agents": len(rankings),
            "series": 91,
            "date": "2026-03-08",
        },
    }


@api_v1.post("/play", response_model=PlayResponse)
def api_play(req: PlayRequest) -> PlayResponse:
    """Run a best-of-7 series: player build vs balanced bear (5/5/5/5)."""
    total = req.hp + req.atk + req.spd + req.wil
    if total != 20:
        raise HTTPException(
            status_code=400,
            detail=f"Stats must sum to 20, got {total} ({req.hp}+{req.atk}+{req.spd}+{req.wil})",
        )

    try:
        animal_p, hp_p, atk_p, spd_p, wil_p = _parse_build(
            f"{req.animal} {req.hp} {req.atk} {req.spd} {req.wil}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Opponent: balanced bear 5/5/5/5
    animal_o, hp_o, atk_o, spd_o, wil_o = _parse_build("bear 5 5 5 5")

    engine = CombatEngine()
    player_wins = 0
    opponent_wins = 0
    game_results: list[PlayGameResult] = []
    base_seed = random.randint(0, 100000)

    for g in range(7):
        if player_wins >= 4 or opponent_wins >= 4:
            break

        match_seed = base_seed + g
        creature_p = _create_creature(
            animal_p, hp_p, atk_p, spd_p, wil_p, "a", match_seed
        )
        creature_o = _create_creature(
            animal_o, hp_o, atk_o, spd_o, wil_o, "b", match_seed
        )

        result = engine.run_combat(creature_p, creature_o, match_seed)

        if result.winner == "a":
            player_wins += 1
            winner_label = "player"
        elif result.winner == "b":
            opponent_wins += 1
            winner_label = "opponent"
        else:
            winner_label = "draw"

        game_results.append(PlayGameResult(
            game=g + 1,
            winner=winner_label,
            ticks=result.ticks,
        ))

    return PlayResponse(
        player_wins=player_wins,
        opponent_wins=opponent_wins,
        games=game_results,
    )


@api_v1.post("/play/s1", response_model=PlayResponse)
def api_play_s1(req: PlayRequest) -> PlayResponse:
    """Run a best-of-7 series using the Season 1 engine: player build vs balanced bear (5/5/5/5)."""
    total = req.hp + req.atk + req.spd + req.wil
    if total != 20:
        raise HTTPException(
            status_code=400,
            detail=f"Stats must sum to 20, got {total} ({req.hp}+{req.atk}+{req.spd}+{req.wil})",
        )

    animal = req.animal.strip().lower()
    if animal not in S1_ANIMALS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid S1 animal '{animal}'. Valid: {', '.join(S1_ANIMALS)}",
        )

    player_wins = 0
    opponent_wins = 0
    game_results: list[PlayGameResult] = []
    base_seed = random.randint(0, 100000)

    for g in range(7):
        if player_wins >= 4 or opponent_wins >= 4:
            break

        match_seed = base_seed + g
        result = s1_run_match(
            animal, (req.hp, req.atk, req.spd, req.wil),
            "bear", (5, 5, 5, 5),
            match_seed,
        )

        if result["winner"] == "a":
            player_wins += 1
            winner_label = "player"
        elif result["winner"] == "b":
            opponent_wins += 1
            winner_label = "opponent"
        else:
            winner_label = "draw"

        game_results.append(PlayGameResult(
            game=g + 1,
            winner=winner_label,
            ticks=result["ticks"],
        ))

    return PlayResponse(
        player_wins=player_wins,
        opponent_wins=opponent_wins,
        games=game_results,
    )


@api_v1.post("/strategy", response_model=StrategyResponse)
def api_strategy(req: StrategyRequest) -> StrategyResponse:
    """Parse natural language strategy, run against tournament agents, return rank estimate."""
    result = _strategy_logic(req.strategy, req.games)
    return StrategyResponse(**result)


@api_v1.post("/submit")
async def api_submit(file: UploadFile) -> dict[str, Any]:
    """Accept a JSONL file upload, validate, and store it."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")

    lines = text.strip().split("\n")
    if not lines or (len(lines) == 1 and not lines[0].strip()):
        raise HTTPException(status_code=400, detail="File is empty")

    errors: list[str] = []
    record_count = 0

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # Validate JSON
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Line {i}: Invalid JSON: {e}")
            continue

        record_count += 1

        # Validate required fields
        for field in ("agent_a", "agent_b", "winner", "games"):
            if field not in record:
                errors.append(f"Line {i}: Missing required field '{field}'")

        # Validate games array contains valid builds
        games_data = record.get("games", [])
        if not isinstance(games_data, list):
            errors.append(f"Line {i}: 'games' must be an array")
            continue

        for gi, game in enumerate(games_data, 1):
            if not isinstance(game, dict):
                errors.append(f"Line {i}, game {gi}: must be an object")
                continue
            for build_key in ("build_a", "build_b"):
                build = game.get(build_key)
                if build is None:
                    continue  # build keys are optional per game
                if not isinstance(build, dict):
                    errors.append(f"Line {i}, game {gi}: '{build_key}' must be an object")
                    continue
                animal = build.get("animal", "").lower()
                if animal and animal not in VALID_ANIMALS:
                    errors.append(
                        f"Line {i}, game {gi}: '{build_key}' has invalid animal '{animal}'"
                    )
                stats = [
                    build.get("hp", 0), build.get("atk", 0),
                    build.get("spd", 0), build.get("wil", 0),
                ]
                if all(isinstance(s, (int, float)) for s in stats):
                    total = sum(int(s) for s in stats)
                    if total != 0 and total != 20:
                        errors.append(
                            f"Line {i}, game {gi}: '{build_key}' stats sum to {total}, expected 20"
                        )

    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    if record_count == 0:
        raise HTTPException(status_code=400, detail="No valid records found in file")

    # Store the file
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(
        c if c.isalnum() or c in "-_." else "_"
        for c in (file.filename or "upload")
    )
    dest_name = f"submission_{timestamp}_{safe_name}"
    dest_path = SUBMISSIONS_DIR / dest_name

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "filename": dest_name,
        "records": record_count,
        "status": "accepted",
    }


@api_v1.get("/agents")
def api_agents_list() -> list[dict[str, Any]]:
    """Return summary list of all agents."""
    agents_data = _cache.get("agents", {})
    summary = []
    for name, card in sorted(agents_data.items()):
        summary.append({
            "name": card["name"],
            "type": card["type"],
            "rank_shift": card["rank_shift"],
            "total_record": card["total_record"],
            "tracks": {
                tk: {"rank": tv["rank"], "bt_score": tv["bt_score"]}
                for tk, tv in card["tracks"].items()
            },
        })
    return summary


@api_v1.get("/agent/{name}")
def api_agent_card(name: str) -> dict[str, Any]:
    """Return full agent card data."""
    agents_data = _cache.get("agents", {})
    if name not in agents_data:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return agents_data[name]


@api_v1.get("/match-log/pairs")
def api_match_log_pairs(
    track: str = Query(default="A", pattern="^(A|B)$"),
) -> dict[str, Any]:
    """Return all agent pairs with W-L summary for a track."""
    cache_key = f"match_log_pairs_{track.upper()}"
    if cache_key in _cache:
        return _cache[cache_key]
    return _compute_match_log_pairs(track.upper())


@api_v1.get("/match-log")
def api_match_log(
    track: str = Query(default="A", pattern="^(A|B)$"),
    agent_a: str = Query(...),
    agent_b: str = Query(...),
) -> dict[str, Any]:
    """Return all series between two agents with per-game details."""
    return _compute_match_log_detail(track.upper(), agent_a, agent_b)


@api_v1.get("/methodology/variance")
def api_methodology_variance() -> dict[str, Any]:
    """Return variance decomposition stats computed from data."""
    if "variance_decomposition" in _cache:
        return _cache["variance_decomposition"]
    return _compute_variance_decomposition()


@api_v1.get("/methodology/random-baseline")
def api_methodology_random_baseline() -> dict[str, Any]:
    """Return random agent stats."""
    if "random_baseline" in _cache:
        return _cache["random_baseline"]
    return _compute_random_baseline()


app.include_router(api_v1)


# Agent card page route — must come AFTER api_v1 router is included
@app.get("/agent/{name}")
def agent_page(name: str) -> FileResponse:
    """Serve the agent card template page."""
    agents_data = _cache.get("agents", {})
    if name not in agents_data:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return FileResponse(STATIC_DIR / "agent.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
