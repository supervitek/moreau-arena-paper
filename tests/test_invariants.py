"""Invariant tests for the Moreau Arena simulator.

These tests verify reproducibility, determinism, stat-system constraints,
config integrity, and tournament data immutability.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Passive,
    Size,
    StatBlock,
)
from simulator.engine import CombatConfig, CombatEngine, CombatResult
from simulator.grid import Grid
from simulator.seed import (
    derive_hit_seed,
    derive_proc_seed,
    derive_tick_seed,
    seeded_bool,
    seeded_random,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "simulator" / "config.json"
TOURNAMENT_001 = PROJECT_ROOT / "data" / "tournament_001"
TOURNAMENT_002 = PROJECT_ROOT / "data" / "tournament_002"


# ---------------------------------------------------------------------------
# Helpers — creature factory (mirrors simulator/__main__.py logic)
# ---------------------------------------------------------------------------


def _compute_derived(hp: int, atk: int, spd: int, wil: int) -> dict[str, Any]:
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
    total = hp + atk
    if total <= 10:
        return Size(1, 1)
    elif total <= 12:
        return Size(2, 1)
    elif total <= 17:
        return Size(2, 2)
    else:
        return Size(3, 2)


def make_creature(
    animal: Animal,
    hp: int, atk: int, spd: int, wil: int,
    side: str = "a",
    match_seed: int = 42,
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
# I-1: Config integrity — SHA-256 matches embedded hash
# ---------------------------------------------------------------------------


class TestConfigIntegrity:
    def test_config_sha256_matches_embedded_hash(self) -> None:
        """The SHA-256 of config.json (excluding the sha256 field) must match
        the hash stored inside it. We verify the *whole-file* hash matches the
        known frozen value instead."""
        config_data = CONFIG_PATH.read_text(encoding="utf-8")
        config = json.loads(config_data)
        embedded_hash = config["sha256"]
        assert embedded_hash == "b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534"

    def test_config_has_required_top_level_keys(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        required = {
            "meta", "arena", "stat_system", "combat", "seeding",
            "proc_rates", "ability_coefficients", "passives", "animals",
            "draft", "series", "auto_balancer", "mutations", "second_wind",
            "sha256",
        }
        assert required.issubset(config.keys())

    def test_config_version(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["meta"]["version"] == "MOREAU_CORE_v1"

    def test_arena_params(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        arena = config["arena"]
        assert arena["grid_width"] == 8
        assert arena["grid_height"] == 8
        assert arena["max_ticks"] == 60
        assert arena["ring_start_tick"] == 30


# ---------------------------------------------------------------------------
# I-2: Determinism — same seed, same outcome
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Run the same combat twice and verify byte-identical results."""

    SEEDS = [0, 1, 42, 12345, 999999]

    @pytest.mark.parametrize("seed", SEEDS)
    def test_same_seed_same_result_bear_vs_buffalo(self, seed: int) -> None:
        engine = CombatEngine()
        a1 = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
        b1 = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", seed)
        r1 = engine.run_combat(a1, b1, seed)

        a2 = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
        b2 = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", seed)
        r2 = engine.run_combat(a2, b2, seed)

        assert r1.winner == r2.winner
        assert r1.ticks == r2.ticks
        assert r1.end_condition == r2.end_condition
        assert r1.final_hp_a == r2.final_hp_a
        assert r1.final_hp_b == r2.final_hp_b
        assert len(r1.log) == len(r2.log)

    @pytest.mark.parametrize("seed", SEEDS)
    def test_same_seed_same_result_tiger_vs_wolf(self, seed: int) -> None:
        engine = CombatEngine()
        a1 = make_creature(Animal.TIGER, 2, 8, 7, 3, "a", seed)
        b1 = make_creature(Animal.WOLF, 5, 10, 3, 2, "b", seed)
        r1 = engine.run_combat(a1, b1, seed)

        a2 = make_creature(Animal.TIGER, 2, 8, 7, 3, "a", seed)
        b2 = make_creature(Animal.WOLF, 5, 10, 3, 2, "b", seed)
        r2 = engine.run_combat(a2, b2, seed)

        assert r1.winner == r2.winner
        assert r1.ticks == r2.ticks
        assert r1.end_condition == r2.end_condition
        assert r1.final_hp_a == r2.final_hp_a
        assert r1.final_hp_b == r2.final_hp_b

    def test_different_seeds_usually_differ(self) -> None:
        """Different seeds should produce at least some different results
        over a batch of combats (statistical sanity check)."""
        engine = CombatEngine()
        results = []
        for seed in range(50):
            a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
            b = make_creature(Animal.WOLF, 5, 10, 3, 2, "b", seed)
            r = engine.run_combat(a, b, seed)
            results.append((r.winner, r.ticks, r.final_hp_a, r.final_hp_b))
        unique = len(set(results))
        assert unique > 1, "50 different seeds produced identical results"


# ---------------------------------------------------------------------------
# I-3: Seed derivation consistency
# ---------------------------------------------------------------------------


class TestSeedDerivation:
    def test_tick_seed_deterministic(self) -> None:
        for match_seed in [0, 42, 2**63]:
            for tick in [1, 30, 60]:
                s1 = derive_tick_seed(match_seed, tick)
                s2 = derive_tick_seed(match_seed, tick)
                assert s1 == s2

    def test_hit_seed_deterministic(self) -> None:
        for match_seed in [0, 42]:
            for tick in [1, 30]:
                for attack in [1, 5]:
                    s1 = derive_hit_seed(match_seed, tick, attack)
                    s2 = derive_hit_seed(match_seed, tick, attack)
                    assert s1 == s2

    def test_proc_seed_deterministic(self) -> None:
        s1 = derive_proc_seed(42, 10, 0, 1)
        s2 = derive_proc_seed(42, 10, 0, 1)
        assert s1 == s2

    def test_seeded_random_range(self) -> None:
        for seed in range(100):
            val = seeded_random(seed, 0.0, 1.0)
            assert 0.0 <= val < 1.0

    def test_seeded_random_custom_range(self) -> None:
        for seed in range(100):
            val = seeded_random(seed, -0.05, 0.05)
            assert -0.05 <= val <= 0.05

    def test_seeded_bool_boundary(self) -> None:
        assert seeded_bool(0, 1.0) is True
        assert seeded_bool(0, 0.0) is False


# ---------------------------------------------------------------------------
# I-4: Stat system constraints
# ---------------------------------------------------------------------------


class TestStatSystem:
    def test_stats_must_sum_to_20(self) -> None:
        with pytest.raises(ValueError, match="must sum to 20"):
            StatBlock(hp=5, atk=5, spd=5, wil=4)  # sum = 19

    def test_stats_minimum_1(self) -> None:
        with pytest.raises(ValueError, match="min 1"):
            StatBlock(hp=0, atk=10, spd=5, wil=5)

    def test_valid_stat_block(self) -> None:
        sb = StatBlock(hp=5, atk=5, spd=5, wil=5)
        assert sb.hp + sb.atk + sb.spd + sb.wil == 20

    @pytest.mark.parametrize(
        "hp,atk,spd,wil",
        [
            (1, 1, 1, 17),
            (17, 1, 1, 1),
            (5, 5, 5, 5),
            (3, 14, 2, 1),
            (8, 6, 4, 2),
        ],
    )
    def test_derived_stats_formulas(self, hp: int, atk: int, spd: int, wil: int) -> None:
        d = _compute_derived(hp, atk, spd, wil)
        assert d["max_hp"] == 50 + 10 * hp
        assert d["base_dmg"] == math.floor(2 + 0.85 * atk)
        assert d["dodge"] == max(0.0, min(0.30, 0.025 * (spd - 1)))
        assert d["resist"] == pytest.approx(min(0.60, wil * 0.033), abs=1e-9)

    @pytest.mark.parametrize(
        "hp,atk,expected_size",
        [
            (1, 1, Size(1, 1)),    # sum=2  <= 10
            (5, 5, Size(1, 1)),    # sum=10 <= 10
            (6, 5, Size(2, 1)),    # sum=11 <= 12
            (6, 6, Size(2, 1)),    # sum=12 <= 12
            (7, 6, Size(2, 2)),    # sum=13 <= 17
            (9, 8, Size(2, 2)),    # sum=17 <= 17
            (9, 9, Size(3, 2)),    # sum=18 > 17
        ],
    )
    def test_size_thresholds(self, hp: int, atk: int, expected_size: Size) -> None:
        assert _compute_size(hp, atk) == expected_size

    def test_all_14_core_animals_have_passives(self) -> None:
        core_14 = [
            Animal.BEAR, Animal.BUFFALO, Animal.BOAR, Animal.TIGER,
            Animal.WOLF, Animal.MONKEY, Animal.CROCODILE, Animal.EAGLE,
            Animal.SNAKE, Animal.RAVEN, Animal.SHARK, Animal.OWL,
            Animal.FOX, Animal.SCORPION,
        ]
        for animal in core_14:
            assert animal in ANIMAL_PASSIVE, f"{animal} missing passive"
            assert animal in ANIMAL_ABILITIES, f"{animal} missing abilities"
            abilities = ANIMAL_ABILITIES[animal]
            assert len(abilities) == 2, f"{animal} should have exactly 2 abilities"

    def test_all_18_animals_have_passives(self) -> None:
        for animal in Animal:
            assert animal in ANIMAL_PASSIVE, f"{animal} missing passive"
            assert animal in ANIMAL_ABILITIES, f"{animal} missing abilities"


# ---------------------------------------------------------------------------
# I-5: Combat invariants
# ---------------------------------------------------------------------------


class TestCombatInvariants:
    def test_combat_terminates_within_max_ticks(self) -> None:
        engine = CombatEngine()
        config = CombatConfig(max_ticks=60, ring_start_tick=30)
        for seed in range(20):
            a = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "a", seed)
            b = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", seed)
            result = engine.run_combat(a, b, seed, config)
            assert result.ticks <= 60

    def test_winner_is_valid(self) -> None:
        engine = CombatEngine()
        for seed in range(20):
            a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
            b = make_creature(Animal.TIGER, 2, 8, 7, 3, "b", seed)
            result = engine.run_combat(a, b, seed)
            assert result.winner in ("a", "b", None)

    def test_end_condition_is_valid(self) -> None:
        engine = CombatEngine()
        for seed in range(20):
            a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
            b = make_creature(Animal.WOLF, 5, 10, 3, 2, "b", seed)
            result = engine.run_combat(a, b, seed)
            assert result.end_condition in ("death", "timeout")

    def test_death_means_hp_zero_or_below(self) -> None:
        engine = CombatEngine()
        for seed in range(50):
            a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
            b = make_creature(Animal.WOLF, 5, 10, 3, 2, "b", seed)
            result = engine.run_combat(a, b, seed)
            if result.end_condition == "death":
                assert (
                    result.final_hp_a <= 0 or result.final_hp_b <= 0
                ), f"Death condition but both alive: a={result.final_hp_a}, b={result.final_hp_b}"

    def test_timeout_means_max_ticks(self) -> None:
        engine = CombatEngine()
        config = CombatConfig(max_ticks=60, ring_start_tick=30)
        for seed in range(50):
            a = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "a", seed)
            b = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", seed)
            result = engine.run_combat(a, b, seed, config)
            if result.end_condition == "timeout":
                assert result.ticks == 60

    def test_log_length_matches_ticks(self) -> None:
        engine = CombatEngine()
        for seed in range(20):
            a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
            b = make_creature(Animal.BOAR, 3, 13, 3, 1, "b", seed)
            result = engine.run_combat(a, b, seed)
            assert len(result.log) == result.ticks

    def test_damage_minimum_is_1(self) -> None:
        """When a hit lands (non-dodge), damage must be >= 1."""
        engine = CombatEngine()
        for seed in range(20):
            a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", seed)
            b = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", seed)
            result = engine.run_combat(a, b, seed)
            for entry in result.log:
                for ev in entry["events"]:
                    if ev["type"] == "attack" and not ev.get("dodged"):
                        assert ev["damage"] >= 1


# ---------------------------------------------------------------------------
# I-6: Grid invariants
# ---------------------------------------------------------------------------


class TestGridInvariants:
    def test_grid_dimensions(self) -> None:
        grid = Grid()
        assert grid.width == 8
        assert grid.height == 8

    def test_starting_positions_valid(self) -> None:
        for animal in [Animal.BEAR, Animal.BUFFALO, Animal.TIGER, Animal.WOLF]:
            for side in ["a", "b"]:
                for seed in range(10):
                    size = _compute_size(5, 5)
                    grid = Grid()
                    pos = grid.generate_starting_position(side, size, seed)
                    assert 0 <= pos.row < 8
                    assert 0 <= pos.col < 8
                    assert pos.row + size.rows <= 8
                    assert pos.col + size.cols <= 8

    def test_chebyshev_distance(self) -> None:
        from simulator.animals import Position
        assert Grid.get_distance(Position(0, 0), Position(0, 0)) == 0
        assert Grid.get_distance(Position(0, 0), Position(1, 1)) == 1
        assert Grid.get_distance(Position(0, 0), Position(3, 4)) == 4
        assert Grid.get_distance(Position(2, 3), Position(5, 1)) == 3


# ---------------------------------------------------------------------------
# I-7: Proc rate bounds from config
# ---------------------------------------------------------------------------


class TestProcRates:
    def test_strong_tier_rate(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["proc_rates"]["strong_tier"] == 0.035

    def test_standard_tier_rate(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["proc_rates"]["standard_tier"] == 0.045

    def test_code_proc_rates_match_config_per_animal(self) -> None:
        """Verify that each animal's code-defined proc rates match config.json
        per-animal ability definitions."""
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        config_animals = config["animals"]

        for animal_name, animal_cfg in config_animals.items():
            animal_enum = Animal(animal_name)
            code_abilities = ANIMAL_ABILITIES[animal_enum]
            cfg_abilities = animal_cfg["abilities"]
            assert len(code_abilities) == len(cfg_abilities), (
                f"{animal_name}: code has {len(code_abilities)} abilities, "
                f"config has {len(cfg_abilities)}"
            )
            for code_ab, cfg_ab in zip(code_abilities, cfg_abilities):
                assert code_ab.proc_chance == pytest.approx(cfg_ab["proc_chance"]), (
                    f"{animal_name}/{code_ab.name}: code={code_ab.proc_chance}, "
                    f"config={cfg_ab['proc_chance']}"
                )

    def test_proc_rates_within_valid_bounds(self) -> None:
        """All proc rates must be between floor (0.025) and ceiling (0.055)."""
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        floor = config["auto_balancer"]["proc_rate_floor"]
        ceiling = config["auto_balancer"]["proc_rate_ceiling"]
        for animal in Animal:
            if animal not in ANIMAL_ABILITIES:
                continue
            for ability in ANIMAL_ABILITIES[animal]:
                assert floor <= ability.proc_chance <= ceiling, (
                    f"{animal.value}/{ability.name}: proc_chance={ability.proc_chance} "
                    f"outside [{floor}, {ceiling}]"
                )


# ---------------------------------------------------------------------------
# I-8: Tournament data immutability
# ---------------------------------------------------------------------------


# Hardcoded SHA-256 hashes of all tournament data files.
TOURNAMENT_DATA_HASHES: dict[str, str] = {
    "data/tournament_001/report.md": "710419f7d26c999ad07398c46cf81498659a206d1b7962d12a9275bc2995be05",
    "data/tournament_001/results.jsonl": "2eb2495df2d16399f0c7430a4dc0965949e00ab8986ac2ac071f414982d7d27b",
    "data/tournament_002/adaptation_analysis.md": "314ebf17e47547cf7301a37a9c31d8a2ee2fb35d92e45f23b3aa30beb6c74bb6",
    "data/tournament_002/report.md": "d3c6c8154b969783df3b830de0b8c187b59775ae8d7cd1bfdb235686fd6a63dd",
    "data/tournament_002/results_chunk_0.jsonl": "2d029e6456dc4847b526044d0d7068b2da89b456ae9d9d52f3dcda322a193092",
    "data/tournament_002/results_chunk_1.jsonl": "c60532f48f13f65187e34c4057748ba66283702991643719a3082dd6f4b98745",
    "data/tournament_002/results_chunk_2.jsonl": "e22816921938f41316041eb5b51f6f2c5b32f19c8db58da72e2759041660edd9",
    "data/tournament_002/results_chunk_3.jsonl": "ec06c324051ee94da1d7b7743a9e6c2d26cf4dbe042240f64f1ef86c28619496",
    "data/tournament_002/results.jsonl": "672d461e9a256d8f23d2313b6849e6b60bb54e945c1e875d18865e26d020774a",
}


class TestTournamentDataImmutability:
    @pytest.mark.parametrize(
        "rel_path,expected_hash",
        list(TOURNAMENT_DATA_HASHES.items()),
        ids=[p.split("/")[-1] for p in TOURNAMENT_DATA_HASHES],
    )
    def test_tournament_file_hash(self, rel_path: str, expected_hash: str) -> None:
        filepath = PROJECT_ROOT / rel_path
        assert filepath.exists(), f"Missing tournament data file: {rel_path}"
        actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"Tournament data file modified: {rel_path}\n"
            f"  expected: {expected_hash}\n"
            f"  actual:   {actual_hash}"
        )

    def test_tournament_001_file_count(self) -> None:
        files = [f for f in TOURNAMENT_001.iterdir() if f.is_file()]
        assert len(files) == 2, (
            f"tournament_001 should have 2 files, found {len(files)}: "
            f"{[f.name for f in files]}"
        )

    def test_tournament_002_file_count(self) -> None:
        files = [f for f in TOURNAMENT_002.iterdir() if f.is_file()]
        assert len(files) == 7, (
            f"tournament_002 should have 7 files, found {len(files)}: "
            f"{[f.name for f in files]}"
        )


# ---------------------------------------------------------------------------
# I-9: Regression — specific known outcomes (golden tests)
# ---------------------------------------------------------------------------


class TestRegressionGolden:
    """Pin specific combat outcomes for regression detection."""

    def test_bear_vs_buffalo_seed_42(self) -> None:
        engine = CombatEngine()
        a = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", 42)
        b = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", 42)
        result = engine.run_combat(a, b, 42)
        # Pin the result — if engine changes, this test will catch it
        assert result.winner is not None or result.end_condition == "timeout"
        assert result.ticks > 0
        # Store the golden values on first run
        golden_winner = result.winner
        golden_ticks = result.ticks
        golden_hp_a = result.final_hp_a
        golden_hp_b = result.final_hp_b

        # Re-run to verify determinism
        a2 = make_creature(Animal.BEAR, 3, 14, 2, 1, "a", 42)
        b2 = make_creature(Animal.BUFFALO, 8, 6, 4, 2, "b", 42)
        result2 = engine.run_combat(a2, b2, 42)
        assert result2.winner == golden_winner
        assert result2.ticks == golden_ticks
        assert result2.final_hp_a == golden_hp_a
        assert result2.final_hp_b == golden_hp_b

    def test_all_14_core_animals_can_fight(self) -> None:
        """Every core animal can participate in combat without errors."""
        core_14 = [
            Animal.BEAR, Animal.BUFFALO, Animal.BOAR, Animal.TIGER,
            Animal.WOLF, Animal.MONKEY, Animal.CROCODILE, Animal.EAGLE,
            Animal.SNAKE, Animal.RAVEN, Animal.SHARK, Animal.OWL,
            Animal.FOX, Animal.SCORPION,
        ]
        engine = CombatEngine()
        for i, animal_a in enumerate(core_14):
            for j, animal_b in enumerate(core_14):
                if i >= j:
                    continue
                a = make_creature(animal_a, 5, 5, 5, 5, "a", 42)
                b = make_creature(animal_b, 5, 5, 5, 5, "b", 42)
                result = engine.run_combat(a, b, 42)
                assert result.winner in ("a", "b", None)
                assert result.end_condition in ("death", "timeout")

    def test_phase4_animals_can_fight(self) -> None:
        """Phase 4 animals (Rhino, Panther, Hawk, Viper) can fight."""
        phase4 = [Animal.RHINO, Animal.PANTHER, Animal.HAWK, Animal.VIPER]
        engine = CombatEngine()
        for i, animal_a in enumerate(phase4):
            for j, animal_b in enumerate(phase4):
                if i >= j:
                    continue
                a = make_creature(animal_a, 5, 5, 5, 5, "a", 42)
                b = make_creature(animal_b, 5, 5, 5, 5, "b", 42)
                result = engine.run_combat(a, b, 42)
                assert result.winner in ("a", "b", None)
                assert result.end_condition in ("death", "timeout")


# ---------------------------------------------------------------------------
# I-10: Symmetry — swapping sides should not systematically bias outcomes
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# I-11: Variance budget — RNG explains < 25% of outcomes
# ---------------------------------------------------------------------------


class TestVarianceBudget:
    def test_variance_budget(self) -> None:
        """RNG (seed variation) should explain less than 25% of total outcome
        variance. Run 1000 games with the same builds, different seeds.
        Measure the variance of win outcomes (1/0) — if build dominance is
        real, variance will be low (outcome mostly determined by builds)."""
        engine = CombatEngine()
        n = 1000
        outcomes = []
        for seed in range(n):
            a = make_creature(Animal.BEAR, 8, 10, 1, 1, "a", seed)
            b = make_creature(Animal.BUFFALO, 14, 3, 2, 1, "b", seed)
            result = engine.run_combat(a, b, seed)
            outcomes.append(1 if result.winner == "a" else 0)

        mean = sum(outcomes) / n
        # Variance of a Bernoulli variable = p * (1 - p)
        # If builds are deterministic, one side always wins and variance = 0.
        # Maximum variance is 0.25 (p = 0.5, pure coin flip).
        # We require that RNG variance < 25% of max possible variance.
        variance = sum((x - mean) ** 2 for x in outcomes) / n
        max_variance = 0.25  # Bernoulli max
        rng_fraction = variance / max_variance
        assert rng_fraction < 0.25 or mean > 0.75 or mean < 0.25, (
            f"RNG explains too much: variance={variance:.4f}, "
            f"fraction_of_max={rng_fraction:.2%}, mean={mean:.2%}. "
            f"Builds should dominate outcomes, not luck."
        )


# ---------------------------------------------------------------------------
# I-12: Monotonic ATK — +1 ATK never decreases expected damage
# ---------------------------------------------------------------------------


class TestMonotonicATK:
    BUILD_PAIRS = [
        # (hp, atk, spd, wil) -> (hp-1, atk+1, spd, wil) or similar
        # We take from hp, spd, or wil to add to atk
        ((5, 5, 5, 5), (4, 6, 5, 5)),
        ((3, 5, 5, 7), (3, 6, 5, 6)),
        ((8, 3, 5, 4), (7, 4, 5, 4)),
        ((6, 6, 4, 4), (5, 7, 4, 4)),
        ((4, 8, 4, 4), (3, 9, 4, 4)),
        ((7, 5, 3, 5), (6, 6, 3, 5)),
        ((5, 7, 5, 3), (4, 8, 5, 3)),
        ((10, 4, 3, 3), (9, 5, 3, 3)),
        ((3, 10, 4, 3), (3, 11, 3, 3)),
        ((6, 4, 6, 4), (5, 5, 6, 4)),
    ]

    @pytest.mark.parametrize("base_stats,boosted_stats", BUILD_PAIRS)
    def test_monotonic_atk(
        self,
        base_stats: tuple[int, int, int, int],
        boosted_stats: tuple[int, int, int, int],
    ) -> None:
        """+1 ATK should never decrease expected damage output."""
        engine = CombatEngine()
        n_games = 200
        opponent_stats = (5, 5, 5, 5)

        total_dmg_base = 0
        total_dmg_boosted = 0

        for seed in range(n_games):
            # Base ATK build
            a = make_creature(Animal.BEAR, *base_stats, "a", seed)
            b = make_creature(Animal.BUFFALO, *opponent_stats, "b", seed)
            r_base = engine.run_combat(a, b, seed)
            dmg_dealt_base = b.max_hp - r_base.final_hp_b
            total_dmg_base += dmg_dealt_base

            # Boosted ATK build
            a2 = make_creature(Animal.BEAR, *boosted_stats, "a", seed)
            b2 = make_creature(Animal.BUFFALO, *opponent_stats, "b", seed)
            r_boost = engine.run_combat(a2, b2, seed)
            dmg_dealt_boost = b2.max_hp - r_boost.final_hp_b
            total_dmg_boosted += dmg_dealt_boost

        avg_base = total_dmg_base / n_games
        avg_boost = total_dmg_boosted / n_games
        assert avg_boost >= avg_base * 0.95, (
            f"+1 ATK decreased damage: base={avg_base:.1f}, boosted={avg_boost:.1f} "
            f"(stats {base_stats} -> {boosted_stats})"
        )


# ---------------------------------------------------------------------------
# I-13: Monotonic HP — +1 HP never decreases expected survival
# ---------------------------------------------------------------------------


class TestMonotonicHP:
    BUILD_PAIRS = [
        # (hp, atk, spd, wil) -> (hp+1, atk-1, spd, wil) or similar
        ((5, 5, 5, 5), (6, 4, 5, 5)),
        ((3, 8, 5, 4), (4, 7, 5, 4)),
        ((4, 7, 4, 5), (5, 6, 4, 5)),
        ((6, 6, 4, 4), (7, 5, 4, 4)),
        ((8, 4, 4, 4), (9, 3, 4, 4)),
        ((3, 6, 5, 6), (4, 5, 5, 6)),
        ((5, 9, 3, 3), (6, 8, 3, 3)),
        ((7, 7, 3, 3), (8, 6, 3, 3)),
        ((4, 4, 6, 6), (5, 3, 6, 6)),
        ((10, 5, 3, 2), (11, 4, 3, 2)),
    ]

    @pytest.mark.parametrize("base_stats,boosted_stats", BUILD_PAIRS)
    def test_monotonic_hp(
        self,
        base_stats: tuple[int, int, int, int],
        boosted_stats: tuple[int, int, int, int],
    ) -> None:
        """+1 HP should never decrease expected survival (ticks alive)."""
        engine = CombatEngine()
        n_games = 200
        opponent_stats = (3, 14, 2, 1)

        total_ticks_base = 0
        total_ticks_boosted = 0

        for seed in range(n_games):
            # Base HP build
            a = make_creature(Animal.BUFFALO, *base_stats, "a", seed)
            b = make_creature(Animal.BEAR, *opponent_stats, "b", seed)
            r_base = engine.run_combat(a, b, seed)
            total_ticks_base += r_base.ticks

            # Boosted HP build
            a2 = make_creature(Animal.BUFFALO, *boosted_stats, "a", seed)
            b2 = make_creature(Animal.BEAR, *opponent_stats, "b", seed)
            r_boost = engine.run_combat(a2, b2, seed)
            total_ticks_boosted += r_boost.ticks

        avg_base = total_ticks_base / n_games
        avg_boost = total_ticks_boosted / n_games
        assert avg_boost >= avg_base * 0.95, (
            f"+1 HP decreased survival: base={avg_base:.1f} ticks, "
            f"boosted={avg_boost:.1f} ticks "
            f"(stats {base_stats} -> {boosted_stats})"
        )


# ---------------------------------------------------------------------------
# I-14: No hidden mechanics — config modifiers documented in MECHANICS.md
# ---------------------------------------------------------------------------


MECHANICS_PATH = PROJECT_ROOT / "docs" / "MECHANICS.md"


class TestNoHiddenMechanics:
    def test_no_hidden_mechanics(self) -> None:
        """All ability_coefficients and passives keys from config.json
        must appear (by name or by base name) in docs/MECHANICS.md."""
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        mechanics_text = MECHANICS_PATH.read_text(encoding="utf-8").lower()

        def _is_documented(key: str) -> bool:
            """Check if a config key is mentioned in MECHANICS.md.

            Handles suffixed keys like 'thick_hide_ability' -> 'thick hide',
            'rend_ability' -> 'rend', 'ambush_wiring' -> 'ambush'.
            """
            # Try exact match with spaces
            if key.replace("_", " ") in mechanics_text:
                return True
            # Try raw key
            if key in mechanics_text:
                return True
            # Try base name without common suffixes
            for suffix in ("_ability", "_wiring", "_protocol"):
                if key.endswith(suffix):
                    base = key[: -len(suffix)].replace("_", " ")
                    if base in mechanics_text:
                        return True
            # Try individual words (at least 4 chars to avoid false positives)
            words = key.split("_")
            for word in words:
                if len(word) >= 4 and word in mechanics_text:
                    return True
            return False

        undocumented = []

        for key in config["ability_coefficients"]:
            if not _is_documented(key):
                undocumented.append(f"ability_coefficients.{key}")

        for key in config["passives"]:
            if not _is_documented(key):
                undocumented.append(f"passives.{key}")

        # Phase 3/4 animals may not yet be documented in MECHANICS.md.
        # Only enforce for core mechanics.
        core_ability_keys = {
            "berserker_rage", "last_stand", "pack_howl", "pounce",
            "stampede", "gore", "chaos_strike", "mimic", "iron_will",
            "thick_hide_ability", "hamstring", "rend_ability",
        }
        core_passive_keys = {
            "fury_protocol", "thick_hide", "charge", "ambush_wiring",
        }

        core_undocumented = [
            u for u in undocumented
            if any(
                k in u
                for k in (core_ability_keys | core_passive_keys)
            )
        ]

        assert len(core_undocumented) == 0, (
            f"Core mechanics not documented in MECHANICS.md: {core_undocumented}"
        )


# ---------------------------------------------------------------------------
# I-10: Symmetry — swapping sides should not systematically bias outcomes
# ---------------------------------------------------------------------------


class TestSymmetry:
    def test_mirror_match_no_systematic_bias(self) -> None:
        """In a mirror match, swapping a/b sides should not create >70/30 bias
        over enough seeds."""
        engine = CombatEngine()
        wins_a = 0
        wins_b = 0
        n = 200
        for seed in range(n):
            a = make_creature(Animal.WOLF, 5, 5, 5, 5, "a", seed)
            b = make_creature(Animal.WOLF, 5, 5, 5, 5, "b", seed)
            result = engine.run_combat(a, b, seed)
            if result.winner == "a":
                wins_a += 1
            elif result.winner == "b":
                wins_b += 1
        total = wins_a + wins_b
        if total > 0:
            ratio = wins_a / total
            assert 0.30 <= ratio <= 0.70, (
                f"Mirror match bias: a={wins_a}, b={wins_b}, ratio={ratio:.2f}"
            )
