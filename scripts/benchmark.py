#!/usr/bin/env python3
"""Moreau Arena — Performance Benchmark
Times 1000 fights and reports M4 performance stats.
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.animals import Animal, Creature, Size, StatBlock, ANIMAL_ABILITIES, ANIMAL_PASSIVE
from simulator.engine import CombatEngine
from simulator.grid import Grid
import math


def compute_derived(hp, atk, spd, wil):
    return {
        "max_hp": 50 + 10 * hp,
        "base_dmg": math.floor(2 + 0.85 * atk),
        "dodge": max(0.0, min(0.30, 0.025 * (spd - 1))),
        "resist": min(0.60, wil * 0.033),
    }


def compute_size(hp, atk):
    total = hp + atk
    if total <= 10:
        return Size(1, 1)
    elif total <= 12:
        return Size(2, 1)
    elif total <= 17:
        return Size(2, 2)
    else:
        return Size(3, 2)


def create_creature(animal, hp, atk, spd, wil, side, match_seed):
    stats = StatBlock(hp=hp, atk=atk, spd=spd, wil=wil)
    derived = compute_derived(hp, atk, spd, wil)
    size = compute_size(hp, atk)
    passive = ANIMAL_PASSIVE.get(animal, list(ANIMAL_PASSIVE.values())[0])
    abilities = ANIMAL_ABILITIES.get(animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)
    return Creature(
        animal=animal, stats=stats, passive=passive,
        current_hp=derived["max_hp"], max_hp=derived["max_hp"],
        base_dmg=derived["base_dmg"], armor_flat=0, size=size,
        position=position, dodge_chance=derived["dodge"],
        resist_chance=derived["resist"], movement_range=movement,
        abilities=abilities,
    )


BUILDS = [
    (Animal("bear"), 3, 14, 2, 1, Animal("buffalo"), 8, 6, 4, 2),
    (Animal("wolf"), 5, 10, 3, 2, Animal("eagle"), 2, 8, 6, 4),
    (Animal("bear"), 10, 5, 3, 2, Animal("wolf"), 3, 12, 3, 2),
    (Animal("buffalo"), 6, 8, 4, 2, Animal("eagle"), 4, 10, 4, 2),
    (Animal("bear"), 7, 7, 3, 3, Animal("bear"), 3, 14, 2, 1),
]


def run_benchmark(n_games=1000):
    print(f"Moreau Arena Benchmark — {n_games} fights")
    print(f"{'=' * 50}")

    engine = CombatEngine()
    total_ticks = 0
    wins_a = 0
    wins_b = 0
    draws = 0

    start = time.perf_counter()

    for i in range(n_games):
        b = BUILDS[i % len(BUILDS)]
        seed = 42 + i
        ca = create_creature(b[0], b[1], b[2], b[3], b[4], "a", seed)
        cb = create_creature(b[5], b[6], b[7], b[8], b[9], "b", seed)
        result = engine.run_combat(ca, cb, seed)
        total_ticks += result.ticks
        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1
        else:
            draws += 1

    elapsed = time.perf_counter() - start

    print(f"\nResults:")
    print(f"  Build A wins:  {wins_a:>5} ({wins_a / n_games * 100:.1f}%)")
    print(f"  Build B wins:  {wins_b:>5} ({wins_b / n_games * 100:.1f}%)")
    print(f"  Draws:         {draws:>5} ({draws / n_games * 100:.1f}%)")
    print(f"\nPerformance:")
    print(f"  Total time:    {elapsed:.3f}s")
    print(f"  Per fight:     {elapsed / n_games * 1000:.2f}ms")
    print(f"  Fights/sec:    {n_games / elapsed:.0f}")
    print(f"  Avg ticks:     {total_ticks / n_games:.1f}")
    print(f"  Platform:      Mac Mini M4")
    print(f"  Python:        {sys.version.split()[0]}")

    return elapsed


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run_benchmark(n)
