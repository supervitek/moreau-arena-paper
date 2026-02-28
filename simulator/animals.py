"""Core types for Moreau Arena.

Standalone version for the companion repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Animal(Enum):
    BEAR = "bear"
    BUFFALO = "buffalo"
    BOAR = "boar"
    TIGER = "tiger"
    WOLF = "wolf"
    MONKEY = "monkey"
    CROCODILE = "crocodile"
    EAGLE = "eagle"
    SNAKE = "snake"
    RAVEN = "raven"
    SHARK = "shark"
    OWL = "owl"
    FOX = "fox"
    SCORPION = "scorpion"


class Passive(Enum):
    FURY_PROTOCOL = "fury_protocol"
    THICK_HIDE = "thick_hide"
    CHARGE = "charge"
    AMBUSH_WIRING = "ambush_wiring"
    PACK_SENSE = "pack_sense"
    PRIMATE_CORTEX = "primate_cortex"
    DEATH_ROLL = "death_roll"
    AERIAL_STRIKE = "aerial_strike"
    VENOM_GLANDS = "venom_glands"
    OMEN = "omen"
    BLOOD_FRENZY = "blood_frenzy"
    NIGHT_VISION = "night_vision"
    CUNNING = "cunning"
    PARALYTIC_STING = "paralytic_sting"


class ActiveAbilityType(Enum):
    # Bear
    ROAR = "roar"
    MAUL = "maul"
    # Buffalo
    FORTIFY = "fortify"
    HORN_CHARGE = "horn_charge"
    # Tiger
    AMBUSH = "ambush"
    CRIPPLE = "cripple"
    # Wolf
    RALLY = "rally"
    LIFE_BITE = "life_bite"
    # Monkey
    CONFUSE = "confuse"
    FLING = "fling"
    # Boar
    TRAMPLE = "trample"
    TUSK_GUARD = "tusk_guard"
    # Crocodile
    DEATH_GRIP = "death_grip"
    SUBMERGE = "submerge"
    # Eagle
    SWOOP = "swoop"
    WIND_GUST = "wind_gust"
    # Snake
    INJECT = "inject"
    SHED_SKIN = "shed_skin"
    # Raven
    HEX = "hex"
    SHADOW_STEP = "shadow_step"
    # Shark
    FEEDING_FRENZY = "feeding_frenzy"
    THRASH = "thrash"
    # Owl
    PREDICT = "predict"
    SCREECH = "screech"
    # Fox
    DECOY = "decoy"
    PILFER = "pilfer"
    # Scorpion
    PINCH = "pinch"
    BURROW = "burrow"


class AbilityType(Enum):
    BERSERKER_RAGE = "berserker_rage"
    THICK_HIDE_ABILITY = "thick_hide_ability"
    POUNCE = "pounce"
    HAMSTRING = "hamstring"
    PACK_HOWL = "pack_howl"
    REND_ABILITY = "rend_ability"
    CHAOS_STRIKE = "chaos_strike"
    MIMIC = "mimic"
    STAMPEDE = "stampede"
    IRON_WILL = "iron_will"
    GORE = "gore"
    LAST_STAND = "last_stand"
    # Phase 3 — new animal abilities
    DEATH_ROLL_ABILITY = "death_roll_ability"
    THICK_SCALES = "thick_scales"
    DIVE = "dive"
    KEEN_EYE = "keen_eye"
    VENOM = "venom"
    COIL = "coil"
    SHADOW_CLONE = "shadow_clone"
    CURSE = "curse"
    BLOOD_FRENZY_ABILITY = "blood_frenzy_ability"
    BITE = "bite"
    FORESIGHT = "foresight"
    SILENT_STRIKE = "silent_strike"
    EVASION = "evasion"
    TRICK = "trick"
    STING = "sting"
    EXOSKELETON = "exoskeleton"


ANIMAL_PASSIVE: dict[Animal, Passive] = {
    Animal.BEAR: Passive.FURY_PROTOCOL,
    Animal.BUFFALO: Passive.THICK_HIDE,
    Animal.BOAR: Passive.CHARGE,
    Animal.TIGER: Passive.AMBUSH_WIRING,
    Animal.WOLF: Passive.PACK_SENSE,
    Animal.MONKEY: Passive.PRIMATE_CORTEX,
    Animal.CROCODILE: Passive.DEATH_ROLL,
    Animal.EAGLE: Passive.AERIAL_STRIKE,
    Animal.SNAKE: Passive.VENOM_GLANDS,
    Animal.RAVEN: Passive.OMEN,
    Animal.SHARK: Passive.BLOOD_FRENZY,
    Animal.OWL: Passive.NIGHT_VISION,
    Animal.FOX: Passive.CUNNING,
    Animal.SCORPION: Passive.PARALYTIC_STING,
}


class MutationBranch(Enum):
    APEX = "apex"
    FERAL = "feral"


class MutationTier(Enum):
    L1 = 1
    L2 = 2
    L3 = 3


@dataclass(frozen=True, order=True)
class Position:
    row: int
    col: int


@dataclass(frozen=True)
class Size:
    rows: int
    cols: int


@dataclass(frozen=True)
class StatBlock:
    hp: int
    atk: int
    spd: int
    wil: int

    def __post_init__(self) -> None:
        for stat_name in ("hp", "atk", "spd", "wil"):
            if getattr(self, stat_name) < 1:
                raise ValueError(
                    f"All stats must have min 1, got {stat_name}={getattr(self, stat_name)}"
                )
        total = self.hp + self.atk + self.spd + self.wil
        if total != 20:
            raise ValueError(f"Stats must sum to 20, got {total}")


@dataclass(frozen=True)
class Mutation:
    id: str
    name: str
    branch: MutationBranch
    tier: MutationTier
    cost: int
    success_rate: float
    effect: str


@dataclass
class ActiveEffect:
    name: str
    remaining_ticks: int
    damage_per_tick: int = 0
    heal_per_tick: int = 0


@dataclass(frozen=True)
class Ability:
    name: str
    ability_type: AbilityType
    proc_chance: float = 0.04
    duration: int = 0
    is_single_charge: bool = False
    animal: Animal = Animal.BEAR


@dataclass
class AbilityBuff:
    ability_type: AbilityType
    remaining_ticks: int
    source_side: str = "a"
    is_mimic_copy: bool = False


_STRONG_RATE = 0.035  # Last Stand, Berserker Rage, Gore, Mimic, Iron Will
_OTHER_RATE = 0.045   # Pounce, Hamstring, Pack Howl, Rend, Chaos Strike, Stampede, Thick Hide

ANIMAL_ABILITIES: dict[Animal, tuple[Ability, Ability]] = {
    Animal.BEAR: (
        Ability(
            name="Berserker Rage",
            ability_type=AbilityType.BERSERKER_RAGE,
            proc_chance=_STRONG_RATE,
            duration=3,
            animal=Animal.BEAR,
        ),
        Ability(
            name="Last Stand",
            ability_type=AbilityType.LAST_STAND,
            proc_chance=_STRONG_RATE,
            duration=0,
            is_single_charge=True,
            animal=Animal.BEAR,
        ),
    ),
    Animal.BUFFALO: (
        Ability(
            name="Thick Hide",
            ability_type=AbilityType.THICK_HIDE_ABILITY,
            proc_chance=_OTHER_RATE,
            duration=1,
            animal=Animal.BUFFALO,
        ),
        Ability(
            name="Iron Will",
            ability_type=AbilityType.IRON_WILL,
            proc_chance=_STRONG_RATE,
            duration=0,
            is_single_charge=True,
            animal=Animal.BUFFALO,
        ),
    ),
    Animal.TIGER: (
        Ability(
            name="Pounce",
            ability_type=AbilityType.POUNCE,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.TIGER,
        ),
        Ability(
            name="Hamstring",
            ability_type=AbilityType.HAMSTRING,
            proc_chance=_OTHER_RATE,
            duration=4,
            animal=Animal.TIGER,
        ),
    ),
    Animal.WOLF: (
        Ability(
            name="Pack Howl",
            ability_type=AbilityType.PACK_HOWL,
            proc_chance=_OTHER_RATE,
            duration=4,
            animal=Animal.WOLF,
        ),
        Ability(
            name="Rend",
            ability_type=AbilityType.REND_ABILITY,
            proc_chance=_OTHER_RATE,
            duration=3,
            animal=Animal.WOLF,
        ),
    ),
    Animal.MONKEY: (
        Ability(
            name="Chaos Strike",
            ability_type=AbilityType.CHAOS_STRIKE,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.MONKEY,
        ),
        Ability(
            name="Mimic",
            ability_type=AbilityType.MIMIC,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=Animal.MONKEY,
        ),
    ),
    Animal.BOAR: (
        Ability(
            name="Stampede",
            ability_type=AbilityType.STAMPEDE,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.BOAR,
        ),
        Ability(
            name="Gore",
            ability_type=AbilityType.GORE,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=Animal.BOAR,
        ),
    ),
    Animal.CROCODILE: (
        Ability(
            name="Death Roll",
            ability_type=AbilityType.DEATH_ROLL_ABILITY,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.CROCODILE,
        ),
        Ability(
            name="Thick Scales",
            ability_type=AbilityType.THICK_SCALES,
            proc_chance=_OTHER_RATE,
            duration=2,
            animal=Animal.CROCODILE,
        ),
    ),
    Animal.EAGLE: (
        Ability(
            name="Dive",
            ability_type=AbilityType.DIVE,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=Animal.EAGLE,
        ),
        Ability(
            name="Keen Eye",
            ability_type=AbilityType.KEEN_EYE,
            proc_chance=_OTHER_RATE,
            duration=3,
            animal=Animal.EAGLE,
        ),
    ),
    Animal.SNAKE: (
        Ability(
            name="Venom",
            ability_type=AbilityType.VENOM,
            proc_chance=_OTHER_RATE,
            duration=3,
            animal=Animal.SNAKE,
        ),
        Ability(
            name="Coil",
            ability_type=AbilityType.COIL,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.SNAKE,
        ),
    ),
    Animal.RAVEN: (
        Ability(
            name="Shadow Clone",
            ability_type=AbilityType.SHADOW_CLONE,
            proc_chance=_OTHER_RATE,
            duration=0,
            is_single_charge=True,
            animal=Animal.RAVEN,
        ),
        Ability(
            name="Curse",
            ability_type=AbilityType.CURSE,
            proc_chance=_OTHER_RATE,
            duration=3,
            animal=Animal.RAVEN,
        ),
    ),
    Animal.SHARK: (
        Ability(
            name="Blood Frenzy",
            ability_type=AbilityType.BLOOD_FRENZY_ABILITY,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=Animal.SHARK,
        ),
        Ability(
            name="Bite",
            ability_type=AbilityType.BITE,
            proc_chance=_OTHER_RATE,
            duration=2,
            animal=Animal.SHARK,
        ),
    ),
    Animal.OWL: (
        Ability(
            name="Foresight",
            ability_type=AbilityType.FORESIGHT,
            proc_chance=_OTHER_RATE,
            duration=2,
            animal=Animal.OWL,
        ),
        Ability(
            name="Silent Strike",
            ability_type=AbilityType.SILENT_STRIKE,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.OWL,
        ),
    ),
    Animal.FOX: (
        Ability(
            name="Evasion",
            ability_type=AbilityType.EVASION,
            proc_chance=_OTHER_RATE,
            duration=3,
            animal=Animal.FOX,
        ),
        Ability(
            name="Trick",
            ability_type=AbilityType.TRICK,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.FOX,
        ),
    ),
    Animal.SCORPION: (
        Ability(
            name="Sting",
            ability_type=AbilityType.STING,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.SCORPION,
        ),
        Ability(
            name="Exoskeleton",
            ability_type=AbilityType.EXOSKELETON,
            proc_chance=_OTHER_RATE,
            duration=0,
            animal=Animal.SCORPION,
        ),
    ),
}


@dataclass
class Creature:
    animal: Animal
    stats: StatBlock
    passive: Passive
    current_hp: int
    max_hp: int
    base_dmg: int
    armor_flat: int
    size: Size
    position: Position
    mutations: list[Mutation] = field(default_factory=list)
    active_effects: list[ActiveEffect] = field(default_factory=list)
    second_wind_available: bool = False
    second_wind_triggered: bool = False
    charge_used: bool = False
    first_hit_taken: bool = False
    has_rend: bool = False
    has_critical_strike: bool = False
    has_execute: bool = False
    has_regeneration: bool = False
    has_bloodlust: bool = False
    dodge_chance: float = 0.0
    movement_range: int = 1
    ability_range: int = 1
    ability_power: float = 1.0
    resist_chance: float = 0.0
    abilities: tuple[Ability, ...] = ()
    active_buffs: list[AbilityBuff] = field(default_factory=list)
    iron_will_used: bool = False
    last_stand_used: bool = False
    last_ability_procced: AbilityType | None = None
    skip_next_attack: bool = False
    fury_triggered: bool = False
    fury_active_ticks: int = 0
    active_cooldowns: dict[str, int] = field(default_factory=dict)


@dataclass
class MatchResult:
    winner: str | None
    ticks: int
    end_condition: str
    seed: int
    log: list[Any] = field(default_factory=list)
