#!/usr/bin/env python3
"""Rules-as-Data ability generator for Moreau Arena seasons.

Generates new ability sets expressed in the formal ability grammar,
subject to meta-level constraints (diversity, max win rate).

Uses analytical EV from the grammar to estimate win rates without
running full combat simulations.

Usage:
    python seasons/ability_generator.py --dry-run
    python seasons/ability_generator.py --ability-count 8 --diversity-target 0.9 --dry-run
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from collections import defaultdict

# Add project root to path when running as script
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from simulator.ability_grammar import (
    AbilityDescriptor,
    AbilityEV,
    Trigger,
    Target,
    EffectType,
    Constraint,
    compute_ev,
    compute_effective_proc_rate,
    REF_BASE_DMG,
    REF_MAX_HP,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_ANIMALS: list[str] = [
    "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
    "crocodile", "eagle", "snake", "raven", "shark", "owl",
    "fox", "scorpion",
]

PROC_FLOOR = 0.025
PROC_CEILING = 0.055

MAX_ATTEMPTS = 100

# Effect types excluded from random generation (too complex / special-case)
_EXCLUDED_EFFECTS: set[EffectType] = {EffectType.COPY}

# Triggers available for random generation
_USABLE_TRIGGERS: list[Trigger] = list(Trigger)

# Targets available for random generation
_USABLE_TARGETS: list[Target] = [Target.SELF, Target.OPPONENT, Target.BOTH]

# Constraints available for random generation (excluding special-case ones)
_USABLE_CONSTRAINTS: list[Constraint] = [
    Constraint.NONE,
    Constraint.SINGLE_CHARGE,
    Constraint.HP_THRESHOLD_50,
    Constraint.MAX_STACKS,
]

# Effect types available for random generation
_USABLE_EFFECTS: list[EffectType] = [
    e for e in EffectType if e not in _EXCLUDED_EFFECTS
]

# Name fragments for procedural ability naming
_NAME_PREFIXES: list[str] = [
    "Primal", "Savage", "Keen", "Swift", "Dark", "Iron",
    "Storm", "Blood", "Shadow", "Razor", "Feral", "Ancient",
    "Wild", "Dread", "Frost", "Flame", "Venom", "Stone",
]

_NAME_SUFFIXES: dict[EffectType, list[str]] = {
    EffectType.ATK_BUFF: ["Strike", "Fury", "Surge", "Blow"],
    EffectType.ATK_BUFF_DURATION: ["Rage", "Frenzy", "Wrath", "Onslaught"],
    EffectType.DMG_BLOCK: ["Shield", "Guard", "Wall", "Barrier"],
    EffectType.DODGE_BUFF: ["Reflex", "Evasion", "Sidestep", "Blur"],
    EffectType.DODGE_DEBUFF: ["Snare", "Hex", "Bind", "Entangle"],
    EffectType.DOT: ["Bleed", "Burn", "Toxin", "Decay"],
    EffectType.HEAL: ["Mend", "Restoration", "Recovery", "Vitality"],
    EffectType.SKIP_ATTACK: ["Stun", "Daze", "Paralyze", "Disrupt"],
    EffectType.IGNORE_DODGE: ["Pierce", "Thrust", "Impale", "Breach"],
    EffectType.RANDOM_ATK: ["Gambit", "Wildcard", "Chaos", "Roulette"],
    EffectType.NEGATE_PROC: ["Silence", "Nullify", "Counter", "Interrupt"],
    EffectType.INSTANT_DMG: ["Bolt", "Blast", "Impact", "Smite"],
}


# ---------------------------------------------------------------------------
# Ability name generation
# ---------------------------------------------------------------------------


def _generate_ability_name(effect: EffectType, rng: random.Random) -> str:
    """Generate a procedural ability name based on effect type."""
    prefix = rng.choice(_NAME_PREFIXES)
    suffixes = _NAME_SUFFIXES.get(effect, ["Strike", "Force", "Power"])
    suffix = rng.choice(suffixes)
    return f"{prefix} {suffix}"


# ---------------------------------------------------------------------------
# Random ability generation
# ---------------------------------------------------------------------------


def _random_ability(animal: str, rng: random.Random) -> AbilityDescriptor:
    """Generate a single random ability for the given animal.

    Selects random grammar components (trigger, target, effect, constraint)
    and generates appropriate coefficients for the chosen effect type.
    Proc chance is drawn uniformly from [PROC_FLOOR, PROC_CEILING].
    """
    trigger = rng.choice(_USABLE_TRIGGERS)
    target = rng.choice(_USABLE_TARGETS)
    effect = rng.choice(_USABLE_EFFECTS)
    constraint = rng.choice(_USABLE_CONSTRAINTS)

    proc_chance = round(rng.uniform(PROC_FLOOR, PROC_CEILING), 4)
    name = _generate_ability_name(effect, rng)

    # Default coefficient values
    atk_mod = 0.0
    duration = 0
    dot_pct = 0.0
    heal_pct = 0.0
    block_pct = 0.0
    dodge_delta = 0.0
    random_range = (1.0, 1.0)
    max_stacks = 1
    is_single_charge = constraint == Constraint.SINGLE_CHARGE
    skip_opponent = False

    # Set coefficients based on effect type
    if effect == EffectType.ATK_BUFF:
        atk_mod = round(rng.uniform(0.2, 1.0), 2)
        # ATK_BUFF with Target.BOTH can also skip opponent attack
        if target == Target.BOTH:
            skip_opponent = True

    elif effect == EffectType.ATK_BUFF_DURATION:
        atk_mod = round(rng.uniform(0.2, 0.8), 2)
        duration = rng.randint(2, 4)
        # Optionally add a dodge penalty for strong buffs
        if atk_mod > 0.5:
            dodge_delta = -round(rng.uniform(0.1, 0.4), 2)

    elif effect == EffectType.DMG_BLOCK:
        # Either full block (1.0) or partial block
        if rng.random() < 0.3:
            block_pct = 1.0
            duration = 1
        else:
            block_pct = round(rng.uniform(0.10, 0.30), 2)
            duration = rng.randint(1, 2)

    elif effect == EffectType.DODGE_BUFF:
        dodge_delta = round(rng.uniform(0.15, 0.60), 2)
        duration = rng.randint(1, 3)

    elif effect == EffectType.DODGE_DEBUFF:
        dodge_delta = -round(rng.uniform(0.05, 0.15), 2)
        duration = rng.randint(2, 4)
        target = Target.OPPONENT  # debuffs always target opponent

    elif effect == EffectType.DOT:
        dot_pct = round(rng.uniform(0.02, 0.06), 3)
        duration = rng.randint(2, 4)
        if constraint == Constraint.MAX_STACKS:
            max_stacks = rng.randint(2, 4)
        target = Target.OPPONENT  # DOTs always target opponent

    elif effect == EffectType.HEAL:
        heal_pct = round(rng.uniform(0.05, 0.15), 2)
        target = Target.SELF  # heals always target self

    elif effect == EffectType.SKIP_ATTACK:
        skip_opponent = True
        target = Target.OPPONENT

    elif effect == EffectType.IGNORE_DODGE:
        # Ignore dodge with ATK penalty (tradeoff)
        atk_mod = -round(rng.uniform(0.2, 0.5), 2)

    elif effect == EffectType.RANDOM_ATK:
        lo = round(rng.uniform(0.5, 1.0), 1)
        hi = round(rng.uniform(1.5, 2.5), 1)
        random_range = (lo, hi)

    elif effect == EffectType.NEGATE_PROC:
        duration = 1
        target = Target.SELF

    elif effect == EffectType.INSTANT_DMG:
        atk_mod = round(rng.uniform(0.3, 0.8), 2)

    return AbilityDescriptor(
        name=name,
        animal=animal,
        trigger=trigger,
        target=target,
        effect_type=effect,
        constraint=constraint,
        proc_chance=proc_chance,
        atk_mod=atk_mod,
        duration=duration,
        dot_pct=dot_pct,
        heal_pct=heal_pct,
        block_pct=block_pct,
        dodge_delta=dodge_delta,
        random_range=random_range,
        max_stacks=max_stacks,
        is_single_charge=is_single_charge,
        skip_opponent=skip_opponent,
    )


# ---------------------------------------------------------------------------
# Ability set evaluation
# ---------------------------------------------------------------------------


def _compute_animal_ev(abilities: list[AbilityDescriptor]) -> dict[str, float]:
    """Compute total EV (damage + mitigation) for each animal.

    Groups abilities by animal, sums their per-tick EV contributions,
    and returns a dict of animal -> total_ev.
    """
    ev_by_animal: dict[str, float] = defaultdict(float)

    for ab in abilities:
        ev = compute_ev(ab)
        total_per_tick = ev.ev_damage_per_tick + (
            ev.ev_mitigation_per_proc
            * compute_effective_proc_rate(ab.proc_chance)
        )
        ev_by_animal[ab.animal] += total_per_tick

    return dict(ev_by_animal)


def _estimate_win_rates(
    abilities: list[AbilityDescriptor],
) -> dict[str, float]:
    """Estimate per-animal win rates from analytical EV.

    Animals with higher total EV are assumed to win more often.
    Win rates are computed via a logistic function centered at the mean EV,
    which naturally compresses extreme values into (0, 1) and prevents
    any single high-EV ability from dominating the ranking.

    For animals without any generated abilities, a baseline EV of 0.0
    is used (they rely only on base stats, which are equal for all).
    """
    ev_map = _compute_animal_ev(abilities)

    # Include all 14 animals, defaulting to 0.0 EV for those without abilities
    all_evs: dict[str, float] = {}
    for animal in ALL_ANIMALS:
        all_evs[animal] = ev_map.get(animal, 0.0)

    n = len(ALL_ANIMALS)
    mean_ev = sum(all_evs.values()) / n

    # Compute standard deviation for scaling
    variance = sum((ev - mean_ev) ** 2 for ev in all_evs.values()) / max(n, 1)
    std_ev = math.sqrt(variance) if variance > 0 else 1.0

    if std_ev < 1e-9:
        # All EVs are effectively equal
        return {animal: 0.5 for animal in ALL_ANIMALS}

    # Logistic function: wr = 1 / (1 + exp(-k * (ev - mean)))
    # k controls sensitivity; set so that 1 std dev -> ~0.12 WR change
    # sigmoid(0.5) ~ 0.62, so k = 0.5/std gives 1 std -> ~62% WR
    k = 0.5 / std_ev

    win_rates: dict[str, float] = {}
    for animal in ALL_ANIMALS:
        z = k * (all_evs[animal] - mean_ev)
        # Clamp z to avoid overflow
        z = max(-10.0, min(10.0, z))
        wr = 1.0 / (1.0 + math.exp(-z))
        win_rates[animal] = wr

    return win_rates


def _evaluate_ability_set(
    abilities: list[AbilityDescriptor],
    config: dict,
) -> tuple[bool, dict]:
    """Evaluate whether an ability set meets config constraints.

    Checks:
    1. diversity_target: fraction of animals with at least one ability
    2. max_win_rate: no animal's estimated win rate exceeds the threshold

    Returns (passes, metrics_dict) where metrics_dict contains:
        - diversity: fraction of animals with abilities
        - max_wr: highest estimated win rate
        - min_wr: lowest estimated win rate
        - wr_spread: max_wr - min_wr
        - win_rates: full per-animal win rate dict
    """
    diversity_target = config.get("diversity_target", 0.8)
    max_win_rate = config.get("max_win_rate", 0.65)

    # Diversity: fraction of animals that have at least one ability
    animals_with_abilities = set(ab.animal for ab in abilities)
    diversity = len(animals_with_abilities) / len(ALL_ANIMALS)

    # Win rates
    win_rates = _estimate_win_rates(abilities)
    max_wr = max(win_rates.values())
    min_wr = min(win_rates.values())

    metrics = {
        "diversity": round(diversity, 4),
        "max_wr": round(max_wr, 4),
        "min_wr": round(min_wr, 4),
        "wr_spread": round(max_wr - min_wr, 4),
        "win_rates": {k: round(v, 4) for k, v in sorted(win_rates.items())},
    }

    passes = diversity >= diversity_target and max_wr <= max_win_rate

    return passes, metrics


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------


def generate_ability_set(
    config: dict,
    seed: int | None = None,
) -> tuple[list[AbilityDescriptor], dict]:
    """Generate a new ability set matching the config constraints.

    Uses sampling + rejection: generates random ability sets, evaluates
    them against the constraints, and returns the first passing set.
    If no set passes within MAX_ATTEMPTS, returns the best found so far.

    Args:
        config: Dict with keys:
            - diversity_target (float): minimum fraction of animals picked
            - max_win_rate (float): no animal exceeds this win rate
            - ability_count (int): number of abilities to generate
        seed: Optional random seed for reproducibility.

    Returns:
        (abilities, metrics) tuple where abilities is a list of
        AbilityDescriptor and metrics is the evaluation dict.
    """
    rng = random.Random(seed)
    ability_count = config.get("ability_count", 6)
    diversity_target = config.get("diversity_target", 0.8)

    # Compute minimum number of distinct animals needed
    min_animals = max(1, math.ceil(diversity_target * len(ALL_ANIMALS)))

    best_abilities: list[AbilityDescriptor] = []
    best_metrics: dict = {}
    best_score = -float("inf")

    for attempt in range(MAX_ATTEMPTS):
        # Select animals to receive abilities
        # Ensure at least min_animals distinct animals are chosen
        if ability_count >= min_animals:
            # Pick min_animals distinct animals, then fill remaining slots
            chosen = rng.sample(ALL_ANIMALS, min_animals)
            remaining_slots = ability_count - min_animals
            if remaining_slots > 0:
                extras = rng.choices(ALL_ANIMALS, k=remaining_slots)
                chosen.extend(extras)
        else:
            # ability_count < min_animals: just pick ability_count distinct
            chosen = rng.sample(ALL_ANIMALS, min(ability_count, len(ALL_ANIMALS)))

        # Generate one ability per slot
        abilities = [_random_ability(animal, rng) for animal in chosen]

        # Validate proc rates
        valid = all(PROC_FLOOR <= ab.proc_chance <= PROC_CEILING for ab in abilities)
        if not valid:
            continue

        # Evaluate against constraints
        passes, metrics = _evaluate_ability_set(abilities, config)

        # Score: prefer higher diversity and lower spread
        score = metrics["diversity"] * 10 - metrics["wr_spread"] * 5
        if passes:
            score += 100  # Bonus for passing

        if score > best_score:
            best_score = score
            best_abilities = abilities
            best_metrics = metrics

        if passes:
            return best_abilities, best_metrics

    return best_abilities, best_metrics


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def _format_ability(ab: AbilityDescriptor, ev: AbilityEV) -> str:
    """Format a single ability for display."""
    eff_proc = compute_effective_proc_rate(ab.proc_chance)
    lines = [
        f"  {ab.name} ({ab.animal})",
        f"    Grammar: {ab.trigger.value} x {ab.target.value} x "
        f"{ab.effect_type.value} x {ab.constraint.value}",
        f"    Proc: {ab.proc_chance:.4f} (effective: {eff_proc:.4f})",
        f"    EV/proc: dmg={ev.ev_damage_per_proc:.2f}, "
        f"mit={ev.ev_mitigation_per_proc:.2f}",
        f"    EV/tick: dmg={ev.ev_damage_per_tick:.4f}",
        f"    Var: {ev.variance_per_proc:.2f}",
        f"    {ev.description}",
    ]

    # Show relevant coefficients
    coeffs: list[str] = []
    if ab.atk_mod != 0.0:
        coeffs.append(f"atk_mod={ab.atk_mod:+.2f}")
    if ab.duration > 0:
        coeffs.append(f"duration={ab.duration}")
    if ab.dot_pct > 0:
        coeffs.append(f"dot_pct={ab.dot_pct:.3f}")
    if ab.heal_pct > 0:
        coeffs.append(f"heal_pct={ab.heal_pct:.2f}")
    if ab.block_pct > 0:
        coeffs.append(f"block_pct={ab.block_pct:.2f}")
    if ab.dodge_delta != 0.0:
        coeffs.append(f"dodge_delta={ab.dodge_delta:+.2f}")
    if ab.random_range != (1.0, 1.0):
        coeffs.append(f"random_range={ab.random_range}")
    if ab.max_stacks > 1:
        coeffs.append(f"max_stacks={ab.max_stacks}")
    if ab.is_single_charge:
        coeffs.append("single_charge=True")
    if ab.skip_opponent:
        coeffs.append("skip_opponent=True")

    if coeffs:
        lines.append(f"    Coefficients: {', '.join(coeffs)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate new ability sets for Moreau Arena seasons",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate one valid ability set and print results",
    )
    parser.add_argument(
        "--ability-count",
        type=int,
        default=6,
        help="Number of abilities to generate (default: 6)",
    )
    parser.add_argument(
        "--diversity-target",
        type=float,
        default=0.8,
        help="Minimum fraction of animals that must receive abilities (default: 0.8)",
    )
    parser.add_argument(
        "--max-win-rate",
        type=float,
        default=0.65,
        help="Maximum allowed estimated win rate for any animal (default: 0.65)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args(argv)

    if not args.dry_run:
        parser.error("Currently only --dry-run mode is supported")

    config = {
        "diversity_target": args.diversity_target,
        "max_win_rate": args.max_win_rate,
        "ability_count": args.ability_count,
    }

    print("=" * 72)
    print("MOREAU ARENA -- Ability Generator (Rules-as-Data)")
    print("=" * 72)
    print()
    print("Configuration:")
    print(f"  ability_count:    {config['ability_count']}")
    print(f"  diversity_target: {config['diversity_target']:.0%}")
    print(f"  max_win_rate:     {config['max_win_rate']:.0%}")
    print(f"  proc range:       [{PROC_FLOOR}, {PROC_CEILING}]")
    print(f"  max_attempts:     {MAX_ATTEMPTS}")
    if args.seed is not None:
        print(f"  seed:             {args.seed}")
    print()

    abilities, metrics = generate_ability_set(config, seed=args.seed)

    # Check if constraints were met
    passes = (
        metrics["diversity"] >= config["diversity_target"]
        and metrics["max_wr"] <= config["max_win_rate"]
    )

    print("=" * 72)
    print("Generated Ability Set")
    print("=" * 72)
    print()

    for i, ab in enumerate(abilities, 1):
        ev = compute_ev(ab)
        print(f"[{i}] {_format_ability(ab, ev)}")
        print()

    print("=" * 72)
    print("Evaluation Metrics")
    print("=" * 72)
    print()
    print(f"  Diversity:  {metrics['diversity']:.0%} "
          f"(target: >= {config['diversity_target']:.0%}) "
          f"{'PASS' if metrics['diversity'] >= config['diversity_target'] else 'FAIL'}")
    print(f"  Max WR:     {metrics['max_wr']:.4f} "
          f"(target: <= {config['max_win_rate']:.2f}) "
          f"{'PASS' if metrics['max_wr'] <= config['max_win_rate'] else 'FAIL'}")
    print(f"  Min WR:     {metrics['min_wr']:.4f}")
    print(f"  WR Spread:  {metrics['wr_spread']:.4f}")
    print()

    print("  Per-animal estimated win rates:")
    for animal, wr in sorted(
        metrics["win_rates"].items(), key=lambda x: -x[1]
    ):
        has_ability = any(ab.animal == animal for ab in abilities)
        marker = "*" if has_ability else " "
        print(f"    {marker} {animal:12s}  {wr:.4f}")
    print()
    print("  (* = has generated ability)")
    print()

    status = "PASS" if passes else "BEST-EFFORT (constraints not fully met)"
    print(f"  Overall: {status}")
    print()

    if not passes:
        print(
            "  Note: Could not find a fully passing set within "
            f"{MAX_ATTEMPTS} attempts."
        )
        print("  Returned best set found. Try increasing --ability-count")
        print("  or relaxing constraints.")
        print()

    print("[dry-run] No files written.")


if __name__ == "__main__":
    main()
