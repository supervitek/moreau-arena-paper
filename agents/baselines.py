"""External-facing agent interface for LLM agents.

This module provides a simplified, draft-aware agent interface designed for
external LLM agents to plug into via API calls.

- Build is flat: animal + 4 stats, no mutations
- choose_build receives opponent_animal and banned list (draft-aware)

Standalone version for the companion repository.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from simulator.animals import Animal
from simulator.seed import seeded_random, derive_hit_seed


@dataclass(frozen=True)
class Build:
    """Flat build for external agents: animal + 4 stats, no mutations."""

    animal: Animal
    hp: int
    atk: int
    spd: int
    wil: int

    def __post_init__(self) -> None:
        total = self.hp + self.atk + self.spd + self.wil
        if total != 20:
            raise ValueError(f"Stats must sum to 20, got {total}")
        for name in ("hp", "atk", "spd", "wil"):
            if getattr(self, name) < 1:
                raise ValueError(
                    f"All stats must be >= 1, got {name}={getattr(self, name)}"
                )


class BaseAgent(ABC):
    """Abstract base class for external-facing agents."""

    @abstractmethod
    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        """Choose a build given draft context.

        Args:
            opponent_animal: The opponent's chosen animal, or None if unknown.
            banned: List of animals that cannot be picked.
            opponent_reveal: Optional OpponentReveal with partial stat info.

        Returns:
            A valid Build with stats summing to 20, all >= 1.
        """
        ...


class RandomAgent(BaseAgent):
    """Picks a random unbanned animal with random valid stat allocation."""

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        available = [a for a in Animal if a not in banned]
        if not available:
            raise ValueError("All animals are banned")

        animal_idx = int(
            seeded_random(self._seed, 0, len(available) - 0.001)
        )
        animal = available[animal_idx]

        stats = self._random_stats(self._seed + 1)
        return Build(
            animal=animal, hp=stats[0], atk=stats[1], spd=stats[2], wil=stats[3]
        )

    def _random_stats(self, seed: int) -> tuple[int, int, int, int]:
        remaining = 16  # 20 - 4 (min 1 each)
        values = [1, 1, 1, 1]
        for i in range(4):
            sub_seed = derive_hit_seed(seed, 0, i)
            if i == 3:
                values[i] += remaining
            else:
                max_alloc = min(remaining, 16)
                if max_alloc > 0:
                    alloc = int(seeded_random(sub_seed, 0, max_alloc + 0.999))
                    alloc = max(0, min(alloc, remaining))
                    values[i] += alloc
                    remaining -= alloc
        return (values[0], values[1], values[2], values[3])


_GREEDY_FALLBACKS: list[tuple[Animal, int, int, int, int]] = [
    (Animal.BOAR, 8, 8, 3, 1),
    (Animal.BUFFALO, 8, 6, 4, 2),
    (Animal.BEAR, 5, 5, 5, 5),
]


class GreedyAgent(BaseAgent):
    """Always returns the best known tournament build.

    Primary: Boar 8/8/3/1 (highest WR in Phase 2).
    Falls back to Buffalo 8/6/4/2 then Bear 5/5/5/5 if banned.
    """

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        for animal, hp, atk, spd, wil in _GREEDY_FALLBACKS:
            if animal not in banned:
                return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
        raise ValueError("All fallback animals are banned")


# -- Counter-pick table for SmartAgent -----------------------------------------
# Empirically validated: each counter tested at 100-200 matches vs target.
_COUNTER_PICKS: dict[Animal, list[tuple[Animal, int, int, int, int]]] = {
    Animal.BOAR: [
        (Animal.BEAR, 3, 14, 2, 1),
        (Animal.BOAR, 7, 9, 3, 1),
    ],
    Animal.TIGER: [
        (Animal.BEAR, 4, 13, 2, 1),
        (Animal.BOAR, 8, 8, 3, 1),
    ],
    Animal.BEAR: [
        (Animal.BEAR, 5, 11, 3, 1),
        (Animal.BOAR, 9, 8, 2, 1),
    ],
    Animal.BUFFALO: [
        (Animal.BUFFALO, 7, 7, 4, 2),
        (Animal.BEAR, 4, 12, 3, 1),
    ],
    Animal.WOLF: [
        (Animal.BUFFALO, 8, 6, 4, 2),
        (Animal.BOAR, 8, 8, 3, 1),
    ],
    Animal.MONKEY: [
        (Animal.BEAR, 3, 14, 2, 1),
        (Animal.BOAR, 8, 8, 3, 1),
    ],
}

_DEFAULT_BUILDS: list[tuple[Animal, int, int, int, int]] = [
    (Animal.BEAR, 3, 14, 2, 1),
    (Animal.BOAR, 8, 8, 3, 1),
    (Animal.BUFFALO, 7, 7, 4, 2),
]


class SmartAgent(BaseAgent):
    """Strategic counter-picking agent with empirically-validated builds.

    Counter-picks tested at 200 matches each:
    - vs Boar: Bear 3/14/2/1 (82% WR)
    - vs Tiger: Bear 4/13/2/1 (99% WR)
    - vs Bear: Bear 5/11/3/1 (87% WR)
    - vs Buffalo: Buffalo 7/7/4/2 (82% WR)
    - vs Wolf: Buffalo 8/6/4/2 (100% WR)
    - vs Monkey: Bear 3/14/2/1 (98% WR)
    - Default: Bear 3/14/2/1 (strongest generalist)
    """

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        if opponent_reveal is not None and opponent_animal is not None:
            adapted = self._adapt_to_reveal(opponent_animal, banned, opponent_reveal)
            if adapted is not None:
                return adapted

        if opponent_animal is not None:
            candidates = _COUNTER_PICKS.get(opponent_animal, _DEFAULT_BUILDS)
        else:
            candidates = _DEFAULT_BUILDS

        for animal, hp, atk, spd, wil in candidates:
            if animal not in banned:
                return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)

        for animal, hp, atk, spd, wil in _DEFAULT_BUILDS:
            if animal not in banned:
                return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)

        raise ValueError("All counter-pick animals are banned")

    def _adapt_to_reveal(
        self,
        opponent_animal: Animal,
        banned: list[Animal],
        reveal: object,
    ) -> Build | None:
        revealed = getattr(reveal, "revealed_stats", None)
        if revealed is None:
            return None

        opp_atk = revealed.get("atk")
        if opp_atk is None:
            return None

        if opp_atk >= 10:
            tank_builds: list[tuple[Animal, int, int, int, int]] = [
                (Animal.BEAR, 7, 9, 3, 1),
                (Animal.BUFFALO, 9, 5, 4, 2),
                (Animal.BOAR, 9, 7, 3, 1),
            ]
            for animal, hp, atk, spd, wil in tank_builds:
                if animal not in banned:
                    return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)

        if opp_atk < 7:
            aggro_builds: list[tuple[Animal, int, int, int, int]] = [
                (Animal.BEAR, 3, 14, 2, 1),
                (Animal.BOAR, 5, 11, 3, 1),
            ]
            for animal, hp, atk, spd, wil in aggro_builds:
                if animal not in banned:
                    return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)

        return None


# -- Conservative and HighVariance agents --------------------------------------

_CONSERVATIVE_BUILDS: list[tuple[Animal, int, int, int, int]] = [
    (Animal.BUFFALO, 8, 6, 4, 2),
    (Animal.BOAR, 8, 7, 3, 2),
    (Animal.BEAR, 7, 7, 3, 3),
    (Animal.WOLF, 7, 5, 4, 4),
    (Animal.SNAKE, 7, 5, 4, 4),
    (Animal.SCORPION, 7, 6, 4, 3),
    (Animal.EAGLE, 6, 6, 5, 3),
    (Animal.TIGER, 6, 5, 6, 3),
    (Animal.FOX, 6, 5, 5, 4),
    (Animal.MONKEY, 6, 6, 5, 3),
]


class ConservativeAgent(BaseAgent):
    """High-DEF, low-variance agent that favors tanky, survivable builds."""

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        for animal, hp, atk, spd, wil in _CONSERVATIVE_BUILDS:
            if animal not in banned:
                return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
        available = [a for a in Animal if a not in banned]
        if not available:
            raise ValueError("All animals are banned")
        return Build(animal=available[0], hp=5, atk=5, spd=5, wil=5)


_HIGH_VARIANCE_BUILDS: list[tuple[Animal, int, int, int, int]] = [
    (Animal.BEAR, 3, 14, 2, 1),
    (Animal.TIGER, 1, 3, 15, 1),
    (Animal.EAGLE, 1, 15, 3, 1),
    (Animal.SNAKE, 1, 3, 3, 13),
    (Animal.WOLF, 1, 14, 2, 3),
    (Animal.SCORPION, 2, 12, 3, 3),
    (Animal.FOX, 2, 3, 12, 3),
    (Animal.MONKEY, 1, 13, 3, 3),
    (Animal.BOAR, 4, 13, 2, 1),
    (Animal.BUFFALO, 3, 12, 4, 1),
    (Animal.CROCODILE, 2, 14, 2, 2),
    (Animal.RAVEN, 1, 3, 13, 3),
    (Animal.SHARK, 3, 11, 3, 3),
    (Animal.OWL, 1, 3, 3, 13),
]


class HighVarianceAgent(BaseAgent):
    """Extreme stat allocations and risky animal picks."""

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        available = [
            (a, hp, atk, spd, wil)
            for a, hp, atk, spd, wil in _HIGH_VARIANCE_BUILDS
            if a not in banned
        ]
        if not available:
            unbanned = [a for a in Animal if a not in banned]
            if not unbanned:
                raise ValueError("All animals are banned")
            return Build(animal=unbanned[0], hp=1, atk=15, spd=3, wil=1)

        idx = self._seed % len(available)
        animal, hp, atk, spd, wil = available[idx]
        return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
