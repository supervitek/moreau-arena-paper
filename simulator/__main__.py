"""Standalone CLI for the Moreau Arena simulator.

Usage:
    # Single match
    python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 100

    # Round-robin
    python -m simulator --round-robin \
        --builds "bear 3 14 2 1" "buffalo 8 6 4 2" "wolf 5 10 3 2" --games 100

    # Series (best-of-7)
    python -m simulator --series --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" \
        --series-count 10
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Position,
    Size,
    StatBlock,
)
from simulator.engine import CombatConfig, CombatEngine, CombatResult
from simulator.grid import Grid
from simulator.seed import seeded_random


def _load_config_hash() -> str:
    """Load config.json and return first 8 chars of SHA-256."""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        return "unknown"
    data = config_path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:8]


def _parse_build(build_str: str) -> tuple[Animal, int, int, int, int]:
    """Parse 'animal hp atk spd wil' string into components.

    Raises ValueError on invalid input.
    """
    parts = build_str.strip().lower().split()
    if len(parts) != 5:
        raise ValueError(
            f"Build must be 'animal hp atk spd wil', got: {build_str!r}"
        )
    animal_name = parts[0]
    try:
        animal = Animal(animal_name)
    except ValueError:
        valid = ", ".join(a.value for a in Animal)
        raise ValueError(
            f"Unknown animal '{animal_name}'. Valid: {valid}"
        )
    try:
        hp, atk, spd, wil = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
    except ValueError:
        raise ValueError(f"Stats must be integers, got: {parts[1:]}")

    total = hp + atk + spd + wil
    if total != 20:
        raise ValueError(f"Stats must sum to 20, got {total} ({hp}+{atk}+{spd}+{wil})")
    for name, val in [("hp", hp), ("atk", atk), ("spd", spd), ("wil", wil)]:
        if val < 1:
            raise ValueError(f"All stats must be >= 1, got {name}={val}")

    return animal, hp, atk, spd, wil


def _compute_derived(hp: int, atk: int, spd: int, wil: int) -> dict[str, Any]:
    """Compute derived stats from raw stat allocation."""
    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)
    return {
        "max_hp": max_hp,
        "base_dmg": base_dmg,
        "dodge": dodge,
        "resist": resist,
    }


def _compute_size(hp: int, atk: int) -> Size:
    """Compute creature size from HP+ATK sum."""
    total = hp + atk
    if total <= 10:
        return Size(1, 1)
    elif total <= 12:
        return Size(2, 1)
    elif total <= 17:
        return Size(2, 2)
    else:
        return Size(3, 2)


def _create_creature(
    animal: Animal, hp: int, atk: int, spd: int, wil: int,
    side: str, match_seed: int,
) -> Creature:
    """Create a Creature from raw build parameters."""
    stats = StatBlock(hp=hp, atk=atk, spd=spd, wil=wil)
    derived = _compute_derived(hp, atk, spd, wil)
    size = _compute_size(hp, atk)
    passive = ANIMAL_PASSIVE.get(animal, list(ANIMAL_PASSIVE.values())[0])
    abilities = ANIMAL_ABILITIES.get(animal, ())

    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)

    if spd <= 3:
        movement = 1
    elif spd <= 6:
        movement = 2
    else:
        movement = 3

    return Creature(
        animal=animal,
        stats=stats,
        passive=passive,
        current_hp=derived["max_hp"],
        max_hp=derived["max_hp"],
        base_dmg=derived["base_dmg"],
        armor_flat=0,
        size=size,
        position=position,
        dodge_chance=derived["dodge"],
        resist_chance=derived["resist"],
        movement_range=movement,
        abilities=abilities,
    )


def _run_games(
    animal_a: Animal, hp_a: int, atk_a: int, spd_a: int, wil_a: int,
    animal_b: Animal, hp_b: int, atk_b: int, spd_b: int, wil_b: int,
    num_games: int, base_seed: int,
    verbose_game: int | None = None,
) -> dict[str, Any]:
    """Run N games between two builds, returning aggregate results."""
    engine = CombatEngine()
    wins_a = 0
    wins_b = 0
    draws = 0
    total_ticks = 0

    for i in range(num_games):
        match_seed = base_seed + i
        creature_a = _create_creature(animal_a, hp_a, atk_a, spd_a, wil_a, "a", match_seed)
        creature_b = _create_creature(animal_b, hp_b, atk_b, spd_b, wil_b, "b", match_seed)

        result = engine.run_combat(creature_a, creature_b, match_seed)
        total_ticks += result.ticks

        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1
        else:
            draws += 1

        if verbose_game is not None and i == verbose_game:
            _print_verbose_log(result, match_seed)

    avg_ticks = total_ticks / num_games if num_games > 0 else 0
    return {
        "wins_a": wins_a,
        "wins_b": wins_b,
        "draws": draws,
        "avg_ticks": avg_ticks,
        "num_games": num_games,
    }


def _print_verbose_log(result: CombatResult, match_seed: int) -> None:
    """Print tick-by-tick combat log for one game."""
    print(f"\n--- Verbose Log (seed={match_seed}) ---")
    for entry in result.log:
        tick = entry["tick"]
        events = entry["events"]
        if not events:
            continue
        for ev in events:
            etype = ev["type"]
            side = ev.get("side", "?")
            if etype == "attack":
                dodged = " (dodged)" if ev.get("dodged") else ""
                print(
                    f"  Tick {tick:2d} | {side} attacks: "
                    f"{ev['damage']} dmg{dodged}, "
                    f"target HP={ev['hp_remaining']}"
                )
            elif etype == "move":
                print(f"  Tick {tick:2d} | {side} moves to {ev['to']}")
            elif etype == "ability_proc":
                print(f"  Tick {tick:2d} | {side} procs {ev['ability']}")
            elif etype == "ability_resisted":
                print(f"  Tick {tick:2d} | {side}'s {ev['ability']} resisted")
            elif etype == "dot":
                print(
                    f"  Tick {tick:2d} | {side} takes {ev['damage']} DOT, "
                    f"HP={ev['hp_remaining']}"
                )
            elif etype == "ring_damage":
                print(
                    f"  Tick {tick:2d} | {side} takes {ev['damage']} ring dmg, "
                    f"HP={ev['hp_remaining']}"
                )
            elif etype == "second_wind":
                print(
                    f"  Tick {tick:2d} | {side} Second Wind! "
                    f"+{ev['heal']} HP={ev['hp_remaining']}"
                )
            elif etype == "skip_attack":
                print(f"  Tick {tick:2d} | {side} skips attack (stunned)")
    print(
        f"  Result: {'a wins' if result.winner == 'a' else 'b wins' if result.winner == 'b' else 'draw'} "
        f"in {result.ticks} ticks ({result.end_condition})"
    )
    print("--- End Verbose Log ---\n")


def _format_build(animal: Animal, hp: int, atk: int, spd: int, wil: int) -> str:
    """Format a build as 'animal hp/atk/spd/wil'."""
    return f"{animal.value} {hp}/{atk}/{spd}/{wil}"


def _format_derived(hp: int, atk: int, spd: int, wil: int) -> str:
    """Format derived stats for display."""
    d = _compute_derived(hp, atk, spd, wil)
    return (
        f"max_hp={d['max_hp']}, base_dmg={d['base_dmg']}, "
        f"dodge={d['dodge']:.1%}, resist={d['resist']:.1%}"
    )


def _run_single(args: argparse.Namespace) -> None:
    """Run single match mode."""
    animal_a, hp_a, atk_a, spd_a, wil_a = _parse_build(args.build1)
    animal_b, hp_b, atk_b, spd_b, wil_b = _parse_build(args.build2)

    config_hash = _load_config_hash()
    print("Moreau Arena \u2014 Standalone Simulator")
    print(f"Config: config.json (hash: {config_hash})")
    print()
    print(f"Build 1: {_format_build(animal_a, hp_a, atk_a, spd_a, wil_a)} ({_format_derived(hp_a, atk_a, spd_a, wil_a)})")
    print(f"Build 2: {_format_build(animal_b, hp_b, atk_b, spd_b, wil_b)} ({_format_derived(hp_b, atk_b, spd_b, wil_b)})")
    print()
    print(f"Simulating {args.games} games...")
    print()

    verbose_game = 0 if args.verbose else None
    results = _run_games(
        animal_a, hp_a, atk_a, spd_a, wil_a,
        animal_b, hp_b, atk_b, spd_b, wil_b,
        args.games, args.seed,
        verbose_game=verbose_game,
    )

    wr_a = results["wins_a"] / results["num_games"] * 100
    wr_b = results["wins_b"] / results["num_games"] * 100

    print("Results:")
    print(f"  Build 1 wins: {results['wins_a']} ({wr_a:.1f}%)")
    print(f"  Build 2 wins: {results['wins_b']} ({wr_b:.1f}%)")
    print(f"  Draws: {results['draws']}")
    print(f"  Avg game length: {results['avg_ticks']:.1f} ticks")
    print()

    if results["wins_a"] > results["wins_b"]:
        print(f"Build 1 ({_format_build(animal_a, hp_a, atk_a, spd_a, wil_a)}) wins.")
    elif results["wins_b"] > results["wins_a"]:
        print(f"Build 2 ({_format_build(animal_b, hp_b, atk_b, spd_b, wil_b)}) wins.")
    else:
        print("Tie!")


def _run_round_robin(args: argparse.Namespace) -> None:
    """Run round-robin mode."""
    builds = []
    for b in args.builds:
        builds.append(_parse_build(b))

    if len(builds) < 2:
        print("Error: need at least 2 builds for round-robin.", file=sys.stderr)
        sys.exit(1)

    config_hash = _load_config_hash()
    print("Moreau Arena \u2014 Round-Robin Mode")
    print(f"Config: config.json (hash: {config_hash})")
    print()

    for i, (animal, hp, atk, spd, wil) in enumerate(builds, 1):
        print(f"Build {i}: {_format_build(animal, hp, atk, spd, wil)} ({_format_derived(hp, atk, spd, wil)})")
    print()
    print(f"Simulating {args.games} games per pair...")
    print()

    n = len(builds)
    # win_rates[i][j] = win rate of build i vs build j
    win_rates: list[list[float | None]] = [[None] * n for _ in range(n)]
    total_wins: list[int] = [0] * n
    total_games: list[int] = [0] * n

    pair_seed = args.seed
    for i in range(n):
        for j in range(i + 1, n):
            ai, hi, ati, si, wi = builds[i]
            aj, hj, atj, sj, wj = builds[j]
            res = _run_games(
                ai, hi, ati, si, wi,
                aj, hj, atj, sj, wj,
                args.games, pair_seed,
            )
            pair_seed += args.games

            wr_i = res["wins_a"] / res["num_games"] if res["num_games"] > 0 else 0
            wr_j = res["wins_b"] / res["num_games"] if res["num_games"] > 0 else 0
            win_rates[i][j] = wr_i
            win_rates[j][i] = wr_j
            total_wins[i] += res["wins_a"]
            total_wins[j] += res["wins_b"]
            total_games[i] += res["num_games"]
            total_games[j] += res["num_games"]

    # Print pairwise matrix
    labels = [f"B{i+1}" for i in range(n)]
    header = f"{'':>8}" + "".join(f"{lbl:>8}" for lbl in labels)
    print("Pairwise Win Rates:")
    print(header)
    for i in range(n):
        row = f"{labels[i]:>8}"
        for j in range(n):
            if i == j:
                row += f"{'--':>8}"
            elif win_rates[i][j] is not None:
                row += f"{win_rates[i][j]:.1%}".rjust(8)
            else:
                row += f"{'?':>8}"
        print(row)
    print()

    # Average win rate
    avg_wrs: list[tuple[float, int]] = []
    for i in range(n):
        avg = total_wins[i] / total_games[i] if total_games[i] > 0 else 0
        avg_wrs.append((avg, i))
    avg_wrs.sort(reverse=True)

    print("Rankings (by average win rate):")
    for rank, (wr, idx) in enumerate(avg_wrs, 1):
        animal, hp, atk, spd, wil = builds[idx]
        print(f"  {rank}. {_format_build(animal, hp, atk, spd, wil)} \u2014 {wr:.1%} avg win rate")


def _run_series(args: argparse.Namespace) -> None:
    """Run series (best-of-7) mode."""
    animal_a, hp_a, atk_a, spd_a, wil_a = _parse_build(args.build1)
    animal_b, hp_b, atk_b, spd_b, wil_b = _parse_build(args.build2)

    config_hash = _load_config_hash()
    print("Moreau Arena \u2014 Series Mode (best-of-7)")
    print(f"Config: config.json (hash: {config_hash})")
    print()
    print(f"Build 1: {_format_build(animal_a, hp_a, atk_a, spd_a, wil_a)} ({_format_derived(hp_a, atk_a, spd_a, wil_a)})")
    print(f"Build 2: {_format_build(animal_b, hp_b, atk_b, spd_b, wil_b)} ({_format_derived(hp_b, atk_b, spd_b, wil_b)})")
    print()
    print(f"Simulating {args.series_count} best-of-7 series...")
    print()

    engine = CombatEngine()
    series_wins_a = 0
    series_wins_b = 0
    total_games_played = 0

    for s in range(args.series_count):
        series_seed = args.seed + s * 100
        game_wins_a = 0
        game_wins_b = 0

        for g in range(7):
            if game_wins_a >= 4 or game_wins_b >= 4:
                break

            match_seed = series_seed + g
            creature_a = _create_creature(animal_a, hp_a, atk_a, spd_a, wil_a, "a", match_seed)
            creature_b = _create_creature(animal_b, hp_b, atk_b, spd_b, wil_b, "b", match_seed)

            result = engine.run_combat(creature_a, creature_b, match_seed)
            total_games_played += 1

            if result.winner == "a":
                game_wins_a += 1
            elif result.winner == "b":
                game_wins_b += 1

        if game_wins_a > game_wins_b:
            series_wins_a += 1
        elif game_wins_b > game_wins_a:
            series_wins_b += 1

    print("Series Results:")
    print(f"  Build 1 wins: {series_wins_a}/{args.series_count} series")
    print(f"  Build 2 wins: {series_wins_b}/{args.series_count} series")
    print(f"  Total games played: {total_games_played}")
    print()

    if series_wins_a > series_wins_b:
        print(f"Build 1 ({_format_build(animal_a, hp_a, atk_a, spd_a, wil_a)}) wins {series_wins_a}/{args.series_count} series.")
    elif series_wins_b > series_wins_a:
        print(f"Build 2 ({_format_build(animal_b, hp_b, atk_b, spd_b, wil_b)}) wins {series_wins_b}/{args.series_count} series.")
    else:
        print("Series tied!")


def main() -> None:
    """Entry point for the simulator CLI."""
    parser = argparse.ArgumentParser(
        description="Moreau Arena \u2014 Standalone Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 100\n'
            '  python -m simulator --round-robin --builds "bear 3 14 2 1" "buffalo 8 6 4 2" "wolf 5 10 3 2" --games 100\n'
            '  python -m simulator --series --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --series-count 10\n'
        ),
    )

    # Mode flags
    parser.add_argument(
        "--round-robin", action="store_true",
        help="Run round-robin between multiple builds",
    )
    parser.add_argument(
        "--series", action="store_true",
        help="Run best-of-7 series between two builds",
    )

    # Build arguments
    parser.add_argument(
        "--build1", type=str,
        help='First build: "animal hp atk spd wil"',
    )
    parser.add_argument(
        "--build2", type=str,
        help='Second build: "animal hp atk spd wil"',
    )
    parser.add_argument(
        "--builds", nargs="+", type=str,
        help='Multiple builds for round-robin: "animal hp atk spd wil" ...',
    )

    # Simulation parameters
    parser.add_argument(
        "--games", type=int, default=100,
        help="Number of games per pair (default: 100)",
    )
    parser.add_argument(
        "--series-count", type=int, default=10,
        help="Number of series to run in series mode (default: 10)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print tick-by-tick combat log for one game",
    )

    args = parser.parse_args()

    try:
        if args.round_robin:
            if not args.builds or len(args.builds) < 2:
                parser.error("--round-robin requires --builds with at least 2 builds")
            _run_round_robin(args)
        elif args.series:
            if not args.build1 or not args.build2:
                parser.error("--series requires --build1 and --build2")
            _run_series(args)
        else:
            if not args.build1 or not args.build2:
                parser.error("Single match mode requires --build1 and --build2")
            _run_single(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
