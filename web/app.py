"""Moreau Arena — FastAPI Web UI.

Provides a simple web interface for running fights between creature builds
and viewing leaderboard data from tournament results.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
from simulator.__main__ import _parse_build, _run_games

app = FastAPI(title="Moreau Arena", version="1.0.0")

# CORS middleware — allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
RESULTS_DIR = _project_root / "results"
DATA_DIR = _project_root / "data"

# Tournament track mapping
TRACK_PATHS: dict[str, list[Path]] = {
    "A": [DATA_DIR / "tournament_001" / "results.jsonl"],
    "B": [DATA_DIR / "tournament_002" / "results.jsonl"],
    "all": [
        DATA_DIR / "tournament_001" / "results.jsonl",
        DATA_DIR / "tournament_002" / "results.jsonl",
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


class LeaderboardEntry(BaseModel):
    agent: str
    series_wins: int
    series_losses: int
    series_draws: int
    win_rate: float


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
    key = track.upper() if track.upper() in ("A", "B") else "all"
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


# -- Original routes (kept working) ---------------------------------------------


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/fight", response_model=FightResponse)
def fight(req: FightRequest) -> FightResponse:
    return _fight_logic(req.build1, req.build2, req.games)


@app.get("/leaderboard")
def leaderboard_page() -> FileResponse:
    """Serve the leaderboard HTML page."""
    return FileResponse(STATIC_DIR / "leaderboard.html")


# -- API v1 router ---------------------------------------------------------------

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.post("/fight", response_model=FightResponse)
def api_fight(req: FightRequest) -> FightResponse:
    return _fight_logic(req.build1, req.build2, req.games)


@api_v1.get("/leaderboard")
def api_leaderboard() -> list[dict[str, Any]]:
    return _load_leaderboard()


@api_v1.post("/challenge", response_model=ChallengeResponse)
def api_challenge(req: ChallengeRequest) -> ChallengeResponse:
    return _challenge_logic(req.build, req.games)


@api_v1.get("/leaderboard/bt")
def api_leaderboard_bt(
    track: str = Query(default="all", pattern="^(A|B|all)$"),
) -> dict[str, Any]:
    """Return BT scores + Elo ratings for the given track."""
    results = _load_track_results(track)
    if not results:
        return {"track": track, "bt_scores": [], "elo_ratings": []}

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
    track: str = Query(default="all", pattern="^(A|B|all)$"),
) -> dict[str, Any]:
    """Return pairwise win-rate matrix for the given track."""
    results = _load_track_results(track)
    if not results:
        return {"track": track, "agents": [], "win_rates": {}, "game_counts": {}}

    pairwise = _compute_pairwise_from_results(results)
    return {
        "track": track,
        **pairwise,
    }


@api_v1.get("/leaderboard/cycles")
def api_leaderboard_cycles(
    track: str = Query(default="all", pattern="^(A|B|all)$"),
) -> dict[str, Any]:
    """Return detected 3-cycles for the given track."""
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


app.include_router(api_v1)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
