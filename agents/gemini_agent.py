"""GeminiFlashAgent — Moreau Arena agent powered by Google Gemini Flash.

Implements the MoreauAgent interface (docs/AGENT_API.md) using raw HTTP
calls to the Google Generative AI API.  No third-party SDK required.

Usage:
    from agents.gemini_agent import GeminiFlashAgent
    agent = GeminiFlashAgent()           # reads GEMINI_API_KEY from env
    build = agent.get_build(prompt_text)  # -> dict
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# MoreauAgent interface (from docs/AGENT_API.md)
# ---------------------------------------------------------------------------

class GeminiFlashAgent:
    """Moreau Arena agent using Google Gemini 2.0 Flash Lite (cheapest).

    Implements the MoreauAgent interface:
        get_build(prompt, game_state=None) -> dict
        adapt_build(prompt, opponent_build, my_build, result, game_state) -> dict
    """

    VALID_ANIMALS = [
        "BEAR", "BUFFALO", "BOAR", "TIGER", "WOLF", "MONKEY",
        "CROCODILE", "EAGLE", "SNAKE", "RAVEN", "SHARK", "OWL",
        "FOX", "SCORPION",
    ]

    BUILD_SCHEMA: dict[str, Any] = {
        "type": "OBJECT",
        "properties": {
            "animal": {"type": "STRING", "enum": VALID_ANIMALS},
            "hp": {"type": "INTEGER"},
            "atk": {"type": "INTEGER"},
            "spd": {"type": "INTEGER"},
            "wil": {"type": "INTEGER"},
        },
        "required": ["animal", "hp", "atk", "spd", "wil"],
    }

    def __init__(
        self,
        model: str = "gemini-2.0-flash-lite",
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set GEMINI_API_KEY environment variable "
                "or pass api_key= to the constructor."
            )
        self.temperature = temperature
        self.max_tokens = max_tokens

    # -- MoreauAgent interface -----------------------------------------------

    def get_build(
        self,
        prompt: str,
        game_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call Gemini Flash and return a build dict."""
        response_text = self._call_api(prompt)
        build = self._parse_response(response_text)
        return build

    def adapt_build(
        self,
        prompt: str,
        opponent_build: dict[str, Any],
        my_build: dict[str, Any],
        result: str,
        game_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Adapt build after seeing opponent's winning build."""
        adapt_prompt = (
            f"{prompt}\n\n"
            f"You lost to: {opponent_build['animal']} "
            f"{opponent_build['hp']}/{opponent_build['atk']}/"
            f"{opponent_build['spd']}/{opponent_build['wil']}\n"
            f"Adapt your build to counter this opponent."
        )
        return self.get_build(adapt_prompt, game_state)

    # -- Internal API call ---------------------------------------------------

    def _call_api(self, prompt: str) -> str:
        """Make a raw HTTP request to the Generative AI REST API."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": self.BUILD_SCHEMA,
                "maxOutputTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        ctx = ssl.create_default_context()

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

        # Extract text from response
        candidates = result.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""

    def _parse_response(self, text: str) -> dict[str, Any]:
        """Parse Gemini response into a valid build dict."""
        fallback = {"animal": "BEAR", "hp": 5, "atk": 5, "spd": 5, "wil": 5}

        if not text.strip():
            return fallback

        try:
            data = json.loads(text.strip())
        except (json.JSONDecodeError, TypeError):
            return fallback

        animal = str(data.get("animal", "")).upper()
        if animal not in self.VALID_ANIMALS:
            return fallback

        try:
            hp = int(data["hp"])
            atk = int(data["atk"])
            spd = int(data["spd"])
            wil = int(data["wil"])
        except (KeyError, ValueError, TypeError):
            return fallback

        # Validate constraints
        if any(v < 1 for v in (hp, atk, spd, wil)):
            return fallback
        if hp + atk + spd + wil != 20:
            return fallback

        return {"animal": animal, "hp": hp, "atk": atk, "spd": spd, "wil": wil}


# ---------------------------------------------------------------------------
# BaseAgent adapter for use with run_ablation.py
# ---------------------------------------------------------------------------

from agents.baselines import BaseAgent, Build
from simulator.animals import Animal

_ANIMAL_MAP = {a.value.upper(): a for a in Animal}


class GeminiAblationAgent(BaseAgent):
    """Adapter wrapping GeminiFlashAgent for the ablation framework.

    Uses the existing ablation prompt builders and integrates with the
    run_ablation.py round-robin infrastructure.
    """

    def __init__(self, name: str, gemini_agent: GeminiFlashAgent) -> None:
        self._name = name
        self._gemini = gemini_agent

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        """Call Gemini via the MoreauAgent interface, return a Build."""
        # Build a simple prompt for the Gemini agent
        from agents.llm_agent import build_prompt
        prompt = build_prompt(opponent_animal, banned)

        result = self._gemini.get_build(prompt)

        animal_str = result.get("animal", "").upper()
        animal = _ANIMAL_MAP.get(animal_str)
        if animal is None or animal in banned:
            # Fallback
            from agents.baselines import GreedyAgent
            return GreedyAgent().choose_build(opponent_animal, banned)

        try:
            return Build(
                animal=animal,
                hp=int(result["hp"]),
                atk=int(result["atk"]),
                spd=int(result["spd"]),
                wil=int(result["wil"]),
            )
        except (ValueError, KeyError):
            from agents.baselines import GreedyAgent
            return GreedyAgent().choose_build(opponent_animal, banned)
