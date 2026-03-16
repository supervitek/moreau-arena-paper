from __future__ import annotations

from chronicler import generate_chronicler_reading


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
