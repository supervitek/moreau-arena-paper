"""ScriptAgent — a BaseAgent that runs Moreau Script (.ms) files.

Loads a .ms script, parses/validates it once, then uses the interpreter
in choose_build() to produce a valid Build each round.
"""

from __future__ import annotations

import random

from agents.baselines import BaseAgent, Build
from simulator.animals import Animal

from moreau_script.parser import parse_file, Rule
from moreau_script.validator import validate, VALID_ANIMALS
from moreau_script.interpreter import interpret, GameContext


# Map uppercase animal names to Animal enum values
_ANIMAL_MAP: dict[str, Animal] = {a.value.upper(): a for a in Animal}

# Default build used when the script produces something invalid
_DEFAULT_BUILD = Build(animal=Animal.BEAR, hp=5, atk=5, spd=5, wil=5)


class ScriptAgent(BaseAgent):
    """An agent driven by a Moreau Script (.ms) file.

    Parses and validates the script once at construction time.
    Each call to choose_build() runs the interpreter with the current
    game context and returns a valid Build.

    Args:
        script_path: Path to the .ms file.
    """

    def __init__(self, script_path: str) -> None:
        self._script_path = script_path
        self._rules: list[Rule] = []
        self._valid = False
        self._last_opponent_build: dict[str, int] | None = None

        # Parse and validate once
        try:
            self._rules = parse_file(script_path)
            with open(script_path, "r", encoding="utf-8") as f:
                source = f.read()
            errors = validate(self._rules, source)
            if errors:
                self._valid = False
                self._errors = errors
            else:
                self._valid = True
                self._errors = []
        except (SyntaxError, FileNotFoundError, OSError) as e:
            self._valid = False
            self._errors = [str(e)]

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        """Choose a build using the loaded Moreau Script.

        Args:
            opponent_animal: The opponent's animal, or None.
            banned: Animals that cannot be picked.
            opponent_reveal: Optional partial stat reveal.

        Returns:
            A valid Build with stats summing to 20, all >= 1.
        """
        if not self._valid:
            return self._default_build(banned)

        # Build game context
        opp_animal_str = opponent_animal.value.upper() if opponent_animal else None

        # Extract opponent reveal info if available
        opp_build_dict: dict[str, int] | None = None
        if opponent_reveal is not None:
            revealed = getattr(opponent_reveal, "revealed_stats", None)
            if revealed and isinstance(revealed, dict):
                opp_build_dict = revealed
        if opp_build_dict is None:
            opp_build_dict = self._last_opponent_build

        ctx = GameContext(
            opponent_animal=opp_animal_str,
            opponent_last_build=opp_build_dict,
            my_hp_pct=100,
        )

        # Run interpreter
        try:
            build_dict = interpret(self._rules, ctx)
        except Exception:
            return self._default_build(banned)

        # Convert to Build object
        return self._build_from_dict(build_dict, banned)

    def _build_from_dict(
        self,
        build_dict: dict,
        banned: list[Animal],
    ) -> Build:
        """Convert an interpreter output dict to a valid Build.

        Falls back to defaults if the dict produces invalid results.
        """
        # Resolve animal
        animal_name = build_dict.get("animal", "BEAR").upper()
        animal = _ANIMAL_MAP.get(animal_name)

        if animal is None or animal in banned:
            # Pick first unbanned valid animal
            animal = self._pick_unbanned(banned)
            if animal is None:
                return _DEFAULT_BUILD

        # Resolve stats
        hp = build_dict.get("hp", 5)
        atk = build_dict.get("atk", 5)
        spd = build_dict.get("spd", 5)
        wil = build_dict.get("wil", 5)

        # Ensure all >= 1
        hp = max(1, hp)
        atk = max(1, atk)
        spd = max(1, spd)
        wil = max(1, wil)

        # Ensure sum == 20
        total = hp + atk + spd + wil
        if total != 20:
            # Scale proportionally
            if total > 0:
                factor = 16.0 / (total - 4) if total > 4 else 1.0
                hp = max(1, round(1 + (hp - 1) * factor))
                atk = max(1, round(1 + (atk - 1) * factor))
                spd = max(1, round(1 + (spd - 1) * factor))
                wil = max(1, round(1 + (wil - 1) * factor))

            # Final fixup: adjust wil to make sum exactly 20
            total = hp + atk + spd + wil
            diff = 20 - total
            wil = wil + diff
            if wil < 1:
                # Redistribute from other stats
                wil = 1
                total = hp + atk + spd + wil
                diff = 20 - total
                if diff > 0:
                    atk += diff
                elif diff < 0:
                    # Reduce largest stat
                    for _ in range(-diff):
                        vals = {"hp": hp, "atk": atk, "spd": spd}
                        biggest = max(vals, key=lambda k: vals[k])
                        if biggest == "hp" and hp > 1:
                            hp -= 1
                        elif biggest == "atk" and atk > 1:
                            atk -= 1
                        elif biggest == "spd" and spd > 1:
                            spd -= 1

        try:
            return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
        except (ValueError, TypeError):
            return self._default_build(banned)

    def _pick_unbanned(self, banned: list[Animal]) -> Animal | None:
        """Pick the first unbanned animal from the valid set."""
        # Only pick from the 14 core animals
        core_animals = [
            a for a in Animal
            if a.value.upper() in VALID_ANIMALS and a not in banned
        ]
        if not core_animals:
            return None
        return core_animals[0]

    def _default_build(self, banned: list[Animal]) -> Build:
        """Return a safe default build with an unbanned animal."""
        animal = self._pick_unbanned(banned)
        if animal is None:
            # Absolute fallback
            available = [a for a in Animal if a not in banned]
            if not available:
                return _DEFAULT_BUILD
            animal = available[0]
        return Build(animal=animal, hp=5, atk=5, spd=5, wil=5)
