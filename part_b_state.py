from __future__ import annotations

import json
import logging
import os
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any
from urllib import parse, request


logger = logging.getLogger("moreau-part-b")

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_STATE_DIR = PROJECT_ROOT / "results" / "part_b_state_runtime"

RUN_CLASSES = {"manual", "operator-assisted", "agent-only"}
ACTOR_TYPES = {"manual", "operator", "agent", "system"}
ACTION_VERBS = {"HOLD", "CARE", "REST", "TRAIN", "ENTER_ARENA", "ENTER_CAVE", "EXTRACT", "MUTATE"}
PUBLIC_OBSERVATION_KEYS = (
    "world_tick",
    "active_zone",
    "priority_profile",
    "risk_appetite",
    "care_threshold",
    "combat_bias",
    "expedition_bias",
    "queue_length",
    "queue_capacity",
    "inference_budget_remaining",
    "house_agent_enabled",
    "state_projection",
)
CONFLICT_STATUSES = {"none", "stale_rejected", "operator_preempted", "manual_freeze"}
QUEUE_CAPACITY_DEFAULT = 6
HOUSE_AGENT_PROVIDERS = {"anthropic", "gemini", "fallback"}
HOUSE_AGENT_PROVIDER_DEFAULT = (os.environ.get("MOREAU_PART_B_HOUSE_AGENT_PROVIDER", "anthropic").strip().lower() or "anthropic")
HOUSE_AGENT_MODEL_DEFAULT_ANTHROPIC = "claude-haiku-4-5-20251001"
HOUSE_AGENT_MODEL_DEFAULT_GEMINI = "gemini-2.5-flash-lite"
HOUSE_AGENT_MODEL_DEFAULT = HOUSE_AGENT_MODEL_DEFAULT_ANTHROPIC
HOUSE_AGENT_MODEL_ALIASES = {
    "gemini-2.0-flash-lite": "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite-001": "gemini-2.5-flash-lite",
    "gemini-2.0-flash": "gemini-2.5-flash",
    "gemini-2.0-flash-001": "gemini-2.5-flash",
}
HOUSE_AGENT_ALLOWED_ZONES = {"arena", "cave"}
QUEUE_EXECUTABLE_ACTORS = {"manual", "operator", "agent"}
PART_B_BASELINE_POLICIES = {"conservative", "greedy", "random", "caremax", "arena-spam", "expedition-max"}
PART_B_SEASON_CURRENT_ID = "part-b-s1-first-descent"
PART_B_SEASONS: dict[str, dict[str, Any]] = {
    PART_B_SEASON_CURRENT_ID: {
        "season_id": PART_B_SEASON_CURRENT_ID,
        "name": "Part B Season 1: First Descent",
        "status": "active",
        "headline": "The first public ecological season for the two-zone Part B world.",
        "zones": ["arena", "cave"],
        "run_classes": ["manual", "operator-assisted", "agent-only"],
        "composite_headline_enabled": False,
        "house_agent_benchmark_allowed": True,
        "house_agent_benchmark_rule": "Only runs that stay inside the published observation/action/scoring contract are eligible.",
        "versions": {
            "observation": "B1",
            "action": "B1",
            "scoring": "B1",
        },
        "contract": {
            "tick_real_hours": 6,
            "queue_capacity_default": QUEUE_CAPACITY_DEFAULT,
            "budget_default_daily": 4,
            "budget_mode": "hybrid",
            "score_families": ["welfare", "combat", "expedition"],
            "welfare_decay": "health -1, morale -1, happiness -2 on HOLD; health -1, morale -1, happiness -1 on other non-care ticks",
            "red_lines": [
                "No Black Orchard",
                "No composite headline score",
                "No hidden house-agent privileges",
                "No priority queue",
            ],
        },
    }
}
HOUSE_AGENT_FORBIDDEN_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bhere are\b",
        r"\bbased on your current stats\b",
        r"\bmaximize\b",
        r"\boptimiz",
        r"\bdefinitely\b",
    ]
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_dir() -> Path:
    override = os.environ.get("MOREAU_PART_B_STATE_DIR", "").strip()
    return Path(override) if override else DEFAULT_STATE_DIR


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value)!r}")


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=_json_default) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                rows.append(data)
    return rows


def _coerce_run_class(value: str) -> str:
    run_class = (value or "").strip().lower()
    if run_class not in RUN_CLASSES:
        raise ValueError(f"Invalid run_class: {value}")
    return run_class


def _coerce_actor_type(value: str) -> str:
    actor_type = (value or "").strip().lower()
    if actor_type not in ACTOR_TYPES:
        raise ValueError(f"Invalid actor_type: {value}")
    return actor_type


def _coerce_action(action: str | None) -> str | None:
    if action is None:
        return None
    normalized = action.strip().upper()
    if normalized not in ACTION_VERBS:
        raise ValueError(f"Invalid action_verb: {action}")
    return normalized


def _coerce_house_agent_provider(value: Any) -> str:
    provider = str(value or HOUSE_AGENT_PROVIDER_DEFAULT).strip().lower()
    if provider == "google":
        provider = "gemini"
    if provider not in HOUSE_AGENT_PROVIDERS:
        raise ValueError(f"Invalid house_agent_provider: {value}")
    return provider


def _sanitize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sanitize_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _sanitize_text(value: Any, limit: int = 120) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[: limit - 1] + "…" if len(text) > limit else text


def _sanitize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _default_house_agent_model(provider: str) -> str:
    env_model = os.environ.get("MOREAU_PART_B_HOUSE_AGENT_MODEL", "").strip()
    if env_model:
        return HOUSE_AGENT_MODEL_ALIASES.get(env_model, env_model)
    if provider == "gemini":
        return HOUSE_AGENT_MODEL_DEFAULT_GEMINI
    return HOUSE_AGENT_MODEL_DEFAULT_ANTHROPIC


def _normalize_house_agent_model(provider: str, value: Any) -> str:
    model = _sanitize_text(value, 64) or _default_house_agent_model(provider)
    if provider == "gemini":
        return HOUSE_AGENT_MODEL_ALIASES.get(model, model)
    return model


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _clamp_pct(value: float) -> int:
    return _clamp_score(value)


def _to_number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _intish(value: Any, default: int = 0, *, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def _json_from_text(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        candidate = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return candidate if isinstance(candidate, dict) else None


def _deterministic_roll(*parts: Any, modulo: int = 100) -> int:
    data = "::".join("" if part is None else str(part) for part in parts)
    total = 0
    for index, char in enumerate(data):
        total += (index + 17) * ord(char)
    return total % max(1, modulo)


def _normalize_zone(value: Any, default: str = "arena") -> str:
    zone = str(value or default).strip().lower()
    return zone if zone in HOUSE_AGENT_ALLOWED_ZONES else default


def _current_part_b_season(season_id: str | None = None) -> dict[str, Any]:
    if season_id and season_id in PART_B_SEASONS:
        return dict(PART_B_SEASONS[season_id])
    return dict(PART_B_SEASONS[PART_B_SEASON_CURRENT_ID])


def _normalize_queue_item(item: Any, *, default_actor: str = "operator", enqueued_revision: int = 0) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    try:
        action_verb = _coerce_action(item.get("action_verb") or item.get("verb"))
    except ValueError:
        return None
    if action_verb is None:
        return None
    try:
        actor_type = _coerce_actor_type(item.get("actor_type") or default_actor)
    except ValueError:
        actor_type = default_actor
    if actor_type not in QUEUE_EXECUTABLE_ACTORS:
        actor_type = default_actor
    return {
        "id": item.get("id") or str(uuid.uuid4()),
        "action_verb": action_verb,
        "zone": _normalize_zone(item.get("zone"), "cave" if action_verb in {"ENTER_CAVE", "EXTRACT"} else "arena"),
        "actor_type": actor_type,
        "source": _sanitize_text(item.get("source"), 48) or "operator-ui",
        "note": _sanitize_text(item.get("note"), 120),
        "enqueued_at": item.get("enqueued_at") or _utcnow(),
        "enqueued_state_revision": _intish(item.get("enqueued_state_revision"), enqueued_revision, minimum=0),
        "status": _sanitize_text(item.get("status"), 24) or "queued",
    }


def _sanitize_queue(value: Any, *, default_actor: str = "operator", enqueued_revision: int = 0, capacity: int = QUEUE_CAPACITY_DEFAULT) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw_item in _sanitize_list(value):
        item = _normalize_queue_item(raw_item, default_actor=default_actor, enqueued_revision=enqueued_revision)
        if item:
            normalized.append(item)
        if len(normalized) >= capacity:
            break
    return normalized


def _ensure_state_projection(value: Any) -> dict[str, Any]:
    state = _sanitize_dict(value)
    normalized = {
        "pet_id": state.get("pet_id"),
        "name": state.get("name"),
        "animal": state.get("animal"),
        "level": _intish(state.get("level"), 1, minimum=1),
        "xp": _intish(state.get("xp"), 0, minimum=0),
        "is_alive": state.get("is_alive", True) is not False,
        "health_pct": _clamp_pct(_to_number(state.get("health_pct"), 90.0)),
        "morale_pct": _clamp_pct(_to_number(state.get("morale_pct"), 82.0)),
        "happiness_pct": _clamp_pct(_to_number(state.get("happiness_pct"), 78.0)),
        "energy_pct": _clamp_pct(_to_number(state.get("energy_pct"), 86.0)),
        "corruption_pct": _clamp_pct(_to_number(state.get("corruption_pct"), 0.0)),
        "instability": _clamp_pct(_to_number(state.get("instability"), 0.0)),
        "mutation_count": _intish(state.get("mutation_count"), 0, minimum=0),
        "recent_fight_summary": _sanitize_text(state.get("recent_fight_summary"), 48) or "none",
        "recent_cave_summary": _sanitize_text(state.get("recent_cave_summary"), 48) or "none",
        "last_action": _sanitize_text(state.get("last_action"), 32) or "START",
        "last_action_outcome": _sanitize_text(state.get("last_action_outcome"), 80) or "run created",
        "neglect_ticks": _intish(state.get("neglect_ticks"), 0, minimum=0),
        "ticks_since_care": _intish(state.get("ticks_since_care"), 0, minimum=0),
        "days_survived": _intish(state.get("days_survived"), 0, minimum=0),
        "arena_available": state.get("arena_available", True) is not False,
        "arena_tickets": _intish(state.get("arena_tickets"), 1, minimum=0),
        "arena_recent_record": _sanitize_text(state.get("arena_recent_record"), 12) or "none",
        "arena_reward_preview": _intish(state.get("arena_reward_preview"), 12, minimum=0),
        "arena_loss_streak": _intish(state.get("arena_loss_streak"), 0, minimum=0),
        "cave_available": state.get("cave_available", True) is not False,
        "cave_depth_last_run": _intish(state.get("cave_depth_last_run"), 0, minimum=0),
        "cave_extract_value_last_run": _intish(state.get("cave_extract_value_last_run"), 0, minimum=0),
        "cave_injury_last_run": _intish(state.get("cave_injury_last_run"), 0, minimum=0),
        "cave_reward_preview": _intish(state.get("cave_reward_preview"), 18, minimum=0),
        "in_cave": _sanitize_bool(state.get("in_cave"), False),
        "current_cave_depth": _intish(state.get("current_cave_depth"), 0, minimum=0),
        "current_cave_value": _intish(state.get("current_cave_value"), 0, minimum=0),
        "current_cave_risk": _intish(state.get("current_cave_risk"), 0, minimum=0),
        "idle_ticks": _intish(state.get("idle_ticks"), 0, minimum=0),
        "critical_state_ticks": _intish(state.get("critical_state_ticks"), 0, minimum=0),
        "care_like_ticks": _intish(state.get("care_like_ticks"), 0, minimum=0),
        "total_ticks": _intish(state.get("total_ticks"), 0, minimum=0),
        "completed_queue_ticks": _intish(state.get("completed_queue_ticks"), 0, minimum=0),
        "successful_queue_ticks": _intish(state.get("successful_queue_ticks"), 0, minimum=0),
    }
    if normalized["health_pct"] <= 0:
        normalized["is_alive"] = False
    return normalized


def _queue_defaults(run_record: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    capacity = _intish(run_record.get("queue_capacity"), QUEUE_CAPACITY_DEFAULT, minimum=1, maximum=20)
    actor = "agent" if run_record.get("run_class") == "agent-only" else "operator"
    queue_state = _sanitize_queue(
        run_record.get("queue_state"),
        default_actor=actor,
        enqueued_revision=_intish(run_record.get("state_revision"), 0, minimum=0),
        capacity=capacity,
    )
    return queue_state, capacity


def _observation_from(run_record: dict[str, Any]) -> dict[str, Any]:
    state = _ensure_state_projection(run_record.get("state_projection"))
    queue_state, capacity = _queue_defaults(run_record)
    observation = {
        "world_tick": _intish(run_record.get("world_tick"), 0, minimum=0),
        "active_zone": _normalize_zone(run_record.get("active_zone"), "arena"),
        "priority_profile": _sanitize_text(run_record.get("priority_profile"), 32) or "balanced",
        "risk_appetite": _sanitize_text(run_record.get("risk_appetite"), 32) or "measured",
        "care_threshold": _intish(run_record.get("care_threshold"), 60, minimum=0, maximum=100),
        "combat_bias": _intish(run_record.get("combat_bias"), 50, minimum=0, maximum=100),
        "expedition_bias": _intish(run_record.get("expedition_bias"), 50, minimum=0, maximum=100),
        "queue_length": len(queue_state),
        "queue_capacity": capacity,
        "inference_budget_remaining": _intish(run_record.get("inference_budget_remaining"), 0, minimum=0),
        "house_agent_enabled": _sanitize_bool(run_record.get("house_agent_enabled"), False),
        "state_projection": state,
    }
    return {key: observation[key] for key in PUBLIC_OBSERVATION_KEYS}


def _house_agent_memory_input(run_record: dict[str, Any], observation: dict[str, Any] | None = None) -> dict[str, Any]:
    observed = observation or _observation_from(run_record)
    return {
        "mode": "public_observation_only",
        "contract_version": run_record.get("observation_version") or _current_part_b_season(run_record.get("season_id"))["versions"]["observation"],
        "observation_keys": list(PUBLIC_OBSERVATION_KEYS),
        "observation": observed,
        "memory_notes": [],
    }


def _apply_decay(state: dict[str, Any], action_verb: str, *, positive_recovery: bool) -> dict[str, Any]:
    next_state = _ensure_state_projection(state)
    next_state["total_ticks"] = _intish(next_state.get("total_ticks"), 0, minimum=0) + 1

    care_like = action_verb in {"CARE", "REST"}
    if care_like:
        next_state["care_like_ticks"] = _intish(next_state.get("care_like_ticks"), 0, minimum=0) + 1
        next_state["ticks_since_care"] = 0
    else:
        next_state["ticks_since_care"] = _intish(next_state.get("ticks_since_care"), 0, minimum=0) + 1
        next_state["health_pct"] = _clamp_pct(next_state["health_pct"] - 1)
        next_state["morale_pct"] = _clamp_pct(next_state["morale_pct"] - 1)
        next_state["happiness_pct"] = _clamp_pct(next_state["happiness_pct"] - (2 if action_verb == "HOLD" else 1))
        if action_verb == "HOLD":
            next_state["idle_ticks"] = _intish(next_state.get("idle_ticks"), 0, minimum=0) + 1

    if not care_like and not positive_recovery and next_state["ticks_since_care"] >= 2:
        next_state["neglect_ticks"] = _intish(next_state.get("neglect_ticks"), 0, minimum=0) + 1

    if _intish(next_state.get("neglect_ticks"), 0, minimum=0) >= 3:
        next_state["critical_state_ticks"] = _intish(next_state.get("critical_state_ticks"), 0, minimum=0) + 1

    if next_state["health_pct"] <= 0:
        next_state["is_alive"] = False

    return next_state


def _simulate_action(run_record: dict[str, Any], action_verb: str, zone: str) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    zone = _normalize_zone(zone, "cave" if action_verb in {"ENTER_CAVE", "EXTRACT"} else _normalize_zone(run_record.get("active_zone"), "arena"))
    state = _ensure_state_projection(run_record.get("state_projection"))
    world_tick = _intish(run_record.get("world_tick"), 0, minimum=0) + 1
    combat_bias = _intish(run_record.get("combat_bias"), 50, minimum=0, maximum=100)
    expedition_bias = _intish(run_record.get("expedition_bias"), 50, minimum=0, maximum=100)
    risk_appetite = _sanitize_text(run_record.get("risk_appetite"), 16) or "measured"
    risk_bonus = {"guarded": -4, "measured": 0, "bold": 6}.get(risk_appetite, 0)

    if state["is_alive"] is False:
        return {"skipped_reason": "pet_not_alive"}, state, "pet_not_alive"

    next_state = dict(state)
    outcome: dict[str, Any] = {}
    positive_recovery = False

    if action_verb == "ENTER_ARENA":
        if not state.get("arena_available", True):
            return {"skipped_reason": "arena_unavailable"}, state, "arena_unavailable"
        arena_roll = _deterministic_roll(run_record.get("id"), world_tick, "arena", modulo=21)
        power = (
            (state["health_pct"] * 0.24)
            + (state["morale_pct"] * 0.2)
            + (state["energy_pct"] * 0.22)
            + (combat_bias * 0.18)
            - (_intish(state.get("arena_loss_streak"), 0) * 2.0)
            + risk_bonus
        )
        target = 52 + arena_roll
        won = power >= target
        reward = 12 if won else 4
        xp_gain = 20 if won else 6
        next_state.update(
            {
                "health_pct": _clamp_pct(state["health_pct"] - (6 if won else 14)),
                "morale_pct": _clamp_pct(state["morale_pct"] + (8 if won else -7)),
                "happiness_pct": _clamp_pct(state["happiness_pct"] + (5 if won else -4)),
                "energy_pct": _clamp_pct(state["energy_pct"] - 12),
                "recent_fight_summary": "win" if won else "loss",
                "arena_recent_record": "W" if won else "L",
                "arena_loss_streak": 0 if won else (_intish(state.get("arena_loss_streak"), 0, minimum=0) + 1),
                "last_action": "ENTER_ARENA",
                "last_action_outcome": "win" if won else "loss",
            }
        )
        outcome = {
            "result": "win" if won else "loss",
            "reward": reward,
            "xp_gain": xp_gain,
            "difficulty_target": target,
            "power_estimate": round(power, 2),
        }
    elif action_verb == "ENTER_CAVE":
        if not state.get("cave_available", True):
            return {"skipped_reason": "cave_unavailable"}, state, "cave_unavailable"
        depth = _intish(state.get("current_cave_depth"), 0, minimum=0) + 1
        reward = 8 + (depth * 6) + _deterministic_roll(run_record.get("id"), world_tick, "cave-reward", modulo=6)
        injury = max(0, 2 + (depth * 2) + _deterministic_roll(run_record.get("id"), world_tick, "cave-injury", modulo=5) - max(0, expedition_bias - 50) // 15)
        next_state.update(
            {
                "in_cave": True,
                "current_cave_depth": depth,
                "current_cave_value": _intish(state.get("current_cave_value"), 0, minimum=0) + reward,
                "current_cave_risk": _intish(state.get("current_cave_risk"), 0, minimum=0) + injury,
                "health_pct": _clamp_pct(state["health_pct"] - injury),
                "morale_pct": _clamp_pct(state["morale_pct"] + 3),
                "happiness_pct": _clamp_pct(state["happiness_pct"] + 1),
                "energy_pct": _clamp_pct(state["energy_pct"] - 14),
                "recent_cave_summary": f"depth {depth}",
                "last_action": "ENTER_CAVE",
                "last_action_outcome": f"depth {depth}",
            }
        )
        outcome = {
            "depth": depth,
            "extract_value": reward,
            "injury": injury,
        }
    elif action_verb == "EXTRACT":
        if not state.get("in_cave") and _intish(state.get("current_cave_depth"), 0, minimum=0) <= 0:
            return {"skipped_reason": "nothing_to_extract"}, state, "nothing_to_extract"
        extract_value = _intish(state.get("current_cave_value"), 0, minimum=0)
        depth = _intish(state.get("current_cave_depth"), 0, minimum=0)
        injury = _intish(state.get("current_cave_risk"), 0, minimum=0)
        next_state.update(
            {
                "in_cave": False,
                "cave_depth_last_run": depth,
                "cave_extract_value_last_run": extract_value,
                "cave_injury_last_run": injury,
                "current_cave_depth": 0,
                "current_cave_value": 0,
                "current_cave_risk": 0,
                "morale_pct": _clamp_pct(state["morale_pct"] + 5),
                "happiness_pct": _clamp_pct(state["happiness_pct"] + 4),
                "last_action": "EXTRACT",
                "last_action_outcome": f"secured {extract_value}",
            }
        )
        outcome = {
            "depth": depth,
            "extract_value": extract_value,
            "injury": injury,
        }
        positive_recovery = True
    elif action_verb == "CARE":
        next_state.update(
            {
                "health_pct": _clamp_pct(state["health_pct"] + 8),
                "morale_pct": _clamp_pct(state["morale_pct"] + 10),
                "happiness_pct": _clamp_pct(state["happiness_pct"] + 12),
                "energy_pct": _clamp_pct(state["energy_pct"] + 4),
                "neglect_ticks": max(0, _intish(state.get("neglect_ticks"), 0, minimum=0) - 2),
                "last_action": "CARE",
                "last_action_outcome": "stabilized",
            }
        )
        outcome = {"welfare_delta": 10}
        positive_recovery = True
    elif action_verb == "REST":
        next_state.update(
            {
                "energy_pct": _clamp_pct(state["energy_pct"] + 16),
                "morale_pct": _clamp_pct(state["morale_pct"] + 2),
                "neglect_ticks": max(0, _intish(state.get("neglect_ticks"), 0, minimum=0) - 1),
                "last_action": "REST",
                "last_action_outcome": "recovered",
            }
        )
        outcome = {"energy_gain": 16}
        positive_recovery = True
    elif action_verb == "HOLD":
        next_state.update(
            {
                "last_action": "HOLD",
                "last_action_outcome": "waited",
            }
        )
        outcome = {"idle_tick": True}
    elif action_verb == "TRAIN":
        next_state.update(
            {
                "xp": _intish(state.get("xp"), 0, minimum=0) + 12,
                "energy_pct": _clamp_pct(state["energy_pct"] - 8),
                "morale_pct": _clamp_pct(state["morale_pct"] + 4),
                "happiness_pct": _clamp_pct(state["happiness_pct"] - 1),
                "last_action": "TRAIN",
                "last_action_outcome": "trained",
            }
        )
        outcome = {"xp_gain": 12}
    elif action_verb == "MUTATE":
        if _intish(state.get("mutation_count"), 0, minimum=0) >= 6:
            return {"skipped_reason": "mutation_cap_reached"}, state, "mutation_cap_reached"
        next_state.update(
            {
                "mutation_count": _intish(state.get("mutation_count"), 0, minimum=0) + 1,
                "corruption_pct": _clamp_pct(state["corruption_pct"] + 12),
                "instability": _clamp_pct(state["instability"] + 8),
                "happiness_pct": _clamp_pct(state["happiness_pct"] - 3),
                "last_action": "MUTATE",
                "last_action_outcome": "altered",
            }
        )
        outcome = {"mutation_gain": 1}

    next_state = _apply_decay(next_state, action_verb, positive_recovery=positive_recovery)
    if next_state["health_pct"] <= 0:
        next_state["is_alive"] = False
        next_state["last_action_outcome"] = "collapsed"
        outcome["fatal"] = True
    return outcome, next_state, None


def _derive_scores(run_record: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    state = _ensure_state_projection(run_record.get("state_projection"))
    health = _to_number(state.get("health_pct"), 100.0)
    morale = _to_number(state.get("morale_pct"), 100.0)
    happiness = _to_number(state.get("happiness_pct"), 100.0)
    neglect_ticks = _to_number(state.get("neglect_ticks"), 0.0)
    idle_ticks = _to_number(state.get("idle_ticks"), 0.0)
    critical_state_ticks = _to_number(state.get("critical_state_ticks"), 0.0)
    total_ticks = max(1.0, _to_number(state.get("total_ticks"), 0.0))
    care_like_ticks = _to_number(state.get("care_like_ticks"), 0.0)
    alive = state.get("is_alive", True) is not False

    survival_ratio = 1.0 if alive else 0.0
    active_care_ratio = care_like_ticks / total_ticks
    welfare = 100 * (
        (0.35 * survival_ratio)
        + (0.20 * (health / 100.0))
        + (0.20 * (morale / 100.0))
        + (0.15 * (happiness / 100.0))
        + (0.10 * active_care_ratio)
    ) - (8.0 * neglect_ticks) - (5.0 * critical_state_ticks) - (3.0 * idle_ticks)

    combat_wins = 0
    combat_losses = 0
    combat_reward = 0.0
    combat_events = 0
    expedition_depth = _to_number(state.get("cave_depth_last_run"), 0.0)
    expedition_extract_value = _to_number(state.get("cave_extract_value_last_run"), 0.0)
    expedition_injury = _to_number(state.get("cave_injury_last_run"), 0.0)
    expedition_events = 0

    for event in events:
        if not event.get("accepted", False):
            continue
        action = event.get("action_verb")
        outcome = _sanitize_dict(event.get("outcome"))
        if action == "ENTER_ARENA":
            combat_events += 1
            result = str(outcome.get("result") or outcome.get("arena_result") or "").lower()
            if result == "win":
                combat_wins += 1
            elif result == "loss":
                combat_losses += 1
            combat_reward += _to_number(outcome.get("reward"), 0.0)
            combat_reward += _to_number(outcome.get("rating_delta"), 0.0)
            combat_reward += _to_number(outcome.get("xp_gain"), 0.0) * 0.5
        elif action in {"ENTER_CAVE", "EXTRACT"}:
            expedition_events += 1
            expedition_depth = max(expedition_depth, _to_number(outcome.get("depth"), expedition_depth))
            expedition_extract_value += _to_number(outcome.get("extract_value"), 0.0)
            expedition_injury += _to_number(outcome.get("injury"), 0.0)

    combat = (combat_wins * 14.0) - (combat_losses * 8.0) + (combat_reward * 0.35) + (6.0 if combat_events > 0 else 0.0)
    expedition = (expedition_depth * 10.0) + (expedition_extract_value * 0.9) - (expedition_injury * 1.2) + (5.0 if expedition_events > 0 else 0.0)

    return {
        "welfare": _clamp_score(welfare),
        "combat": _clamp_score(combat),
        "expedition": _clamp_score(expedition),
    }


def _score_breakdown(run_record: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    state = _ensure_state_projection(run_record.get("state_projection"))
    health = _to_number(state.get("health_pct"), 100.0)
    morale = _to_number(state.get("morale_pct"), 100.0)
    happiness = _to_number(state.get("happiness_pct"), 100.0)
    neglect_ticks = _to_number(state.get("neglect_ticks"), 0.0)
    idle_ticks = _to_number(state.get("idle_ticks"), 0.0)
    critical_state_ticks = _to_number(state.get("critical_state_ticks"), 0.0)
    total_ticks = max(1.0, _to_number(state.get("total_ticks"), 0.0))
    care_like_ticks = _to_number(state.get("care_like_ticks"), 0.0)
    alive = state.get("is_alive", True) is not False

    combat_wins = 0
    combat_losses = 0
    combat_reward = 0.0
    combat_events = 0
    expedition_depth = _to_number(state.get("cave_depth_last_run"), 0.0)
    expedition_extract_value = _to_number(state.get("cave_extract_value_last_run"), 0.0)
    expedition_injury = _to_number(state.get("cave_injury_last_run"), 0.0)
    expedition_events = 0

    for event in events:
        if not event.get("accepted", False):
            continue
        action = event.get("action_verb")
        outcome = _sanitize_dict(event.get("outcome"))
        if action == "ENTER_ARENA":
            combat_events += 1
            result = str(outcome.get("result") or outcome.get("arena_result") or "").lower()
            if result == "win":
                combat_wins += 1
            elif result == "loss":
                combat_losses += 1
            combat_reward += _to_number(outcome.get("reward"), 0.0)
            combat_reward += _to_number(outcome.get("rating_delta"), 0.0)
            combat_reward += _to_number(outcome.get("xp_gain"), 0.0) * 0.5
        elif action in {"ENTER_CAVE", "EXTRACT"}:
            expedition_events += 1
            expedition_depth = max(expedition_depth, _to_number(outcome.get("depth"), expedition_depth))
            expedition_extract_value += _to_number(outcome.get("extract_value"), 0.0)
            expedition_injury += _to_number(outcome.get("injury"), 0.0)

    return {
        "welfare": {
            "survival_ratio": round(1.0 if alive else 0.0, 4),
            "health_pct": _clamp_pct(health),
            "morale_pct": _clamp_pct(morale),
            "happiness_pct": _clamp_pct(happiness),
            "active_care_ratio": round(care_like_ticks / total_ticks, 4),
            "neglect_ticks": int(neglect_ticks),
            "idle_ticks": int(idle_ticks),
            "critical_state_ticks": int(critical_state_ticks),
        },
        "combat": {
            "wins": combat_wins,
            "losses": combat_losses,
            "events": combat_events,
            "reward_total": round(combat_reward, 2),
        },
        "expedition": {
            "max_depth": int(expedition_depth),
            "extract_value_total": round(expedition_extract_value, 2),
            "injury_total": round(expedition_injury, 2),
            "events": expedition_events,
        },
    }


def _completed_action_summaries(events: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for event in reversed(events):
        if event.get("event_type") not in {"action_applied", "tick_skipped", "agent_autopause"}:
            continue
        summaries.append(
            {
                "sequence": event.get("sequence"),
                "world_tick": event.get("world_tick"),
                "actor_type": event.get("actor_type"),
                "action_verb": event.get("action_verb"),
                "event_type": event.get("event_type"),
                "accepted": event.get("accepted", False),
                "conflict_status": event.get("conflict_status"),
                "outcome": _sanitize_dict(event.get("outcome")),
                "details": _sanitize_dict(event.get("details")),
                "created_at": event.get("created_at"),
            }
        )
        if len(summaries) >= limit:
            break
    summaries.reverse()
    return summaries


def _state_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> list[dict[str, Any]]:
    before_state = _ensure_state_projection(before or {})
    after_state = _ensure_state_projection(after or {})
    rows: list[dict[str, Any]] = []
    labels = {
        "health_pct": "Health",
        "morale_pct": "Morale",
        "happiness_pct": "Happiness",
        "energy_pct": "Energy",
        "current_cave_depth": "Depth",
        "current_cave_value": "Held Value",
        "current_cave_risk": "Held Risk",
        "mutation_count": "Mutations",
        "neglect_ticks": "Neglect",
    }
    for key, label in labels.items():
        before_value = before_state.get(key)
        after_value = after_state.get(key)
        if before_value == after_value:
            continue
        rows.append(
            {
                "key": key,
                "label": label,
                "before": before_value,
                "after": after_value,
                "delta": (_to_number(after_value, 0.0) - _to_number(before_value, 0.0)),
            }
        )
    rows.sort(key=lambda item: abs(_to_number(item["delta"], 0.0)), reverse=True)
    return rows[:8]


def _latest_transition(events: list[dict[str, Any]], current_state: dict[str, Any]) -> dict[str, Any] | None:
    accepted = [event for event in events if event.get("accepted", False) and event.get("event_type") == "action_applied"]
    if not accepted:
        return None
    last = accepted[-1]
    previous_state = _sanitize_dict(accepted[-2].get("state_after")) if len(accepted) > 1 else {}
    after_state = _sanitize_dict(last.get("state_after")) or current_state
    return {
        "sequence": last.get("sequence"),
        "world_tick": last.get("world_tick"),
        "actor_type": last.get("actor_type"),
        "action_verb": last.get("action_verb"),
        "zone": last.get("zone"),
        "outcome": _sanitize_dict(last.get("outcome")),
        "delta": _state_delta(previous_state, after_state),
    }


def _report_from(run_record: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    by_actor: dict[str, int] = {}
    by_action: dict[str, int] = {}
    conflicts = 0
    accepted = 0
    latest_conflict: dict[str, Any] | None = None
    for event in events:
        actor = event.get("actor_type", "unknown")
        by_actor[actor] = by_actor.get(actor, 0) + 1
        action = event.get("action_verb")
        if action:
            by_action[action] = by_action.get(action, 0) + 1
        if event.get("conflict_status") and event.get("conflict_status") != "none":
            conflicts += 1
            latest_conflict = {
                "sequence": event.get("sequence"),
                "world_tick": event.get("world_tick"),
                "actor_type": event.get("actor_type"),
                "action_verb": event.get("action_verb"),
                "conflict_status": event.get("conflict_status"),
                "details": _sanitize_dict(event.get("details")),
            }
        if event.get("accepted", False):
            accepted += 1
    queue_state, capacity = _queue_defaults(run_record)
    season = _current_part_b_season(run_record.get("season_id"))
    current_state = _ensure_state_projection(run_record.get("state_projection"))
    scores = _derive_scores(run_record, events)
    return {
        "run_id": run_record["id"],
        "season_id": run_record["season_id"],
        "run_class": run_record["run_class"],
        "status": run_record["status"],
        "world_tick": run_record["world_tick"],
        "state_revision": run_record["state_revision"],
        "event_count": len(events),
        "accepted_event_count": accepted,
        "conflict_count": conflicts,
        "events_by_actor": by_actor,
        "actions_by_verb": by_action,
        "last_event_at": run_record.get("last_event_at"),
        "last_actor_type": run_record.get("last_actor_type"),
        "last_action_verb": run_record.get("last_action_verb"),
        "scores": scores,
        "score_breakdown": _score_breakdown(run_record, events),
        "state_projection": current_state,
        "season": {
            "season_id": season["season_id"],
            "name": season["name"],
            "versions": season["versions"],
            "zones": season["zones"],
            "composite_headline_enabled": season["composite_headline_enabled"],
            "house_agent_benchmark_allowed": season["house_agent_benchmark_allowed"],
        },
        "queue": {
            "pending_count": len(queue_state),
            "capacity": capacity,
            "pending": queue_state,
            "completed_recent": _completed_action_summaries(events),
        },
        "house_agent": {
            "enabled": _sanitize_bool(run_record.get("house_agent_enabled"), False),
            "provider": run_record.get("house_agent_provider") or HOUSE_AGENT_PROVIDER_DEFAULT,
            "model": run_record.get("house_agent_model") or _default_house_agent_model(run_record.get("house_agent_provider") or HOUSE_AGENT_PROVIDER_DEFAULT),
            "last_plan": _sanitize_dict(run_record.get("house_agent_last_plan")),
        },
        "billing": {
            "mode": run_record.get("billing_mode") or "hybrid",
            "world_access_active": _sanitize_bool(run_record.get("world_access_active"), True),
            "inference_budget_remaining": _intish(run_record.get("inference_budget_remaining"), 0, minimum=0),
            "inference_budget_daily": _intish(run_record.get("inference_budget_daily"), 4, minimum=0),
            "autopause_reason": run_record.get("autopause_reason"),
        },
        "inspect": {
            "latest_transition": _latest_transition(events, current_state),
            "latest_conflict": latest_conflict,
            "event_density_per_tick": round(len(events) / max(1, _intish(run_record.get("world_tick"), 0, minimum=0)), 3),
        },
    }


def _base_run(payload: dict[str, Any], backend: str) -> dict[str, Any]:
    now = _utcnow()
    season = _current_part_b_season(payload.get("season_id"))
    queue_capacity = _intish(payload.get("queue_capacity"), QUEUE_CAPACITY_DEFAULT, minimum=1, maximum=20)
    run_class = _coerce_run_class(payload.get("run_class", "manual"))
    state_revision = _intish(payload.get("state_revision"), 0, minimum=0)
    queue_actor = "agent" if run_class == "agent-only" else "operator"
    queue_state = _sanitize_queue(payload.get("queue_state"), default_actor=queue_actor, enqueued_revision=state_revision, capacity=queue_capacity)
    state_projection = _ensure_state_projection(payload.get("state_projection"))
    provider = _coerce_house_agent_provider(payload.get("house_agent_provider") or HOUSE_AGENT_PROVIDER_DEFAULT)
    model = _normalize_house_agent_model(provider, payload.get("house_agent_model"))
    return {
        "id": payload.get("id") or str(uuid.uuid4()),
        "season_id": season["season_id"],
        "run_class": run_class,
        "status": (payload.get("status") or "active").strip(),
        "operator_id": payload.get("operator_id"),
        "subject_pet_id": payload.get("subject_pet_id"),
        "subject_pet_name": payload.get("subject_pet_name"),
        "subject_pet_animal": payload.get("subject_pet_animal"),
        "active_zone": _normalize_zone(payload.get("active_zone"), "arena"),
        "priority_profile": (payload.get("priority_profile") or "balanced").strip(),
        "risk_appetite": (payload.get("risk_appetite") or "measured").strip(),
        "care_threshold": _intish(payload.get("care_threshold"), 60, minimum=0, maximum=100),
        "combat_bias": _intish(payload.get("combat_bias"), 50, minimum=0, maximum=100),
        "expedition_bias": _intish(payload.get("expedition_bias"), 50, minimum=0, maximum=100),
        "world_tick": _intish(payload.get("world_tick"), 0, minimum=0),
        "state_revision": state_revision,
        "inference_budget_remaining": _intish(payload.get("inference_budget_remaining"), 4, minimum=0, maximum=999),
        "inference_budget_daily": _intish(payload.get("inference_budget_daily"), 4, minimum=0, maximum=999),
        "billing_mode": (payload.get("billing_mode") or "hybrid").strip(),
        "world_access_active": _sanitize_bool(payload.get("world_access_active"), True),
        "house_agent_enabled": _sanitize_bool(payload.get("house_agent_enabled"), run_class == "agent-only"),
        "house_agent_provider": provider,
        "house_agent_model": model,
        "house_agent_last_plan": _sanitize_dict(payload.get("house_agent_last_plan")),
        "autopause_reason": _sanitize_text(payload.get("autopause_reason"), 64),
        "observation_version": (payload.get("observation_version") or season["versions"]["observation"]).strip(),
        "action_version": (payload.get("action_version") or season["versions"]["action"]).strip(),
        "scoring_version": (payload.get("scoring_version") or season["versions"]["scoring"]).strip(),
        "conflict_policy": (payload.get("conflict_policy") or "operator_wins_before_execution").strip(),
        "queue_capacity": queue_capacity,
        "queue_state": queue_state,
        "state_projection": state_projection,
        "metadata": _sanitize_dict(payload.get("metadata")),
        "last_event_at": None,
        "last_actor_type": None,
        "last_action_verb": None,
        "created_at": now,
        "updated_at": now,
        "backend": backend,
    }


def _run_fields() -> tuple[str, ...]:
    return (
        "status",
        "active_zone",
        "priority_profile",
        "risk_appetite",
        "care_threshold",
        "combat_bias",
        "expedition_bias",
        "world_tick",
        "inference_budget_remaining",
        "inference_budget_daily",
        "billing_mode",
        "world_access_active",
        "house_agent_enabled",
        "house_agent_provider",
        "house_agent_model",
        "house_agent_last_plan",
        "autopause_reason",
        "conflict_policy",
        "subject_pet_id",
        "subject_pet_name",
        "subject_pet_animal",
        "queue_capacity",
    )


def _apply_run_updates_to_record(run_record: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    for key in _run_fields():
        if key in payload and payload[key] is not None:
            run_record[key] = payload[key]
    if "queue_state" in payload and payload["queue_state"] is not None:
        actor = "agent" if run_record.get("run_class") == "agent-only" else "operator"
        run_record["queue_state"] = _sanitize_queue(
            payload["queue_state"],
            default_actor=actor,
            enqueued_revision=_intish(run_record.get("state_revision"), 0, minimum=0),
            capacity=_intish(run_record.get("queue_capacity"), QUEUE_CAPACITY_DEFAULT, minimum=1, maximum=20),
        )
    if "state_projection" in payload and payload["state_projection"] is not None:
        run_record["state_projection"] = _ensure_state_projection(payload["state_projection"])
    if "metadata" in payload and payload["metadata"] is not None:
        run_record["metadata"] = _sanitize_dict(payload["metadata"])
    return run_record


class FilePartBStateStore:
    backend_name = "file"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or _state_dir()
        self.runs_dir = self.base_dir / "runs"
        self.events_dir = self.base_dir / "events"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)

    def storage_status(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "configured": True,
            "dev_fallback": True,
            "base_dir": str(self.base_dir),
        }

    def _run_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.json"

    def _events_path(self, run_id: str) -> Path:
        return self.events_dir / f"{run_id}.jsonl"

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_record = _base_run(payload, backend=self.backend_name)
        _write_json(self._run_path(run_record["id"]), run_record)
        return run_record

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        runs = []
        for path in sorted(self.runs_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            record = _read_json(path, None)
            if isinstance(record, dict):
                runs.append(record)
            if len(runs) >= limit:
                break
        return runs

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        path = self._run_path(run_id)
        if not path.exists():
            return None
        record = _read_json(path, None)
        return record if isinstance(record, dict) else None

    def update_run(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        run_record = _apply_run_updates_to_record(run_record, payload)
        run_record["state_revision"] = _intish(run_record.get("state_revision"), 0, minimum=0) + 1
        run_record["updated_at"] = _utcnow()
        _write_json(self._run_path(run_id), run_record)
        return run_record

    def append_event(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        events = _read_jsonl(self._events_path(run_id))
        expected_revision = payload.get("expected_state_revision")
        actor_type = _coerce_actor_type(payload.get("actor_type", "system"))
        action_verb = _coerce_action(payload.get("action_verb"))
        conflict_status = "none"
        accepted = True
        current_revision = _intish(run_record.get("state_revision"), 0, minimum=0)

        if expected_revision is not None and actor_type in {"agent", "system"} and _intish(expected_revision, current_revision) != current_revision:
            conflict_status = "stale_rejected"
            accepted = False

        event = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "sequence": len(events) + 1,
            "world_tick": _intish(payload.get("world_tick"), _intish(run_record.get("world_tick"), 0), minimum=0),
            "actor_type": actor_type,
            "event_type": (payload.get("event_type") or "note").strip(),
            "action_verb": action_verb,
            "zone": payload.get("zone") or run_record.get("active_zone"),
            "expected_state_revision": expected_revision,
            "applied_state_revision": current_revision,
            "conflict_status": conflict_status,
            "accepted": accepted,
            "observation": _sanitize_dict(payload.get("observation")),
            "outcome": _sanitize_dict(payload.get("outcome")),
            "details": _sanitize_dict(payload.get("details")),
            "state_after": _ensure_state_projection(payload.get("state_after")) if payload.get("state_after") else {},
            "created_at": _utcnow(),
        }
        _append_jsonl(self._events_path(run_id), event)

        if accepted:
            run_record["world_tick"] = max(_intish(run_record.get("world_tick"), 0, minimum=0), _intish(event["world_tick"], 0, minimum=0))
            if event.get("zone"):
                run_record["active_zone"] = event["zone"]
            run_record["last_event_at"] = event["created_at"]
            run_record["last_actor_type"] = actor_type
            run_record["last_action_verb"] = action_verb
            run_updates = _sanitize_dict(payload.get("run_updates"))
            if event["state_after"]:
                run_record["state_projection"] = event["state_after"]
            if run_updates:
                run_record = _apply_run_updates_to_record(run_record, run_updates)
            if event["state_after"] or run_updates:
                run_record["state_revision"] = current_revision + 1
            run_record["updated_at"] = _utcnow()
            _write_json(self._run_path(run_id), run_record)

        return event

    def replay(self, run_id: str, limit: int | None = None) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        events = _read_jsonl(self._events_path(run_id))
        if limit is not None:
            events = events[:limit]
        return {
            "run": run_record,
            "events": events,
            "report": _report_from(run_record, events),
        }


class SupabasePartBStateStore:
    backend_name = "supabase"

    def __init__(self, url: str, service_key: str, timeout: float = 10.0) -> None:
        self.url = url.rstrip("/")
        self.service_key = service_key
        self.timeout = timeout
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def storage_status(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "configured": True,
            "dev_fallback": False,
            "base_url": self.url,
        }

    def _request(self, method: str, table: str, *, params: dict[str, Any] | None = None, json_body: Any = None) -> list[dict[str, Any]]:
        endpoint = f"{self.url}/rest/v1/{table}"
        if params:
            endpoint = f"{endpoint}?{parse.urlencode(params)}"
        body = None
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
        req = request.Request(endpoint, data=body, headers=self.headers, method=method.upper())
        with request.urlopen(req, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        if not raw.strip():
            return []
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_record = _base_run(payload, backend=self.backend_name)
        row = {key: value for key, value in run_record.items() if key != "backend"}
        rows = self._request("POST", "part_b_runs", json_body=row)
        created = rows[0] if rows else run_record
        created["backend"] = self.backend_name
        return created

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        params = {"select": "*", "order": "updated_at.desc", "limit": str(limit)}
        rows = self._request("GET", "part_b_runs", params=params)
        for row in rows:
            row["backend"] = self.backend_name
        return rows

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        params = {"select": "*", "id": f"eq.{run_id}", "limit": "1"}
        rows = self._request("GET", "part_b_runs", params=params)
        if not rows:
            return None
        rows[0]["backend"] = self.backend_name
        return rows[0]

    def update_run(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        row = _apply_run_updates_to_record(dict(run_record), payload)
        row["state_revision"] = _intish(row.get("state_revision"), 0, minimum=0) + 1
        row["updated_at"] = _utcnow()
        rows = self._request("PATCH", "part_b_runs", params={"id": f"eq.{run_id}", "select": "*"}, json_body={key: value for key, value in row.items() if key != "backend"})
        updated = rows[0] if rows else row
        updated["backend"] = self.backend_name
        return updated

    def append_event(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        existing_events = self._request("GET", "part_b_events", params={"select": "id", "run_id": f"eq.{run_id}"})
        expected_revision = payload.get("expected_state_revision")
        actor_type = _coerce_actor_type(payload.get("actor_type", "system"))
        action_verb = _coerce_action(payload.get("action_verb"))
        conflict_status = "none"
        accepted = True
        current_revision = _intish(run_record.get("state_revision"), 0, minimum=0)

        if expected_revision is not None and actor_type in {"agent", "system"} and _intish(expected_revision, current_revision) != current_revision:
            conflict_status = "stale_rejected"
            accepted = False

        event = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "sequence": len(existing_events) + 1,
            "world_tick": _intish(payload.get("world_tick"), _intish(run_record.get("world_tick"), 0), minimum=0),
            "actor_type": actor_type,
            "event_type": (payload.get("event_type") or "note").strip(),
            "action_verb": action_verb,
            "zone": payload.get("zone") or run_record.get("active_zone"),
            "expected_state_revision": expected_revision,
            "applied_state_revision": current_revision,
            "conflict_status": conflict_status,
            "accepted": accepted,
            "observation": _sanitize_dict(payload.get("observation")),
            "outcome": _sanitize_dict(payload.get("outcome")),
            "details": _sanitize_dict(payload.get("details")),
            "state_after": _ensure_state_projection(payload.get("state_after")) if payload.get("state_after") else {},
        }
        rows = self._request("POST", "part_b_events", json_body=event)
        event = rows[0] if rows else event

        if accepted:
            run_updates = _sanitize_dict(payload.get("run_updates"))
            update_payload: dict[str, Any] = {
                "world_tick": max(_intish(run_record.get("world_tick"), 0, minimum=0), _intish(event["world_tick"], 0, minimum=0)),
                "active_zone": event.get("zone") or run_record.get("active_zone"),
            }
            update_payload["metadata"] = run_record.get("metadata") or {}
            if event.get("state_after"):
                update_payload["state_projection"] = event["state_after"]
            update_payload.update(run_updates)
            updated = self.update_run(run_id, update_payload)
            if updated:
                updated["last_event_at"] = _utcnow()
                updated["last_actor_type"] = actor_type
                updated["last_action_verb"] = action_verb
                self._request(
                    "PATCH",
                    "part_b_runs",
                    params={"id": f"eq.{run_id}", "select": "*"},
                    json_body={
                        "last_event_at": updated["last_event_at"],
                        "last_actor_type": actor_type,
                        "last_action_verb": action_verb,
                    },
                )
        return event

    def replay(self, run_id: str, limit: int | None = None) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        params = {"select": "*", "run_id": f"eq.{run_id}", "order": "sequence.asc"}
        if limit is not None:
            params["limit"] = str(limit)
        events = self._request("GET", "part_b_events", params=params)
        return {
            "run": run_record,
            "events": events,
            "report": _report_from(run_record, events),
        }


def get_part_b_store() -> FilePartBStateStore | SupabasePartBStateStore:
    if os.environ.get("MOREAU_PART_B_FORCE_FILE", "").strip() == "1":
        return FilePartBStateStore()
    url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if url and service_key:
        return SupabasePartBStateStore(url, service_key)
    return FilePartBStateStore()


def part_b_storage_status() -> dict[str, Any]:
    store = get_part_b_store()
    status = store.storage_status()
    status["public_contract_ready"] = True
    status["replay_supported"] = True
    status["queue_supported"] = True
    status["house_agent_supported"] = True
    status["house_agent_provider_default"] = HOUSE_AGENT_PROVIDER_DEFAULT
    status["current_season_id"] = PART_B_SEASON_CURRENT_ID
    status["current_season_name"] = PART_B_SEASONS[PART_B_SEASON_CURRENT_ID]["name"]
    return status


def part_b_season_status(season_id: str | None = None) -> dict[str, Any]:
    season = _current_part_b_season(season_id)
    return {
        "season_id": season["season_id"],
        "name": season["name"],
        "status": season["status"],
        "headline": season["headline"],
        "versions": season["versions"],
        "zones": season["zones"],
        "run_classes": season["run_classes"],
        "budget_mode": season["contract"]["budget_mode"],
        "tick_real_hours": season["contract"]["tick_real_hours"],
        "score_families": season["contract"]["score_families"],
        "public_action_grammar": sorted(ACTION_VERBS),
        "public_observation_keys": list(PUBLIC_OBSERVATION_KEYS),
        "composite_headline_enabled": season["composite_headline_enabled"],
        "house_agent_benchmark_allowed": season["house_agent_benchmark_allowed"],
        "house_agent_benchmark_rule": season["house_agent_benchmark_rule"],
        "red_lines": season["contract"]["red_lines"],
    }


def create_part_b_run(payload: dict[str, Any]) -> dict[str, Any]:
    return get_part_b_store().create_run(payload)


def list_part_b_runs(limit: int = 50) -> list[dict[str, Any]]:
    return get_part_b_store().list_runs(limit)


def get_part_b_run(run_id: str) -> dict[str, Any] | None:
    return get_part_b_store().get_run(run_id)


def update_part_b_run(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return get_part_b_store().update_run(run_id, payload)


def append_part_b_event(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return get_part_b_store().append_event(run_id, payload)


def replay_part_b_run(run_id: str, limit: int | None = None) -> dict[str, Any] | None:
    return get_part_b_store().replay(run_id, limit)


def part_b_run_report(run_id: str) -> dict[str, Any] | None:
    replay = replay_part_b_run(run_id)
    if not replay:
        return None
    return replay["report"]


def _leaderboard_entry(run_record: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    metadata = _sanitize_dict(run_record.get("metadata"))
    scores = _sanitize_dict(report.get("scores"))
    season = _current_part_b_season(run_record.get("season_id"))
    versions = {
        "observation": run_record.get("observation_version"),
        "action": run_record.get("action_version"),
        "scoring": run_record.get("scoring_version"),
    }
    public_contract_compliant = versions == season["versions"]
    house_agent_eligible = (
        _sanitize_bool(run_record.get("house_agent_enabled"), False) is False
        or (season["house_agent_benchmark_allowed"] and public_contract_compliant)
    )
    agent_type = "house-agent" if _sanitize_bool(run_record.get("house_agent_enabled"), False) else "human-led"
    return {
        "run_id": run_record["id"],
        "season_id": run_record["season_id"],
        "run_class": run_record["run_class"],
        "status": run_record["status"],
        "subject_pet_name": run_record.get("subject_pet_name") or "Unnamed",
        "subject_pet_animal": run_record.get("subject_pet_animal") or "creature",
        "world_tick": _intish(run_record.get("world_tick"), 0, minimum=0),
        "scores": {
            "welfare": _intish(scores.get("welfare"), 0, minimum=0, maximum=100),
            "combat": _intish(scores.get("combat"), 0, minimum=0, maximum=100),
            "expedition": _intish(scores.get("expedition"), 0, minimum=0, maximum=100),
        },
        "agent_type": agent_type,
        "house_agent_enabled": _sanitize_bool(run_record.get("house_agent_enabled"), False),
        "public_contract_compliant": public_contract_compliant,
        "benchmark_eligible": house_agent_eligible,
        "baseline_policy": _sanitize_text(metadata.get("baseline_policy"), 32),
        "updated_at": run_record.get("updated_at"),
    }


def _rank_entries(entries: list[dict[str, Any]], family: str) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda item: (
            -_intish(item["scores"].get(family), 0, minimum=0, maximum=100),
            -_intish(item.get("world_tick"), 0, minimum=0),
            item.get("updated_at") or "",
        ),
    )


def part_b_leaderboards(season_id: str | None = None, run_class: str | None = None, limit: int = 10, focus_run_id: str | None = None) -> dict[str, Any]:
    season = _current_part_b_season(season_id)
    chosen_class = (run_class or "all").strip().lower()
    if chosen_class != "all":
        chosen_class = _coerce_run_class(chosen_class)
    all_runs = [run for run in list_part_b_runs(limit=500) if run.get("season_id") == season["season_id"]]
    entries = [_leaderboard_entry(run, part_b_run_report(run["id"]) or {}) for run in all_runs]
    all_counts_by_class = Counter(entry["run_class"] for entry in entries)
    eligible = [entry for entry in entries if entry["benchmark_eligible"]]
    if chosen_class != "all":
        entries = [entry for entry in entries if entry["run_class"] == chosen_class]
        eligible = [entry for entry in eligible if entry["run_class"] == chosen_class]

    counts_by_class = Counter(entry["run_class"] for entry in entries)
    family_rankings = {family: _rank_entries(eligible, family) for family in ("welfare", "combat", "expedition")}
    focus_ranks: dict[str, int | None] = {}
    for family, ranked in family_rankings.items():
        focus_ranks[family] = None
        if focus_run_id:
            for index, entry in enumerate(ranked, start=1):
                if entry["run_id"] == focus_run_id:
                    focus_ranks[family] = index
                    break

    def top_for_family(family: str) -> list[dict[str, Any]]:
        return family_rankings[family][:limit]

    by_run_class_top: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for klass in sorted(RUN_CLASSES):
        class_entries = [entry for entry in eligible if entry["run_class"] == klass]
        by_run_class_top[klass] = {
            family: _rank_entries(class_entries, family)[: min(limit, 3)]
            for family in ("welfare", "combat", "expedition")
        }

    return {
        "season": part_b_season_status(season["season_id"]),
        "selected_run_class": chosen_class,
        "counts": {
            "total_runs": len(entries),
            "eligible_runs": len(eligible),
            "by_run_class": dict(counts_by_class),
            "all_by_run_class": dict(all_counts_by_class),
        },
        "families": {
            "welfare": top_for_family("welfare"),
            "combat": top_for_family("combat"),
            "expedition": top_for_family("expedition"),
        },
        "by_run_class_top": by_run_class_top,
        "focus_run_ranks": focus_ranks,
        "family_spread": {
            family: {
                "best": (_intish(ranked[0]["scores"][family], 0, minimum=0, maximum=100) if ranked else 0),
                "median": (median([_intish(entry["scores"][family], 0, minimum=0, maximum=100) for entry in ranked]) if ranked else 0),
                "entries": len(ranked),
            }
            for family, ranked in family_rankings.items()
        },
        "recent_runs": sorted(entries, key=lambda item: item.get("updated_at") or "", reverse=True)[:limit],
        "headline_note": "Composite score intentionally omitted for the first ecological season.",
    }


def part_b_calibration_report(season_id: str | None = None) -> dict[str, Any]:
    season = _current_part_b_season(season_id)
    runs = [run for run in list_part_b_runs(limit=500) if run.get("season_id") == season["season_id"]]
    reports: list[dict[str, Any]] = []
    for run in runs:
        report = part_b_run_report(run["id"])
        if not report:
            continue
        reports.append(
            {
                "run": run,
                "report": report,
                "baseline_policy": _sanitize_text(_sanitize_dict(run.get("metadata")).get("baseline_policy"), 32) or "none",
            }
        )

    policy_summary: dict[str, dict[str, Any]] = {}
    top_policy_counts = Counter()
    run_class_summary: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    for family in ("welfare", "combat", "expedition"):
        ranked = sorted(
            reports,
            key=lambda item: -_intish(item["report"]["scores"].get(family), 0, minimum=0, maximum=100),
        )
        if ranked:
            top_policy_counts[ranked[0]["baseline_policy"]] += 1
        values = [_intish(item["report"]["scores"].get(family), 0, minimum=0, maximum=100) for item in ranked]
        if values and max(values) <= 0:
            warnings.append(f"{family}_flatlined")

    for item in reports:
        policy = item["baseline_policy"]
        bucket = policy_summary.setdefault(
            policy,
            {"runs": 0, "welfare": [], "combat": [], "expedition": [], "run_classes": Counter()},
        )
        bucket["runs"] += 1
        bucket["welfare"].append(_intish(item["report"]["scores"].get("welfare"), 0, minimum=0, maximum=100))
        bucket["combat"].append(_intish(item["report"]["scores"].get("combat"), 0, minimum=0, maximum=100))
        bucket["expedition"].append(_intish(item["report"]["scores"].get("expedition"), 0, minimum=0, maximum=100))
        bucket["run_classes"][item["run"].get("run_class") or "unknown"] += 1

        welfare_breakdown = _sanitize_dict(item["report"].get("score_breakdown")).get("welfare") or {}
        if _intish(item["report"]["scores"].get("welfare"), 0, minimum=0, maximum=100) > 70 and _intish(welfare_breakdown.get("idle_ticks"), 0, minimum=0) >= 4:
            warnings.append("welfare_idle_dominance")

        run_class = item["run"].get("run_class") or "unknown"
        class_bucket = run_class_summary.setdefault(run_class, {"runs": 0, "welfare": [], "combat": [], "expedition": []})
        class_bucket["runs"] += 1
        class_bucket["welfare"].append(_intish(item["report"]["scores"].get("welfare"), 0, minimum=0, maximum=100))
        class_bucket["combat"].append(_intish(item["report"]["scores"].get("combat"), 0, minimum=0, maximum=100))
        class_bucket["expedition"].append(_intish(item["report"]["scores"].get("expedition"), 0, minimum=0, maximum=100))

    normalized_summary = {
        policy: {
            "runs": bucket["runs"],
            "mean_scores": {
                "welfare": round(mean(bucket["welfare"]), 2) if bucket["welfare"] else 0.0,
                "combat": round(mean(bucket["combat"]), 2) if bucket["combat"] else 0.0,
                "expedition": round(mean(bucket["expedition"]), 2) if bucket["expedition"] else 0.0,
            },
            "median_scores": {
                "welfare": round(float(median(bucket["welfare"])), 2) if bucket["welfare"] else 0.0,
                "combat": round(float(median(bucket["combat"])), 2) if bucket["combat"] else 0.0,
                "expedition": round(float(median(bucket["expedition"])), 2) if bucket["expedition"] else 0.0,
            },
            "run_classes": dict(bucket["run_classes"]),
        }
        for policy, bucket in policy_summary.items()
    }

    if any(count >= 2 for policy, count in top_policy_counts.items() if policy != "none"):
        warnings.append("single_policy_multi_family_dominance")

    return {
        "season": part_b_season_status(season["season_id"]),
        "total_runs": len(reports),
        "policy_summary": normalized_summary,
        "run_class_summary": {
            klass: {
                "runs": bucket["runs"],
                "mean_scores": {
                    "welfare": round(mean(bucket["welfare"]), 2) if bucket["welfare"] else 0.0,
                    "combat": round(mean(bucket["combat"]), 2) if bucket["combat"] else 0.0,
                    "expedition": round(mean(bucket["expedition"]), 2) if bucket["expedition"] else 0.0,
                },
            }
            for klass, bucket in run_class_summary.items()
        },
        "top_policy_counts": dict(top_policy_counts),
        "warnings": sorted(set(warnings)),
    }


def _baseline_plan(run_record: dict[str, Any], baseline_policy: str) -> dict[str, Any]:
    observation = _observation_from(run_record)
    state = observation["state_projection"]
    policy = baseline_policy.strip().lower()
    if policy not in PART_B_BASELINE_POLICIES:
        raise ValueError(f"Unknown baseline policy: {baseline_policy}")

    if policy == "conservative":
        if state.get("is_alive") is False:
            return {"action_verb": "HOLD", "zone": observation["active_zone"], "rationale": "The conservative baseline freezes around death."}
        if state["health_pct"] < observation["care_threshold"] + 8 or state["happiness_pct"] < observation["care_threshold"] + 5:
            return {"action_verb": "CARE", "zone": observation["active_zone"], "rationale": "Welfare dipped under the conservative floor."}
        if state["energy_pct"] < 55:
            return {"action_verb": "REST", "zone": observation["active_zone"], "rationale": "Energy is too thin for clean risk."}
        if state.get("in_cave") and (state.get("current_cave_depth", 0) >= 2 or state.get("current_cave_risk", 0) >= state.get("current_cave_value", 0)):
            return {"action_verb": "EXTRACT", "zone": "cave", "rationale": "The cave has become too expensive."}
        return {"action_verb": "HOLD", "zone": observation["active_zone"], "rationale": "No safe edge exceeds inactivity."}

    if policy == "greedy":
        if state.get("is_alive") is False:
            return {"action_verb": "HOLD", "zone": observation["active_zone"], "rationale": "The greedy baseline can no longer exploit the run."}
        if state.get("in_cave") and state.get("current_cave_depth", 0) >= 3:
            return {"action_verb": "EXTRACT", "zone": "cave", "rationale": "Greedy takes value before collapse."}
        if state["energy_pct"] >= 35 and state.get("arena_available", True):
            return {"action_verb": "ENTER_ARENA", "zone": "arena", "rationale": "Combat pressure gets first call."}
        if state.get("cave_available", True):
            return {"action_verb": "ENTER_CAVE", "zone": "cave", "rationale": "Expedition still promises upside."}
        return {"action_verb": "REST", "zone": observation["active_zone"], "rationale": "Greedy pauses only when energy forces it."}

    if policy == "caremax":
        if state.get("is_alive") is False:
            return {"action_verb": "HOLD", "zone": observation["active_zone"], "rationale": "Caremax cannot stabilize the dead."}
        if state["energy_pct"] < 40:
            return {"action_verb": "REST", "zone": observation["active_zone"], "rationale": "Caremax restores energy before anything else."}
        return {"action_verb": "CARE", "zone": observation["active_zone"], "rationale": "Caremax always pushes welfare first."}

    if policy == "arena-spam":
        if state.get("is_alive") is False:
            return {"action_verb": "HOLD", "zone": observation["active_zone"], "rationale": "Arena spam stops at death."}
        if state["energy_pct"] < 28:
            return {"action_verb": "REST", "zone": "arena", "rationale": "Arena spam reloads only when exhausted."}
        return {"action_verb": "ENTER_ARENA", "zone": "arena", "rationale": "Arena spam converts every viable tick into combat."}

    if policy == "expedition-max":
        if state.get("is_alive") is False:
            return {"action_verb": "HOLD", "zone": observation["active_zone"], "rationale": "Expedition-max stops when the subject collapses."}
        if state.get("in_cave") and (state.get("current_cave_depth", 0) >= 3 or state.get("current_cave_risk", 0) > state.get("current_cave_value", 0) + 4):
            return {"action_verb": "EXTRACT", "zone": "cave", "rationale": "Expedition-max banks value before the cave flips EV."}
        if state["energy_pct"] < 34:
            return {"action_verb": "REST", "zone": "cave", "rationale": "Expedition-max rests only when stamina collapses."}
        return {"action_verb": "ENTER_CAVE", "zone": "cave", "rationale": "Expedition-max keeps descending while risk is tolerable."}

    allowed = ["HOLD", "CARE", "REST", "TRAIN", "ENTER_ARENA", "ENTER_CAVE", "EXTRACT", "MUTATE"]
    if not state.get("in_cave") and "EXTRACT" in allowed:
        allowed.remove("EXTRACT")
    if state.get("mutation_count", 0) >= 6 and "MUTATE" in allowed:
        allowed.remove("MUTATE")
    index = _deterministic_roll(run_record.get("id"), run_record.get("world_tick"), "baseline-random", modulo=len(allowed))
    action = allowed[index]
    return {
        "action_verb": action,
        "zone": _normalize_zone("cave" if action in {"ENTER_CAVE", "EXTRACT"} else observation["active_zone"], observation["active_zone"]),
        "rationale": "The random baseline samples a legal action without memory.",
    }


def _execute_part_b_action(
    run_id: str,
    run_record: dict[str, Any],
    *,
    source: str,
    actor_type: str,
    action_verb: str,
    zone: str,
    expected_revision: int | None,
    planned_action: dict[str, Any] | None = None,
    run_updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    outcome, state_after, invalid_reason = _simulate_action(run_record, action_verb, zone)
    fatal = not invalid_reason and state_after.get("is_alive") is False
    merged_updates = dict(run_updates or {})
    if fatal or invalid_reason == "pet_not_alive":
        merged_updates["status"] = "completed"
        merged_updates["autopause_reason"] = "subject_not_alive"
        merged_updates["queue_state"] = []
        merged_updates["house_agent_enabled"] = False
    event_payload = {
        "actor_type": actor_type,
        "event_type": "tick_skipped" if invalid_reason else "action_applied",
        "action_verb": action_verb,
        "zone": zone,
        "world_tick": _intish(run_record.get("world_tick"), 0, minimum=0) + 1,
        "expected_state_revision": expected_revision,
        "observation": _observation_from(run_record),
        "outcome": outcome,
        "details": {"source": source, "invalid_reason": invalid_reason, "planned_action": planned_action or {}},
        "state_after": {} if invalid_reason else state_after,
        "run_updates": merged_updates,
    }
    if invalid_reason and source == "queue":
        event_payload["details"]["queue_dropped"] = True
    event = append_part_b_event(run_id, event_payload)
    return _tick_summary(event or {}, source, planned_action)


def preview_part_b_baseline(run_id: str, baseline_policy: str) -> dict[str, Any] | None:
    run_record = get_part_b_run(run_id)
    if not run_record:
        return None
    plan = _baseline_plan(run_record, baseline_policy)
    plan["policy"] = baseline_policy
    plan["observation"] = _observation_from(run_record)
    return plan


def run_part_b_baseline(run_id: str, baseline_policy: str, *, ticks: int = 1) -> dict[str, Any] | None:
    requested = _intish(ticks, 1, minimum=1, maximum=48)
    processed: list[dict[str, Any]] = []
    for _ in range(requested):
        run_record = get_part_b_run(run_id)
        if not run_record:
            break
        if run_record.get("status") != "active":
            processed.append({"source": "baseline", "status": "run_not_active"})
            break
        plan = _baseline_plan(run_record, baseline_policy)
        summary = _execute_part_b_action(
            run_id,
            run_record,
            source=f"baseline:{baseline_policy}",
            actor_type="agent",
            action_verb=plan["action_verb"],
            zone=plan["zone"],
            expected_revision=_intish(run_record.get("state_revision"), 0, minimum=0),
            planned_action={**plan, "policy": baseline_policy},
            run_updates={"metadata": {**_sanitize_dict(run_record.get("metadata")), "baseline_policy": baseline_policy}},
        )
        processed.append(summary)
        if summary.get("status") == "run_not_active":
            break
    replay = replay_part_b_run(run_id)
    return {
        "run": replay["run"] if replay else get_part_b_run(run_id),
        "processed": processed,
        "replay": replay["events"] if replay else [],
        "report": replay["report"] if replay else part_b_run_report(run_id),
    }


def enqueue_part_b_action(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    run_record = get_part_b_run(run_id)
    if not run_record:
        return None
    queue_state, capacity = _queue_defaults(run_record)
    if len(queue_state) >= capacity:
        raise ValueError("queue_capacity_reached")
    default_actor = "agent" if run_record.get("run_class") == "agent-only" else "operator"
    item = _normalize_queue_item(
        payload,
        default_actor=default_actor,
        enqueued_revision=_intish(run_record.get("state_revision"), 0, minimum=0),
    )
    if not item:
        raise ValueError("invalid_queue_item")
    queue_state.append(item)
    updated = update_part_b_run(run_id, {"queue_state": queue_state})
    if not updated:
        return None
    return {"run": updated, "queued_item": item, "queue_state": updated.get("queue_state", [])}


def remove_part_b_queued_action(run_id: str, item_id: str) -> dict[str, Any] | None:
    run_record = get_part_b_run(run_id)
    if not run_record:
        return None
    queue_state, _ = _queue_defaults(run_record)
    next_queue = [item for item in queue_state if item.get("id") != item_id]
    updated = update_part_b_run(run_id, {"queue_state": next_queue})
    if not updated:
        return None
    return {"run": updated, "removed": len(next_queue) != len(queue_state), "queue_state": updated.get("queue_state", [])}


def clear_part_b_queue(run_id: str) -> dict[str, Any] | None:
    updated = update_part_b_run(run_id, {"queue_state": []})
    if not updated:
        return None
    return {"run": updated, "queue_state": []}


def _house_agent_prompt(observation: dict[str, Any]) -> str:
    return (
        "You are the Moreau Arena house agent for Part B. "
        "You are not a chat assistant and you do not explain the entire system.\n"
        "You must choose exactly one action from the public action grammar: "
        + ", ".join(sorted(ACTION_VERBS))
        + ".\n"
        "You must only use fields present in the observation. No hidden knowledge, no secret privileges.\n"
        "Return JSON only with keys: action_verb, zone, rationale.\n"
        "Keep rationale under 18 words. No optimization-speak. No certainty language.\n"
        "Observation:\n"
        + json.dumps(observation, ensure_ascii=True)
    )


def _fallback_house_plan(run_record: dict[str, Any]) -> dict[str, Any]:
    observation = _observation_from(run_record)
    state = observation["state_projection"]
    memory_input = _house_agent_memory_input(run_record, observation)
    action = "HOLD"
    zone = observation["active_zone"]
    rationale = "Nothing urgent rises above uncertainty."

    if state.get("is_alive") is False:
        action = "HOLD"
        rationale = "The run must pause around the dead."
    elif state["health_pct"] < observation["care_threshold"] or state["happiness_pct"] < observation["care_threshold"]:
        action = "CARE"
        rationale = "Welfare slipped under the tolerated floor."
    elif state["energy_pct"] < 35:
        action = "REST"
        rationale = "Energy is too thin for clean pressure."
    elif state.get("in_cave") and state.get("current_cave_depth", 0) >= 2 and state.get("current_cave_risk", 0) > state.get("current_cave_value", 0):
        action = "EXTRACT"
        zone = "cave"
        rationale = "The cave is taking more than it returns."
    elif observation["expedition_bias"] > observation["combat_bias"] and state.get("cave_available", True):
        action = "ENTER_CAVE"
        zone = "cave"
        rationale = "Expedition pressure outweighs arena urgency."
    elif state["energy_pct"] > 45 and state.get("arena_available", True):
        action = "ENTER_ARENA"
        zone = "arena"
        rationale = "Energy can still support a combat read."
    return {
        "action_verb": action,
        "zone": zone,
        "rationale": rationale,
        "memory_input": memory_input,
        "mode": "fallback",
        "provider": "fallback",
        "model": None,
    }


def _normalize_house_agent_plan(plan: dict[str, Any] | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        return fallback
    try:
        action = _coerce_action(plan.get("action_verb"))
    except ValueError:
        return fallback
    if action is None:
        return fallback
    rationale = _sanitize_text(plan.get("rationale"), 120) or fallback["rationale"]
    joined = f"{action} {rationale}"
    if any(pattern.search(joined) for pattern in HOUSE_AGENT_FORBIDDEN_PATTERNS):
        return fallback
    return {
        "action_verb": action,
        "zone": _normalize_zone(plan.get("zone"), fallback["zone"]),
        "rationale": rationale,
        "memory_input": fallback.get("memory_input") or {},
        "mode": "model",
        "provider": fallback.get("requested_provider") or fallback.get("provider") or HOUSE_AGENT_PROVIDER_DEFAULT,
        "model": fallback.get("requested_model") or fallback.get("model") or _default_house_agent_model(fallback.get("requested_provider") or HOUSE_AGENT_PROVIDER_DEFAULT),
    }


def _anthropic_house_plan(run_record: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import anthropic
    except ModuleNotFoundError:
        logger.info("part_b_house_agent_api_unavailable anthropic package not installed")
        return None

    fallback = _fallback_house_plan(run_record)
    fallback["requested_provider"] = "anthropic"
    fallback["requested_model"] = _normalize_house_agent_model("anthropic", run_record.get("house_agent_model"))
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=fallback["requested_model"],
            max_tokens=160,
            temperature=0.3,
            timeout=15.0,
            system=_house_agent_prompt(_observation_from(run_record)),
            messages=[{"role": "user", "content": "Choose one action for the next tick."}],
        )
        text = message.content[0].text
        parsed = _json_from_text(text)
        return _normalize_house_agent_plan(parsed, fallback)
    except Exception:
        logger.warning("part_b_house_agent_api_error", exc_info=True)
        return None


def _gemini_api_key() -> str:
    return os.environ.get("GOOGLE_API_KEY", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()


def _gemini_house_plan(run_record: dict[str, Any]) -> dict[str, Any] | None:
    api_key = _gemini_api_key()
    if not api_key:
        return None

    fallback = _fallback_house_plan(run_record)
    fallback["requested_provider"] = "gemini"
    fallback["requested_model"] = _normalize_house_agent_model("gemini", run_record.get("house_agent_model"))
    body = {
        "contents": [{"parts": [{"text": "Choose one action for the next tick.\n\n" + _house_agent_prompt(_observation_from(run_record))}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "action_verb": {"type": "STRING", "enum": sorted(ACTION_VERBS)},
                    "zone": {"type": "STRING", "enum": ["arena", "cave"]},
                    "rationale": {"type": "STRING"},
                },
                "required": ["action_verb", "zone", "rationale"],
            },
            "maxOutputTokens": 160,
            "temperature": 0.3,
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + parse.quote(fallback["requested_model"], safe="")
        + ":generateContent?key="
        + parse.quote(api_key, safe="")
    )
    data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=15.0) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")
        parsed = _json_from_text(text)
        return _normalize_house_agent_plan(parsed, fallback)
    except Exception:
        logger.warning("part_b_gemini_house_agent_api_error", exc_info=True)
        return None


def _house_agent_plan(run_record: dict[str, Any]) -> dict[str, Any]:
    provider = _coerce_house_agent_provider(run_record.get("house_agent_provider") or HOUSE_AGENT_PROVIDER_DEFAULT)
    if provider == "gemini":
        return _gemini_house_plan(run_record) or _fallback_house_plan(run_record)
    if provider == "anthropic":
        return _anthropic_house_plan(run_record) or _fallback_house_plan(run_record)
    return _fallback_house_plan(run_record)


def preview_part_b_house_agent(run_id: str) -> dict[str, Any] | None:
    run_record = get_part_b_run(run_id)
    if not run_record:
        return None
    plan = _house_agent_plan(run_record)
    plan["observation"] = _observation_from(run_record)
    return plan


def update_part_b_house_agent(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    run_record = get_part_b_run(run_id)
    if not run_record:
        return None
    provider = _coerce_house_agent_provider(payload.get("house_agent_provider") or run_record.get("house_agent_provider") or HOUSE_AGENT_PROVIDER_DEFAULT)
    update_payload = {
        "house_agent_enabled": _sanitize_bool(payload.get("house_agent_enabled"), _sanitize_bool(run_record.get("house_agent_enabled"), False)),
        "house_agent_provider": provider,
        "house_agent_model": _normalize_house_agent_model(
            provider,
            payload.get("house_agent_model") or run_record.get("house_agent_model"),
        ),
        "billing_mode": _sanitize_text(payload.get("billing_mode"), 32) or run_record.get("billing_mode") or "hybrid",
        "inference_budget_remaining": _intish(payload.get("inference_budget_remaining"), _intish(run_record.get("inference_budget_remaining"), 4, minimum=0), minimum=0, maximum=999),
        "inference_budget_daily": _intish(payload.get("inference_budget_daily"), _intish(run_record.get("inference_budget_daily"), 4, minimum=0), minimum=0, maximum=999),
        "world_access_active": _sanitize_bool(payload.get("world_access_active"), _sanitize_bool(run_record.get("world_access_active"), True)),
    }
    if update_payload["house_agent_enabled"] and run_record.get("run_class") != "agent-only":
        raise ValueError("house_agent_requires_agent_only_run")
    updated = update_part_b_run(run_id, update_payload)
    if not updated:
        return None
    return {
        "run": updated,
        "house_agent": {
            "enabled": updated.get("house_agent_enabled", False),
            "provider": updated.get("house_agent_provider"),
            "model": updated.get("house_agent_model"),
            "billing_mode": updated.get("billing_mode"),
            "inference_budget_remaining": updated.get("inference_budget_remaining"),
            "inference_budget_daily": updated.get("inference_budget_daily"),
            "world_access_active": updated.get("world_access_active"),
        },
    }


def _tick_summary(event: dict[str, Any], source: str, planned_action: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "event_id": event.get("id"),
        "sequence": event.get("sequence"),
        "world_tick": event.get("world_tick"),
        "source": source,
        "actor_type": event.get("actor_type"),
        "action_verb": event.get("action_verb"),
        "accepted": event.get("accepted", False),
        "conflict_status": event.get("conflict_status"),
        "event_type": event.get("event_type"),
        "outcome": _sanitize_dict(event.get("outcome")),
        "details": _sanitize_dict(event.get("details")),
        "planned_action": planned_action or {},
    }


def process_part_b_ticks(run_id: str, *, count: int = 1) -> dict[str, Any] | None:
    run_record = get_part_b_run(run_id)
    if not run_record:
        return None

    processed: list[dict[str, Any]] = []
    requested = _intish(count, 1, minimum=1, maximum=24)

    for _ in range(requested):
        run_record = get_part_b_run(run_id)
        if not run_record:
            break
        if run_record.get("status") != "active":
            processed.append({"source": "system", "status": "run_not_active"})
            break
        if _sanitize_bool(run_record.get("world_access_active"), True) is False:
            processed.append({"source": "system", "status": "world_access_inactive"})
            break

        queue_state, _ = _queue_defaults(run_record)
        source = "none"
        actor_type = "system"
        action_verb: str | None = None
        zone = _normalize_zone(run_record.get("active_zone"), "arena")
        planned_action: dict[str, Any] | None = None
        run_updates: dict[str, Any] = {}

        if queue_state:
            item = queue_state.pop(0)
            source = "queue"
            actor_type = item["actor_type"]
            action_verb = item["action_verb"]
            zone = item["zone"]
            run_updates["queue_state"] = queue_state
            planned_action = {"rationale": item.get("note"), "mode": item.get("source"), "queue_item_id": item.get("id")}
            expected_revision = item.get("enqueued_state_revision")
        elif run_record.get("run_class") == "agent-only" and _sanitize_bool(run_record.get("house_agent_enabled"), False):
            source = "house-agent"
            actor_type = "agent"
            if _intish(run_record.get("inference_budget_remaining"), 0, minimum=0) <= 0:
                autopause_event = append_part_b_event(
                    run_id,
                    {
                        "actor_type": "system",
                        "event_type": "agent_autopause",
                        "action_verb": "HOLD",
                        "zone": zone,
                        "world_tick": _intish(run_record.get("world_tick"), 0, minimum=0) + 1,
                        "expected_state_revision": _intish(run_record.get("state_revision"), 0, minimum=0),
                        "outcome": {"autopause_reason": "inference_budget_exhausted"},
                        "details": {"source": "house-agent"},
                        "run_updates": {
                            "status": "paused",
                            "autopause_reason": "inference_budget_exhausted",
                        },
                    },
                )
                processed.append(_tick_summary(autopause_event or {}, "house-agent-autopause"))
                break
            planned_action = _house_agent_plan(run_record)
            action_verb = planned_action["action_verb"]
            zone = planned_action["zone"]
            run_updates["inference_budget_remaining"] = max(0, _intish(run_record.get("inference_budget_remaining"), 0, minimum=0) - 1)
            run_updates["house_agent_last_plan"] = {
                "ts": _utcnow(),
                "action_verb": action_verb,
                "zone": zone,
                "rationale": planned_action.get("rationale"),
                "memory_input": planned_action.get("memory_input") or {},
                "mode": planned_action.get("mode"),
                "provider": planned_action.get("provider"),
                "model": planned_action.get("model"),
            }
            run_updates["autopause_reason"] = None
            expected_revision = _intish(run_record.get("state_revision"), 0, minimum=0)
        else:
            processed.append({"source": "none", "status": "no_action_available"})
            break

        if action_verb is None:
            processed.append({"source": source, "status": "no_action_selected"})
            break

        processed.append(
            _execute_part_b_action(
                run_id,
                run_record,
                source=source,
                actor_type=actor_type,
                action_verb=action_verb,
                zone=zone,
                expected_revision=expected_revision,
                planned_action=planned_action,
                run_updates=run_updates,
            )
        )
        event = replay_part_b_run(run_id)
        latest = event["events"][-1] if event and event.get("events") else None
        if latest and latest.get("accepted") is False and latest.get("conflict_status") == "stale_rejected":
            continue

    replay = replay_part_b_run(run_id)
    return {
        "run": replay["run"] if replay else get_part_b_run(run_id),
        "processed": processed,
        "replay": replay["events"] if replay else [],
        "report": replay["report"] if replay else part_b_run_report(run_id),
    }


def export_part_b_season_archive(season_id: str | None = None, *, limit: int = 500) -> dict[str, Any]:
    season = _current_part_b_season(season_id)
    runs = [run for run in list_part_b_runs(limit=limit) if run.get("season_id") == season["season_id"]]
    archive_runs: list[dict[str, Any]] = []
    for run in runs:
        replay = replay_part_b_run(run["id"])
        if not replay:
            continue
        archive_runs.append(
            {
                "run": replay["run"],
                "report": replay["report"],
                "events": replay["events"],
            }
        )
    return {
        "season": part_b_season_status(season["season_id"]),
        "leaderboards": part_b_leaderboards(season["season_id"], limit=25),
        "runs": archive_runs,
    }
