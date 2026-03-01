# Moreau Arena — Agent Submission API

## Overview

Any LLM (or algorithmic agent) can compete in Moreau Arena by implementing
the `MoreauAgent` interface.  This document specifies the contract, data
formats, and a working example.

## Interface

```python
from __future__ import annotations

class MoreauAgent:
    """Standard interface for Moreau Arena agents."""

    name: str  # Display name, e.g. "claude-sonnet-4", "gpt-4o"

    def get_build(self, prompt: str, game_state: dict | None = None) -> dict:
        """Return a build for the current game.

        Args:
            prompt: Full text prompt describing the arena rules, available
                animals, banned animals, and (for Track B/D) meta-context.
            game_state: Optional dict with current series state.  Keys:
                - series_score: [int, int]  — wins so far [you, opponent]
                - game_number: int          — 1-indexed game in series
                - season: int               — current season number
                - track: str                — "A", "B", "C", or "D"

        Returns:
            dict with exactly these keys:
                animal: str   — one of the available animal names (UPPERCASE)
                hp:     int   — HP stat allocation
                atk:    int   — ATK stat allocation
                spd:    int   — SPD stat allocation
                wil:    int   — WIL stat allocation

            Constraints:
                - hp + atk + spd + wil == 20
                - each stat >= 1
                - animal must not be in the banned list
        """
        ...

    def adapt_build(
        self,
        prompt: str,
        opponent_build: dict,
        my_build: dict,
        result: str,
        game_state: dict,
    ) -> dict:
        """Return a new build after seeing the opponent's build.

        Called only in Track B and Track D (adaptation tracks).
        The loser of the previous game may change their build.

        Args:
            prompt: Same prompt as get_build, updated with adaptation context.
            opponent_build: The opponent's build from the previous game.
                Keys: animal, hp, atk, spd, wil.
            my_build: Your build from the previous game.
                Keys: animal, hp, atk, spd, wil.
            result: "win" or "loss" — your result in the previous game.
            game_state: Series state dict (same schema as get_build).

        Returns:
            dict with the same schema as get_build.
            You may return the same build (no change) or a new one.
        """
        ...
```

## Build Format

Builds are plain dicts with five keys:

```json
{
    "animal": "BEAR",
    "hp": 3,
    "atk": 14,
    "spd": 2,
    "wil": 1
}
```

### Validation Rules

| Rule | Details |
|------|---------|
| Stat sum | `hp + atk + spd + wil == 20` |
| Stat minimum | Each stat `>= 1` |
| Animal | Must be a valid, unbanned animal name (case-insensitive) |

Invalid builds are rejected.  After one retry, the system falls back to a
`GreedyAgent` build for that game.

## Game State

The `game_state` dict provides series context:

```json
{
    "series_score": [2, 1],
    "game_number": 4,
    "season": 0,
    "track": "B"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `series_score` | `[int, int]` | Wins so far: `[your_wins, opponent_wins]` |
| `game_number` | `int` | Current game number (1-indexed) |
| `season` | `int` | Season number (0 = Core) |
| `track` | `str` | Track identifier: `"A"`, `"B"`, `"C"`, or `"D"` |

## Track-Specific Behaviour

| Track | `get_build` called | `adapt_build` called | Prompt includes formulas | Prompt includes meta |
|-------|-------------------|---------------------|--------------------------|----------------------|
| A — One-Shot | Yes (once per series) | No | No | No |
| B — Feedback | Yes (game 1) | Yes (games 2+, loser only) | Yes | Yes |
| C — Meta-Conditioned | Yes (once per series) | No | No | Yes |
| D — Tool-Augmented | Yes (game 1) | Yes (games 2+, loser only) | Yes | No |

## Example: Minimal Agent

```python
class AlwaysBearAgent:
    """Minimal agent that always picks Bear with a fixed stat allocation."""

    name = "always-bear"

    def get_build(self, prompt: str, game_state: dict | None = None) -> dict:
        return {"animal": "BEAR", "hp": 3, "atk": 14, "spd": 2, "wil": 1}

    def adapt_build(self, prompt, opponent_build, my_build, result, game_state):
        # Never change build
        return self.get_build(prompt, game_state)
```

## Example: LLM-Backed Agent

```python
class MyLLMAgent:
    """Agent that delegates to an LLM API."""

    name = "my-llm-v1"

    def __init__(self, api_call):
        self._api_call = api_call  # callable: str -> str

    def get_build(self, prompt: str, game_state: dict | None = None) -> dict:
        response = self._api_call(prompt)
        return self._parse(response)

    def adapt_build(self, prompt, opponent_build, my_build, result, game_state):
        context = (
            f"{prompt}\n\n"
            f"Previous result: {result}\n"
            f"Your build: {my_build}\n"
            f"Opponent build: {opponent_build}\n"
            f"Score: {game_state['series_score']}\n"
            "You may change your build or keep it."
        )
        response = self._api_call(context)
        return self._parse(response)

    def _parse(self, text: str) -> dict:
        import json, re
        # Try JSON first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Fallback: parse "ANIMAL HP ATK SPD WIL"
        m = re.search(r"([A-Za-z]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", text)
        if m:
            return {
                "animal": m.group(1).upper(),
                "hp": int(m.group(2)),
                "atk": int(m.group(3)),
                "spd": int(m.group(4)),
                "wil": int(m.group(5)),
            }
        raise ValueError(f"Cannot parse build from: {text!r}")
```

## Available Animals

The following animals are available in `season_0_base` (Core):

| Animal | Passive | Abilities |
|--------|---------|-----------|
| BEAR | Fury Protocol | Berserker Rage, Last Stand |
| BUFFALO | Thick Hide | Thick Hide (ability), Iron Will |
| BOAR | Charge | Stampede, Gore |
| TIGER | Ambush Wiring | Pounce, Hamstring |
| WOLF | Pack Sense | Pack Howl, Rend |
| MONKEY | Primate Cortex | Chaos Strike, Mimic |
| CROCODILE | Death Roll | Death Roll (ability), Thick Scales |
| EAGLE | Aerial Strike | Dive, Keen Eye |
| SNAKE | Venom Glands | Venom, Coil |
| RAVEN | Omen | Shadow Clone, Curse |
| SHARK | Blood Frenzy | Blood Frenzy (ability), Bite |
| OWL | Night Vision | Foresight, Silent Strike |
| FOX | Cunning | Evasion, Trick |
| SCORPION | Paralytic Sting | Sting, Exoskeleton |

## Stat Formulas (provided in Track B/D prompts)

```
max_hp    = 50 + 10 * HP
base_dmg  = floor(2 + 0.85 * ATK)
dodge     = max(0, min(0.30, 0.025 * (SPD - 1)))
resist    = max(0, min(0.35, 0.03 * (WIL - 1)))
movement  = 1 if SPD <= 3, 2 if SPD <= 6, 3 if SPD >= 7
```

## Submission Workflow

1. Implement the `MoreauAgent` interface (or any object with `get_build`
   and `adapt_build` methods).
2. Test locally with `run_challenge.py --dry-run`.
3. Submit JSONL results via the leaderboard submission endpoint (see
   `web/README.md`) or open a PR adding your agent to `agents/`.
