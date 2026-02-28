"""Ability system — proc rolls, buff tracking, effect application.

Standalone version for the companion repository.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

from simulator.animals import (
    Ability,
    AbilityBuff,
    AbilityType,
    ActiveEffect,
    ANIMAL_ABILITIES,
    Creature,
    Passive,
)
from simulator.seed import derive_proc_seed, seeded_bool, seeded_random

# Abilities that Mimic cannot copy
MIMIC_BLOCKED = frozenset({
    AbilityType.IRON_WILL,
    AbilityType.LAST_STAND,
    AbilityType.MIMIC,
})


# -- Proc system --------------------------------------------------------------


def roll_ability_procs(
    creature: Creature,
    opponent: Creature,
    match_seed: int,
    tick: int,
    creature_index: int,
    side: str,
    events: list[dict[str, Any]],
) -> tuple[Creature, Creature]:
    """Roll ability procs for a creature, applying WIL resist checks."""
    last_procced: AbilityType | None = None
    for ability_index, ability in enumerate(creature.abilities):
        if ability.is_single_charge:
            if (
                ability.ability_type == AbilityType.IRON_WILL
                and creature.iron_will_used
            ):
                continue
            if (
                ability.ability_type == AbilityType.LAST_STAND
                and creature.last_stand_used
            ):
                continue

        # Last Stand only procs when HP < 15%
        if ability.ability_type == AbilityType.LAST_STAND:
            if creature.current_hp >= creature.max_hp * 0.15:
                continue

        proc_seed = derive_proc_seed(
            match_seed, tick, creature_index, ability_index,
        )
        eff_proc = ability.proc_chance + creature.stats.wil * 0.0008
        if not seeded_bool(proc_seed, eff_proc):
            continue

        resist_seed = proc_seed + 7
        wil_resist_chance = min(0.60, opponent.stats.wil * 0.033)
        if seeded_bool(resist_seed, wil_resist_chance):
            events.append({
                "type": "ability_resisted",
                "side": side,
                "ability": ability.ability_type.value,
            })
            continue

        # Trick reflection: opponent's Trick buff negates this proc
        trick_idx = _find_trick_buff_index(opponent)
        if trick_idx is not None:
            new_buffs = [
                b for i, b in enumerate(opponent.active_buffs) if i != trick_idx
            ]
            opponent = dataclasses.replace(opponent, active_buffs=new_buffs)
            events.append({
                "type": "trick_reflected",
                "side": side,
                "ability": ability.ability_type.value,
            })
            continue

        creature, opponent = _apply_ability_proc(
            creature, opponent, ability, side, events, proc_seed,
        )
        last_procced = ability.ability_type

    if last_procced is not None:
        creature = dataclasses.replace(
            creature, last_ability_procced=last_procced,
        )
    return creature, opponent


def _apply_ability_proc(
    creature: Creature,
    opponent: Creature,
    ability: Ability,
    side: str,
    events: list[dict[str, Any]],
    proc_seed: int,
) -> tuple[Creature, Creature]:
    """Apply a single ability proc effect."""
    atype = ability.ability_type

    # Single-charge: mark as used
    if ability.is_single_charge:
        if atype == AbilityType.IRON_WILL:
            creature = dataclasses.replace(creature, iron_will_used=True)
        elif atype == AbilityType.LAST_STAND:
            creature = dataclasses.replace(creature, last_stand_used=True)

    # -- Self-buff abilities (duration or instant) --

    if atype == AbilityType.BERSERKER_RAGE:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == AbilityType.THICK_HIDE_ABILITY:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == AbilityType.PACK_HOWL:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype in (
        AbilityType.POUNCE,
        AbilityType.CHAOS_STRIKE,
        AbilityType.GORE,
        AbilityType.STAMPEDE,
        AbilityType.LAST_STAND,
        AbilityType.DIVE,
    ):
        # Instant "next hit" buffs -- 1-tick duration
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )
        # Stampede and Pounce make opponent skip next attack
        if atype in (AbilityType.STAMPEDE, AbilityType.POUNCE):
            opponent = dataclasses.replace(
                opponent, skip_next_attack=True,
            )

    # -- Phase 3: Self-buff abilities (duration) --

    elif atype == AbilityType.KEEN_EYE:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == AbilityType.EVASION:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == AbilityType.COIL:
        # Guaranteed dodge for 1 tick
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == AbilityType.TRICK:
        # Negate next opponent proc -- 1 tick
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == AbilityType.EXOSKELETON:
        # Block damage up to 15% max_hp -- 1 tick
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
        )

    # -- Instant effects --

    elif atype == AbilityType.IRON_WILL:
        heal = math.floor(creature.max_hp * 0.12)
        new_hp = min(creature.max_hp, creature.current_hp + heal)
        creature = dataclasses.replace(creature, current_hp=new_hp)

    # -- Opponent-affecting abilities --

    elif atype == AbilityType.HAMSTRING:
        debuff = AbilityBuff(atype, ability.duration, side)
        opponent = dataclasses.replace(
            opponent,
            active_buffs=[*opponent.active_buffs, debuff],
        )

    elif atype == AbilityType.REND_ABILITY:
        dot_dmg = max(1, math.floor(creature.max_hp * 0.05))
        bleed = ActiveEffect(
            name="ability_rend",
            remaining_ticks=3,
            damage_per_tick=dot_dmg,
        )
        opponent = dataclasses.replace(
            opponent,
            active_effects=[*opponent.active_effects, bleed],
        )

    elif atype == AbilityType.VENOM:
        # Stacking poison DOT: 3% of opponent max_hp per tick, 3 ticks, max 3 stacks
        existing_venoms = [
            e for e in opponent.active_effects if e.name == "ability_venom"
        ]
        if len(existing_venoms) < 3:
            dot_dmg = max(1, math.floor(opponent.max_hp * 0.03))
            venom = ActiveEffect(
                name="ability_venom",
                remaining_ticks=3,
                damage_per_tick=dot_dmg,
            )
            opponent = dataclasses.replace(
                opponent,
                active_effects=[*opponent.active_effects, venom],
            )

    elif atype == AbilityType.STING:
        # Paralyze -- opponent skips next attack
        opponent = dataclasses.replace(
            opponent, skip_next_attack=True,
        )

    # -- Mimic --

    elif atype == AbilityType.MIMIC:
        creature, opponent = _apply_mimic(
            creature, opponent, side, events, proc_seed,
        )

    events.append({
        "type": "ability_proc",
        "side": side,
        "ability": atype.value,
        "duration": ability.duration,
    })

    return creature, opponent


def _apply_mimic(
    creature: Creature,
    opponent: Creature,
    side: str,
    events: list[dict[str, Any]],
    proc_seed: int,
) -> tuple[Creature, Creature]:
    """Apply Mimic: copy opponent's last procced ability at 75% strength."""
    target_ability = opponent.last_ability_procced
    if target_ability is None or not can_mimic(target_ability):
        return creature, opponent

    # Find the original ability definition
    original: Ability | None = None
    for animal_abilities in ANIMAL_ABILITIES.values():
        for ab in animal_abilities:
            if ab.ability_type == target_ability:
                original = ab
                break
        if original is not None:
            break

    if original is None:
        return creature, opponent

    # Copy as mimic buff at 75% strength (1-tick delay handled naturally)
    duration = max(1, original.duration) if original.duration > 0 else 1
    buff = AbilityBuff(
        ability_type=target_ability,
        remaining_ticks=duration,
        source_side=side,
        is_mimic_copy=True,
    )
    creature = dataclasses.replace(
        creature,
        active_buffs=[*creature.active_buffs, buff],
    )

    return creature, opponent


# -- Attack modifiers from ability buffs ---------------------------------------


def apply_ability_attack_mods(
    attacker: Creature,
    atk_mod: float,
    hit_seed: int,
) -> tuple[Creature, float]:
    """Apply ATK modifiers from active ability buffs."""
    for buff in attacker.active_buffs:
        mimic_scale = 0.75 if buff.is_mimic_copy else 1.0

        if buff.ability_type == AbilityType.PACK_HOWL:
            atk_mod *= 1.0 + 0.30 * mimic_scale

        elif buff.ability_type == AbilityType.POUNCE:
            atk_mod *= 1.0 + 0.70 * mimic_scale

        elif buff.ability_type == AbilityType.STAMPEDE:
            atk_mod *= 1.0 + 0.50 * mimic_scale

        elif buff.ability_type == AbilityType.LAST_STAND:
            if attacker.current_hp < attacker.max_hp * 0.15:
                atk_mod *= 1.0 + 1.0 * mimic_scale

        elif buff.ability_type == AbilityType.GORE:
            atk_mod *= 0.60

        elif buff.ability_type == AbilityType.CHAOS_STRIKE:
            chaos_mod = get_chaos_strike_mod(hit_seed + 777)
            if buff.is_mimic_copy:
                # 75% strength: narrow range toward 1.0
                chaos_mod = 1.0 + (chaos_mod - 1.0) * 0.75
            atk_mod = chaos_mod

        elif buff.ability_type == AbilityType.DIVE:
            atk_mod *= 1.0 + 1.0 * mimic_scale

    return attacker, atk_mod


# -- Buff queries --------------------------------------------------------------


def has_buff(creature: Creature, ability_type: AbilityType) -> bool:
    """Check if creature has an active buff of the given type."""
    return any(
        b.ability_type == ability_type for b in creature.active_buffs
    )


def has_ignore_dodge_buff(creature: Creature) -> bool:
    """Check if creature has a buff that ignores dodge (Pounce, Gore, or Dive)."""
    return any(
        b.ability_type in (AbilityType.POUNCE, AbilityType.GORE, AbilityType.DIVE)
        for b in creature.active_buffs
    )


def get_effective_dodge(creature: Creature) -> float:
    """Calculate effective dodge chance accounting for ability buffs/debuffs."""
    # Coil: guaranteed dodge, overrides everything
    for buff in creature.active_buffs:
        if buff.ability_type == AbilityType.COIL:
            return 1.0

    dodge = creature.dodge_chance

    # Additive dodge bonuses (Keen Eye, Evasion)
    for buff in creature.active_buffs:
        if buff.ability_type == AbilityType.KEEN_EYE:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge += 0.20 * scale

        elif buff.ability_type == AbilityType.EVASION:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge += 0.50 * scale

    # Berserker Rage: -40% dodge
    for buff in creature.active_buffs:
        if buff.ability_type == AbilityType.BERSERKER_RAGE:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge *= (1.0 - 0.40 * scale)

    # Hamstring: SPD -55% + flat -10% dodge
    for buff in creature.active_buffs:
        if buff.ability_type == AbilityType.HAMSTRING:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge *= (1.0 - 0.55 * scale)
            dodge -= 0.10 * scale

    return max(0.0, min(1.0, dodge))


def can_mimic(ability_type: AbilityType) -> bool:
    """Check if an ability type can be copied by Mimic."""
    return ability_type not in MIMIC_BLOCKED


# -- Defense from ability buffs ------------------------------------------------


def apply_ability_defense(
    defender: Creature, dmg: int,
) -> tuple[Creature, int]:
    """Apply defensive ability effects (Thick Hide block, Exoskeleton)."""
    # Check for Thick Hide first (full block, highest priority)
    has_thick_hide = any(
        b.ability_type == AbilityType.THICK_HIDE_ABILITY
        for b in defender.active_buffs
    )
    if has_thick_hide:
        remaining = [
            b for b in defender.active_buffs
            if b.ability_type != AbilityType.THICK_HIDE_ABILITY
        ]
        return dataclasses.replace(defender, active_buffs=remaining), 0

    # Check for Exoskeleton (partial block up to 15% max_hp)
    has_exo = any(
        b.ability_type == AbilityType.EXOSKELETON
        for b in defender.active_buffs
    )
    if has_exo:
        remaining = [
            b for b in defender.active_buffs
            if b.ability_type != AbilityType.EXOSKELETON
        ]
        block_amount = math.floor(defender.max_hp * 0.15)
        dmg = max(0, dmg - block_amount)
        return dataclasses.replace(defender, active_buffs=remaining), dmg

    return defender, dmg


# -- Fury C3 -------------------------------------------------------------------


def check_fury_trigger(creature: Creature) -> Creature:
    """Check and trigger Fury Protocol (< 50% HP, 3-tick window)."""
    if creature.passive != Passive.FURY_PROTOCOL:
        return creature
    if creature.fury_triggered:
        return creature
    if creature.current_hp >= creature.max_hp * 0.5:
        return creature
    return dataclasses.replace(
        creature,
        fury_triggered=True,
        fury_active_ticks=3,
    )


def tick_fury(creature: Creature) -> Creature:
    """Decrement Fury active ticks."""
    if creature.fury_active_ticks <= 0:
        return creature
    return dataclasses.replace(
        creature,
        fury_active_ticks=creature.fury_active_ticks - 1,
    )


# -- Buff management -----------------------------------------------------------


def tick_ability_buffs(creature: Creature) -> Creature:
    """Tick down all ability buff durations, removing expired ones."""
    if not creature.active_buffs:
        return creature
    remaining = [
        AbilityBuff(
            ability_type=buff.ability_type,
            remaining_ticks=buff.remaining_ticks - 1,
            source_side=buff.source_side,
            is_mimic_copy=buff.is_mimic_copy,
        )
        for buff in creature.active_buffs
    ]
    remaining = [b for b in remaining if b.remaining_ticks > 0]
    return dataclasses.replace(creature, active_buffs=remaining)


# -- Internal helpers ----------------------------------------------------------


def get_chaos_strike_mod(seed: int) -> float:
    return seeded_random(seed, 0.8, 2.2)


def _find_trick_buff_index(creature: Creature) -> int | None:
    """Find the index of an active Trick buff, or None."""
    for i, buff in enumerate(creature.active_buffs):
        if buff.ability_type == AbilityType.TRICK:
            return i
    return None
