"""Moreau Arena — FastAPI Web UI.

Provides a simple web interface for running fights between creature builds
and viewing leaderboard data from tournament results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# Add parent directory to sys.path so we can import the simulator package
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from simulator.__main__ import _parse_build, _run_games

app = FastAPI(title="Moreau Arena", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
RESULTS_DIR = _project_root / "results"


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


class LeaderboardEntry(BaseModel):
    agent: str
    series_wins: int
    series_losses: int
    series_draws: int
    win_rate: float


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/fight", response_model=FightResponse)
def fight(req: FightRequest) -> FightResponse:
    try:
        animal_a, hp_a, atk_a, spd_a, wil_a = _parse_build(req.build1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build1: {e}")

    try:
        animal_b, hp_b, atk_b, spd_b, wil_b = _parse_build(req.build2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid build2: {e}")

    try:
        result = _run_games(
            animal_a, hp_a, atk_a, spd_a, wil_a,
            animal_b, hp_b, atk_b, spd_b, wil_b,
            req.games, base_seed=42,
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


@app.get("/leaderboard")
def leaderboard() -> list[dict[str, Any]]:
    return _load_leaderboard()


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
