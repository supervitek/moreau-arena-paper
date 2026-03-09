"""Tests for the Moreau Pets soul engine."""

import os
from unittest.mock import patch, MagicMock

import pytest
from pets.soul import (
    generate_soul_response,
    calculate_mood,
    _build_system_prompt,
    FALLBACK_MSG,
    ANIMAL_PERSONALITIES,
)


def _make_pet(**overrides):
    pet = {
        "name": "Shadow",
        "animal": "fox",
        "level": 5,
        "xp": 200,
        "base_stats": {"hp": 5, "atk": 7, "spd": 6, "wil": 2},
        "mutations": ["blood_rage"],
        "fights": [
            {"opponent": "GreedyAgent", "result": "win", "ticks": 34},
            {"opponent": "SmartAgent", "result": "loss", "ticks": 45},
        ],
        "mood": "philosophical",
    }
    pet.update(overrides)
    return pet


# ---- mood calculation ----

def test_mood_3_wins():
    pet = _make_pet(fights=[
        {"opponent": "A", "result": "win", "ticks": 30},
        {"opponent": "B", "result": "win", "ticks": 25},
        {"opponent": "C", "result": "win", "ticks": 20},
    ])
    assert calculate_mood(pet) == "happy"


def test_mood_3_losses():
    pet = _make_pet(fights=[
        {"opponent": "A", "result": "loss", "ticks": 30},
        {"opponent": "B", "result": "loss", "ticks": 25},
        {"opponent": "C", "result": "loss", "ticks": 20},
    ])
    assert calculate_mood(pet) == "angry"


def test_mood_no_fights():
    pet = _make_pet(fights=[])
    assert calculate_mood(pet) == "tired"


# ---- fallback ----

def test_fallback_no_api_key():
    pet = _make_pet()
    with patch.dict(os.environ, {}, clear=True):
        # Remove ANTHROPIC_API_KEY if present
        os.environ.pop("ANTHROPIC_API_KEY", None)
        result = generate_soul_response(pet, context="idle")
    assert "stares at you silently" in result
    assert "Shadow" in result


# ---- prompt building ----

def test_system_prompt_contains_personality():
    pet = _make_pet(animal="tiger")
    prompt = _build_system_prompt(pet, context="idle")
    assert "tiger" in prompt.lower()
    assert pet["name"] in prompt
    assert "Level 5" in prompt
    assert "Terse" in prompt or "Clinical" in prompt


def test_system_prompt_context_post_fight():
    pet = _make_pet()
    prompt = _build_system_prompt(pet, context="post_fight_win", opponent="SmartAgent")
    assert "SmartAgent" in prompt
    assert "won" in prompt.lower() or "win" in prompt.lower()


def test_all_animals_have_personalities():
    from pets.mutation_tree import VALID_ANIMALS
    for animal in VALID_ANIMALS:
        assert animal in ANIMAL_PERSONALITIES, f"Missing personality for {animal}"


# ---- generate with mock API ----

def test_generate_with_mock_api():
    pet = _make_pet()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="I see through your tricks, kid.")]

    mock_anthropic_mod = MagicMock()
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    mock_anthropic_mod.Anthropic.return_value = mock_client

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch.dict("sys.modules", {"anthropic": mock_anthropic_mod}):
            result = generate_soul_response(pet, context="idle")

    assert result == "I see through your tricks, kid."
