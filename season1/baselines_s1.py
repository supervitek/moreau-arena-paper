"""Season 1 baseline agents for Moreau Arena.

Five agent classes using S1Animal (14 animals) and season1.engine_s1.run_match.

Interface:
    choose_build(opponent_animal: str | None, banned: list[str]) -> dict
    Returns {"animal": "name", "hp": N, "atk": N, "spd": N, "wil": N}
    stats sum to 20, each min 1.
"""

from __future__ import annotations

import json
import os
import random
import sys
from abc import ABC, abstractmethod

# Allow `python3 season1/baselines_s1.py` (direct invocation from project root)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from season1.animals_s1 import S1Animal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_ANIMALS: list[str] = [a.value for a in S1Animal]

_BALANCE_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "balance_results.json")
_PAIRWISE_MATRIX_PATH = os.path.join(os.path.dirname(__file__), "pairwise_matrix.csv")


def _validate_build(animal: str, hp: int, atk: int, spd: int, wil: int) -> dict:
    """Validate stats and return build dict."""
    # Validate animal
    S1Animal(animal)  # raises ValueError if invalid
    total = hp + atk + spd + wil
    if total != 20:
        raise ValueError(f"Stats must sum to 20, got {total}")
    for name, val in (("hp", hp), ("atk", atk), ("spd", spd), ("wil", wil)):
        if val < 1:
            raise ValueError(f"All stats must be >= 1, got {name}={val}")
    return {"animal": animal, "hp": hp, "atk": atk, "spd": spd, "wil": wil}


def _load_pairwise() -> dict[str, dict[str, float]]:
    """Load pairwise win-rate matrix from CSV.

    Returns nested dict: matrix[row_animal][col_animal] = win_rate of row vs col.
    """
    matrix: dict[str, dict[str, float]] = {}
    with open(_PAIRWISE_MATRIX_PATH) as f:
        lines = f.read().splitlines()
    header = lines[0].split(",")
    col_animals = header[1:]  # first cell is empty
    for line in lines[1:]:
        parts = line.split(",")
        row_animal = parts[0]
        matrix[row_animal] = {}
        for col_animal, val in zip(col_animals, parts[1:]):
            if val:
                matrix[row_animal][col_animal] = float(val)
    return matrix


# Loaded once at module level for SmartAgent_S1
_PAIRWISE: dict[str, dict[str, float]] = _load_pairwise()


def _best_counter(opponent: str, banned: list[str]) -> str | None:
    """Return the animal with the highest win rate vs opponent (excluding banned)."""
    if opponent not in _PAIRWISE:
        return None
    matchups = _PAIRWISE  # matrix[row][col] = row's WR vs col
    # For each candidate animal, find its WR vs opponent
    best_animal: str | None = None
    best_wr = -1.0
    for candidate in _ALL_ANIMALS:
        if candidate in banned:
            continue
        wr = matchups.get(candidate, {}).get(opponent, 0.0)
        if wr > best_wr:
            best_wr = wr
            best_animal = candidate
    return best_animal


# ---------------------------------------------------------------------------
# Stat heuristics for SmartAgent_S1
# ---------------------------------------------------------------------------

# Stat allocation strategy per chosen animal (based on passive/ability profile):
# fox: SPD-focused (Cunning dodge charges), some ATK
# tiger: SPD for Ambush Wiring opener, high ATK
# porcupine: HP-focused (survive to reflect via Quill Armor)
# rhino: balanced tank (Bulwark Frame + Fortify)
# eagle: SPD + ATK (Aerial Advantage + Dive)
# wolf: ATK + SPD (Pack Howl/Rend)
# scorpion: ATK + WIL (Envenom DoT + anti-heal)
# buffalo: HP tank (Thick Hide + Iron Will)
# monkey: SPD/WIL for Primate Cortex
# bear: ATK burst (Berserker Rage + Last Stand)
# viper: WIL + ATK (Hemotoxin DoT)
# panther: SPD stealth opener (Shadow Stalk)
# boar: ATK (Charge opener)
# vulture: WIL + HP (Carrion Feeder sustain)

_SMART_STAT_ALLOCS: dict[str, tuple[int, int, int, int]] = {
    # animal: (hp, atk, spd, wil)
    "fox":       (4,  7,  7,  2),
    "tiger":     (3,  8,  7,  2),
    "porcupine": (8,  4,  5,  3),
    "rhino":     (7,  6,  4,  3),
    "eagle":     (3,  8,  7,  2),
    "wolf":      (4,  8,  6,  2),
    "scorpion":  (4,  8,  4,  4),
    "buffalo":   (10, 4,  3,  3),
    "monkey":    (4,  6,  6,  4),
    "bear":      (3,  13, 3,  1),
    "viper":     (4,  7,  4,  5),
    "panther":   (3,  7,  8,  2),
    "boar":      (4,  12, 3,  1),
    "vulture":   (6,  5,  4,  5),
}


def _smart_build(animal: str) -> dict:
    hp, atk, spd, wil = _SMART_STAT_ALLOCS[animal]
    return _validate_build(animal, hp, atk, spd, wil)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class S1BaseAgent(ABC):
    """Abstract base class for Season 1 agents."""

    @abstractmethod
    def choose_build(
        self,
        opponent_animal: str | None,
        banned: list[str],
    ) -> dict:
        """Choose a build given draft context.

        Args:
            opponent_animal: Opponent's chosen animal name (lowercase), or None.
            banned: List of animal name strings that cannot be picked.

        Returns:
            dict with keys: animal, hp, atk, spd, wil
            Stats sum to 20, each >= 1.
        """
        ...


# ---------------------------------------------------------------------------
# RandomAgent_S1
# ---------------------------------------------------------------------------

class RandomAgent_S1(S1BaseAgent):
    """Picks a random unbanned animal with a random valid stat allocation."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def choose_build(
        self,
        opponent_animal: str | None,
        banned: list[str],
    ) -> dict:
        available = [a for a in _ALL_ANIMALS if a not in banned]
        if not available:
            raise ValueError("All animals are banned")

        animal = self._rng.choice(available)

        # Random stats: distribute 16 extra points across 4 slots (each starts at 1)
        extra = 16
        cuts = sorted(self._rng.sample(range(extra + 1), 3))
        slices = [cuts[0], cuts[1] - cuts[0], cuts[2] - cuts[1], extra - cuts[2]]
        hp, atk, spd, wil = (1 + s for s in slices)

        return _validate_build(animal, hp, atk, spd, wil)


# ---------------------------------------------------------------------------
# GreedyAgent_S1
# ---------------------------------------------------------------------------

# Primary: fox (57.1% overall WR), fallbacks in WR order
_GREEDY_FALLBACKS_S1: list[tuple[str, int, int, int, int]] = [
    # (animal, hp, atk, spd, wil)
    ("fox",       4,  7,  7,  2),   # 1st: highest WR — SPD dodge + ATK
    ("tiger",     3,  8,  7,  2),   # 2nd: Ambush Wiring + SPD
    ("porcupine", 8,  4,  5,  3),   # 3rd: HP to survive & reflect
]


class GreedyAgent_S1(S1BaseAgent):
    """Always picks the best overall-WR animal with an optimised fixed build.

    Priority: fox 4/7/7/2 → tiger 3/8/7/2 → porcupine 8/4/5/3.
    """

    def choose_build(
        self,
        opponent_animal: str | None,
        banned: list[str],
    ) -> dict:
        for animal, hp, atk, spd, wil in _GREEDY_FALLBACKS_S1:
            if animal not in banned:
                return _validate_build(animal, hp, atk, spd, wil)
        # Last resort: pick highest-WR available animal with balanced stats
        available = [a for a in _ALL_ANIMALS if a not in banned]
        if not available:
            raise ValueError("All animals are banned")
        return _validate_build(available[0], 5, 5, 5, 5)


# ---------------------------------------------------------------------------
# ConservativeAgent_S1
# ---------------------------------------------------------------------------

_CONSERVATIVE_BUILDS_S1: list[tuple[str, int, int, int, int]] = [
    # Maximise HP for Iron Will heal and Thick Hide mitigation
    ("buffalo",   10, 4,  3,  3),
    ("rhino",     10, 4,  3,  3),
    ("porcupine",  9, 4,  4,  3),
    ("bear",       8, 5,  4,  3),
    ("wolf",       7, 5,  5,  3),
    ("scorpion",   7, 6,  4,  3),
    ("eagle",      6, 5,  6,  3),
    ("tiger",      6, 5,  6,  3),
    ("fox",        6, 5,  5,  4),
    ("monkey",     6, 5,  5,  4),
    ("viper",      6, 5,  4,  5),
    ("panther",    6, 5,  6,  3),
    ("boar",       7, 6,  4,  3),
    ("vulture",    7, 4,  4,  5),
]


class ConservativeAgent_S1(S1BaseAgent):
    """High-HP, low-variance agent — maximises survivability.

    Primary: buffalo 10/4/3/3 (Thick Hide + Iron Will tank).
    Falls back through rhino then other tanky animals.
    """

    def choose_build(
        self,
        opponent_animal: str | None,
        banned: list[str],
    ) -> dict:
        for animal, hp, atk, spd, wil in _CONSERVATIVE_BUILDS_S1:
            if animal not in banned:
                return _validate_build(animal, hp, atk, spd, wil)
        available = [a for a in _ALL_ANIMALS if a not in banned]
        if not available:
            raise ValueError("All animals are banned")
        return _validate_build(available[0], 8, 4, 4, 4)


# ---------------------------------------------------------------------------
# HighVarianceAgent_S1
# ---------------------------------------------------------------------------

_HIGH_VARIANCE_BUILDS_S1: list[tuple[str, int, int, int, int]] = [
    # Glass cannons: min defensive stats, max burst
    ("tiger",     1, 14, 4,  1),   # Max ATK for Ambush Wiring 2x opener
    ("eagle",     1, 12, 6,  1),   # ATK + SPD for Dive burst
    ("boar",      1, 14, 4,  1),   # Max ATK Charge opener
    ("fox",       1,  4, 14, 1),   # Max SPD — extreme dodge builds
    ("wolf",      1, 14, 4,  1),   # ATK burst
    ("bear",      1, 16, 2,  1),   # Berserker Rage + max ATK
    ("panther",   1,  3, 15, 1),   # Max SPD Shadow Stalk
    ("scorpion",  1, 14, 4,  1),   # ATK + Envenom
    ("viper",     1,  8, 4,  7),   # WIL + Hemotoxin DoT
    ("porcupine", 1, 14, 4,  1),   # ATK to proc Quill Armor on opponent quickly
    ("monkey",    1, 13, 5,  1),   # Chaos Strike ATK burst
    ("rhino",     1, 14, 4,  1),   # Horn Charge ATK burst
    ("buffalo",   1, 15, 3,  1),   # Iron Will gamble
    ("vulture",   1,  4, 4, 11),   # Max WIL Carrion Feeder sustain
]


class HighVarianceAgent_S1(S1BaseAgent):
    """Extreme glass-cannon builds — high ATK or SPD, minimal survivability.

    Cycles through high-variance presets based on a seed.
    """

    def __init__(self, seed: int = 0) -> None:
        self._seed = seed

    def choose_build(
        self,
        opponent_animal: str | None,
        banned: list[str],
    ) -> dict:
        available = [
            (animal, hp, atk, spd, wil)
            for animal, hp, atk, spd, wil in _HIGH_VARIANCE_BUILDS_S1
            if animal not in banned
        ]
        if not available:
            unbanned = [a for a in _ALL_ANIMALS if a not in banned]
            if not unbanned:
                raise ValueError("All animals are banned")
            return _validate_build(unbanned[0], 1, 16, 2, 1)

        idx = self._seed % len(available)
        animal, hp, atk, spd, wil = available[idx]
        return _validate_build(animal, hp, atk, spd, wil)


# ---------------------------------------------------------------------------
# SmartAgent_S1
# ---------------------------------------------------------------------------

class SmartAgent_S1(S1BaseAgent):
    """Counter-picking agent using pairwise win-rate data from balance_results.json.

    For each opponent animal, selects the animal with the highest historical
    win rate vs that opponent, then applies sensible stat heuristics.

    Default (opponent unknown): fox 4/7/7/2.
    """

    def choose_build(
        self,
        opponent_animal: str | None,
        banned: list[str],
    ) -> dict:
        if opponent_animal is not None:
            counter = _best_counter(opponent_animal, banned)
            if counter is not None:
                return _smart_build(counter)

        # Default: fox (highest overall WR)
        if "fox" not in banned:
            return _smart_build("fox")

        # Fallback: pick highest-overall-WR available animal
        wr_order = [
            "fox", "tiger", "porcupine", "rhino", "eagle", "wolf",
            "scorpion", "buffalo", "monkey", "bear", "viper", "panther",
            "boar", "vulture",
        ]
        for animal in wr_order:
            if animal not in banned:
                return _smart_build(animal)

        raise ValueError("All animals are banned")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from season1.engine_s1 import run_match

    def _run_series(
        agent_a: S1BaseAgent,
        agent_b: S1BaseAgent,
        n: int,
        name_a: str,
        name_b: str,
        base_seed: int = 0,
    ) -> None:
        wins_a = wins_b = draws = 0
        for i in range(n):
            build_a = agent_a.choose_build(None, [])
            build_b = agent_b.choose_build(build_a["animal"], [])
            stats_a = (build_a["hp"], build_a["atk"], build_a["spd"], build_a["wil"])
            stats_b = (build_b["hp"], build_b["atk"], build_b["spd"], build_b["wil"])
            result = run_match(
                build_a["animal"], stats_a,
                build_b["animal"], stats_b,
                seed=base_seed + i,
            )
            if result["winner"] == "a":
                wins_a += 1
            elif result["winner"] == "b":
                wins_b += 1
            else:
                draws += 1

        total = wins_a + wins_b + draws
        print(
            f"{name_a} vs {name_b} ({n} games): "
            f"{name_a} {wins_a/total:.1%}  |  "
            f"{name_b} {wins_b/total:.1%}  |  "
            f"draws {draws/total:.1%}"
        )

    print("=== Season 1 Baseline Self-Test ===\n")

    smart = SmartAgent_S1()
    random_agent = RandomAgent_S1(seed=42)
    greedy = GreedyAgent_S1()
    conservative = ConservativeAgent_S1()
    high_var = HighVarianceAgent_S1(seed=7)

    _run_series(smart, random_agent, 100, "SmartAgent_S1", "RandomAgent_S1", base_seed=1000)
    _run_series(greedy, conservative, 100, "GreedyAgent_S1", "ConservativeAgent_S1", base_seed=2000)

    print("\nDone.")
