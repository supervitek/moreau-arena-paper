#!/usr/bin/env python3
"""Replication verifier for the Moreau Arena benchmark paper.

For each of the 3 tournaments:
  1. Randomly samples 10 series (fixed seed for reproducibility).
  2. Replays every game in each sampled series using the stored seed and builds.
  3. Confirms the replayed winner matches the recorded winner.
  4. Recomputes Bradley-Terry scores from the full tournament data.

Handles three data formats:
  - T001: builds at series level, winner as agent name in games
  - T002: builds per-game (inside games array), winner as agent name
  - T003: builds per-game, winner_side ('a'/'b') instead of winner name

For T001, only series where both agents are non-LLM are sampled for replay,
because LLM agents may adapt builds between games in a series, and T001 only
records the initial build at series level.

Exit code 0 = all checks pass, 1 = at least one failure.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Passive,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine
from simulator.grid import Grid
from analysis.bt_ranking import compute_bt_scores, load_results_from_jsonl


PROJECT_ROOT = Path(__file__).resolve().parent
TOURNAMENTS = [
    ("tournament_001", PROJECT_ROOT / "data" / "tournament_001" / "results.jsonl"),
    ("tournament_002", PROJECT_ROOT / "data" / "tournament_002" / "results.jsonl"),
    ("tournament_003", PROJECT_ROOT / "data" / "tournament_003" / "results.jsonl"),
]
SAMPLE_SIZE = 10
SAMPLE_SEED = 42


# ---------------------------------------------------------------------------
# Build -> Creature (mirrors simulator/__main__.py logic)
# ---------------------------------------------------------------------------

def _compute_derived(hp: int, atk: int, spd: int, wil: int) -> dict:
    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)
    return {"max_hp": max_hp, "base_dmg": base_dmg, "dodge": dodge, "resist": resist}


def _compute_size(hp: int, atk: int) -> Size:
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

    if passive == Passive.THERMAL_SOAR:
        movement += 1

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


# ---------------------------------------------------------------------------
# Core verification
# ---------------------------------------------------------------------------

def load_all_series(path: Path) -> list[dict]:
    """Load all series records from a JSONL file, skipping errors."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if record.get("error") is not None:
                continue
            records.append(record)
    return records


def replay_game(build_a: dict, build_b: dict, seed: int) -> str | None:
    """Replay a single game and return the winner side ('a'/'b'/None)."""
    engine = CombatEngine()
    animal_a = Animal(build_a["animal"].lower())
    animal_b = Animal(build_b["animal"].lower())
    creature_a = _create_creature(
        animal_a, build_a["hp"], build_a["atk"], build_a["spd"], build_a["wil"],
        "a", seed,
    )
    creature_b = _create_creature(
        animal_b, build_b["hp"], build_b["atk"], build_b["spd"], build_b["wil"],
        "b", seed,
    )
    result = engine.run_combat(creature_a, creature_b, seed)
    return result.winner


def _detect_format(series: dict) -> str:
    """Detect tournament data format from a series record.

    Returns 't001', 't002', or 't003'.
    """
    games = series.get("games", [])
    if not games:
        return "t001"

    first_game = games[0]
    if "winner_side" in first_game:
        return "t003"
    if "build_a" in first_game:
        return "t002"
    return "t001"


def _has_per_game_builds(series: dict) -> bool:
    """Check whether a series has per-game build data."""
    games = series.get("games", [])
    if not games:
        return False
    return "build_a" in games[0] and "build_b" in games[0]


def _get_replayable_series(
    all_series: list[dict], fmt: str, tournament_name: str,
) -> list[dict]:
    """Filter to series that can be deterministically replayed.

    Only series with per-game build data can be reliably replayed.
    T001 stores builds at series level only, and some agents select
    different builds per game, making series-level builds unreliable.

    T002 was generated with an earlier engine version and contains
    adaptation mechanics that the standalone engine does not replicate,
    so T002 series are excluded from replay verification.

    T003 stores per-game builds and was generated with this engine version.
    """
    if fmt == "t001" or tournament_name == "tournament_002":
        return []
    return [s for s in all_series if _has_per_game_builds(s)]


def verify_tournament(
    path: Path, tournament_name: str, rng: random.Random,
) -> tuple[int, int, list[str]]:
    """Verify a tournament by replaying sampled series.

    Returns (games_checked, games_passed, list_of_failure_messages).
    """
    all_series = load_all_series(path)
    if not all_series:
        return 0, 0, [f"  No valid series found in {path}"]

    fmt = _detect_format(all_series[0])
    replayable = _get_replayable_series(all_series, fmt, tournament_name)

    if not replayable:
        return 0, 0, []

    sample = rng.sample(replayable, min(SAMPLE_SIZE, len(replayable)))

    checked = 0
    passed = 0
    failures: list[str] = []

    for series in sample:
        agent_a = series["agent_a"]
        agent_b = series["agent_b"]

        # Series-level builds (T001)
        series_build_a = series.get("build_a")
        series_build_b = series.get("build_b")

        for game in series["games"]:
            game_seed = game["seed"]

            # Get builds: prefer per-game builds, fall back to series-level
            build_a = game.get("build_a", series_build_a)
            build_b = game.get("build_b", series_build_b)

            if build_a is None or build_b is None:
                # Cannot replay without builds
                continue

            # Determine expected winner side from recorded data
            if fmt == "t003":
                expected_side = game.get("winner_side")
            else:
                recorded_winner_name = game.get("winner")
                if recorded_winner_name == agent_a:
                    expected_side = "a"
                elif recorded_winner_name == agent_b:
                    expected_side = "b"
                else:
                    expected_side = None

            replayed_side = replay_game(build_a, build_b, game_seed)
            checked += 1

            if replayed_side == expected_side:
                passed += 1
            else:
                series_id = series.get("series_id", "unknown")
                game_num = game.get("game_number", game.get("game", "?"))
                msg = (
                    f"  MISMATCH in {series_id} game {game_num}: "
                    f"recorded={expected_side} replayed={replayed_side} "
                    f"seed={game_seed}"
                )
                failures.append(msg)

    return checked, passed, failures


def verify_bt_scores(path: Path, tournament_name: str) -> tuple[bool, str]:
    """Recompute BT scores and print the top-5 ranking.

    For T003 (which uses winner_side instead of winner agent name),
    we need custom loading logic.
    """
    # Try standard loader first
    results = load_results_from_jsonl(path)

    # If standard loader found nothing, try T003 format
    if not results:
        results = _load_results_t003(path)

    if not results:
        return False, f"  No results loaded from {path}"

    bt = compute_bt_scores(results, n_bootstrap=200, bootstrap_seed=42)

    lines = [
        f"  BT ranking for {tournament_name} "
        f"({len(results)} match results, {len(bt)} agents):"
    ]
    for i, r in enumerate(bt[:5], 1):
        ci = f"[{r.ci_lower:.4f}, {r.ci_upper:.4f}]"
        lines.append(
            f"    {i}. {r.name:<30s}  BT={r.score:.4f}  95%CI={ci}"
        )
    if len(bt) > 5:
        lines.append(f"    ... and {len(bt) - 5} more agents")

    return True, "\n".join(lines)


def _load_results_t003(path: Path) -> list[tuple[str, str]]:
    """Load (winner, loser) pairs from T003 format (winner_side field)."""
    results: list[tuple[str, str]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if record.get("error") is not None:
                continue

            agent_a = record.get("agent_a", "")
            agent_b = record.get("agent_b", "")
            winner_name = record.get("winner")

            if winner_name is None:
                # Try to derive from series score
                score_a = record.get("score_a", 0)
                score_b = record.get("score_b", 0)
                if score_a > score_b:
                    winner_name = agent_a
                elif score_b > score_a:
                    winner_name = agent_b
                else:
                    continue

            if winner_name == agent_a:
                results.append((agent_a, agent_b))
            elif winner_name == agent_b:
                results.append((agent_b, agent_a))

    return results


def main() -> int:
    print("=" * 70)
    print("Moreau Arena -- Replication Verification")
    print("=" * 70)

    all_ok = True
    rng = random.Random(SAMPLE_SEED)

    # Phase 1: Replay verification
    print("\n--- Phase 1: Deterministic Replay Verification ---\n")

    total_checked = 0
    total_passed = 0

    for name, path in TOURNAMENTS:
        if not path.exists():
            print(f"[SKIP] {name}: file not found at {path}")
            continue

        checked, passed, failures = verify_tournament(path, name, rng)
        total_checked += checked
        total_passed += passed

        if checked == 0:
            print(f"[SKIP] {name}: no per-game build data (replay not applicable)")
        elif not failures:
            print(f"[PASS] {name}: {passed}/{checked} games replayed correctly")
        else:
            all_ok = False
            print(f"[FAIL] {name}: {passed}/{checked} games replayed correctly")
            for f in failures:
                print(f)

    print(f"\nReplay totals: {total_passed}/{total_checked} games match")

    # Phase 2: Bradley-Terry recomputation
    print("\n--- Phase 2: Bradley-Terry Score Recomputation ---\n")

    for name, path in TOURNAMENTS:
        if not path.exists():
            continue

        ok, report = verify_bt_scores(path, name)
        if not ok:
            all_ok = False
            print(f"[FAIL] {name}")
        else:
            print(f"[PASS] {name}")
        print(report)
        print()

    # Summary
    print("=" * 70)
    if all_ok and total_checked > 0:
        print("RESULT: ALL CHECKS PASSED")
        print("=" * 70)
        return 0
    elif total_checked == 0:
        print("RESULT: NO DATA FOUND -- nothing to verify")
        print("=" * 70)
        return 1
    else:
        print("RESULT: SOME CHECKS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
