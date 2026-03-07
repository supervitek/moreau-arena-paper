"""Season 1 combat engine for Moreau Arena.

Self-contained engine handling all 14 Season 1 animals with WIL regen.
No imports from simulator/ — all seed, grid, and ability logic is inline.
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import struct
from dataclasses import dataclass, field
from typing import Any

from season1.animals_s1 import (
    Ability,
    AbilityBuff,
    ActiveEffect,
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Creature,
    Position,
    S1AbilityType,
    S1Animal,
    S1Passive,
    Size,
    StatBlock,
)


# ===========================================================================
# Seed functions (inline from simulator/seed.py)
# ===========================================================================

def derive_tick_seed(match_seed: int, tick_index: int) -> int:
    data = struct.pack(">QI", match_seed, tick_index)
    h = hashlib.sha256(data).digest()
    return struct.unpack(">I", h[:4])[0]


def derive_hit_seed(match_seed: int, tick_index: int, attack_index: int) -> int:
    data = struct.pack(">QII", match_seed, tick_index, attack_index)
    h = hashlib.sha256(data).digest()
    return struct.unpack(">I", h[:4])[0]


def seeded_random(seed: int, min_val: float = 0.0, max_val: float = 1.0) -> float:
    seed = seed & 0xFFFFFFFF
    data = struct.pack(">I", seed)
    h = hashlib.sha256(data).digest()
    raw = struct.unpack(">Q", h[:8])[0]
    normalized = raw / (2**64)
    return min_val + normalized * (max_val - min_val)


def seeded_bool(seed: int, probability: float) -> bool:
    return seeded_random(seed) < probability


def derive_proc_seed(
    match_seed: int, tick_index: int, creature_index: int, ability_index: int,
) -> int:
    data = struct.pack(">QIBB", match_seed, tick_index, creature_index, ability_index)
    h = hashlib.sha256(data).digest()
    return struct.unpack(">I", h[:4])[0]


# ===========================================================================
# Grid (inline from simulator/grid.py)
# ===========================================================================

class Grid:
    def __init__(self, width: int = 8, height: int = 8) -> None:
        self.width = width
        self.height = height
        self._cells: dict[Position, Creature] = {}

    def is_valid_position(self, position: Position, size: Size) -> bool:
        if position.row < 0 or position.col < 0:
            return False
        if position.row + size.rows > self.height:
            return False
        if position.col + size.cols > self.width:
            return False
        return True

    def get_occupied_cells(self, position: Position, size: Size) -> list[Position]:
        cells = []
        for dr in range(size.rows):
            for dc in range(size.cols):
                cells.append(Position(position.row + dr, position.col + dc))
        return cells

    def place_creature(self, creature: Creature) -> None:
        if not self.is_valid_position(creature.position, creature.size):
            raise ValueError(f"Position {creature.position} invalid for size {creature.size}")
        cells = self.get_occupied_cells(creature.position, creature.size)
        for cell in cells:
            if cell in self._cells and self._cells[cell] is not creature:
                raise ValueError(f"Cell {cell} already occupied")
        for cell in cells:
            self._cells[cell] = creature

    def remove_creature(self, creature: Creature) -> None:
        cells = self.get_occupied_cells(creature.position, creature.size)
        for cell in cells:
            if cell in self._cells and self._cells[cell] is creature:
                del self._cells[cell]

    @staticmethod
    def get_distance(a: Position, b: Position) -> int:
        return max(abs(a.row - b.row), abs(a.col - b.col))

    def _is_position_free(self, pos: Position, size: Size, exclude: Creature | None = None) -> bool:
        if not self.is_valid_position(pos, size):
            return False
        for cell in self.get_occupied_cells(pos, size):
            occupant = self._cells.get(cell)
            if occupant is not None and occupant is not exclude:
                return False
        return True

    def find_path_toward(self, creature: Creature, target: Position) -> Position:
        best_pos = creature.position
        best_dist = self.get_distance(creature.position, target)
        for dr in range(-creature.movement_range, creature.movement_range + 1):
            for dc in range(-creature.movement_range, creature.movement_range + 1):
                if dr == 0 and dc == 0:
                    continue
                candidate = Position(creature.position.row + dr, creature.position.col + dc)
                move_dist = self.get_distance(creature.position, candidate)
                if move_dist > creature.movement_range:
                    continue
                if not self._is_position_free(candidate, creature.size, exclude=creature):
                    continue
                dist_to_target = self.get_distance(candidate, target)
                if dist_to_target < best_dist:
                    best_dist = dist_to_target
                    best_pos = candidate
                elif dist_to_target == best_dist and candidate < best_pos:
                    best_pos = candidate
        return best_pos

    def generate_starting_position(self, side: str, size: Size, seed: int) -> Position:
        max_col = self.width - size.cols
        col_f = seeded_random(seed, 0.0, max_col + 0.999)
        col = int(col_f)
        col = max(0, min(col, max_col))
        if side == "a":
            max_row = min(1, self.height - size.rows)
            row = 0 if size.rows >= 2 else max_row
        else:
            min_start = self.height - size.rows - 1
            row = max(min_start, self.height - size.rows)
        return Position(row=row, col=col)


# ===========================================================================
# Creature factory
# ===========================================================================

def create_creature(
    animal_name: str,
    stats: tuple[int, int, int, int],
    side: str,
    grid: Grid,
    seed: int,
) -> Creature:
    """Create a Creature from animal name and stat tuple (hp, atk, spd, wil)."""
    animal = S1Animal(animal_name)
    sb = StatBlock(hp=stats[0], atk=stats[1], spd=stats[2], wil=stats[3])
    passive = ANIMAL_PASSIVE[animal]
    abilities = ANIMAL_ABILITIES[animal]

    max_hp = 50 + 10 * sb.hp
    base_dmg = math.floor(2 + 0.85 * sb.atk)
    dodge = max(0.0, min(0.30, 0.025 * (sb.spd - 1)))
    movement = 1 if sb.spd <= 3 else (2 if sb.spd <= 6 else 3)
    resist = max(0.0, min(0.60, sb.wil * 0.033))
    ability_power = 1.0 + 0.05 * sb.wil

    size = Size(1, 1)
    pos = grid.generate_starting_position(side, size, seed)

    # Panther starts undetected
    is_undetected = (passive == S1Passive.SHADOW_STALK)
    # Eagle starts with aerial
    aerial_active = (passive == S1Passive.AERIAL_ADVANTAGE)

    creature = Creature(
        animal=animal,
        stats=sb,
        passive=passive,
        current_hp=max_hp,
        max_hp=max_hp,
        base_dmg=base_dmg,
        armor_flat=0,
        size=size,
        position=pos,
        dodge_chance=dodge,
        movement_range=movement,
        ability_power=ability_power,
        resist_chance=resist,
        abilities=abilities,
        is_undetected=is_undetected,
        aerial_active=aerial_active,
    )
    grid.place_creature(creature)
    return creature


# ===========================================================================
# Mimic blocked list
# ===========================================================================

MIMIC_BLOCKED = frozenset({
    S1AbilityType.IRON_WILL,
    S1AbilityType.LAST_STAND,
    S1AbilityType.MIMIC,
})


# ===========================================================================
# Initiative
# ===========================================================================

def calculate_initiative(spd: int, tick_seed: int, creature_index: int) -> float:
    seed = tick_seed + creature_index * 7919
    u = seeded_random(seed, 0.0, 0.49)
    return spd + u


# ===========================================================================
# Damage calculation
# ===========================================================================

def calculate_physical_damage(
    attacker: Creature,
    target: Creature,
    hit_seed: int,
    dodge_seed: int,
    ability_mod: float = 1.0,
    ignore_dodge: bool = False,
    effective_dodge: float | None = None,
) -> int:
    raw = math.floor(attacker.base_dmg * ability_mod)

    if not ignore_dodge:
        dodge = effective_dodge if effective_dodge is not None else target.dodge_chance
        if dodge > 0:
            dodge_roll = seeded_random(dodge_seed, 0.0, 1.0)
            if dodge_roll < dodge:
                return 0

    effective_armor = min(target.armor_flat, math.floor(raw * 0.5))
    after_armor = max(1, raw - effective_armor)

    eps = seeded_random(hit_seed + 1, -0.05, 0.05)
    final = math.floor(after_armor * (1.0 + eps))
    return max(1, final)


# ===========================================================================
# Chaos Strike
# ===========================================================================

def get_chaos_strike_mod(seed: int) -> float:
    return seeded_random(seed, 1.2, 2.8)


# ===========================================================================
# Ability proc system
# ===========================================================================

def roll_ability_procs(
    creature: Creature,
    opponent: Creature,
    match_seed: int,
    tick: int,
    creature_index: int,
    side: str,
    events: list[dict[str, Any]],
) -> tuple[Creature, Creature]:
    last_procced: S1AbilityType | None = None

    # Wolf Pack Sense: +1.5% to all proc rates
    # Monkey Primate Cortex: +2.0% to all proc rates
    pack_sense_bonus = 0.015 if creature.passive == S1Passive.PACK_SENSE else 0.0
    if creature.passive == S1Passive.PRIMATE_CORTEX:
        pack_sense_bonus = 0.025

    # Fox Cunning: opponent proc rates reduced by 30% — applied when opponent rolls
    # (handled in the opponent's roll, not here)

    for ability_index, ability in enumerate(creature.abilities):
        if ability.is_single_charge:
            if ability.ability_type == S1AbilityType.IRON_WILL and creature.iron_will_used:
                continue
            if ability.ability_type == S1AbilityType.LAST_STAND and creature.last_stand_used:
                continue

        # Last Stand only procs when HP < 15%
        if ability.ability_type == S1AbilityType.LAST_STAND:
            if creature.current_hp >= creature.max_hp * 0.15:
                continue

        proc_seed = derive_proc_seed(match_seed, tick, creature_index, ability_index)
        eff_proc = ability.proc_chance + creature.stats.wil * 0.0008 + pack_sense_bonus

        # Fox Cunning: if opponent has Cunning passive, reduce this creature's proc rates by 50%
        if opponent.passive == S1Passive.CUNNING:
            eff_proc *= 0.50

        if not seeded_bool(proc_seed, eff_proc):
            continue

        # WIL resist check
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
            new_buffs = [b for i, b in enumerate(opponent.active_buffs) if i != trick_idx]
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
        creature = dataclasses.replace(creature, last_ability_procced=last_procced)
    return creature, opponent


def _find_trick_buff_index(creature: Creature) -> int | None:
    for i, buff in enumerate(creature.active_buffs):
        if buff.ability_type == S1AbilityType.TRICK:
            return i
    return None


def _apply_ability_proc(
    creature: Creature,
    opponent: Creature,
    ability: Ability,
    side: str,
    events: list[dict[str, Any]],
    proc_seed: int,
) -> tuple[Creature, Creature]:
    atype = ability.ability_type

    # Single-charge: mark as used
    if ability.is_single_charge:
        if atype == S1AbilityType.IRON_WILL:
            creature = dataclasses.replace(creature, iron_will_used=True)
        elif atype == S1AbilityType.LAST_STAND:
            creature = dataclasses.replace(creature, last_stand_used=True)

    # ---- BEAR ----
    if atype == S1AbilityType.BERSERKER_RAGE:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.LAST_STAND:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- BUFFALO ----
    elif atype == S1AbilityType.THICK_HIDE_BLOCK:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.IRON_WILL:
        heal = math.floor(creature.max_hp * 0.12)
        new_hp = min(creature.max_hp, creature.current_hp + heal)
        creature = dataclasses.replace(creature, current_hp=new_hp)

    # ---- BOAR ----
    elif atype == S1AbilityType.STAMPEDE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )
        opponent = dataclasses.replace(opponent, skip_next_attack=True)

    elif atype == S1AbilityType.GORE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- TIGER ----
    elif atype == S1AbilityType.POUNCE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )
        opponent = dataclasses.replace(opponent, skip_next_attack=True)

    elif atype == S1AbilityType.HAMSTRING:
        debuff = AbilityBuff(atype, ability.duration, side)
        opponent = dataclasses.replace(
            opponent, active_buffs=[*opponent.active_buffs, debuff],
        )

    # ---- WOLF ----
    elif atype == S1AbilityType.PACK_HOWL:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.REND:
        dot_dmg = max(1, math.floor(opponent.max_hp * 0.03))
        bleed = ActiveEffect(name="ability_rend", remaining_ticks=3, damage_per_tick=dot_dmg)
        opponent = dataclasses.replace(
            opponent, active_effects=[*opponent.active_effects, bleed],
        )

    # ---- MONKEY ----
    elif atype == S1AbilityType.CHAOS_STRIKE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.MIMIC:
        creature, opponent = _apply_mimic(creature, opponent, side, events, proc_seed)

    # ---- PORCUPINE ----
    elif atype == S1AbilityType.SPIKE_SHIELD:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.CURL_UP:
        creature = dataclasses.replace(
            creature, curl_up_active=True, curl_up_immobile_ticks=2,
        )

    # ---- SCORPION ----
    elif atype == S1AbilityType.ENVENOM:
        # Refresh-only DOT: remove existing envenom, replace with fresh
        new_effects = [e for e in opponent.active_effects if e.name != "envenom"]
        dot_dmg = max(1, math.floor(opponent.max_hp * 0.015))
        venom = ActiveEffect(name="envenom", remaining_ticks=3, damage_per_tick=dot_dmg)
        new_effects.append(venom)
        opponent = dataclasses.replace(opponent, active_effects=new_effects)

    elif atype == S1AbilityType.TAIL_STRIKE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- VULTURE ----
    elif atype == S1AbilityType.DEATH_SPIRAL:
        if opponent.current_hp < opponent.max_hp * 0.50:
            buff = AbilityBuff(atype, ability.duration, side)
            creature = dataclasses.replace(
                creature, active_buffs=[*creature.active_buffs, buff],
            )

    elif atype == S1AbilityType.FEAST:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- RHINO ----
    elif atype == S1AbilityType.HORN_CHARGE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.FORTIFY:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- VIPER ----
    elif atype == S1AbilityType.TOXIC_BITE:
        # Refresh + extend hemotoxin DOT to 5 ticks
        new_effects = [e for e in opponent.active_effects if e.name != "hemotoxin"]
        dot_dmg = max(1, math.floor(opponent.max_hp * 0.015))
        toxin = ActiveEffect(name="hemotoxin", remaining_ticks=4, damage_per_tick=dot_dmg)
        new_effects.append(toxin)
        opponent = dataclasses.replace(opponent, active_effects=new_effects)

    elif atype == S1AbilityType.SHED_SKIN:
        # Remove all debuffs + heal 8% max HP
        new_buffs = [b for b in creature.active_buffs if b.source_side == side]
        new_effects = [e for e in creature.active_effects if e.damage_per_tick == 0]
        heal = math.floor(creature.max_hp * 0.08)
        new_hp = min(creature.max_hp, creature.current_hp + heal)
        creature = dataclasses.replace(
            creature,
            current_hp=new_hp,
            active_buffs=new_buffs,
            active_effects=new_effects,
            anti_heal_ticks=0,
        )

    # ---- FOX ----
    elif atype == S1AbilityType.OUTFOX:
        creature = dataclasses.replace(creature, outfox_charges=3)

    elif atype == S1AbilityType.TRICK:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- EAGLE ----
    elif atype == S1AbilityType.DIVE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature,
            active_buffs=[*creature.active_buffs, buff],
            aerial_active=False,
            aerial_lost_ticks=5,
        )

    elif atype == S1AbilityType.TAILWIND:
        buff = AbilityBuff(atype, ability.duration, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    # ---- PANTHER ----
    elif atype == S1AbilityType.LUNGE:
        buff = AbilityBuff(atype, 1, side)
        creature = dataclasses.replace(
            creature, active_buffs=[*creature.active_buffs, buff],
        )

    elif atype == S1AbilityType.FADE:
        creature = dataclasses.replace(
            creature, is_undetected=True, has_taken_damage=False, shadow_stalk_hits=0,
        )

    events.append({
        "type": "ability_proc",
        "side": side,
        "ability": atype.value,
    })
    return creature, opponent


def _apply_mimic(
    creature: Creature,
    opponent: Creature,
    side: str,
    events: list[dict[str, Any]],
    proc_seed: int,
) -> tuple[Creature, Creature]:
    target_ability = opponent.last_ability_procced
    if target_ability is None or target_ability in MIMIC_BLOCKED:
        return creature, opponent

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

    duration = max(1, original.duration) if original.duration > 0 else 1
    buff = AbilityBuff(
        ability_type=target_ability,
        remaining_ticks=duration,
        source_side=side,
        is_mimic_copy=True,
    )
    creature = dataclasses.replace(
        creature, active_buffs=[*creature.active_buffs, buff],
    )
    return creature, opponent


# ===========================================================================
# Attack modifiers from ability buffs
# ===========================================================================

def apply_ability_attack_mods(
    attacker: Creature, atk_mod: float, hit_seed: int,
) -> tuple[Creature, float]:
    for buff in attacker.active_buffs:
        mimic_scale = 0.75 if buff.is_mimic_copy else 1.0

        if buff.ability_type == S1AbilityType.PACK_HOWL:
            atk_mod *= 1.0 + 0.30 * mimic_scale

        elif buff.ability_type == S1AbilityType.POUNCE:
            atk_mod *= 1.0 + 0.70 * mimic_scale

        elif buff.ability_type == S1AbilityType.STAMPEDE:
            atk_mod *= 1.0 + 0.60 * mimic_scale

        elif buff.ability_type == S1AbilityType.LAST_STAND:
            if attacker.current_hp < attacker.max_hp * 0.15:
                atk_mod *= 1.0 + 1.0 * mimic_scale

        elif buff.ability_type == S1AbilityType.GORE:
            atk_mod *= 0.70  # -30% ATK but ignores dodge

        elif buff.ability_type == S1AbilityType.CHAOS_STRIKE:
            chaos_mod = get_chaos_strike_mod(hit_seed + 777)
            if buff.is_mimic_copy:
                chaos_mod = 1.0 + (chaos_mod - 1.0) * 0.75
            atk_mod = chaos_mod

        # Season 1 new ability attack mods
        elif buff.ability_type == S1AbilityType.TAIL_STRIKE:
            atk_mod *= 1.0 + 0.80 * mimic_scale

        elif buff.ability_type == S1AbilityType.DEATH_SPIRAL:
            atk_mod *= 1.0 + 0.40 * mimic_scale

        elif buff.ability_type == S1AbilityType.HORN_CHARGE:
            atk_mod *= 1.0 + 0.60 * mimic_scale

        elif buff.ability_type == S1AbilityType.DIVE:
            atk_mod *= 1.0 + 1.0 * mimic_scale

        elif buff.ability_type == S1AbilityType.LUNGE:
            atk_mod *= 1.0 + 0.70 * mimic_scale

    return attacker, atk_mod


# ===========================================================================
# Dodge and defense from ability buffs
# ===========================================================================

def has_ignore_dodge_buff(creature: Creature) -> bool:
    return any(
        b.ability_type in (S1AbilityType.POUNCE, S1AbilityType.GORE, S1AbilityType.DIVE)
        for b in creature.active_buffs
    )


def get_effective_dodge(creature: Creature) -> float:
    # Curl Up: guaranteed full block handled separately
    # Outfox charges: guaranteed dodge
    if creature.outfox_charges > 0:
        return 1.0

    dodge = creature.dodge_chance

    # Eagle Aerial Advantage: +15% dodge while active and HP > 60%
    if creature.passive == S1Passive.AERIAL_ADVANTAGE and creature.aerial_active:
        if creature.current_hp > creature.max_hp * 0.60:
            dodge += 0.15

    # Tailwind: +10% dodge
    for buff in creature.active_buffs:
        if buff.ability_type == S1AbilityType.TAILWIND:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge += 0.10 * scale

    # Berserker Rage: -40% dodge
    for buff in creature.active_buffs:
        if buff.ability_type == S1AbilityType.BERSERKER_RAGE:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge *= (1.0 - 0.40 * scale)

    # Hamstring: SPD debuff + flat -10% dodge
    for buff in creature.active_buffs:
        if buff.ability_type == S1AbilityType.HAMSTRING:
            scale = 0.75 if buff.is_mimic_copy else 1.0
            dodge *= (1.0 - 0.55 * scale)
            dodge -= 0.10 * scale

    return max(0.0, min(1.0, dodge))


def apply_ability_defense(defender: Creature, dmg: int) -> tuple[Creature, int]:
    # Thick Hide Block: full block
    has_block = any(
        b.ability_type == S1AbilityType.THICK_HIDE_BLOCK for b in defender.active_buffs
    )
    if has_block:
        remaining = [b for b in defender.active_buffs if b.ability_type != S1AbilityType.THICK_HIDE_BLOCK]
        return dataclasses.replace(defender, active_buffs=remaining), 0

    # Fortify: +30% damage reduction
    has_fortify = any(
        b.ability_type == S1AbilityType.FORTIFY for b in defender.active_buffs
    )
    if has_fortify:
        dmg = max(1, math.floor(dmg * 0.70))

    return defender, dmg


# ===========================================================================
# Fury C3 system
# ===========================================================================

def check_fury_trigger(creature: Creature) -> Creature:
    if creature.passive != S1Passive.FURY_PROTOCOL:
        return creature
    if creature.fury_triggered:
        return creature
    if creature.current_hp >= creature.max_hp * 0.55:
        return creature
    return dataclasses.replace(creature, fury_triggered=True, fury_active_ticks=4)


def tick_fury(creature: Creature) -> Creature:
    """Tick down fury_active_ticks for Bear (Fury Protocol) and Rhino (Bulwark Frame)."""
    if creature.fury_active_ticks <= 0:
        return creature
    return dataclasses.replace(creature, fury_active_ticks=creature.fury_active_ticks - 1)


# ===========================================================================
# Buff management
# ===========================================================================

def tick_ability_buffs(creature: Creature) -> Creature:
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


# ===========================================================================
# Combat Engine
# ===========================================================================

class S1CombatEngine:
    """Season 1 combat engine with WIL regen and all 14 animals."""

    def __init__(self, max_ticks: int = 60, ring_start_tick: int = 30):
        self.max_ticks = max_ticks
        self.ring_start_tick = ring_start_tick

    def run(
        self,
        a: Creature,
        b: Creature,
        match_seed: int,
        grid: Grid,
    ) -> dict:
        log: list[dict[str, Any]] = []
        attack_index = 0

        # Primate Cortex: copy a random ability from opponent at fight start
        a, b = self._apply_primate_cortex(a, b, match_seed)

        for tick in range(1, self.max_ticks + 1):
            tick_seed = derive_tick_seed(match_seed, tick)
            hp_a_start = a.current_hp
            hp_b_start = b.current_hp
            tick_events: list[dict[str, Any]] = []

            # Tick down Curl Up immobile
            if a.curl_up_immobile_ticks > 0:
                a = dataclasses.replace(a, curl_up_immobile_ticks=a.curl_up_immobile_ticks - 1)
            if b.curl_up_immobile_ticks > 0:
                b = dataclasses.replace(b, curl_up_immobile_ticks=b.curl_up_immobile_ticks - 1)

            # Tick down Eagle aerial lost
            if a.aerial_lost_ticks > 0:
                new_ticks = a.aerial_lost_ticks - 1
                a = dataclasses.replace(
                    a, aerial_lost_ticks=new_ticks,
                    aerial_active=True if new_ticks == 0 and a.passive == S1Passive.AERIAL_ADVANTAGE else a.aerial_active,
                )
            if b.aerial_lost_ticks > 0:
                new_ticks = b.aerial_lost_ticks - 1
                b = dataclasses.replace(
                    b, aerial_lost_ticks=new_ticks,
                    aerial_active=True if new_ticks == 0 and b.passive == S1Passive.AERIAL_ADVANTAGE else b.aerial_active,
                )

            # Initiative
            init_a = calculate_initiative(a.stats.spd, tick_seed, 0)
            init_b = calculate_initiative(b.stats.spd, tick_seed, 1)
            turn_order = ["a", "b"] if init_a >= init_b else ["b", "a"]

            # -- Attack phase --
            for side in turn_order:
                attacker = a if side == "a" else b
                defender = b if side == "a" else a

                if attacker.current_hp <= 0:
                    continue

                # Skip if stunned
                if attacker.skip_next_attack:
                    attacker = dataclasses.replace(attacker, skip_next_attack=False)
                    if side == "a":
                        a = attacker
                    else:
                        b = attacker
                    tick_events.append({"type": "skip_attack", "side": side})
                    continue

                # Curl Up immobile: can't move but CAN attack if adjacent
                can_move = attacker.curl_up_immobile_ticks <= 0

                # Move toward opponent if not adjacent
                if not self._is_adjacent(attacker, defender) and can_move:
                    target_pos = grid.find_path_toward(attacker, defender.position)
                    if target_pos != attacker.position:
                        grid.remove_creature(attacker)
                        attacker = dataclasses.replace(attacker, position=target_pos)
                        grid.place_creature(attacker)
                        if side == "a":
                            a = attacker
                        else:
                            b = attacker

                # Refresh defender ref
                defender = b if side == "a" else a

                # Execute attack if adjacent
                if self._is_adjacent(attacker, defender) and defender.current_hp > 0:
                    attack_index += 1
                    hit_seed = derive_hit_seed(match_seed, tick, attack_index)
                    dodge_seed = hit_seed + 31337

                    atk_mod = 1.0

                    # -- Attack passives --
                    attacker, atk_mod = self._apply_attack_passives(
                        attacker, defender, atk_mod, side,
                    )
                    attacker, atk_mod = apply_ability_attack_mods(attacker, atk_mod, hit_seed)
                    if side == "a":
                        a = attacker
                    else:
                        b = attacker

                    # Dodge calculation
                    ignore_dodge = has_ignore_dodge_buff(attacker)
                    # Boar Charge: first attack ignores dodge
                    # charge_used is set to True during _apply_attack_passives on the first attack
                    # first_hit_taken is still False at this point for the first attack
                    if attacker.passive == S1Passive.CHARGE and not attacker.first_hit_taken:
                        ignore_dodge = True
                        attacker = dataclasses.replace(attacker, first_hit_taken=True)
                        if side == "a":
                            a = attacker
                        else:
                            b = attacker
                    eff_dodge = get_effective_dodge(defender)

                    # Curl Up: block next hit entirely
                    if defender.curl_up_active:
                        dmg = 0
                        defender = dataclasses.replace(defender, curl_up_active=False)
                    else:
                        dmg = calculate_physical_damage(
                            attacker, defender, hit_seed, dodge_seed,
                            atk_mod, ignore_dodge=ignore_dodge,
                            effective_dodge=eff_dodge,
                        )

                    # Outfox: consume a charge on dodge
                    if dmg == 0 and defender.outfox_charges > 0:
                        defender = dataclasses.replace(
                            defender, outfox_charges=defender.outfox_charges - 1,
                        )

                    if dmg > 0:
                        # Defense passives
                        defender, dmg = self._apply_defense_passives(defender, dmg)

                    if dmg > 0:
                        # Ability defense (Thick Hide Block, Fortify)
                        defender, dmg = apply_ability_defense(defender, dmg)

                    # Tail Strike: ignores 50% damage reduction on defender
                    # (already computed as higher ATK mod — the ignore is baked in)

                    # Porcupine Quill Armor: reflect 15% melee damage on hit
                    reflect_dmg = 0
                    if dmg > 0 and defender.passive == S1Passive.QUILL_ARMOR:
                        # 50% chance to reflect per hit
                        if seeded_bool(hit_seed + 5555, 0.50):
                            reflect_pct = 0.15
                            # Spike Shield: +15% reflect
                            for buff in defender.active_buffs:
                                if buff.ability_type == S1AbilityType.SPIKE_SHIELD:
                                    reflect_pct += 0.15
                                    break
                            reflect_dmg = max(1, math.floor(dmg * reflect_pct))

                    # Scorpion Venom Gland: 35% chance on hit to apply anti-heal for 2 ticks
                    if dmg > 0 and attacker.passive == S1Passive.VENOM_GLAND:
                        if seeded_bool(hit_seed + 8888, 0.25):
                            defender = dataclasses.replace(defender, anti_heal_ticks=2)

                    # Viper Hemotoxin: 15% chance per hit to apply 1% max HP DOT for 2 ticks (refresh only)
                    if dmg > 0 and attacker.passive == S1Passive.HEMOTOXIN:
                        if seeded_bool(hit_seed + 9999, 0.12):
                            new_effects = [e for e in defender.active_effects if e.name != "hemotoxin"]
                            toxin_dmg = max(1, math.floor(defender.max_hp * 0.01))
                            toxin = ActiveEffect(name="hemotoxin", remaining_ticks=2, damage_per_tick=toxin_dmg)
                            new_effects.append(toxin)
                            defender = dataclasses.replace(defender, active_effects=new_effects)

                    # Vulture Feast: heal 20% of damage dealt
                    feast_heal = 0
                    if dmg > 0:
                        for buff in attacker.active_buffs:
                            if buff.ability_type == S1AbilityType.FEAST:
                                feast_heal = math.floor(dmg * 0.30)
                                break

                    # Apply damage to defender
                    defender = dataclasses.replace(
                        defender,
                        current_hp=defender.current_hp - dmg,
                        has_taken_damage=True if dmg > 0 else defender.has_taken_damage,
                    )
                    # Panther: undetected only breaks after shadow_stalk_hits exhausted
                    # (no break on taking damage)

                    # Apply reflect damage to attacker
                    if reflect_dmg > 0:
                        attacker = dataclasses.replace(
                            attacker, current_hp=attacker.current_hp - reflect_dmg,
                        )
                        tick_events.append({
                            "type": "reflect",
                            "side": "b" if side == "a" else "a",
                            "damage": reflect_dmg,
                        })

                    # Apply feast heal
                    if feast_heal > 0:
                        new_hp = min(attacker.max_hp, attacker.current_hp + feast_heal)
                        attacker = dataclasses.replace(attacker, current_hp=new_hp)

                    if side == "a":
                        a = attacker
                        b = defender
                    else:
                        b = attacker
                        a = defender

                    tick_events.append({
                        "type": "attack",
                        "side": side,
                        "damage": dmg,
                        "dodged": dmg == 0,
                        "hp_remaining": defender.current_hp,
                    })

            # -- Tick ability buffs AFTER attacks --
            a = tick_ability_buffs(a)
            b = tick_ability_buffs(b)

            # -- Roll ability procs --
            for side in turn_order:
                creature_idx = 0 if side == "a" else 1
                attacker = a if side == "a" else b
                opponent = b if side == "a" else a
                if attacker.current_hp > 0:
                    attacker, opponent = roll_ability_procs(
                        attacker, opponent, match_seed, tick,
                        creature_idx, side, tick_events,
                    )
                    if side == "a":
                        a, b = attacker, opponent
                    else:
                        b, a = attacker, opponent

            # -- Fury check and tick --
            a = check_fury_trigger(a)
            b = check_fury_trigger(b)
            a = tick_fury(a)
            b = tick_fury(b)

            # -- DOT effects --
            a = self._process_dot(a, "a", tick_events)
            b = self._process_dot(b, "b", tick_events)

            # -- Ring damage --
            a, b = self._apply_ring_damage(a, b, tick, tick_events)

            # -- WIL Regen (Season 1 key change) --
            a = self._apply_wil_regen(a, "a", tick_events)
            b = self._apply_wil_regen(b, "b", tick_events)

            # -- Second Wind --
            a = self._try_second_wind(a, "a", tick_events)
            b = self._try_second_wind(b, "b", tick_events)

            # -- Anti-heal tick down --
            if a.anti_heal_ticks > 0:
                a = dataclasses.replace(a, anti_heal_ticks=a.anti_heal_ticks - 1)
            if b.anti_heal_ticks > 0:
                b = dataclasses.replace(b, anti_heal_ticks=b.anti_heal_ticks - 1)

            log.append({"tick": tick, "events": tick_events})

            # -- Death check --
            if a.current_hp <= 0 or b.current_hp <= 0:
                winner = self._resolve_death(a, b, hp_a_start, hp_b_start)
                return {
                    "winner": winner,
                    "ticks": tick,
                    "hp_a": max(0, a.current_hp),
                    "hp_b": max(0, b.current_hp),
                }

        # Timeout
        winner = self._resolve_timeout(a, b)
        return {
            "winner": winner,
            "ticks": self.max_ticks,
            "hp_a": max(0, a.current_hp),
            "hp_b": max(0, b.current_hp),
        }

    # -- Helpers ---------------------------------------------------------------

    def _apply_primate_cortex(
        self, a: Creature, b: Creature, match_seed: int,
    ) -> tuple[Creature, Creature]:
        """At fight start, Monkey copies a random ability from opponent."""
        for creature, opponent, idx in [(a, b, 0), (b, a, 1)]:
            if creature.passive != S1Passive.PRIMATE_CORTEX:
                continue
            # Pick one of opponent's abilities (seeded)
            pick_seed = derive_proc_seed(match_seed, 0, idx, 99)
            pick = int(seeded_random(pick_seed, 0.0, len(opponent.abilities) - 0.001))
            pick = max(0, min(pick, len(opponent.abilities) - 1))
            copied = opponent.abilities[pick]
            # Don't copy blocked abilities
            if copied.ability_type in MIMIC_BLOCKED:
                pick = (pick + 1) % len(opponent.abilities)
                copied = opponent.abilities[pick]
                if copied.ability_type in MIMIC_BLOCKED:
                    continue
            # Add copied ability to creature's abilities
            creature = dataclasses.replace(
                creature, abilities=(*creature.abilities, copied),
            )
            if idx == 0:
                a = creature
            else:
                b = creature
        return a, b

    def _is_adjacent(self, a: Creature, b: Creature) -> bool:
        for dr_a in range(a.size.rows):
            for dc_a in range(a.size.cols):
                cell_a = Position(a.position.row + dr_a, a.position.col + dc_a)
                for dr_b in range(b.size.rows):
                    for dc_b in range(b.size.cols):
                        cell_b = Position(b.position.row + dr_b, b.position.col + dc_b)
                        if Grid.get_distance(cell_a, cell_b) <= 1:
                            return True
        return False

    def _apply_attack_passives(
        self,
        attacker: Creature,
        defender: Creature,
        atk_mod: float,
        side: str,
    ) -> tuple[Creature, float]:
        # Fury Protocol / Berserker Rage: take max, don't stack
        fury_or_rage_mod = 1.0
        if attacker.passive == S1Passive.FURY_PROTOCOL and attacker.fury_active_ticks > 0:
            fury_or_rage_mod = 1.5
        for buff in attacker.active_buffs:
            if buff.ability_type == S1AbilityType.BERSERKER_RAGE:
                scale = 0.75 if buff.is_mimic_copy else 1.0
                rage_mod = 1.0 + 0.60 * scale
                fury_or_rage_mod = max(fury_or_rage_mod, rage_mod)
        if fury_or_rage_mod > 1.0:
            atk_mod *= fury_or_rage_mod

        # Tiger Ambush Wiring: +15% ATK when opponent has Hamstring debuff
        if attacker.passive == S1Passive.AMBUSH_WIRING:
            for buff in defender.active_buffs:
                if buff.ability_type == S1AbilityType.HAMSTRING:
                    atk_mod *= 1.15
                    break

        # Boar Charge: first attack +85% and ignores dodge
        if attacker.passive == S1Passive.CHARGE and not attacker.charge_used:
            atk_mod *= 1.85
            attacker = dataclasses.replace(attacker, charge_used=True)
            # Note: dodge ignore handled in attack phase via charge_used check

        # Tiger Ambush Wiring: first attack 2x if at least as fast
        if attacker.passive == S1Passive.AMBUSH_WIRING and not attacker.charge_used:
            if attacker.stats.spd >= defender.stats.spd:
                atk_mod *= 2.0
                attacker = dataclasses.replace(attacker, charge_used=True)

        # Panther Shadow Stalk: +35% damage while undetected (first 3 attacks)
        if attacker.passive == S1Passive.SHADOW_STALK and attacker.is_undetected:
            if attacker.shadow_stalk_hits < 3:
                atk_mod *= 1.35
                attacker = dataclasses.replace(
                    attacker, shadow_stalk_hits=attacker.shadow_stalk_hits + 1,
                )
                # After 3rd hit, lose undetected
                if attacker.shadow_stalk_hits >= 3:
                    attacker = dataclasses.replace(attacker, is_undetected=False)

        # Vulture Carrion Feeder: +3.5% ATK per 10% HP opponent is missing
        if attacker.passive == S1Passive.CARRION_FEEDER:
            missing_pct = (defender.max_hp - defender.current_hp) / defender.max_hp
            bonus_pct = math.floor(missing_pct * 10) * 0.035
            atk_mod *= (1.0 + bonus_pct)

        return attacker, atk_mod

    def _apply_defense_passives(
        self, defender: Creature, dmg: int,
    ) -> tuple[Creature, int]:
        # Buffalo Thick Hide: first hit 50% reduced
        if defender.passive == S1Passive.THICK_HIDE and not defender.first_hit_taken:
            dmg = max(1, math.floor(dmg * 0.5))
            defender = dataclasses.replace(defender, first_hit_taken=True)

        # Rhino Bulwark Frame: when HP < 60% (one-time trigger), +30% DR for 5 ticks
        # Uses fury_triggered/fury_active_ticks fields (Rhino can't be Bear)
        if defender.passive == S1Passive.BULWARK_FRAME:
            if not defender.fury_triggered and defender.current_hp < defender.max_hp * 0.60:
                defender = dataclasses.replace(
                    defender, fury_triggered=True, fury_active_ticks=4,
                )
            if defender.fury_active_ticks > 0:
                dmg = max(1, math.floor(dmg * 0.72))

        return defender, dmg

    def _process_dot(
        self, creature: Creature, side: str, events: list[dict[str, Any]],
    ) -> Creature:
        if not creature.active_effects:
            return creature
        total_dot = 0
        remaining: list[ActiveEffect] = []
        for eff in creature.active_effects:
            if eff.damage_per_tick > 0:
                total_dot += eff.damage_per_tick
            updated = ActiveEffect(
                name=eff.name,
                remaining_ticks=eff.remaining_ticks - 1,
                damage_per_tick=eff.damage_per_tick,
                heal_per_tick=eff.heal_per_tick,
            )
            if updated.remaining_ticks > 0:
                remaining.append(updated)
        if total_dot > 0:
            creature = dataclasses.replace(
                creature,
                current_hp=creature.current_hp - total_dot,
                active_effects=remaining,
            )
            events.append({
                "type": "dot",
                "side": side,
                "damage": total_dot,
                "hp_remaining": creature.current_hp,
            })
        else:
            creature = dataclasses.replace(creature, active_effects=remaining)
        return creature

    def _apply_ring_damage(
        self,
        a: Creature,
        b: Creature,
        tick: int,
        events: list[dict[str, Any]],
    ) -> tuple[Creature, Creature]:
        if tick < self.ring_start_tick:
            return a, b

        if self._is_in_ring(a, tick):
            ring_dmg = max(1, math.floor(a.max_hp * 0.02))
            a = dataclasses.replace(a, current_hp=a.current_hp - ring_dmg)
            events.append({
                "type": "ring_damage", "side": "a",
                "damage": ring_dmg, "hp_remaining": a.current_hp,
            })
        if self._is_in_ring(b, tick):
            ring_dmg = max(1, math.floor(b.max_hp * 0.02))
            b = dataclasses.replace(b, current_hp=b.current_hp - ring_dmg)
            events.append({
                "type": "ring_damage", "side": "b",
                "damage": ring_dmg, "hp_remaining": b.current_hp,
            })
        return a, b

    def _is_in_ring(self, creature: Creature, tick: int) -> bool:
        if tick < self.ring_start_tick:
            return False
        offset = tick - self.ring_start_tick
        if offset <= 4:
            safe_min, safe_max = 1, 6
        else:
            safe_min, safe_max = 2, 5

        for dr in range(creature.size.rows):
            for dc in range(creature.size.cols):
                r = creature.position.row + dr
                c = creature.position.col + dc
                if r < safe_min or r > safe_max or c < safe_min or c > safe_max:
                    return True
        return False

    def _apply_wil_regen(
        self, creature: Creature, side: str, events: list[dict[str, Any]],
    ) -> Creature:
        """WIL Regen: each tick, heal wil * 0.0025 * max_hp. Scorpion anti-heal halves it."""
        if creature.current_hp <= 0:
            return creature

        regen = creature.stats.wil * 0.0025 * creature.max_hp
        # Scorpion anti-heal reduces by 50%
        if creature.anti_heal_ticks > 0:
            regen *= 0.5
        heal = math.floor(regen)
        if heal <= 0:
            return creature

        new_hp = min(creature.max_hp, creature.current_hp + heal)
        if new_hp != creature.current_hp:
            creature = dataclasses.replace(creature, current_hp=new_hp)
            events.append({
                "type": "wil_regen",
                "side": side,
                "heal": new_hp - (creature.current_hp - heal + (new_hp - creature.current_hp)),
                "hp_remaining": creature.current_hp,
            })
        return creature

    def _try_second_wind(
        self, creature: Creature, side: str, events: list[dict[str, Any]],
    ) -> Creature:
        if (
            creature.second_wind_available
            and not creature.second_wind_triggered
            and creature.current_hp > 0
            and creature.current_hp < creature.max_hp * 0.3
        ):
            heal = math.floor(creature.max_hp * 0.25)
            creature = dataclasses.replace(
                creature,
                current_hp=min(creature.max_hp, creature.current_hp + heal),
                second_wind_triggered=True,
            )
            events.append({
                "type": "second_wind",
                "side": side,
                "heal": heal,
                "hp_remaining": creature.current_hp,
            })
        return creature

    def _resolve_death(
        self, a: Creature, b: Creature, hp_a_start: int, hp_b_start: int,
    ) -> str | None:
        if a.current_hp <= 0 and b.current_hp <= 0:
            pct_a = hp_a_start / a.max_hp
            pct_b = hp_b_start / b.max_hp
            if pct_a > pct_b:
                return "a"
            elif pct_b > pct_a:
                return "b"
            return None
        if a.current_hp <= 0:
            return "b"
        return "a"

    def _resolve_timeout(self, a: Creature, b: Creature) -> str | None:
        pct_a = a.current_hp / a.max_hp
        pct_b = b.current_hp / b.max_hp
        if pct_a > pct_b:
            return "a"
        elif pct_b > pct_a:
            return "b"
        return None


# ===========================================================================
# Public API
# ===========================================================================

def run_match(
    animal_a: str,
    stats_a: tuple[int, int, int, int],
    animal_b: str,
    stats_b: tuple[int, int, int, int],
    seed: int,
) -> dict:
    """Run a single Season 1 match.

    Args:
        animal_a: Animal name (e.g. "bear")
        stats_a: (hp, atk, spd, wil) tuple summing to 20
        animal_b: Animal name
        stats_b: (hp, atk, spd, wil) tuple summing to 20
        seed: Match seed for deterministic RNG

    Returns:
        {"winner": "a"|"b"|None, "ticks": int, "hp_a": int, "hp_b": int}
    """
    grid = Grid()
    a = create_creature(animal_a, stats_a, "a", grid, seed)
    b = create_creature(animal_b, stats_b, "b", grid, seed + 1)

    engine = S1CombatEngine()
    return engine.run(a, b, seed, grid)
