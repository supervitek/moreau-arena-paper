"""LLM-powered agent for Moreau Arena (Tournament 001).

Sends a prompt describing the game rules to an LLM API callable,
parses the response into a Build. Model-agnostic: the caller injects
the api_call function (Claude, GPT, Grok, or a test stub).

Standalone version for the companion repository.
"""

from __future__ import annotations

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

_PASSIVE_DESCRIPTIONS: dict[Animal, str] = {
    Animal.BEAR: "Fury Protocol — gains +ATK when damaged",
    Animal.BUFFALO: "Thick Hide — takes reduced damage",
    Animal.BOAR: "Charge — bonus damage on first hit",
    Animal.TIGER: "Ambush Wiring — high dodge, first-strike advantage",
    Animal.WOLF: "Pack Sense — bonus to ability proc chance",
    Animal.MONKEY: "Primate Cortex — adaptive, copies opponent abilities",
}

_ABILITY_DESCRIPTIONS: dict[str, str] = {
    "Berserker Rage": "+ATK buff for 3 ticks (3.5% proc)",
    "Last Stand": "2x damage when below 15% HP (single charge, 3.5% proc)",
    "Thick Hide": "Reduces incoming damage for 1 tick (4.5% proc)",
    "Iron Will": "Survives a killing blow at 1 HP (single charge, 3.5% proc)",
    "Pounce": "+70% damage + stun (4.5% proc)",
    "Hamstring": "-55% SPD, -10% dodge for 4 ticks (4.5% proc)",
    "Pack Howl": "+ATK buff for 4 ticks (4.5% proc)",
    "Rend": "DoT bleed for 3 ticks (4.5% proc)",
    "Chaos Strike": "Random damage multiplier 0.5x-2.0x (4.5% proc)",
    "Mimic": "Copies opponent's last ability (3.5% proc)",
    "Stampede": "AoE damage + knockback (4.5% proc)",
    "Gore": "0.6x damage but ignores dodge (3.5% proc)",
}


def _build_animal_section(banned: list[Animal]) -> str:
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
            ability_strs.append(f"{ab.name}: {desc}")
        lines.append(
            f"  {name} — Passive: {passive}\n"
            f"    Abilities: {'; '.join(ability_strs)}"
        )
    return "\n".join(lines)


def build_prompt(
    opponent_animal: Animal | None,
    banned: list[Animal],
) -> str:
    """Construct the LLM prompt describing Moreau Arena rules."""
    animal_section = _build_animal_section(banned)

    opponent_line = ""
    if opponent_animal is not None:
        opponent_line = f"\nYour opponent chose: {opponent_animal.value.upper()}\n"

    banned_line = ""
    if banned:
        banned_line = (
            f"\nBanned animals (cannot pick): "
            f"{', '.join(a.value.upper() for a in banned)}\n"
        )

    return (
        "You are designing a creature for Moreau Arena, a 1v1 combat game on an 8x8 grid.\n"
        "\n"
        "RULES:\n"
        "- Allocate exactly 20 stat points across 4 stats: HP, ATK, SPD, WIL (each minimum 1)\n"
        "- Stat formulas:\n"
        "    max_hp = 50 + 10 * HP\n"
        "    base_dmg = floor(2 + 0.85 * ATK)\n"
        "    dodge = SPD * 2.5%  (capped 30%)\n"
        "    resist = min(60%, WIL * 3.3%)\n"
        "- Closing Ring starts at tick 30, dealing increasing damage to creatures on outer tiles\n"
        "- Abilities proc randomly each tick based on proc chance\n"
        "\n"
        "AVAILABLE ANIMALS:\n"
        f"{animal_section}\n"
        f"{opponent_line}"
        f"{banned_line}"
        "\n"
        "Choose an animal and allocate 20 stat points.\n"
        "Respond ONLY in this exact format: ANIMAL HP ATK SPD WIL\n"
        "Example: BOAR 8 8 3 1"
    )


_RETRY_PROMPT = (
    "Invalid format. Respond ONLY in this exact format: ANIMAL HP ATK SPD WIL\n"
    "Example: BOAR 8 8 3 1"
)

_RESPONSE_PATTERN = re.compile(
    r"\b([A-Za-z]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\b"
)

_ANIMAL_LOOKUP: dict[str, Animal] = {
    a.value.upper(): a for a in _ORIGINAL_ANIMALS
}


def parse_response(response: str, banned: list[Animal]) -> Build | None:
    """Parse an LLM response into a Build, or None on failure."""
    match = _RESPONSE_PATTERN.search(response)
    if match is None:
        return None

    animal_str = match.group(1).upper()
    animal = _ANIMAL_LOOKUP.get(animal_str)
    if animal is None:
        return None
    if animal in banned:
        return None

    try:
        hp = int(match.group(2))
        atk = int(match.group(3))
        spd = int(match.group(4))
        wil = int(match.group(5))
        return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
    except (ValueError, TypeError):
        return None


class LLMAgent(BaseAgent):
    """Agent that delegates build choice to an LLM via an injectable callable.

    Args:
        name: Display name for this agent (e.g. "claude-sonnet", "gpt-4o").
        api_call: Function that takes a prompt string and returns a response string.
    """

    def __init__(self, name: str, api_call: Callable[[str], str]) -> None:
        self._name = name
        self._api_call = api_call

    @property
    def name(self) -> str:
        return self._name

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        prompt = build_prompt(opponent_animal, banned)

        response = self._api_call(prompt)
        build = parse_response(response, banned)
        if build is not None:
            return build

        retry_response = self._api_call(_RETRY_PROMPT)
        build = parse_response(retry_response, banned)
        if build is not None:
            return build

        return GreedyAgent().choose_build(opponent_animal, banned)
