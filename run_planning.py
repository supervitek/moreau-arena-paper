#!/usr/bin/env python3
"""Moreau Arena Ban/Pick Planning Suite (Task 3.3).

Implements a draft phase (ban/pick/build/reroll/arena) on top of the
frozen Moreau Core combat engine.  Two baseline DraftAgents are provided:
RandomDraftAgent and SmartDraftAgent.

Usage:
    # Quick smoke-test (dry-run, 3-game series):
    python run_planning.py --dry-run --series 3

    # Full best-of-7 series:
    python run_planning.py --series 5

    # Custom output directory:
    python run_planning.py --dry-run --series 3 --output-dir results/planning
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.baselines import Build
from analysis.bt_ranking import BTResult, compute_bt_scores
from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine, CombatResult
from simulator.grid import Grid
from simulator.seed import derive_hit_seed, seeded_random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The 14 core animals available in the draft pool.
# Phase-4 animals (Rhino, Panther, Hawk, Viper) are excluded from draft
# as they are not present in the config.json "animals" section used for
# tournament balance.
_DRAFT_POOL: list[Animal] = [
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
    Animal.CROCODILE,
    Animal.EAGLE,
    Animal.SNAKE,
    Animal.RAVEN,
    Animal.SHARK,
    Animal.OWL,
    Animal.FOX,
    Animal.SCORPION,
]

_VALID_GRID_SIZES = (6, 8, 10)

# Reroll penalty: pay 2 HP points from the stat budget.
_REROLL_HP_PENALTY = 2


# ---------------------------------------------------------------------------
# DraftAgent interface
# ---------------------------------------------------------------------------


class DraftAgent(ABC):
    """Abstract agent for the ban/pick planning phase."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def choose_ban(
        self,
        available_animals: list[Animal],
        opponent_bans: list[Animal],
    ) -> Animal:
        """Choose an animal to ban from *available_animals*."""
        ...

    @abstractmethod
    def choose_pick(self, available_animals: list[Animal]) -> Animal:
        """Choose an animal to play from *available_animals*."""
        ...

    @abstractmethod
    def choose_build(
        self,
        animal: Animal,
        opponent_animal: Animal | None,
    ) -> Build:
        """Allocate stats (summing to 20, each >= 1) for the chosen *animal*."""
        ...

    @abstractmethod
    def choose_reroll(self, build: Build) -> bool:
        """Whether to pay 2 HP to re-roll (get a new stat allocation)."""
        ...

    @abstractmethod
    def choose_arena(self) -> int:
        """Choose grid size: 6, 8, or 10."""
        ...


# ---------------------------------------------------------------------------
# Baseline DraftAgents
# ---------------------------------------------------------------------------


class RandomDraftAgent(DraftAgent):
    """Bans/picks randomly, random stat allocation, never rerolls, 8x8 arena."""

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed
        self._counter = 0

    @property
    def name(self) -> str:
        return "RandomDraft"

    def _next_seed(self) -> int:
        self._counter += 1
        return self._seed + self._counter

    def choose_ban(
        self,
        available_animals: list[Animal],
        opponent_bans: list[Animal],
    ) -> Animal:
        s = self._next_seed()
        idx = int(seeded_random(s, 0, len(available_animals) - 0.001))
        return available_animals[idx]

    def choose_pick(self, available_animals: list[Animal]) -> Animal:
        s = self._next_seed()
        idx = int(seeded_random(s, 0, len(available_animals) - 0.001))
        return available_animals[idx]

    def choose_build(
        self,
        animal: Animal,
        opponent_animal: Animal | None,
    ) -> Build:
        stats = self._random_stats(self._next_seed())
        return Build(animal=animal, hp=stats[0], atk=stats[1], spd=stats[2], wil=stats[3])

    def choose_reroll(self, build: Build) -> bool:
        return False

    def choose_arena(self) -> int:
        return 8

    # -- helpers ---------------------------------------------------------------

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


# Tier list used by SmartDraftAgent for banning and picking.
_ANIMAL_TIER: dict[Animal, int] = {
    Animal.BEAR: 10,
    Animal.BOAR: 9,
    Animal.BUFFALO: 8,
    Animal.TIGER: 7,
    Animal.WOLF: 6,
    Animal.CROCODILE: 6,
    Animal.EAGLE: 5,
    Animal.SHARK: 5,
    Animal.MONKEY: 5,
    Animal.SNAKE: 4,
    Animal.SCORPION: 4,
    Animal.RAVEN: 3,
    Animal.OWL: 3,
    Animal.FOX: 3,
}

# Preferred builds for SmartDraftAgent, keyed by animal.
_SMART_BUILDS: dict[Animal, tuple[int, int, int, int]] = {
    Animal.BEAR: (3, 14, 2, 1),
    Animal.BOAR: (8, 8, 3, 1),
    Animal.BUFFALO: (8, 6, 4, 2),
    Animal.TIGER: (2, 8, 7, 3),
    Animal.WOLF: (5, 10, 3, 2),
    Animal.CROCODILE: (5, 9, 4, 2),
    Animal.EAGLE: (3, 10, 5, 2),
    Animal.SHARK: (4, 10, 4, 2),
    Animal.MONKEY: (3, 10, 5, 2),
    Animal.SNAKE: (3, 5, 5, 7),
    Animal.SCORPION: (4, 8, 5, 3),
    Animal.RAVEN: (3, 5, 7, 5),
    Animal.OWL: (3, 5, 5, 7),
    Animal.FOX: (3, 5, 7, 5),
}


class SmartDraftAgent(DraftAgent):
    """Strategic drafter: bans top-tier, picks the best available,
    uses optimised stat allocations, never rerolls, always 8x8."""

    @property
    def name(self) -> str:
        return "SmartDraft"

    def choose_ban(
        self,
        available_animals: list[Animal],
        opponent_bans: list[Animal],
    ) -> Animal:
        # Ban the highest-tier animal still available.
        return max(available_animals, key=lambda a: _ANIMAL_TIER.get(a, 0))

    def choose_pick(self, available_animals: list[Animal]) -> Animal:
        return max(available_animals, key=lambda a: _ANIMAL_TIER.get(a, 0))

    def choose_build(
        self,
        animal: Animal,
        opponent_animal: Animal | None,
    ) -> Build:
        stats = _SMART_BUILDS.get(animal, (5, 5, 5, 5))
        return Build(animal=animal, hp=stats[0], atk=stats[1], spd=stats[2], wil=stats[3])

    def choose_reroll(self, build: Build) -> bool:
        return False

    def choose_arena(self) -> int:
        return 8


# ---------------------------------------------------------------------------
# Creature factory (mirrors run_challenge._create_creature)
# ---------------------------------------------------------------------------


def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
    """Create a Creature from a flat Build (same logic as run_challenge.py)."""
    hp, atk, spd, wil = build.hp, build.atk, build.spd, build.wil
    animal = build.animal

    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)

    hp_atk = hp + atk
    if hp_atk <= 10:
        size = Size(1, 1)
    elif hp_atk <= 12:
        size = Size(2, 1)
    elif hp_atk <= 17:
        size = Size(2, 2)
    else:
        size = Size(3, 2)

    passive = ANIMAL_PASSIVE.get(animal)
    abilities = ANIMAL_ABILITIES.get(animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)

    return Creature(
        animal=animal,
        stats=StatBlock(hp=hp, atk=atk, spd=spd, wil=wil),
        passive=passive,
        current_hp=max_hp,
        max_hp=max_hp,
        base_dmg=base_dmg,
        armor_flat=0,
        size=size,
        position=position,
        dodge_chance=dodge,
        resist_chance=resist,
        movement_range=movement,
        abilities=abilities,
    )


# ---------------------------------------------------------------------------
# Reroll logic
# ---------------------------------------------------------------------------


def _apply_reroll(build: Build, seed: int) -> Build:
    """Re-allocate stats with a 2 HP penalty (budget effectively 18).

    The animal stays the same.  Stats still each >= 1 but now sum to 18
    (displayed as stat_total=20 with hp reduced by the 2-point penalty).
    """
    effective_budget = 18  # 20 - 2 penalty
    remaining = effective_budget - 4  # min 1 each
    values = [1, 1, 1, 1]
    for i in range(4):
        sub_seed = derive_hit_seed(seed, 1, i)
        if i == 3:
            values[i] += remaining
        else:
            max_alloc = min(remaining, effective_budget - 4)
            if max_alloc > 0:
                alloc = int(seeded_random(sub_seed, 0, max_alloc + 0.999))
                alloc = max(0, min(alloc, remaining))
                values[i] += alloc
                remaining -= alloc
    return Build(
        animal=build.animal,
        hp=values[0],
        atk=values[1],
        spd=values[2],
        wil=values[3],
    )


# ---------------------------------------------------------------------------
# Draft phase
# ---------------------------------------------------------------------------


@dataclass
class DraftResult:
    """Outcome of a single draft phase."""

    bans_a: list[str]
    bans_b: list[str]
    pick_a: str
    pick_b: str
    build_a: dict[str, Any]
    build_b: dict[str, Any]
    reroll_a: bool
    reroll_b: bool
    arena_a: int
    arena_b: int
    chosen_arena: int


def _run_draft(
    agent_a: DraftAgent,
    agent_b: DraftAgent,
    game_seed: int,
) -> tuple[Build, Build, DraftResult]:
    """Execute the full draft flow and return both builds + metadata.

    Draft order:
      1. Ban phase: A bans, then B bans (1 ban each per the spec).
      2. Pick phase: A picks, then B picks.
      3. Build phase: each agent allocates stats.
      4. Reroll: each agent optionally pays 2 HP to re-roll.
      5. Arena: each agent votes on grid size; average (rounded) is used.
    """
    pool = list(_DRAFT_POOL)

    # --- Ban phase (1 ban each, alternating) ---
    bans_a: list[Animal] = []
    bans_b: list[Animal] = []

    ban_a = agent_a.choose_ban(list(pool), [])
    if ban_a in pool:
        pool.remove(ban_a)
        bans_a.append(ban_a)

    ban_b = agent_b.choose_ban(list(pool), [ba for ba in bans_a])
    if ban_b in pool:
        pool.remove(ban_b)
        bans_b.append(ban_b)

    # --- Pick phase ---
    pick_a = agent_a.choose_pick(list(pool))
    if pick_a not in pool:
        pick_a = pool[0]  # fallback
    pool.remove(pick_a)

    pick_b = agent_b.choose_pick(list(pool))
    if pick_b not in pool:
        pick_b = pool[0]
    pool.remove(pick_b)

    # --- Build phase ---
    build_a = agent_a.choose_build(pick_a, pick_b)
    build_b = agent_b.choose_build(pick_b, pick_a)

    # --- Reroll phase ---
    reroll_a = agent_a.choose_reroll(build_a)
    reroll_b = agent_b.choose_reroll(build_b)

    if reroll_a:
        build_a = _apply_reroll(build_a, game_seed + 7000)
    if reroll_b:
        build_b = _apply_reroll(build_b, game_seed + 8000)

    # --- Arena selection ---
    arena_a = agent_a.choose_arena()
    arena_b = agent_b.choose_arena()
    if arena_a not in _VALID_GRID_SIZES:
        arena_a = 8
    if arena_b not in _VALID_GRID_SIZES:
        arena_b = 8
    chosen_arena = round((arena_a + arena_b) / 2)
    # Snap to nearest valid size
    chosen_arena = min(_VALID_GRID_SIZES, key=lambda s: abs(s - chosen_arena))

    draft_result = DraftResult(
        bans_a=[a.value for a in bans_a],
        bans_b=[a.value for a in bans_b],
        pick_a=pick_a.value,
        pick_b=pick_b.value,
        build_a=_build_to_dict(build_a),
        build_b=_build_to_dict(build_b),
        reroll_a=reroll_a,
        reroll_b=reroll_b,
        arena_a=arena_a,
        arena_b=arena_b,
        chosen_arena=chosen_arena,
    )

    return build_a, build_b, draft_result


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------


def _run_single_game(
    build_a: Build,
    build_b: Build,
    match_seed: int,
) -> CombatResult:
    """Run a single combat between two builds."""
    creature_a = _create_creature(build_a, "a", match_seed)
    creature_b = _create_creature(build_b, "b", match_seed)
    engine = CombatEngine()
    return engine.run_combat(creature_a, creature_b, match_seed)


def _build_to_dict(build: Build) -> dict[str, Any]:
    """Convert a Build to a serialisable dict."""
    return {
        "animal": build.animal.value.upper(),
        "hp": build.hp,
        "atk": build.atk,
        "spd": build.spd,
        "wil": build.wil,
    }


# ---------------------------------------------------------------------------
# Series protocol — best-of-N with draft
# ---------------------------------------------------------------------------


def _run_draft_series(
    agent_a: DraftAgent,
    agent_b: DraftAgent,
    series_seed: int,
    best_of: int = 7,
) -> tuple[str, list[dict[str, Any]]]:
    """Run a best-of-N series with full draft each game.

    Returns (winner_name, game_records).
    """
    wins_to_clinch = (best_of // 2) + 1
    wins_a = 0
    wins_b = 0
    game_records: list[dict[str, Any]] = []

    for g in range(best_of):
        if wins_a >= wins_to_clinch or wins_b >= wins_to_clinch:
            break

        game_seed = series_seed + g * 1000
        match_seed = game_seed + 1

        # Draft
        build_a, build_b, draft_info = _run_draft(agent_a, agent_b, game_seed)

        # Combat
        result = _run_single_game(build_a, build_b, match_seed)

        record: dict[str, Any] = {
            "game": g + 1,
            "seed": match_seed,
            "draft": {
                "bans_a": draft_info.bans_a,
                "bans_b": draft_info.bans_b,
                "pick_a": draft_info.pick_a,
                "pick_b": draft_info.pick_b,
                "build_a": draft_info.build_a,
                "build_b": draft_info.build_b,
                "reroll_a": draft_info.reroll_a,
                "reroll_b": draft_info.reroll_b,
                "arena_vote_a": draft_info.arena_a,
                "arena_vote_b": draft_info.arena_b,
                "arena_chosen": draft_info.chosen_arena,
            },
            "winner_side": result.winner,
            "ticks": result.ticks,
            "end_condition": result.end_condition,
        }
        game_records.append(record)

        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1

    if wins_a > wins_b:
        return agent_a.name, game_records
    elif wins_b > wins_a:
        return agent_b.name, game_records
    return "draw", game_records


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------


def _aggregate_ban_pick_stats(
    all_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute ban/pick frequency tables from series records."""
    ban_counts: dict[str, int] = defaultdict(int)
    pick_counts: dict[str, int] = defaultdict(int)

    for series in all_records:
        for game in series.get("games", []):
            draft = game.get("draft", {})
            for b in draft.get("bans_a", []):
                ban_counts[b] += 1
            for b in draft.get("bans_b", []):
                ban_counts[b] += 1
            pick_a = draft.get("pick_a", "")
            pick_b = draft.get("pick_b", "")
            if pick_a:
                pick_counts[pick_a] += 1
            if pick_b:
                pick_counts[pick_b] += 1

    return {
        "bans": dict(sorted(ban_counts.items(), key=lambda x: x[1], reverse=True)),
        "picks": dict(sorted(pick_counts.items(), key=lambda x: x[1], reverse=True)),
    }


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def _print_results_table(
    results_by_matchup: dict[str, dict[str, int]],
    agent_names: list[str],
) -> None:
    """Print pairwise series results."""
    print("\n" + "=" * 70)
    print(f"  {'Matchup':<30} {'A Wins':>8} {'B Wins':>8} {'Draws':>8}")
    print("-" * 70)

    total_a, total_b, total_d = 0, 0, 0
    for matchup, counts in results_by_matchup.items():
        w = counts.get("a", 0)
        l = counts.get("b", 0)
        d = counts.get("draw", 0)
        total_a += w
        total_b += l
        total_d += d
        print(f"  {matchup:<30} {w:>8} {l:>8} {d:>8}")

    print("-" * 70)
    print(f"  {'TOTAL':<30} {total_a:>8} {total_b:>8} {total_d:>8}")
    print("=" * 70)


def _print_ban_pick_stats(stats: dict[str, Any]) -> None:
    """Print ban and pick frequency tables."""
    print("\nBan Frequency:")
    print(f"  {'Animal':<15} {'Bans':>6}")
    print("  " + "-" * 23)
    for animal, count in stats.get("bans", {}).items():
        print(f"  {animal:<15} {count:>6}")

    print("\nPick Frequency:")
    print(f"  {'Animal':<15} {'Picks':>6}")
    print("  " + "-" * 23)
    for animal, count in stats.get("picks", {}).items():
        print(f"  {animal:<15} {count:>6}")


# ---------------------------------------------------------------------------
# JSONL output
# ---------------------------------------------------------------------------


def _save_results_jsonl(
    output_dir: Path,
    series_records: list[dict[str, Any]],
) -> Path:
    """Save all series results to a JSONL file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"planning_{timestamp}.jsonl"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        for record in series_records:
            f.write(json.dumps(record, default=str) + "\n")

    return output_path


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_planning(args: argparse.Namespace) -> None:
    """Execute the planning suite."""
    num_series = args.series
    output_dir = Path(args.output_dir)
    dry_run = args.dry_run

    # Agents
    agents: list[DraftAgent] = [
        RandomDraftAgent(seed=42),
        SmartDraftAgent(),
    ]
    agent_names = [a.name for a in agents]

    # Header
    print("=" * 70)
    print("  MOREAU ARENA -- BAN/PICK PLANNING SUITE")
    print("=" * 70)
    print(f"  Agents:      {', '.join(agent_names)}")
    print(f"  Series/pair: {num_series}")
    print(f"  Best-of:     7")
    print(f"  Dry run:     {dry_run}")
    print("=" * 70)
    print()

    # Round-robin: each pair plays num_series times.
    all_bt_pairs: list[tuple[str, str]] = []
    all_series_records: list[dict[str, Any]] = []
    results_by_matchup: dict[str, dict[str, int]] = {}
    base_seed = 200_000
    series_idx = 0

    n_agents = len(agents)
    total_series = (n_agents * (n_agents - 1) // 2) * num_series

    for i in range(n_agents):
        for j in range(i + 1, n_agents):
            matchup_key = f"{agents[i].name} vs {agents[j].name}"
            counts: dict[str, int] = {"a": 0, "b": 0, "draw": 0}

            for s in range(num_series):
                series_idx += 1
                series_seed = base_seed + series_idx * 1000

                t_start = time.monotonic()
                winner, game_records = _run_draft_series(
                    agents[i], agents[j], series_seed
                )
                elapsed = time.monotonic() - t_start

                # Classify
                if winner == agents[i].name:
                    counts["a"] += 1
                    all_bt_pairs.append((agents[i].name, agents[j].name))
                elif winner == agents[j].name:
                    counts["b"] += 1
                    all_bt_pairs.append((agents[j].name, agents[i].name))
                else:
                    counts["draw"] += 1

                series_record = {
                    "agent_a": agents[i].name,
                    "agent_b": agents[j].name,
                    "winner": winner,
                    "series_seed": series_seed,
                    "games": game_records,
                    "elapsed_s": round(elapsed, 2),
                }
                all_series_records.append(series_record)

                status = f"[{series_idx}/{total_series}]"
                games_str = f"{len(game_records)} games"
                print(
                    f"  {status:>10}  {matchup_key:<30} "
                    f"-> {winner:<20} ({games_str}, {elapsed:.1f}s)"
                )

            results_by_matchup[matchup_key] = counts

    # Results table
    _print_results_table(results_by_matchup, agent_names)

    # Ban/Pick stats
    bp_stats = _aggregate_ban_pick_stats(all_series_records)
    _print_ban_pick_stats(bp_stats)

    # BT scores
    if all_bt_pairs:
        bt_results = compute_bt_scores(
            all_bt_pairs, n_bootstrap=1000, bootstrap_seed=42
        )
        print("\nBradley-Terry Rankings:")
        print(f"  {'Rank':<5} {'Agent':<25} {'BT Score':<10} {'95% CI':<22}")
        print("  " + "-" * 60)
        for rank, r in enumerate(bt_results, 1):
            ci_str = f"[{r.ci_lower:.4f}, {r.ci_upper:.4f}]"
            print(f"  {rank:<5} {r.name:<25} {r.score:<10.4f} {ci_str:<22}")
    else:
        print("\n  No decisive results -- cannot compute BT scores.")

    # Save
    output_path = _save_results_jsonl(output_dir, all_series_records)
    print(f"\nResults saved to: {output_path}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Moreau Arena Ban/Pick Planning Suite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_planning.py --dry-run --series 3\n"
            "  python run_planning.py --series 5\n"
            "  python run_planning.py --series 10 --output-dir results/planning\n"
        ),
    )
    parser.add_argument(
        "--series",
        type=int,
        default=5,
        help="Number of best-of-7 series per agent pair (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Smoke-test flag (no behavioural difference for baseline agents, "
        "but signals intent to keep runs short)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Directory for output JSONL files (default: results/)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        run_planning(args)
    except KeyboardInterrupt:
        print("\nPlanning interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
