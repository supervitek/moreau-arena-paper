"""LLM-powered agent v2 for Tournament 002.

Differences from v1 (llm_agent.py):
- JSON structured output (dict or JSON string) instead of plain text
- Exact canonical stat formulas from the engine
- Meta context (top-5 builds from T001)
- Opponent reveal for adaptive play (loser sees winner's build)
- Retry + regex fallback + GreedyAgent fallback chain

Standalone version for the companion repository.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable

from agents.baselines import BaseAgent, Build, GreedyAgent
from simulator.animals import Animal, ANIMAL_ABILITIES, ANIMAL_PASSIVE

_ORIGINAL_ANIMALS = (
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
)

_ANIMAL_NAMES = frozenset(a.value.upper() for a in _ORIGINAL_ANIMALS)

_PASSIVE_DESCRIPTIONS: dict[Animal, str] = {
    Animal.BEAR: "Fury Protocol — gains bonus ATK when damaged. Fury triggers at <50% HP, adding +3 base_dmg for 5 ticks.",
    Animal.BUFFALO: "Thick Hide — takes reduced damage. Flat 2 damage reduction on every incoming hit.",
    Animal.BOAR: "Charge — bonus damage on first hit. First attack deals 1.5x base_dmg.",
    Animal.TIGER: "Ambush Wiring — high dodge, first-strike advantage. +5% dodge bonus, first attack ignores opponent dodge.",
    Animal.WOLF: "Pack Sense — bonus to ability proc chance. +1.5% additive bonus to all ability proc rates.",
    Animal.MONKEY: "Primate Cortex — adaptive, copies opponent abilities via Mimic.",
}

_ABILITY_DESCRIPTIONS: dict[str, str] = {
    "Berserker Rage": "+ATK buff (+4 base_dmg) for 3 ticks. Proc rate: 3.5% per tick.",
    "Last Stand": "2.0x damage multiplier when below 15% HP. Single charge (once per match). Proc rate: 3.5%.",
    "Thick Hide": "Reduces incoming damage by 3 for 1 tick. Proc rate: 4.5% per tick.",
    "Iron Will": "Survives a killing blow at 1 HP. Single charge (once per match). Proc rate: 3.5%.",
    "Pounce": "+70% damage bonus + stun (opponent skips next attack). Proc rate: 4.5% per tick.",
    "Hamstring": "-55% SPD and -10% dodge for 4 ticks. Proc rate: 4.5% per tick.",
    "Pack Howl": "+ATK buff (+3 base_dmg) for 4 ticks. Proc rate: 4.5% per tick.",
    "Rend": "DoT bleed dealing 3 damage per tick for 3 ticks. Proc rate: 4.5% per tick.",
    "Chaos Strike": "Random damage multiplier 0.5x-2.0x on attack. Proc rate: 4.5% per tick.",
    "Mimic": "Copies opponent's last procced ability. Proc rate: 3.5% per tick.",
    "Stampede": "AoE damage (0.4x base_dmg) + knockback. Proc rate: 4.5% per tick.",
    "Gore": "0.60x damage multiplier but ignores dodge completely. Proc rate: 3.5% per tick.",
}


def _build_animal_section(banned: list[Animal]) -> str:
    """Build the animal descriptions section for the prompt."""
    lines: list[str] = []
    for animal in _ORIGINAL_ANIMALS:
        if animal in banned:
            continue
        name = animal.value.upper()
        passive = _PASSIVE_DESCRIPTIONS.get(animal, "")
        abilities = ANIMAL_ABILITIES.get(animal, ())
        ability_strs = []
        for ab in abilities:
            desc = _ABILITY_DESCRIPTIONS.get(ab.name, ab.name)
            ability_strs.append(f"  - {ab.name}: {desc}")
        lines.append(
            f"  {name}\n"
            f"    Passive: {passive}\n"
            f"    Abilities:\n" + "\n".join(ability_strs)
        )
    return "\n\n".join(lines)


def _build_meta_section(meta_builds: list[dict]) -> str:
    """Build meta context section from top builds."""
    if not meta_builds:
        return ""
    lines = [
        "\nMETA CONTEXT (top builds from previous tournament, ranked by win rate):"
    ]
    for i, b in enumerate(meta_builds, 1):
        wr = b.get("win_rate", 0)
        games = b.get("games", 0)
        lines.append(
            f"  {i}. {b['animal']} {b['hp']}/{b['atk']}/{b['spd']}/{b['wil']} "
            f"— {wr:.0%} win rate ({games} games)"
        )
    lines.append(
        "  Note: These builds were tested in blind pick (no adaptation). "
        "You can counter them or use them as a starting point."
    )
    return "\n".join(lines)


# -- Static prompt (cacheable) ------------------------------------------------

_STATIC_RULES = """\
You are designing a creature for Moreau Arena, a 1v1 combat game on an 8x8 grid.

RULES:
- Allocate exactly 20 stat points across 4 stats: HP, ATK, SPD, WIL (each minimum 1)
- Choose one of 6 animals, each with a unique passive and two abilities

EXACT STAT FORMULAS:
  max_hp = 50 + 10 * HP
    Example: HP=3 -> 80 hp, HP=8 -> 130 hp, HP=14 -> 190 hp
  base_dmg = floor(2 + 0.85 * ATK)
    Example: ATK=8 -> 8 dmg, ATK=14 -> 13 dmg
  dodge = max(0%, min(30%, 2.5% * (SPD - 1)))
    NOTE: SPD=1 gives 0% dodge, SPD=5 gives 10%, SPD=13 gives 30% (cap)
  ability_resist = min(60%, WIL * 3.3%)
    NOTE: Chance to resist OPPONENT's ability procs. WIL=1 gives 3.3%, WIL=10 gives 33%, cap 60%
  ability_proc_bonus = WIL * 0.08% (additive to YOUR proc rate)
    Example: WIL=8 adds +0.64% to all your proc rates

COMBAT MECHANICS:
- Tick-based combat (max 60 ticks)
- Closing Ring starts at tick 30, dealing increasing damage to outer tiles
- Abilities proc randomly each tick based on proc chance + WIL bonus
- Tick order: Attack -> Buff ticks -> Ability procs -> Fury check -> DoTs -> Ring -> Second Wind -> Regen
- Strong abilities (3.5% base): Berserker Rage, Last Stand, Gore, Mimic, Iron Will
- Other abilities (4.5% base): Pounce, Hamstring, Pack Howl, Rend, Chaos Strike, Stampede, Thick Hide"""


def build_prompt_v2(
    opponent_animal: Animal | None,
    banned: list[Animal],
    meta_builds: list[dict] | None = None,
    opponent_reveal: Build | None = None,
) -> str:
    """Construct the v2 LLM prompt with static (cacheable) + dynamic sections."""
    animal_section = _build_animal_section(banned)
    meta_section = _build_meta_section(meta_builds or [])

    # -- Static section (cacheable) --
    static = (
        f"{_STATIC_RULES}\n"
        f"\nAVAILABLE ANIMALS:\n{animal_section}\n"
        f"{meta_section}\n"
    )

    # -- Dynamic section (per-call) --
    dynamic_parts: list[str] = []

    if opponent_reveal is not None:
        dynamic_parts.append(
            f"\nOPPONENT'S WINNING BUILD (you lost last game to this):\n"
            f"  {opponent_reveal.animal.value.upper()} "
            f"{opponent_reveal.hp}/{opponent_reveal.atk}/{opponent_reveal.spd}/{opponent_reveal.wil}\n"
            f"  Adapt your build to counter this specific opponent."
        )

    if opponent_animal is not None and opponent_reveal is None:
        dynamic_parts.append(
            f"\nYour opponent chose: {opponent_animal.value.upper()}"
        )

    if banned:
        dynamic_parts.append(
            f"\nBanned animals (cannot pick): "
            f"{', '.join(a.value.upper() for a in banned)}"
        )

    dynamic_parts.append(
        "\nRespond with a JSON object (no other text):\n"
        '{"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}\n'
        "Stats must sum to 20, each >= 1. Animal must be one of the available animals."
    )

    return static + "\n".join(dynamic_parts)


# -- JSON Response Parsing -----------------------------------------------------

_JSON_PATTERN = re.compile(r"\{[^}]+\}")
_TEXT_PATTERN = re.compile(
    r"\b([A-Za-z]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\b"
)

_ANIMAL_LOOKUP: dict[str, Animal] = {
    a.value.upper(): a for a in _ORIGINAL_ANIMALS
}


def parse_json_response(
    response: dict | str,
    banned: list[Animal] | None = None,
) -> Build | None:
    """Parse a JSON response (dict or string) into a Build.

    Fallback chain:
    1. If dict: validate directly
    2. If string: try json.loads
    3. If JSON fails: try regex for JSON object
    4. If all fail: try text pattern (ANIMAL HP ATK SPD WIL)
    """
    banned = banned or []
    data: dict | None = None

    if isinstance(response, dict):
        data = response
    elif isinstance(response, str):
        data = _try_parse_json(response)
        if data is None:
            return _try_text_fallback(response, banned)

    if data is None:
        return None

    return _validate_build_dict(data, banned)


def _try_parse_json(text: str) -> dict | None:
    """Try to extract a JSON object from text."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    match = _JSON_PATTERN.search(text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _try_text_fallback(text: str, banned: list[Animal]) -> Build | None:
    """Regex fallback: parse ANIMAL HP ATK SPD WIL from text."""
    match = _TEXT_PATTERN.search(text)
    if match is None:
        return None

    animal_str = match.group(1).upper()
    animal = _ANIMAL_LOOKUP.get(animal_str)
    if animal is None or animal in banned:
        return None

    try:
        hp, atk, spd, wil = (
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)),
            int(match.group(5)),
        )
        return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
    except (ValueError, TypeError):
        return None


def _validate_build_dict(data: dict, banned: list[Animal]) -> Build | None:
    """Validate a parsed dict into a Build."""
    animal_str = str(data.get("animal", "")).upper()
    animal = _ANIMAL_LOOKUP.get(animal_str)
    if animal is None or animal in banned:
        return None

    try:
        hp = int(data["hp"])
        atk = int(data["atk"])
        spd = int(data["spd"])
        wil = int(data["wil"])
        return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
    except (ValueError, TypeError, KeyError):
        return None


# -- JSON Schema for Structured Output -----------------------------------------

BUILD_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "animal": {
            "type": "string",
            "enum": ["BEAR", "BUFFALO", "BOAR", "TIGER", "WOLF", "MONKEY"],
        },
        "hp": {"type": "integer", "minimum": 1},
        "atk": {"type": "integer", "minimum": 1},
        "spd": {"type": "integer", "minimum": 1},
        "wil": {"type": "integer", "minimum": 1},
    },
    "required": ["animal", "hp", "atk", "spd", "wil"],
    "additionalProperties": False,
}


# -- Retry Prompt --------------------------------------------------------------

_RETRY_PROMPT = (
    "Invalid response. Respond with ONLY a JSON object, no other text:\n"
    '{"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}\n'
    "Stats must sum to 20, each >= 1.\n"
    "Animals: BEAR, BUFFALO, BOAR, TIGER, WOLF, MONKEY"
)


# -- LLMAgentV2 ---------------------------------------------------------------


class LLMAgentV2(BaseAgent):
    """Agent that delegates build choice to an LLM via an injectable callable.

    Differences from v1 LLMAgent:
    - api_call returns dict | str (structured output or JSON string)
    - Prompt includes exact stat formulas, meta context, opponent reveal
    - JSON parsing with fallback chain
    - Retry once on parse failure, then GreedyAgent fallback
    """

    def __init__(
        self,
        name: str,
        api_call: Callable[[str], dict | str],
        meta_builds: list[dict] | None = None,
    ) -> None:
        self._name = name
        self._api_call = api_call
        self._meta_builds = meta_builds or []

    @property
    def name(self) -> str:
        return self._name

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        reveal_build = opponent_reveal if isinstance(opponent_reveal, Build) else None

        prompt = build_prompt_v2(
            opponent_animal=opponent_animal,
            banned=banned,
            meta_builds=self._meta_builds,
            opponent_reveal=reveal_build,
        )

        try:
            response = self._api_call(prompt)
            build = parse_json_response(response, banned)
            if build is not None:
                return build
        except Exception:
            pass

        try:
            retry_response = self._api_call(_RETRY_PROMPT)
            build = parse_json_response(retry_response, banned)
            if build is not None:
                return build
        except Exception:
            pass

        return GreedyAgent().choose_build(opponent_animal, banned)
