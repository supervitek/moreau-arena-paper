from __future__ import annotations

import json
import logging
import os
import re
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger("moreau-chronicler")

ALLOWED_ACTIONS = {
    "none",
    "train",
    "caretaker",
    "lab",
    "dreams",
    "prophecy",
    "pact",
    "rivals",
    "tides",
    "deep_tide",
    "profile",
    "menagerie",
}

INTERPRETIVE_ACTIONS = {"dreams", "prophecy", "pact", "profile", "menagerie", "tides", "deep_tide"}

_COST_LOCK = threading.Lock()
_SUGGESTION_LOCK = threading.Lock()
_RECENT_RUNS: deque[dict[str, Any]] = deque(maxlen=300)
_RECENT_EVENTS: deque[dict[str, Any]] = deque(maxlen=1000)
_DAILY_COST_TRACKER = {"date": "", "usd": 0.0}
_SUGGESTION_TRACKER: dict[str, dict[str, int]] = {}
FORBIDDEN_RESPONSE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bhere are\b",
        r"\bbased on your current stats\b",
        r"\bi suggest optimiz",
        r"\byou should definitely\b",
        r"\bkey metrics\b",
        r"\bmaximize\b",
        r"\bas an ai assistant\b",
        r"\bgreat job\b",
    ]
]


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_cost_if_needed() -> None:
    today = _today_key()
    if _DAILY_COST_TRACKER["date"] != today:
        _DAILY_COST_TRACKER["date"] = today
        _DAILY_COST_TRACKER["usd"] = 0.0


def get_daily_cost_cap_usd() -> float:
    try:
        return max(0.0, float(os.environ.get("MOREAU_CHRONICLER_DAILY_CAP_USD", "5.0")))
    except ValueError:
        return 5.0


def get_estimated_model_call_cost_usd() -> float:
    try:
        return max(0.0, float(os.environ.get("MOREAU_CHRONICLER_ESTIMATED_CALL_USD", "0.003")))
    except ValueError:
        return 0.003


def is_chronicler_enabled() -> bool:
    return os.environ.get("MOREAU_ENABLE_CHRONICLER", "1").strip().lower() not in {"0", "false", "off", "no"}


def reserve_cost(amount: float) -> bool:
    with _COST_LOCK:
        _reset_cost_if_needed()
        if _DAILY_COST_TRACKER["usd"] + amount > get_daily_cost_cap_usd():
            return False
        _DAILY_COST_TRACKER["usd"] += amount
        return True


def refund_cost(amount: float) -> None:
    with _COST_LOCK:
        _reset_cost_if_needed()
        _DAILY_COST_TRACKER["usd"] = max(0.0, _DAILY_COST_TRACKER["usd"] - amount)


def current_cost_snapshot() -> dict[str, Any]:
    with _COST_LOCK:
        _reset_cost_if_needed()
        return {
            "date": _DAILY_COST_TRACKER["date"],
            "usd_spent": round(_DAILY_COST_TRACKER["usd"], 6),
            "usd_cap": get_daily_cost_cap_usd(),
        }


def _truncate_text(value: Any, limit: int = 180) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[: limit - 1] + "…" if len(text) > limit else text


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_action(value: Any) -> str:
    action = str(value or "none").strip().lower().replace("-", "_")
    return action if action in ALLOWED_ACTIONS else "none"


def _normalize_result(value: Any) -> str:
    result = str(value or "").strip().lower()
    return result if result in {"win", "loss", "draw"} else "unknown"


def build_context(payload: dict[str, Any]) -> dict[str, Any]:
    active_pet = payload.get("active_pet") or {}
    if not isinstance(active_pet, dict):
        active_pet = {}

    recent_fights_raw = payload.get("recent_fights") or []
    recent_fights: list[dict[str, Any]] = []
    if isinstance(recent_fights_raw, list):
        for fight in recent_fights_raw[:3]:
            if not isinstance(fight, dict):
                continue
            recent_fights.append(
                {
                    "opponent": _truncate_text(fight.get("opponent"), 40) or "unknown foe",
                    "result": _normalize_result(fight.get("result")),
                    "ticks": _safe_int(fight.get("ticks"), 0),
                }
            )

    available_actions = []
    payload_actions = payload.get("available_actions") or []
    if isinstance(payload_actions, list):
        available_actions = sorted({_normalize_action(action) for action in payload_actions})

    context = {
        "route": "/island/home",
        "session_id": _truncate_text(payload.get("session_id"), 64) or "unknown-session",
        "offline_mode": bool(payload.get("offline_mode")),
        "pet": {
            "name": _truncate_text(active_pet.get("name"), 32) or "the creature",
            "animal": _truncate_text(active_pet.get("animal"), 24) or "creature",
            "level": _safe_int(active_pet.get("level"), 1),
            "mood": _truncate_text(active_pet.get("mood"), 24) or "unknown",
            "corruption": _safe_int(active_pet.get("corruption"), 0),
            "instability": _safe_int(active_pet.get("instability"), 0),
            "mutations": [str(m) for m in (active_pet.get("mutations") or [])[:3]],
            "is_dead": bool(active_pet.get("deceased")) or active_pet.get("is_alive") is False,
        },
        "recent_fights": recent_fights,
        "recent_dream": _truncate_text(payload.get("recent_dream"), 180),
        "recent_confession": _truncate_text(payload.get("recent_confession"), 180),
        "dream_unread": max(0, _safe_int(payload.get("dream_unread"), 0)),
        "confession_count": max(0, _safe_int(payload.get("confession_count"), 0)),
        "can_mutate": bool(payload.get("can_mutate")),
        "rival_available": bool(payload.get("rival_available")),
        "has_feral": bool(payload.get("has_feral")),
        "has_pact": bool(payload.get("has_pact")),
        "available_actions": available_actions,
        "interpretive_actions_available": [action for action in available_actions if action in INTERPRETIVE_ACTIONS],
    }
    return context


def _fallback_reading(context: dict[str, Any]) -> dict[str, Any]:
    pet = context["pet"]
    fights = context["recent_fights"]
    wins = sum(1 for fight in fights if fight["result"] == "win")
    losses = sum(1 for fight in fights if fight["result"] == "loss")
    dream_unread = context["dream_unread"]
    corruption = pet["corruption"]
    instability = pet["instability"]
    mood = pet["mood"]
    can_mutate = context["can_mutate"]
    actions = set(context["available_actions"])

    observation = "The room is quiet enough to hear a pattern if you do not rush it."
    prompt = "What are you treating as strength that may only be momentum?"
    suggestion = None
    suggested_action = "none"
    uncertainty = "I would not swear to it."

    if pet["is_dead"]:
        observation = f"{pet['name']} is beyond counsel now; only the shape of the absence remains."
        prompt = "Look to the living before you ask the room for more."
        uncertainty = "This is warning, not wisdom."
    elif dream_unread > 0 and "dreams" in actions:
        observation = f"{pet['name']} has left sleep unread, and the Island rarely repeats itself for kindness."
        prompt = "Will you ignore the dream because the waking record looks cleaner?"
        suggestion = "Read the dream before you decide what tonight means."
        suggested_action = "dreams"
        uncertainty = "It may mean nothing, but repeated sleep should not be ignored."
    elif corruption >= 70 and "tides" in actions:
        observation = f"Corruption has become part of {pet['name']}'s silhouette; it is no longer incidental."
        prompt = "If you push deeper now, are you choosing power or simply refusing to stop?"
        suggestion = "The Tides may cool what the Lab would only sharpen."
        suggested_action = "tides"
        uncertainty = "Take this as warning, not law."
    elif context["has_feral"] and "pact" in actions:
        observation = "One of your bonds is fraying badly enough to be heard from the next room."
        prompt = "Do you mean to govern the bond, or merely survive it?"
        suggestion = "The Pact deserves attention before another clean statistic turns ugly."
        suggested_action = "pact"
        uncertainty = "The pattern may be lying, but I mistrust grief left unattended."
    elif losses >= 2 and "caretaker" in actions:
        observation = f"{pet['name']} has been struck often enough that the record now smells of strain, not chance."
        prompt = "What has the arena been taking that the numbers do not name?"
        suggestion = "The Caretaker may see what the fight log refuses to admit."
        suggested_action = "caretaker"
        uncertainty = "Perhaps I am reading wear where there is only weather."
    elif can_mutate and "lab" in actions:
        observation = "The Lab is ready, but readiness is not permission."
        prompt = "Are you seeking transformation, or only trying to outrun a slower doubt?"
        suggestion = "If you enter, enter with doubt still intact."
        suggested_action = "lab"
        uncertainty = "I could be reading too much into the timing."
    elif wins >= 2 and "rivals" in actions and context["rival_available"]:
        observation = f"{pet['name']} is winning cleanly enough that the next honest measure may need teeth."
        prompt = "Do you trust the streak, or do you want it tested?"
        suggestion = "A rival would tell you more than another soft victory."
        suggested_action = "rivals"
        uncertainty = "Perhaps the streak is genuine. I have seen easier lies."
    elif mood in {"tired", "angry"} and "profile" in actions:
        observation = f"{pet['name']} does not look settled; the mood and the record are pulling in different directions."
        prompt = "When did you last look at the creature as more than a sequence of outcomes?"
        suggestion = "Read the dossier before you decide what the next demand should be."
        suggested_action = "profile"
        uncertainty = "It may only be fatigue speaking."
    elif context["confession_count"] >= 3 and "prophecy" in actions:
        observation = "There is enough unspoken residue here that even a false omen might be useful."
        prompt = "What if the next sign is not meant to clarify, but to embarrass certainty?"
        suggestion = "Seek prophecy only if you can survive being misled."
        suggested_action = "prophecy"
        uncertainty = "I mistrust prophecy more than silence, but not by much."
    elif instability >= 50 and "menagerie" in actions:
        observation = f"Instability has started to sound like inheritance."
        prompt = "If this creature breaks, what remains with you?"
        suggestion = "The Menagerie remembers what the Lab discards."
        suggested_action = "menagerie"
        uncertainty = "Perhaps that is too grave a reading for tonight."

    return {
        "observation": observation,
        "prompt": prompt,
        "suggestion": suggestion,
        "suggested_action": suggested_action,
        "uncertainty": uncertainty,
        "mode": "fallback",
        "cost_estimate_usd": 0.0,
    }


def _apply_suggestion_budget(context: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if result.get("suggested_action") in {None, "none"}:
        return result

    budget_key = f"{_today_key()}::{context['session_id']}::{context['pet']['name']}"
    with _SUGGESTION_LOCK:
        bucket = _SUGGESTION_TRACKER.get(budget_key, {"calls": 0, "suggestions": 0})
        bucket["calls"] += 1

        allow_suggestion = bucket["suggestions"] < 2 and (bucket["calls"] % 3 == 1)
        if allow_suggestion:
            bucket["suggestions"] += 1
            _SUGGESTION_TRACKER[budget_key] = bucket
            return result

        _SUGGESTION_TRACKER[budget_key] = bucket

    throttled = dict(result)
    throttled["suggestion"] = None
    throttled["suggested_action"] = "none"
    throttled["uncertainty"] = "I would not make law from a repeated whisper."
    return throttled


def _json_from_text(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        return None
    try:
        candidate = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(candidate, dict):
        return None
    return candidate


def _normalize_model_output(raw: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    observation = _truncate_text(raw.get("observation"), 180) or fallback["observation"]
    prompt = _truncate_text(raw.get("prompt"), 180) or fallback["prompt"]
    suggestion = _truncate_text(raw.get("suggestion"), 180)
    uncertainty = _truncate_text(raw.get("uncertainty"), 120) or fallback["uncertainty"]
    suggested_action = _normalize_action(raw.get("suggested_action"))
    joined = " ".join(part for part in [observation, prompt, suggestion or "", uncertainty] if part)
    if any(pattern.search(joined) for pattern in FORBIDDEN_RESPONSE_PATTERNS):
        return fallback
    if suggested_action != "none" and suggestion is None:
        suggested_action = "none"
    return {
        "observation": observation,
        "prompt": prompt,
        "suggestion": suggestion,
        "suggested_action": suggested_action,
        "uncertainty": uncertainty,
        "mode": "model",
        "cost_estimate_usd": get_estimated_model_call_cost_usd(),
    }


def _build_model_prompt(context: dict[str, Any]) -> str:
    return (
        "You are Chronicler in Moreau Arena. You are not a helpful AI assistant.\n"
        "You speak as a diegetic observer of signs, moods, corruption, and repeated patterns.\n"
        "You must stay brief, concrete, and state-aware.\n"
        "You must not use optimization language, dashboard language, or certainty language.\n"
        "Forbidden phrases include: 'Here are', 'Based on your current stats', 'I suggest optimizing', "
        "'You should definitely', 'key metrics', 'maximize', 'Great job'.\n"
        "You must be fallible through character limits, not random nonsense.\n"
        "Good uncertainty markers include: 'I would not swear to it', 'Take this as warning, not law', "
        "'It may mean nothing, but', 'I mistrust the timing'.\n"
        "Return valid JSON only with keys: observation, prompt, suggestion, suggested_action, uncertainty.\n"
        "Keep observation/prompt/suggestion short. suggestion may be null. suggested_action must be one of: "
        + ", ".join(sorted(ALLOWED_ACTIONS))
        + ".\n"
        "Use uncertainty markers like 'I would not swear to it' or 'Take this as warning, not law.'\n"
        "Context:\n"
        + json.dumps(context, ensure_ascii=True)
    )


def _generate_model_reading(context: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    estimated_cost = get_estimated_model_call_cost_usd()
    if not reserve_cost(estimated_cost):
        return {
            "observation": "The room would speak more freely if it were cheaper to keep alive.",
            "prompt": "For now, you will have to read the signs with your own eyes.",
            "suggestion": None,
            "suggested_action": "none",
            "uncertainty": "The budget is a kind of weather too.",
            "mode": "budget_cap",
            "cost_estimate_usd": 0.0,
        }

    try:
        import anthropic
    except ModuleNotFoundError:
        logger.info("chronicler_api_unavailable anthropic package not installed")
        refund_cost(estimated_cost)
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.environ.get("MOREAU_CHRONICLER_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=220,
            temperature=0.7,
            timeout=15.0,
            system=_build_model_prompt(context),
            messages=[{"role": "user", "content": "Read the room."}],
        )
        text = message.content[0].text
        parsed = _json_from_text(text)
        if not parsed:
            return None
        return _normalize_model_output(parsed, _fallback_reading(context))
    except Exception:
        logger.warning("chronicler_api_error", exc_info=True)
        refund_cost(estimated_cost)
        return None


def _record_run(run: dict[str, Any]) -> None:
    _RECENT_RUNS.append(run)
    logger.info("chronicler_run %s", json.dumps(run, ensure_ascii=False, sort_keys=True))


def log_chronicler_event(event: dict[str, Any]) -> None:
    relation = _truncate_text(event.get("relation"), 24)
    if relation not in {None, "follow", "override", "neutral"}:
        relation = None
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": _truncate_text(event.get("event_type"), 48) or "unknown",
        "trace_id": _truncate_text(event.get("trace_id"), 64),
        "route": _truncate_text(event.get("route"), 64),
        "session_id": _truncate_text(event.get("session_id"), 64),
        "action_id": _normalize_action(event.get("action_id")),
        "suggested_action": _normalize_action(event.get("suggested_action")),
        "relation": relation,
        "dwell_ms": max(0, _safe_int(event.get("dwell_ms"), 0)),
        "details": _truncate_text(event.get("details"), 180),
    }
    _RECENT_EVENTS.append(payload)
    logger.info("chronicler_event %s", json.dumps(payload, ensure_ascii=False, sort_keys=True))


def generate_chronicler_reading(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = secrets.token_hex(8)
    context = build_context(payload)
    started_at = time.time()

    if not is_chronicler_enabled():
        result = {
            "observation": "The Chronicler has gone quiet for now.",
            "prompt": "The room keeps its counsel.",
            "suggestion": None,
            "suggested_action": "none",
            "uncertainty": "Silence is also a reading.",
            "mode": "disabled",
            "cost_estimate_usd": 0.0,
        }
    else:
        result = _generate_model_reading(context) or _fallback_reading(context)
        result = _apply_suggestion_budget(context, result)

    elapsed_ms = int((time.time() - started_at) * 1000)
    response = {
        **result,
        "trace_id": trace_id,
        "elapsed_ms": elapsed_ms,
        "cost_snapshot": current_cost_snapshot(),
    }
    _record_run(
        {
            "trace_id": trace_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "route": context["route"],
            "session_id": context["session_id"],
            "pet_name": context["pet"]["name"],
            "animal": context["pet"]["animal"],
            "level": context["pet"]["level"],
            "context_summary": {
                "dream_unread": context["dream_unread"],
                "confession_count": context["confession_count"],
                "can_mutate": context["can_mutate"],
                "has_feral": context["has_feral"],
                "has_pact": context["has_pact"],
                "recent_fights": context["recent_fights"],
            },
            "response": response,
        }
    )
    return response


def recent_runs(limit: int = 25) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return list(_RECENT_RUNS)[-limit:]


def recent_events(limit: int = 100) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return list(_RECENT_EVENTS)[-limit:]


def chronicler_summary() -> dict[str, Any]:
    runs = list(_RECENT_RUNS)
    events = list(_RECENT_EVENTS)

    response_runs = len(runs)
    mode_counts: dict[str, int] = {}
    suggested_action_counts: dict[str, int] = {}
    for run in runs:
        response = run.get("response", {})
        mode = str(response.get("mode") or "unknown")
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        action = _normalize_action(response.get("suggested_action"))
        suggested_action_counts[action] = suggested_action_counts.get(action, 0) + 1

    event_counts: dict[str, int] = {}
    follow = 0
    override = 0
    neutral = 0
    short_exit = 0
    engaged_exit = 0
    for event in events:
        event_type = str(event.get("event_type") or "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        relation = event.get("relation")
        if relation == "follow":
            follow += 1
        elif relation == "override":
            override += 1
        elif relation == "neutral":
            neutral += 1
        if event_type == "page_exit":
            details = str(event.get("details") or "")
            if details == "short-exit":
                short_exit += 1
            elif details == "engaged-exit":
                engaged_exit += 1

    decision_events = follow + override + neutral
    override_rate = round(override / (follow + override), 4) if (follow + override) > 0 else None
    follow_rate = round(follow / (follow + override), 4) if (follow + override) > 0 else None
    bounce_rate = round(short_exit / (short_exit + engaged_exit), 4) if (short_exit + engaged_exit) > 0 else None

    return {
        "cost": current_cost_snapshot(),
        "runs": {
            "count": response_runs,
            "mode_counts": mode_counts,
            "suggested_action_counts": suggested_action_counts,
        },
        "events": {
            "count": len(events),
            "event_counts": event_counts,
            "decision_events": decision_events,
            "follow": follow,
            "override": override,
            "neutral": neutral,
            "follow_rate": follow_rate,
            "override_rate": override_rate,
            "short_exit": short_exit,
            "engaged_exit": engaged_exit,
            "bounce_rate": bounce_rate,
        },
        "kill_signals": {
            "follow_rate_gt_30pct": follow_rate is not None and follow_rate > 0.30,
            "override_rate_lt_50pct": override_rate is not None and override_rate < 0.50,
            "bounce_rate_gt_5pct": bounce_rate is not None and bounce_rate > 0.05,
            "cost_gt_cap": current_cost_snapshot()["usd_spent"] > current_cost_snapshot()["usd_cap"],
        },
    }
