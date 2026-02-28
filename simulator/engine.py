"""Combat engine — core tick loop.

Standalone version for the companion repository.
This is a reference implementation of the Moreau Arena combat engine.
For the full engine with AI, active abilities, and grid pathfinding,
see the private repository.

This file contains the core CombatEngine class with the complete tick loop,
damage calculation, initiative, ring mechanics, DOTs, second wind, and
all passive/ability interactions used in Tournament 001 and 002.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass, field
from typing import Any

from simulator.animals import (
    Ability,
    Animal,
    AbilityType,
    AbilityBuff,
    ActiveEffect,
    ANIMAL_ABILITIES,
    Creature,
    Passive,
    Position,
)
from simulator.grid import Grid
from simulator.seed import (
    derive_tick_seed,
    derive_hit_seed,
    derive_proc_seed,
    seeded_bool,
    seeded_random,
)
from simulator.abilities import (
    roll_ability_procs,
    apply_ability_attack_mods,
    has_ignore_dodge_buff,
    get_effective_dodge,
    apply_ability_defense,
    check_fury_trigger,
    tick_fury,
    tick_ability_buffs,
)


@dataclass
class CombatConfig:
    max_ticks: int = 60
    ring_start_tick: int = 30


@dataclass
class CombatResult:
    winner: str | None
    ticks: int
    end_condition: str
    seed: int
    log: list[dict[str, Any]] = field(default_factory=list)
    final_hp_a: int = 0
    final_hp_b: int = 0


def calculate_initiative(spd: int, tick_seed: int, creature_index: int) -> float:
    seed = tick_seed + creature_index * 7919
    u = seeded_random(seed, 0.0, 0.49)
    return spd + u


def calculate_physical_damage(
    attacker: Creature,
    target: Creature,
    hit_seed: int,
    dodge_seed: int,
    ability_mod: float = 1.0,
    is_single_target: bool = True,
    ignore_dodge: bool = False,
    effective_dodge: float | None = None,
) -> int:
    raw = math.floor(attacker.base_dmg * ability_mod)

    if is_single_target and not ignore_dodge:
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


# -- Simplified AI for standalone engine ---------------------------------------
# The full AI is in the private repo. This minimal version always attacks.


class _ActionType:
    ATTACK = "attack"
    MOVE_AND_ATTACK = "move_and_attack"


class CombatEngine:
    def run_combat(
        self,
        creature_a: Creature,
        creature_b: Creature,
        match_seed: int,
        config: CombatConfig | None = None,
    ) -> CombatResult:
        cfg = config or CombatConfig()
        grid = Grid()

        a = dataclasses.replace(
            creature_a,
            abilities=creature_a.abilities or ANIMAL_ABILITIES.get(creature_a.animal, ()),
        )
        b = dataclasses.replace(
            creature_b,
            abilities=creature_b.abilities or ANIMAL_ABILITIES.get(creature_b.animal, ()),
        )
        grid.place_creature(a)
        grid.place_creature(b)

        log: list[dict[str, Any]] = []
        attack_index = 0

        for tick in range(1, cfg.max_ticks + 1):
            tick_seed = derive_tick_seed(match_seed, tick)
            hp_a_start = a.current_hp
            hp_b_start = b.current_hp

            tick_events: list[dict[str, Any]] = []

            init_a = calculate_initiative(a.stats.spd, tick_seed, 0)
            init_b = calculate_initiative(b.stats.spd, tick_seed, 1)

            if init_a >= init_b:
                turn_order = ["a", "b"]
            else:
                turn_order = ["b", "a"]

            for side in turn_order:
                attacker = a if side == "a" else b
                defender = b if side == "a" else a

                if attacker.current_hp <= 0:
                    continue

                # Skip attack if stampede flag set
                if attacker.skip_next_attack:
                    attacker = dataclasses.replace(
                        attacker, skip_next_attack=False,
                    )
                    if side == "a":
                        a = attacker
                    else:
                        b = attacker
                    tick_events.append({
                        "type": "skip_attack",
                        "side": side,
                    })
                    continue

                # Move toward opponent if not adjacent
                if not self._is_adjacent(attacker, defender):
                    target_pos = grid.find_path_toward(attacker, defender.position)
                    if target_pos != attacker.position:
                        grid.remove_creature(attacker)
                        attacker = dataclasses.replace(attacker, position=target_pos)
                        grid.place_creature(attacker)
                        if side == "a":
                            a = attacker
                        else:
                            b = attacker
                        tick_events.append({
                            "type": "move",
                            "side": side,
                            "to": (target_pos.row, target_pos.col),
                        })

                # Execute attack if adjacent
                defender = b if side == "a" else a
                if (
                    self._is_adjacent(attacker, defender)
                    and defender.current_hp > 0
                ):
                    attack_index += 1
                    hit_seed = derive_hit_seed(
                        match_seed, tick, attack_index
                    )
                    dodge_seed = hit_seed + 31337

                    atk_mod = 1.0
                    attacker, atk_mod = self._apply_attack_passives(
                        attacker, defender, atk_mod, side, a, b
                    )
                    attacker, atk_mod = apply_ability_attack_mods(
                        attacker, atk_mod, hit_seed,
                    )
                    if side == "a":
                        a = attacker
                    else:
                        b = attacker

                    ignore_dodge = has_ignore_dodge_buff(attacker)
                    eff_dodge = get_effective_dodge(defender)

                    dmg = calculate_physical_damage(
                        attacker, defender, hit_seed, dodge_seed,
                        atk_mod, ignore_dodge=ignore_dodge,
                        effective_dodge=eff_dodge,
                    )

                    if dmg > 0:
                        defender, dmg = self._apply_defense_passives(
                            defender, dmg, side
                        )

                    if dmg > 0:
                        defender, dmg = apply_ability_defense(
                            defender, dmg,
                        )

                    if attacker.has_rend and dmg > 0:
                        bleed = ActiveEffect(
                            name="bleed",
                            remaining_ticks=3,
                            damage_per_tick=2,
                        )
                        defender = dataclasses.replace(
                            defender,
                            active_effects=[
                                *defender.active_effects, bleed
                            ],
                        )

                    defender = dataclasses.replace(
                        defender,
                        current_hp=defender.current_hp - dmg,
                    )

                    if side == "a":
                        a = attacker
                        b = defender
                    else:
                        b = attacker
                        a = defender

                    tick_events.append(
                        {
                            "type": "attack",
                            "side": side,
                            "damage": dmg,
                            "dodged": dmg == 0,
                            "hp_remaining": defender.current_hp,
                        }
                    )

            # Tick ability buffs AFTER attacks, BEFORE procs
            a = tick_ability_buffs(a)
            b = tick_ability_buffs(b)

            # Roll ability procs
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

            # Fury C3: check trigger and tick
            a = check_fury_trigger(a)
            b = check_fury_trigger(b)
            a = tick_fury(a)
            b = tick_fury(b)

            a, b = self._apply_effects(a, b, tick_events)
            a, b = self._apply_ring_damage(a, b, tick, cfg, tick_events)
            a, b = self._check_second_wind(a, b, tick_events)
            a, b = self._apply_regeneration(a, b, tick_events)

            log.append({"tick": tick, "events": tick_events})

            if a.current_hp <= 0 or b.current_hp <= 0:
                winner = self._resolve_death(a, b, hp_a_start, hp_b_start)
                return CombatResult(
                    winner=winner,
                    ticks=tick,
                    end_condition="death",
                    seed=match_seed,
                    log=log,
                    final_hp_a=a.current_hp,
                    final_hp_b=b.current_hp,
                )

        winner = self._resolve_timeout(a, b)
        return CombatResult(
            winner=winner,
            ticks=cfg.max_ticks,
            end_condition="timeout",
            seed=match_seed,
            log=log,
            final_hp_a=a.current_hp,
            final_hp_b=b.current_hp,
        )

    # -- Core combat helpers ---------------------------------------------------

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
        a: Creature,
        b: Creature,
    ) -> tuple[Creature, float]:
        # Fury C3 + Berserker Rage: take max, don't stack
        fury_or_rage_mod = 1.0
        if (
            attacker.passive == Passive.FURY_PROTOCOL
            and attacker.fury_active_ticks > 0
        ):
            fury_or_rage_mod = 1.5
        for buff in attacker.active_buffs:
            if buff.ability_type == AbilityType.BERSERKER_RAGE:
                scale = 0.75 if buff.is_mimic_copy else 1.0
                rage_mod = 1.0 + 0.60 * scale
                fury_or_rage_mod = max(fury_or_rage_mod, rage_mod)
        if fury_or_rage_mod > 1.0:
            atk_mod *= fury_or_rage_mod

        if attacker.passive == Passive.CHARGE and not attacker.charge_used:
            atk_mod *= 1.5
            attacker = dataclasses.replace(attacker, charge_used=True)

        if attacker.passive == Passive.AMBUSH_WIRING and not attacker.charge_used:
            if attacker.stats.spd > defender.stats.spd:
                atk_mod *= 2.0
                attacker = dataclasses.replace(attacker, charge_used=True)

        if attacker.has_execute and defender.current_hp < defender.max_hp * 0.25:
            atk_mod *= 2.0

        return attacker, atk_mod

    def _apply_defense_passives(
        self, defender: Creature, dmg: int, attacker_side: str
    ) -> tuple[Creature, int]:
        if defender.passive == Passive.THICK_HIDE and not defender.first_hit_taken:
            dmg = math.floor(dmg * 0.5)
            dmg = max(1, dmg)
            defender = dataclasses.replace(defender, first_hit_taken=True)
        return defender, dmg

    # -- DOT / Effects ---------------------------------------------------------

    def _apply_effects(
        self, a: Creature, b: Creature, events: list[dict[str, Any]]
    ) -> tuple[Creature, Creature]:
        a = self._process_dot(a, "a", events)
        b = self._process_dot(b, "b", events)
        return a, b

    def _process_dot(
        self, creature: Creature, side: str, events: list[dict[str, Any]]
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
            events.append(
                {
                    "type": "dot",
                    "side": side,
                    "damage": total_dot,
                    "hp_remaining": creature.current_hp,
                }
            )
        else:
            creature = dataclasses.replace(creature, active_effects=remaining)
        return creature

    # -- Ring ------------------------------------------------------------------

    def _apply_ring_damage(
        self,
        a: Creature,
        b: Creature,
        tick: int,
        config: CombatConfig,
        events: list[dict[str, Any]],
    ) -> tuple[Creature, Creature]:
        if tick < config.ring_start_tick:
            return a, b

        if self._is_in_ring(a, tick, config):
            ring_dmg_a = self._get_ring_damage(tick, config, a.max_hp)
            a = dataclasses.replace(a, current_hp=a.current_hp - ring_dmg_a)
            events.append(
                {
                    "type": "ring_damage",
                    "side": "a",
                    "damage": ring_dmg_a,
                    "hp_remaining": a.current_hp,
                }
            )
        if self._is_in_ring(b, tick, config):
            ring_dmg_b = self._get_ring_damage(tick, config, b.max_hp)
            b = dataclasses.replace(b, current_hp=b.current_hp - ring_dmg_b)
            events.append(
                {
                    "type": "ring_damage",
                    "side": "b",
                    "damage": ring_dmg_b,
                    "hp_remaining": b.current_hp,
                }
            )
        return a, b

    def _get_ring_damage(self, tick: int, config: CombatConfig, max_hp: int = 0) -> int:
        if tick < config.ring_start_tick:
            return 0
        return max(1, math.floor(max_hp * 0.02))

    def _is_in_ring(self, creature: Creature, tick: int, config: CombatConfig) -> bool:
        if tick < config.ring_start_tick:
            return False
        offset = tick - config.ring_start_tick
        if offset <= 4:
            safe_min, safe_max = 1, 6
        elif offset <= 9:
            safe_min, safe_max = 2, 5
        else:
            safe_min, safe_max = 2, 5

        for dr in range(creature.size.rows):
            for dc in range(creature.size.cols):
                r = creature.position.row + dr
                c = creature.position.col + dc
                if r < safe_min or r > safe_max or c < safe_min or c > safe_max:
                    return True
        return False

    # -- Second Wind / Regen ---------------------------------------------------

    def _check_second_wind(
        self, a: Creature, b: Creature, events: list[dict[str, Any]]
    ) -> tuple[Creature, Creature]:
        a = self._try_second_wind(a, "a", events)
        b = self._try_second_wind(b, "b", events)
        return a, b

    def _try_second_wind(
        self, creature: Creature, side: str, events: list[dict[str, Any]]
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
            events.append(
                {
                    "type": "second_wind",
                    "side": side,
                    "heal": heal,
                    "hp_remaining": creature.current_hp,
                }
            )
        return creature

    def _apply_regeneration(
        self, a: Creature, b: Creature, events: list[dict[str, Any]]
    ) -> tuple[Creature, Creature]:
        for side, creature in [("a", a), ("b", b)]:
            if creature.has_regeneration and creature.current_hp > 0:
                heal = 0
                new_hp = min(creature.max_hp, creature.current_hp + heal)
                if new_hp != creature.current_hp:
                    updated = dataclasses.replace(creature, current_hp=new_hp)
                    events.append(
                        {
                            "type": "regeneration",
                            "side": side,
                            "heal": heal,
                            "hp_remaining": updated.current_hp,
                        }
                    )
                    if side == "a":
                        a = updated
                    else:
                        b = updated
        return a, b

    # -- Resolution ------------------------------------------------------------

    def _resolve_death(
        self,
        a: Creature,
        b: Creature,
        hp_a_start: int,
        hp_b_start: int,
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
