"""Season 1 animal definitions for Moreau Arena.

14 animals: 6 original (frozen) + 8 new.
All types are self-contained — no imports from simulator/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class S1Animal(Enum):
    # Original 6 (frozen)
    BEAR = "bear"
    BUFFALO = "buffalo"
    BOAR = "boar"
    TIGER = "tiger"
    WOLF = "wolf"
    MONKEY = "monkey"
    # New 8
    PORCUPINE = "porcupine"
    SCORPION = "scorpion"
    VULTURE = "vulture"
    RHINO = "rhino"
    VIPER = "viper"
    FOX = "fox"
    EAGLE = "eagle"
    PANTHER = "panther"


class S1Passive(Enum):
    # Original 6
    FURY_PROTOCOL = "fury_protocol"       # Bear
    THICK_HIDE = "thick_hide"             # Buffalo
    CHARGE = "charge"                     # Boar
    AMBUSH_WIRING = "ambush_wiring"       # Tiger
    PACK_SENSE = "pack_sense"             # Wolf
    PRIMATE_CORTEX = "primate_cortex"     # Monkey
    # New 8
    QUILL_ARMOR = "quill_armor"           # Porcupine
    VENOM_GLAND = "venom_gland"           # Scorpion
    CARRION_FEEDER = "carrion_feeder"     # Vulture
    BULWARK_FRAME = "bulwark_frame"       # Rhino
    HEMOTOXIN = "hemotoxin"              # Viper
    CUNNING = "cunning"                   # Fox
    AERIAL_ADVANTAGE = "aerial_advantage" # Eagle
    SHADOW_STALK = "shadow_stalk"         # Panther


class S1AbilityType(Enum):
    # Bear
    BERSERKER_RAGE = "berserker_rage"
    LAST_STAND = "last_stand"
    # Buffalo
    THICK_HIDE_BLOCK = "thick_hide_block"
    IRON_WILL = "iron_will"
    # Boar
    STAMPEDE = "stampede"
    GORE = "gore"
    # Tiger
    POUNCE = "pounce"
    HAMSTRING = "hamstring"
    # Wolf
    PACK_HOWL = "pack_howl"
    REND = "rend"
    # Monkey
    CHAOS_STRIKE = "chaos_strike"
    MIMIC = "mimic"
    # Porcupine
    SPIKE_SHIELD = "spike_shield"
    CURL_UP = "curl_up"
    # Scorpion
    ENVENOM = "envenom"
    TAIL_STRIKE = "tail_strike"
    # Vulture
    DEATH_SPIRAL = "death_spiral"
    FEAST = "feast"
    # Rhino
    HORN_CHARGE = "horn_charge"
    FORTIFY = "fortify"
    # Viper
    TOXIC_BITE = "toxic_bite"
    SHED_SKIN = "shed_skin"
    # Fox
    OUTFOX = "outfox"
    TRICK = "trick"
    # Eagle
    DIVE = "dive"
    TAILWIND = "tailwind"
    # Panther
    LUNGE = "lunge"
    FADE = "fade"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

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
        if total < 4 or total > 24:
            raise ValueError(f"Stats must sum to 4-24, got {total}")


@dataclass(frozen=True)
class Ability:
    name: str
    ability_type: S1AbilityType
    proc_chance: float = 0.04
    duration: int = 0
    is_single_charge: bool = False
    animal: S1Animal = S1Animal.BEAR


@dataclass
class AbilityBuff:
    ability_type: S1AbilityType
    remaining_ticks: int
    source_side: str = "a"
    is_mimic_copy: bool = False


@dataclass
class ActiveEffect:
    name: str
    remaining_ticks: int
    damage_per_tick: int = 0
    heal_per_tick: int = 0


@dataclass
class Creature:
    animal: S1Animal
    stats: StatBlock
    passive: S1Passive
    current_hp: int
    max_hp: int
    base_dmg: int
    armor_flat: int
    size: Size
    position: Position
    active_effects: list[ActiveEffect] = field(default_factory=list)
    second_wind_available: bool = False
    second_wind_triggered: bool = False
    charge_used: bool = False
    first_hit_taken: bool = False
    dodge_chance: float = 0.0
    movement_range: int = 1
    ability_power: float = 1.0
    resist_chance: float = 0.0
    abilities: tuple[Ability, ...] = ()
    active_buffs: list[AbilityBuff] = field(default_factory=list)
    iron_will_used: bool = False
    last_stand_used: bool = False
    last_ability_procced: S1AbilityType | None = None
    skip_next_attack: bool = False
    fury_triggered: bool = False
    fury_active_ticks: int = 0
    active_cooldowns: dict[str, int] = field(default_factory=dict)
    # Season 1 new fields
    shadow_stalk_hits: int = 0          # Panther: counts attacks while undetected
    is_undetected: bool = False         # Panther: Shadow Stalk state
    has_taken_damage: bool = False      # Panther: tracks if damage received
    aerial_active: bool = True          # Eagle: Aerial Advantage state
    aerial_lost_ticks: int = 0          # Eagle: ticks remaining without Aerial
    outfox_charges: int = 0             # Fox: Outfox dodge charges
    anti_heal_ticks: int = 0            # Scorpion: anti-heal debuff remaining
    curl_up_active: bool = False        # Porcupine: Curl Up block state
    curl_up_immobile_ticks: int = 0     # Porcupine: immobile after Curl Up


# ---------------------------------------------------------------------------
# Passive mapping
# ---------------------------------------------------------------------------

ANIMAL_PASSIVE: dict[S1Animal, S1Passive] = {
    S1Animal.BEAR: S1Passive.FURY_PROTOCOL,
    S1Animal.BUFFALO: S1Passive.THICK_HIDE,
    S1Animal.BOAR: S1Passive.CHARGE,
    S1Animal.TIGER: S1Passive.AMBUSH_WIRING,
    S1Animal.WOLF: S1Passive.PACK_SENSE,
    S1Animal.MONKEY: S1Passive.PRIMATE_CORTEX,
    S1Animal.PORCUPINE: S1Passive.QUILL_ARMOR,
    S1Animal.SCORPION: S1Passive.VENOM_GLAND,
    S1Animal.VULTURE: S1Passive.CARRION_FEEDER,
    S1Animal.RHINO: S1Passive.BULWARK_FRAME,
    S1Animal.VIPER: S1Passive.HEMOTOXIN,
    S1Animal.FOX: S1Passive.CUNNING,
    S1Animal.EAGLE: S1Passive.AERIAL_ADVANTAGE,
    S1Animal.PANTHER: S1Passive.SHADOW_STALK,
}


# ---------------------------------------------------------------------------
# Ability definitions
# ---------------------------------------------------------------------------

_STRONG_RATE = 0.035
_STANDARD_RATE = 0.045

ANIMAL_ABILITIES: dict[S1Animal, tuple[Ability, Ability]] = {
    # --- Original 6 (frozen) ---
    S1Animal.BEAR: (
        Ability(
            name="Berserker Rage",
            ability_type=S1AbilityType.BERSERKER_RAGE,
            proc_chance=_STRONG_RATE,
            duration=3,
            animal=S1Animal.BEAR,
        ),
        Ability(
            name="Last Stand",
            ability_type=S1AbilityType.LAST_STAND,
            proc_chance=_STRONG_RATE,
            duration=0,
            is_single_charge=True,
            animal=S1Animal.BEAR,
        ),
    ),
    S1Animal.BUFFALO: (
        Ability(
            name="Thick Hide Block",
            ability_type=S1AbilityType.THICK_HIDE_BLOCK,
            proc_chance=_STANDARD_RATE,
            duration=1,
            animal=S1Animal.BUFFALO,
        ),
        Ability(
            name="Iron Will",
            ability_type=S1AbilityType.IRON_WILL,
            proc_chance=_STRONG_RATE,
            duration=0,
            is_single_charge=True,
            animal=S1Animal.BUFFALO,
        ),
    ),
    S1Animal.BOAR: (
        Ability(
            name="Stampede",
            ability_type=S1AbilityType.STAMPEDE,
            proc_chance=_STANDARD_RATE,
            duration=0,
            animal=S1Animal.BOAR,
        ),
        Ability(
            name="Gore",
            ability_type=S1AbilityType.GORE,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.BOAR,
        ),
    ),
    S1Animal.TIGER: (
        Ability(
            name="Pounce",
            ability_type=S1AbilityType.POUNCE,
            proc_chance=_STANDARD_RATE,
            duration=0,
            animal=S1Animal.TIGER,
        ),
        Ability(
            name="Hamstring",
            ability_type=S1AbilityType.HAMSTRING,
            proc_chance=_STANDARD_RATE,
            duration=4,
            animal=S1Animal.TIGER,
        ),
    ),
    S1Animal.WOLF: (
        Ability(
            name="Pack Howl",
            ability_type=S1AbilityType.PACK_HOWL,
            proc_chance=_STANDARD_RATE,
            duration=4,
            animal=S1Animal.WOLF,
        ),
        Ability(
            name="Rend",
            ability_type=S1AbilityType.REND,
            proc_chance=_STANDARD_RATE,
            duration=3,
            animal=S1Animal.WOLF,
        ),
    ),
    S1Animal.MONKEY: (
        Ability(
            name="Chaos Strike",
            ability_type=S1AbilityType.CHAOS_STRIKE,
            proc_chance=_STANDARD_RATE,
            duration=0,
            animal=S1Animal.MONKEY,
        ),
        Ability(
            name="Mimic",
            ability_type=S1AbilityType.MIMIC,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.MONKEY,
        ),
    ),
    # --- New 8 ---
    S1Animal.PORCUPINE: (
        Ability(
            name="Spike Shield",
            ability_type=S1AbilityType.SPIKE_SHIELD,
            proc_chance=_STANDARD_RATE,
            duration=3,
            animal=S1Animal.PORCUPINE,
        ),
        Ability(
            name="Curl Up",
            ability_type=S1AbilityType.CURL_UP,
            proc_chance=_STRONG_RATE,
            duration=0,
            is_single_charge=False,
            animal=S1Animal.PORCUPINE,
        ),
    ),
    S1Animal.SCORPION: (
        Ability(
            name="Envenom",
            ability_type=S1AbilityType.ENVENOM,
            proc_chance=_STANDARD_RATE,
            duration=3,
            animal=S1Animal.SCORPION,
        ),
        Ability(
            name="Tail Strike",
            ability_type=S1AbilityType.TAIL_STRIKE,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.SCORPION,
        ),
    ),
    S1Animal.VULTURE: (
        Ability(
            name="Death Spiral",
            ability_type=S1AbilityType.DEATH_SPIRAL,
            proc_chance=_STANDARD_RATE,
            duration=2,
            animal=S1Animal.VULTURE,
        ),
        Ability(
            name="Feast",
            ability_type=S1AbilityType.FEAST,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.VULTURE,
        ),
    ),
    S1Animal.RHINO: (
        Ability(
            name="Horn Charge",
            ability_type=S1AbilityType.HORN_CHARGE,
            proc_chance=_STANDARD_RATE,
            duration=0,
            animal=S1Animal.RHINO,
        ),
        Ability(
            name="Fortify",
            ability_type=S1AbilityType.FORTIFY,
            proc_chance=_STRONG_RATE,
            duration=4,
            animal=S1Animal.RHINO,
        ),
    ),
    S1Animal.VIPER: (
        Ability(
            name="Toxic Bite",
            ability_type=S1AbilityType.TOXIC_BITE,
            proc_chance=_STANDARD_RATE,
            duration=5,
            animal=S1Animal.VIPER,
        ),
        Ability(
            name="Shed Skin",
            ability_type=S1AbilityType.SHED_SKIN,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.VIPER,
        ),
    ),
    S1Animal.FOX: (
        Ability(
            name="Outfox",
            ability_type=S1AbilityType.OUTFOX,
            proc_chance=_STANDARD_RATE,
            duration=0,
            animal=S1Animal.FOX,
        ),
        Ability(
            name="Trick",
            ability_type=S1AbilityType.TRICK,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.FOX,
        ),
    ),
    S1Animal.EAGLE: (
        Ability(
            name="Dive",
            ability_type=S1AbilityType.DIVE,
            proc_chance=_STRONG_RATE,
            duration=0,
            animal=S1Animal.EAGLE,
        ),
        Ability(
            name="Tailwind",
            ability_type=S1AbilityType.TAILWIND,
            proc_chance=_STANDARD_RATE,
            duration=3,
            animal=S1Animal.EAGLE,
        ),
    ),
    S1Animal.PANTHER: (
        Ability(
            name="Lunge",
            ability_type=S1AbilityType.LUNGE,
            proc_chance=_STANDARD_RATE,
            duration=0,
            animal=S1Animal.PANTHER,
        ),
        Ability(
            name="Fade",
            ability_type=S1AbilityType.FADE,
            proc_chance=_STRONG_RATE,
            duration=3,
            animal=S1Animal.PANTHER,
        ),
    ),
}
