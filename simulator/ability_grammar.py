"""Formal ability grammar for the Moreau Arena.

Decomposes every ability into the product:

    Ability = Trigger x Target x Effect x Constraint

and computes analytical EV and variance for each ability's per-proc
contribution to combat outcomes.

All 14 core animals' abilities are expressed in this grammar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Grammar primitives
# ---------------------------------------------------------------------------


class Trigger(Enum):
    """When the ability activates."""
    PER_TICK_PROC = "per_tick_proc"         # Standard proc roll each tick
    HP_THRESHOLD = "hp_threshold"            # Procs only below HP threshold
    ON_FIRST_HIT = "on_first_hit"           # First attack only (passives)
    ON_SPD_ADVANTAGE = "on_spd_advantage"    # Requires spd > opponent
    ON_HP_BELOW_50 = "on_hp_below_50"       # Fury: passive trigger
    ON_HIT_LAND = "on_hit_land"             # Procs when hit lands


class Target(Enum):
    """Who the ability affects."""
    SELF = "self"
    OPPONENT = "opponent"
    BOTH = "both"            # e.g., Mimic copies from opponent, buffs self


class EffectType(Enum):
    """What the ability does."""
    ATK_BUFF = "atk_buff"               # Multiplicative ATK modifier
    ATK_BUFF_DURATION = "atk_buff_dur"  # ATK buff lasting multiple ticks
    DMG_BLOCK = "dmg_block"             # Block all or partial damage
    DODGE_BUFF = "dodge_buff"           # Increase dodge chance
    DODGE_DEBUFF = "dodge_debuff"       # Decrease opponent dodge
    DOT = "dot"                         # Damage over time
    HEAL = "heal"                       # Instant or over-time healing
    SKIP_ATTACK = "skip_attack"         # Opponent skips next attack
    IGNORE_DODGE = "ignore_dodge"       # Bypasses dodge rolls
    RANDOM_ATK = "random_atk"           # Random ATK multiplier (Chaos Strike)
    COPY = "copy"                       # Copies opponent ability (Mimic)
    NEGATE_PROC = "negate_proc"         # Blocks next opponent proc (Trick)
    INSTANT_DMG = "instant_dmg"         # Direct HP damage (no attack roll)


class Constraint(Enum):
    """Additional conditions or limitations."""
    NONE = "none"
    SINGLE_CHARGE = "single_charge"       # Can only proc once per combat
    HP_THRESHOLD_15 = "hp_threshold_15"   # Only when HP < 15%
    HP_THRESHOLD_50 = "hp_threshold_50"   # Only when HP < 50%
    MAX_STACKS = "max_stacks"             # DOT stack limit
    BLOCKED_LIST = "blocked_list"         # Cannot copy certain abilities
    SPD_CONDITION = "spd_condition"       # Requires spd advantage


# ---------------------------------------------------------------------------
# Ability descriptor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AbilityDescriptor:
    """Formal description of a single ability in the grammar."""
    name: str
    animal: str
    trigger: Trigger
    target: Target
    effect_type: EffectType
    constraint: Constraint

    # Coefficients for EV/variance computation
    proc_chance: float          # Base proc rate (before WIL bonus)
    atk_mod: float = 0.0       # ATK multiplier delta (e.g., 0.6 = +60%)
    duration: int = 0           # Duration in ticks (0 = instant)
    dot_pct: float = 0.0       # DOT as % of max_hp per tick
    heal_pct: float = 0.0      # Heal as % of max_hp
    block_pct: float = 0.0     # Block as % of max_hp
    dodge_delta: float = 0.0   # Dodge bonus/penalty (additive)
    random_range: tuple[float, float] = (1.0, 1.0)  # For Chaos Strike
    max_stacks: int = 1        # Max DOT stacks
    is_single_charge: bool = False
    skip_opponent: bool = False


@dataclass
class AbilityEV:
    """Computed expected value and variance for an ability."""
    name: str
    animal: str
    ev_damage_per_tick: float      # Expected extra damage per tick
    ev_damage_per_proc: float      # Expected damage on proc
    ev_mitigation_per_proc: float  # Expected damage prevented on proc
    variance_per_proc: float       # Variance of damage contribution
    description: str               # Human-readable summary


# ---------------------------------------------------------------------------
# Reference stat block for EV computation (5/5/5/5 baseline)
# ---------------------------------------------------------------------------

REF_HP = 5
REF_ATK = 5
REF_MAX_HP = 50 + 10 * REF_HP       # 100
REF_BASE_DMG = math.floor(2 + 0.85 * REF_ATK)  # floor(6.25) = 6
REF_DODGE = max(0.0, min(0.30, 0.025 * (REF_ATK - 1)))  # 0.10
REF_WIL = 5
REF_WIL_RESIST = min(0.60, REF_WIL * 0.033)  # 0.165
REF_WIL_BONUS = REF_WIL * 0.0008  # 0.004


# ---------------------------------------------------------------------------
# Core 14 animals — ability definitions
# ---------------------------------------------------------------------------

_STRONG = 0.035
_STANDARD = 0.045

ABILITY_GRAMMAR: list[AbilityDescriptor] = [
    # ===== BEAR =====
    AbilityDescriptor(
        name="Berserker Rage",
        animal="bear",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF_DURATION,
        constraint=Constraint.NONE,
        proc_chance=_STRONG,
        atk_mod=0.60,
        duration=3,
        dodge_delta=-0.40,
    ),
    AbilityDescriptor(
        name="Last Stand",
        animal="bear",
        trigger=Trigger.HP_THRESHOLD,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.SINGLE_CHARGE,
        proc_chance=_STRONG,
        atk_mod=1.00,
        is_single_charge=True,
    ),
    # ===== BUFFALO =====
    AbilityDescriptor(
        name="Thick Hide (ability)",
        animal="buffalo",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DMG_BLOCK,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        block_pct=1.0,  # blocks all damage for 1 tick
        duration=1,
    ),
    AbilityDescriptor(
        name="Iron Will",
        animal="buffalo",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.HEAL,
        constraint=Constraint.SINGLE_CHARGE,
        proc_chance=_STRONG,
        heal_pct=0.12,
        is_single_charge=True,
    ),
    # ===== BOAR =====
    AbilityDescriptor(
        name="Stampede",
        animal="boar",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.BOTH,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        atk_mod=0.50,
        skip_opponent=True,
    ),
    AbilityDescriptor(
        name="Gore",
        animal="boar",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.IGNORE_DODGE,
        constraint=Constraint.NONE,
        proc_chance=_STRONG,
        atk_mod=-0.40,
    ),
    # ===== TIGER =====
    AbilityDescriptor(
        name="Pounce",
        animal="tiger",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.BOTH,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        atk_mod=0.70,
        skip_opponent=True,
    ),
    AbilityDescriptor(
        name="Hamstring",
        animal="tiger",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.OPPONENT,
        effect_type=EffectType.DODGE_DEBUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        dodge_delta=-0.10,  # flat penalty
        duration=4,
    ),
    # ===== WOLF =====
    AbilityDescriptor(
        name="Pack Howl",
        animal="wolf",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF_DURATION,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        atk_mod=0.30,
        duration=4,
    ),
    AbilityDescriptor(
        name="Rend",
        animal="wolf",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.OPPONENT,
        effect_type=EffectType.DOT,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        dot_pct=0.05,
        duration=3,
    ),
    # ===== MONKEY =====
    AbilityDescriptor(
        name="Chaos Strike",
        animal="monkey",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.RANDOM_ATK,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        random_range=(0.8, 2.2),
    ),
    AbilityDescriptor(
        name="Mimic",
        animal="monkey",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.BOTH,
        effect_type=EffectType.COPY,
        constraint=Constraint.BLOCKED_LIST,
        proc_chance=_STRONG,
        atk_mod=0.75,  # copy strength
    ),
    # ===== CROCODILE =====
    AbilityDescriptor(
        name="Death Roll",
        animal="crocodile",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        atk_mod=0.0,  # Death Roll proc (handled separately in engine)
    ),
    AbilityDescriptor(
        name="Thick Scales",
        animal="crocodile",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DMG_BLOCK,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        duration=2,
    ),
    # ===== EAGLE =====
    AbilityDescriptor(
        name="Dive",
        animal="eagle",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STRONG,
        atk_mod=1.00,
    ),
    AbilityDescriptor(
        name="Keen Eye",
        animal="eagle",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DODGE_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        dodge_delta=0.20,
        duration=3,
    ),
    # ===== SNAKE =====
    AbilityDescriptor(
        name="Venom",
        animal="snake",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.OPPONENT,
        effect_type=EffectType.DOT,
        constraint=Constraint.MAX_STACKS,
        proc_chance=_STANDARD,
        dot_pct=0.03,
        duration=3,
        max_stacks=3,
    ),
    AbilityDescriptor(
        name="Coil",
        animal="snake",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DODGE_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        dodge_delta=1.0,  # guaranteed dodge
        duration=1,
    ),
    # ===== RAVEN =====
    AbilityDescriptor(
        name="Shadow Clone",
        animal="raven",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.SINGLE_CHARGE,
        proc_chance=_STANDARD,
        is_single_charge=True,
    ),
    AbilityDescriptor(
        name="Curse",
        animal="raven",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.OPPONENT,
        effect_type=EffectType.DODGE_DEBUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        duration=3,
    ),
    # ===== SHARK =====
    AbilityDescriptor(
        name="Blood Frenzy",
        animal="shark",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STRONG,
    ),
    AbilityDescriptor(
        name="Bite",
        animal="shark",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.OPPONENT,
        effect_type=EffectType.DOT,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        duration=2,
    ),
    # ===== OWL =====
    AbilityDescriptor(
        name="Foresight",
        animal="owl",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DODGE_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        duration=2,
    ),
    AbilityDescriptor(
        name="Silent Strike",
        animal="owl",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.ATK_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
    ),
    # ===== FOX =====
    AbilityDescriptor(
        name="Evasion",
        animal="fox",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DODGE_BUFF,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        dodge_delta=0.50,
        duration=3,
    ),
    AbilityDescriptor(
        name="Trick",
        animal="fox",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.NEGATE_PROC,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        duration=1,
    ),
    # ===== SCORPION =====
    AbilityDescriptor(
        name="Sting",
        animal="scorpion",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.OPPONENT,
        effect_type=EffectType.SKIP_ATTACK,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        skip_opponent=True,
    ),
    AbilityDescriptor(
        name="Exoskeleton",
        animal="scorpion",
        trigger=Trigger.PER_TICK_PROC,
        target=Target.SELF,
        effect_type=EffectType.DMG_BLOCK,
        constraint=Constraint.NONE,
        proc_chance=_STANDARD,
        block_pct=0.15,
        duration=1,
    ),
]


# Index by animal for quick lookup
GRAMMAR_BY_ANIMAL: dict[str, list[AbilityDescriptor]] = {}
for _ab in ABILITY_GRAMMAR:
    GRAMMAR_BY_ANIMAL.setdefault(_ab.animal, []).append(_ab)


# ---------------------------------------------------------------------------
# Analytical EV/variance computation
# ---------------------------------------------------------------------------


def compute_effective_proc_rate(
    base_proc: float,
    wil: int = REF_WIL,
    opponent_wil: int = REF_WIL,
) -> float:
    """Compute effective proc rate accounting for WIL bonus and resist.

    effective = (base + wil * 0.0008) * (1 - min(0.60, opponent_wil * 0.033))
    """
    raw_rate = base_proc + wil * 0.0008
    resist = min(0.60, opponent_wil * 0.033)
    return raw_rate * (1.0 - resist)


def compute_ev(
    ability: AbilityDescriptor,
    *,
    base_dmg: int = REF_BASE_DMG,
    max_hp: int = REF_MAX_HP,
    wil: int = REF_WIL,
    opponent_wil: int = REF_WIL,
    opponent_dodge: float = REF_DODGE,
) -> AbilityEV:
    """Compute analytical EV and variance for a single ability.

    Uses the reference stat block unless overridden.
    Returns per-tick expected values.
    """
    eff_proc = compute_effective_proc_rate(ability.proc_chance, wil, opponent_wil)

    ev_dmg_per_proc = 0.0
    ev_mit_per_proc = 0.0
    var_per_proc = 0.0
    desc_parts: list[str] = []

    etype = ability.effect_type

    if etype == EffectType.ATK_BUFF:
        # Instant ATK buff for 1 hit
        extra_dmg = base_dmg * ability.atk_mod
        hit_chance = 1.0 - opponent_dodge
        if ability.skip_opponent:
            # Also denies one opponent attack
            denied_dmg = base_dmg * hit_chance
            ev_dmg_per_proc = extra_dmg * hit_chance + denied_dmg
            desc_parts.append(
                f"+{ability.atk_mod:.0%} ATK buff + skip opponent attack"
            )
        else:
            ev_dmg_per_proc = extra_dmg * hit_chance
            desc_parts.append(f"+{ability.atk_mod:.0%} ATK buff (1 tick)")
        var_per_proc = ev_dmg_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.ATK_BUFF_DURATION:
        # ATK buff lasting multiple ticks
        extra_per_tick = base_dmg * ability.atk_mod
        hit_chance = 1.0 - opponent_dodge
        total_extra = extra_per_tick * ability.duration * hit_chance
        ev_dmg_per_proc = total_extra
        # Dodge penalty reduces self-dodge, net effect on survivability
        if ability.dodge_delta < 0:
            desc_parts.append(
                f"+{ability.atk_mod:.0%} ATK for {ability.duration}t, "
                f"{ability.dodge_delta:+.0%} dodge penalty"
            )
        else:
            desc_parts.append(
                f"+{ability.atk_mod:.0%} ATK for {ability.duration}t"
            )
        var_per_proc = ev_dmg_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.DMG_BLOCK:
        # Block damage
        if ability.block_pct >= 1.0:
            # Full block (Thick Hide ability)
            blocked = base_dmg  # blocks one full attack
            ev_mit_per_proc = blocked * ability.duration
            desc_parts.append(f"Block all damage for {ability.duration}t")
        else:
            # Partial block (Exoskeleton)
            blocked = max_hp * ability.block_pct
            ev_mit_per_proc = blocked * ability.duration
            desc_parts.append(
                f"Block up to {ability.block_pct:.0%} max_hp "
                f"for {ability.duration}t"
            )
        var_per_proc = ev_mit_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.DODGE_BUFF:
        # Dodge buff — equivalent to mitigating (dodge_delta * attacks * dmg)
        attacks_per_tick = 1.0
        dodged_extra = ability.dodge_delta * attacks_per_tick * base_dmg
        total = dodged_extra * max(1, ability.duration)
        ev_mit_per_proc = total
        desc_parts.append(
            f"+{ability.dodge_delta:.0%} dodge for {ability.duration}t"
        )
        var_per_proc = ev_mit_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.DODGE_DEBUFF:
        # Debuff opponent dodge — increases own hit chance
        extra_hits = ability.dodge_delta * base_dmg  # dodge_delta is negative
        total = abs(extra_hits) * max(1, ability.duration)
        ev_dmg_per_proc = total
        desc_parts.append(
            f"Reduce opponent dodge by {abs(ability.dodge_delta):.0%} "
            f"for {ability.duration}t"
        )
        var_per_proc = ev_dmg_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.DOT:
        # Damage over time
        dot_per_tick = max(1, math.floor(max_hp * ability.dot_pct))
        total_dot = dot_per_tick * ability.duration
        ev_dmg_per_proc = total_dot
        desc_parts.append(
            f"{ability.dot_pct:.0%} max_hp/tick DOT for {ability.duration}t"
        )
        var_per_proc = ev_dmg_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.HEAL:
        # Instant heal
        heal_amount = math.floor(max_hp * ability.heal_pct)
        ev_mit_per_proc = heal_amount
        desc_parts.append(f"Heal {ability.heal_pct:.0%} max_hp")
        var_per_proc = ev_mit_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.SKIP_ATTACK:
        # Deny opponent one attack
        denied = base_dmg * (1.0 - opponent_dodge)
        ev_mit_per_proc = denied
        desc_parts.append("Skip opponent's next attack")
        var_per_proc = ev_mit_per_proc * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.IGNORE_DODGE:
        # Ignore dodge with ATK penalty
        # Without this: dmg * (1 - dodge). With this: dmg * (1 + atk_mod)
        normal_ev = base_dmg * (1.0 - opponent_dodge)
        gore_ev = base_dmg * (1.0 + ability.atk_mod)
        delta = gore_ev - normal_ev
        ev_dmg_per_proc = delta
        desc_parts.append(
            f"Ignore dodge, {ability.atk_mod:+.0%} ATK"
        )
        var_per_proc = abs(ev_dmg_per_proc) * (1.0 - eff_proc) * eff_proc

    elif etype == EffectType.RANDOM_ATK:
        # Chaos Strike: uniform [0.8, 2.2]
        lo, hi = ability.random_range
        mean_mod = (lo + hi) / 2.0  # 1.5
        ev_dmg_per_proc = base_dmg * mean_mod * (1.0 - opponent_dodge)
        # Variance of uniform [lo, hi] = (hi - lo)^2 / 12
        uniform_var = (hi - lo) ** 2 / 12.0
        var_per_proc = (base_dmg ** 2) * uniform_var * (1.0 - opponent_dodge) ** 2
        desc_parts.append(
            f"Random ATK mod [{lo:.1f}, {hi:.1f}], mean={mean_mod:.2f}"
        )

    elif etype == EffectType.COPY:
        # Mimic: copies at 75% strength; highly variable
        # EV depends on opponent's abilities — use average proc value
        avg_ability_ev = base_dmg * 0.5 * ability.atk_mod
        ev_dmg_per_proc = avg_ability_ev
        var_per_proc = ev_dmg_per_proc * (1.0 - eff_proc) * eff_proc
        desc_parts.append(f"Copy at {ability.atk_mod:.0%} strength")

    elif etype == EffectType.NEGATE_PROC:
        # Trick: negates opponent's next proc
        # Value = expected value of opponent's average proc
        avg_opp_proc_value = base_dmg * 0.5
        ev_mit_per_proc = avg_opp_proc_value
        var_per_proc = ev_mit_per_proc * (1.0 - eff_proc) * eff_proc
        desc_parts.append("Negate opponent's next ability proc")

    elif etype == EffectType.INSTANT_DMG:
        ev_dmg_per_proc = base_dmg * ability.atk_mod
        desc_parts.append(f"Instant {ability.atk_mod:.0%} base_dmg")
        var_per_proc = ev_dmg_per_proc * (1.0 - eff_proc) * eff_proc

    # Per-tick EV = per-proc EV * effective_proc_rate
    ev_dmg_per_tick = ev_dmg_per_proc * eff_proc
    ev_mit_per_tick = ev_mit_per_proc * eff_proc

    return AbilityEV(
        name=ability.name,
        animal=ability.animal,
        ev_damage_per_tick=ev_dmg_per_tick,
        ev_damage_per_proc=ev_dmg_per_proc,
        ev_mitigation_per_proc=ev_mit_per_proc,
        variance_per_proc=var_per_proc,
        description="; ".join(desc_parts),
    )


# ---------------------------------------------------------------------------
# Batch computation
# ---------------------------------------------------------------------------


def compute_all_ev(
    *,
    base_dmg: int = REF_BASE_DMG,
    max_hp: int = REF_MAX_HP,
    wil: int = REF_WIL,
    opponent_wil: int = REF_WIL,
    opponent_dodge: float = REF_DODGE,
) -> list[AbilityEV]:
    """Compute EV for all 14 core animals' abilities."""
    return [
        compute_ev(
            ab,
            base_dmg=base_dmg,
            max_hp=max_hp,
            wil=wil,
            opponent_wil=opponent_wil,
            opponent_dodge=opponent_dodge,
        )
        for ab in ABILITY_GRAMMAR
    ]


def ability_table() -> list[dict[str, Any]]:
    """Return a list of dicts for all abilities, suitable for DataFrame or display."""
    rows = []
    for ab in ABILITY_GRAMMAR:
        ev = compute_ev(ab)
        rows.append({
            "animal": ab.animal,
            "ability": ab.name,
            "trigger": ab.trigger.value,
            "target": ab.target.value,
            "effect": ab.effect_type.value,
            "constraint": ab.constraint.value,
            "proc_rate": ab.proc_chance,
            "eff_proc_rate": compute_effective_proc_rate(ab.proc_chance),
            "ev_dmg_per_proc": round(ev.ev_damage_per_proc, 2),
            "ev_mit_per_proc": round(ev.ev_mitigation_per_proc, 2),
            "ev_dmg_per_tick": round(ev.ev_damage_per_tick, 4),
            "variance": round(ev.variance_per_proc, 2),
            "description": ev.description,
        })
    return rows


# ---------------------------------------------------------------------------
# Manual validation helpers
# ---------------------------------------------------------------------------


def _manual_ev_checks() -> dict[str, tuple[float, float, bool]]:
    """Return manual calculations alongside computed values for validation.

    Returns dict of ability_name -> (manual_ev, computed_ev, within_1pct)
    """
    checks: dict[str, tuple[float, float, bool]] = {}

    # Berserker Rage: +60% ATK for 3 ticks
    # Extra damage per tick = 6 * 0.60 = 3.6, hit_chance = 0.90
    # Total per proc = 3.6 * 3 * 0.90 = 9.72
    manual_berserker = 6 * 0.60 * 3 * 0.90
    computed = compute_ev(ABILITY_GRAMMAR[0])
    checks["Berserker Rage"] = (
        manual_berserker,
        computed.ev_damage_per_proc,
        abs(manual_berserker - computed.ev_damage_per_proc) / max(manual_berserker, 1e-9) < 0.01,
    )

    # Last Stand: +100% ATK for 1 hit
    # Extra = 6 * 1.0 * 0.90 = 5.4
    manual_last_stand = 6 * 1.0 * 0.90
    computed = compute_ev(ABILITY_GRAMMAR[1])
    checks["Last Stand"] = (
        manual_last_stand,
        computed.ev_damage_per_proc,
        abs(manual_last_stand - computed.ev_damage_per_proc) / max(manual_last_stand, 1e-9) < 0.01,
    )

    # Rend DOT: 5% max_hp/tick for 3 ticks
    # dot_per_tick = floor(100 * 0.05) = 5, total = 15
    manual_rend = 5 * 3  # = 15
    # Rend is at index 9
    computed = compute_ev(ABILITY_GRAMMAR[9])
    checks["Rend"] = (
        manual_rend,
        computed.ev_damage_per_proc,
        abs(manual_rend - computed.ev_damage_per_proc) / max(manual_rend, 1e-9) < 0.01,
    )

    # Iron Will: heal 12% max_hp
    # heal = floor(100 * 0.12) = 12
    manual_iron_will = 12.0
    computed = compute_ev(ABILITY_GRAMMAR[3])
    checks["Iron Will"] = (
        manual_iron_will,
        computed.ev_mitigation_per_proc,
        abs(manual_iron_will - computed.ev_mitigation_per_proc) / max(manual_iron_will, 1e-9) < 0.01,
    )

    # Venom DOT: 3% max_hp/tick for 3 ticks
    # dot_per_tick = floor(100 * 0.03) = 3, total = 9
    manual_venom = 3 * 3  # = 9
    computed = compute_ev(ABILITY_GRAMMAR[16])
    checks["Venom"] = (
        manual_venom,
        computed.ev_damage_per_proc,
        abs(manual_venom - computed.ev_damage_per_proc) / max(manual_venom, 1e-9) < 0.01,
    )

    # Chaos Strike: uniform [0.8, 2.2], mean = 1.5
    # EV = 6 * 1.5 * 0.90 = 8.1
    manual_chaos = 6 * 1.5 * 0.90
    computed = compute_ev(ABILITY_GRAMMAR[10])
    checks["Chaos Strike"] = (
        manual_chaos,
        computed.ev_damage_per_proc,
        abs(manual_chaos - computed.ev_damage_per_proc) / max(manual_chaos, 1e-9) < 0.01,
    )

    # Pounce: +70% ATK + skip opponent attack
    # Extra dmg = 6 * 0.70 * 0.90 = 3.78
    # Denied dmg = 6 * 0.90 = 5.4
    # Total = 9.18
    manual_pounce = 6 * 0.70 * 0.90 + 6 * 0.90
    computed = compute_ev(ABILITY_GRAMMAR[6])
    checks["Pounce"] = (
        manual_pounce,
        computed.ev_damage_per_proc,
        abs(manual_pounce - computed.ev_damage_per_proc) / max(manual_pounce, 1e-9) < 0.01,
    )

    # Gore: -40% ATK, ignore dodge
    # Normal EV = 6 * 0.90 = 5.4
    # Gore EV = 6 * 0.60 = 3.6
    # Delta = 3.6 - 5.4 = -1.8
    manual_gore = 6 * 0.60 - 6 * 0.90
    computed = compute_ev(ABILITY_GRAMMAR[5])
    checks["Gore"] = (
        manual_gore,
        computed.ev_damage_per_proc,
        abs(manual_gore - computed.ev_damage_per_proc) / max(abs(manual_gore), 1e-9) < 0.01,
    )

    # Pack Howl: +30% ATK for 4 ticks
    # Extra per tick = 6 * 0.30 = 1.8, hit_chance = 0.90
    # Total = 1.8 * 4 * 0.90 = 6.48
    manual_howl = 6 * 0.30 * 4 * 0.90
    computed = compute_ev(ABILITY_GRAMMAR[8])
    checks["Pack Howl"] = (
        manual_howl,
        computed.ev_damage_per_proc,
        abs(manual_howl - computed.ev_damage_per_proc) / max(manual_howl, 1e-9) < 0.01,
    )

    # Exoskeleton: block 15% max_hp for 1 tick
    # blocked = 100 * 0.15 = 15
    manual_exo = 100 * 0.15 * 1
    computed = compute_ev(ABILITY_GRAMMAR[27])
    checks["Exoskeleton"] = (
        manual_exo,
        computed.ev_mitigation_per_proc,
        abs(manual_exo - computed.ev_mitigation_per_proc) / max(manual_exo, 1e-9) < 0.01,
    )

    return checks


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 80)
    print("MOREAU ARENA — Ability Grammar Analysis")
    print("=" * 80)
    print()

    print("Reference stats: HP=5 ATK=5 SPD=5 WIL=5")
    print(f"  max_hp={REF_MAX_HP}, base_dmg={REF_BASE_DMG}, dodge={REF_DODGE:.0%}")
    print()

    # Print all abilities
    for animal_name in [
        "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
        "crocodile", "eagle", "snake", "raven", "shark", "owl",
        "fox", "scorpion",
    ]:
        abilities = GRAMMAR_BY_ANIMAL.get(animal_name, [])
        print(f"--- {animal_name.upper()} ---")
        for ab in abilities:
            ev = compute_ev(ab)
            eff = compute_effective_proc_rate(ab.proc_chance)
            print(f"  {ab.name}")
            print(f"    Grammar: {ab.trigger.value} x {ab.target.value} x "
                  f"{ab.effect_type.value} x {ab.constraint.value}")
            print(f"    Proc: {ab.proc_chance:.3f} (eff: {eff:.4f})")
            print(f"    EV/proc: dmg={ev.ev_damage_per_proc:.2f}, "
                  f"mit={ev.ev_mitigation_per_proc:.2f}")
            print(f"    EV/tick: {ev.ev_damage_per_tick:.4f}")
            print(f"    Var: {ev.variance_per_proc:.2f}")
            print(f"    {ev.description}")
        print()

    # Run manual checks
    print("=" * 80)
    print("Manual EV validation (within 1%):")
    print("=" * 80)
    checks = _manual_ev_checks()
    all_pass = True
    for name, (manual, computed, ok) in checks.items():
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  {status}: {name}: manual={manual:.2f}, computed={computed:.2f}")

    print()
    if all_pass:
        print("All manual checks PASSED.")
    else:
        print("Some checks FAILED!")
