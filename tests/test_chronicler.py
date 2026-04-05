from __future__ import annotations

from chronicler import build_context, generate_chronicler_reading


def test_chronicler_fallback_avoids_forbidden_assistant_phrases(monkeypatch):
    monkeypatch.setenv("MOREAU_ENABLE_CHRONICLER", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    reading = generate_chronicler_reading(
        {
            "session_id": "voice-session",
            "active_pet": {
                "name": "Echo",
                "animal": "monkey",
                "level": 3,
                "mood": "excited",
            },
            "available_actions": ["train", "profile"],
        }
    )

    combined = " ".join(
        part for part in [reading["observation"], reading["prompt"], reading.get("suggestion") or "", reading["uncertainty"]] if part
    ).lower()
    forbidden = ["here are", "based on your current stats", "great job", "maximize", "key metrics"]
    assert not any(phrase in combined for phrase in forbidden)


def test_chronicler_prefers_dreams_when_unread(monkeypatch):
    monkeypatch.setenv("MOREAU_ENABLE_CHRONICLER", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    reading = generate_chronicler_reading(
        {
            "session_id": "test-session",
            "active_pet": {
                "name": "Skodik",
                "animal": "fox",
                "level": 5,
                "mood": "philosophical",
                "corruption": 0,
                "instability": 0,
                "mutations": [],
            },
            "recent_fights": [{"opponent": "GreedyAgent", "result": "win", "ticks": 11}],
            "dream_unread": 2,
            "recent_dream": "The fox stood in a corridor of teeth.",
            "available_actions": ["dreams", "train", "profile"],
        }
    )

    assert reading["suggested_action"] == "dreams"
    assert "dream" in (reading["suggestion"] or "").lower()


def test_chronicler_warns_about_corruption(monkeypatch):
    monkeypatch.setenv("MOREAU_ENABLE_CHRONICLER", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    reading = generate_chronicler_reading(
        {
            "session_id": "test-session",
            "active_pet": {
                "name": "Ash",
                "animal": "wolf",
                "level": 8,
                "mood": "angry",
                "corruption": 82,
                "instability": 24,
                "mutations": ["blood_rage"],
            },
            "recent_fights": [{"opponent": "SmartAgent", "result": "loss", "ticks": 18}],
            "available_actions": ["tides", "lab", "caretaker"],
        }
    )

    assert reading["suggested_action"] == "tides"
    assert "corruption" in reading["observation"].lower()


def test_chronicler_can_be_disabled(monkeypatch):
    monkeypatch.setenv("MOREAU_ENABLE_CHRONICLER", "0")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    reading = generate_chronicler_reading(
        {
            "session_id": "test-session",
            "active_pet": {
                "name": "Skodik",
                "animal": "fox",
                "level": 5,
                "mood": "philosophical",
            },
        }
    )

    assert reading["mode"] == "disabled"
    assert reading["suggested_action"] == "none"


def test_chronicler_throttles_repeated_suggestions(monkeypatch):
    monkeypatch.setenv("MOREAU_ENABLE_CHRONICLER", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    payload = {
        "session_id": "budget-session",
        "active_pet": {
            "name": "Ash",
            "animal": "wolf",
            "level": 8,
            "mood": "angry",
            "corruption": 82,
            "instability": 24,
            "mutations": ["blood_rage"],
        },
        "recent_fights": [{"opponent": "SmartAgent", "result": "loss", "ticks": 18}],
        "available_actions": ["tides", "lab", "caretaker"],
    }

    first = generate_chronicler_reading(payload)
    second = generate_chronicler_reading(payload)
    third = generate_chronicler_reading(payload)

    assert first["suggested_action"] == "tides"
    assert second["suggested_action"] == "none"
    assert third["suggested_action"] == "none"


def test_chronicler_accepts_part_b_continuity_payload():
    context = build_context(
        {
            "session_id": "continuity-session",
            "active_pet": {
                "name": "Echo",
                "animal": "fox",
                "level": 4,
                "mood": "tired",
            },
            "part_b_continuity": {
                "state_of_play": "Grow Safely / Guarded; lane stabilizing, posture recovering.",
                "recent_pattern": "t4 care -> stabilized; t5 rest -> recovered",
                "must_remember": [
                    "Welfare already fell below the tolerated floor.",
                    "Energy is below the pressure floor for this standing order.",
                ],
                "compact_handoff": {
                    "carry_forward_summary": "Grow Safely / Guarded: stabilize before new pressure.",
                    "do_next": "Use CARE or REST before another arena read.",
                    "watch_for": ["another welfare dip", "energy collapse"],
                },
            },
        }
    )

    continuity = context["part_b_continuity"]
    assert continuity["state_of_play"]
    assert continuity["recent_pattern"]
    assert continuity["carry_forward_summary"]
    assert continuity["do_next"]
    assert continuity["watch_for"] == ["another welfare dip", "energy collapse"]
