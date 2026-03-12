"""Moreau Pets — Mutation tree, XP system, and pet lifecycle.

Pure data module — no web dependencies.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ANIMALS = [
    "bear", "buffalo", "boar", "tiger", "wolf", "monkey",
    "porcupine", "scorpion", "vulture", "rhino", "viper",
    "fox", "eagle", "panther",
]

STAT_TOTAL = 20
STAT_MIN = 1
STAT_MAX = 16  # 20 - 3*1 = 17, but practical max is 17

LEVEL_THRESHOLDS = {
    1: 0, 2: 50, 3: 100, 4: 150, 5: 200,
    6: 300, 7: 400, 8: 500, 9: 600, 10: 750,
}
MAX_LEVEL = 10

XP_WIN = 30
XP_LOSS = 10

MUTATION_LEVELS = {3, 6, 9}

# ---------------------------------------------------------------------------
# Mutation definitions
# ---------------------------------------------------------------------------

MUTATIONS_L3 = {
    "blood_rage": {
        "id": "blood_rage",
        "name": "Bloodrage",
        "level": 3,
        "parent": None,
        "stat_changes": {"atk": 2, "spd": -1},
        "effect": "+2 ATK, -1 SPD",
        "flavor": "The rage builds. Your muscles swell. Speed is a luxury you no longer need.",
        "color": "red",
    },
    "thick_hide": {
        "id": "thick_hide",
        "name": "Thick Hide",
        "level": 3,
        "parent": None,
        "stat_changes": {"hp": 2, "atk": -1},
        "effect": "+2 HP, -1 ATK",
        "flavor": "Your skin hardens. Blows that once hurt now feel like rain.",
        "color": "blue",
    },
    "quick_feet": {
        "id": "quick_feet",
        "name": "Quick Feet",
        "level": 3,
        "parent": None,
        "stat_changes": {"spd": 2, "hp": -1},
        "effect": "+2 SPD, -1 HP",
        "flavor": "You shed weight, shed armor, shed fear. Only speed remains.",
        "color": "green",
    },
}

MUTATIONS_L6 = {
    "frenzy": {
        "id": "frenzy",
        "name": "Frenzy",
        "level": 6,
        "parent": "blood_rage",
        "stat_changes": {},
        "effect": "Double attack when HP <25%",
        "flavor": "Pain is fuel. The closer to death, the more alive you become.",
        "color": "red",
    },
    "intimidate": {
        "id": "intimidate",
        "name": "Intimidate",
        "level": 6,
        "parent": "blood_rage",
        "stat_changes": {},
        "effect": "Enemy -10% ATK",
        "flavor": "They see the scars. They see the madness in your eyes. They hesitate.",
        "color": "red",
    },
    "regeneration": {
        "id": "regeneration",
        "name": "Regeneration",
        "level": 6,
        "parent": "thick_hide",
        "stat_changes": {},
        "effect": "+1 HP per 5 ticks",
        "flavor": "Your flesh knits itself. What was torn, heals. What was broken, mends.",
        "color": "blue",
    },
    "fortress": {
        "id": "fortress",
        "name": "Fortress",
        "level": 6,
        "parent": "thick_hide",
        "stat_changes": {},
        "effect": "Ignore first hit each game",
        "flavor": "The first blow is free. There won't be a second.",
        "color": "blue",
    },
    "ambush": {
        "id": "ambush",
        "name": "Ambush",
        "level": 6,
        "parent": "quick_feet",
        "stat_changes": {},
        "effect": "First attack deals 2x damage",
        "flavor": "They never see you coming. By the time they do, it's already over.",
        "color": "green",
    },
    "evasion": {
        "id": "evasion",
        "name": "Evasion",
        "level": 6,
        "parent": "quick_feet",
        "stat_changes": {},
        "effect": "+15% dodge chance",
        "flavor": "You exist between their strikes. A ghost in the space where pain should be.",
        "color": "green",
    },
}

MUTATIONS_L9 = {
    "berserker": {
        "id": "berserker",
        "name": "BERSERKER MODE",
        "level": 9,
        "parent": "frenzy",
        "stat_changes": {},
        "effect": "Triple attack at <10% HP, ignore pain",
        "flavor": "I AM BECOME DEATH.",
        "color": "red",
    },
    "warlord": {
        "id": "warlord",
        "name": "WARLORD",
        "level": 9,
        "parent": "intimidate",
        "stat_changes": {},
        "effect": "Aura: all enemies -15% ATK permanently",
        "flavor": "Kneel.",
        "color": "red",
    },
    "immortal": {
        "id": "immortal",
        "name": "IMMORTAL",
        "level": 9,
        "parent": "regeneration",
        "stat_changes": {},
        "effect": "Revive once per game at 25% HP",
        "flavor": "You cannot kill what refuses to die.",
        "color": "blue",
    },
    "juggernaut": {
        "id": "juggernaut",
        "name": "JUGGERNAUT",
        "level": 9,
        "parent": "fortress",
        "stat_changes": {},
        "effect": "Immune to abilities, only raw damage hurts",
        "flavor": "Your tricks mean nothing to me.",
        "color": "blue",
    },
    "phantom_strike": {
        "id": "phantom_strike",
        "name": "PHANTOM STRIKE",
        "level": 9,
        "parent": "ambush",
        "stat_changes": {},
        "effect": "Teleport behind enemy + guaranteed crit",
        "flavor": "Nothing personal, kid.",
        "color": "green",
    },
    "ghost": {
        "id": "ghost",
        "name": "GHOST",
        "level": 9,
        "parent": "evasion",
        "stat_changes": {},
        "effect": "50% dodge for 3 ticks when HP <30%",
        "flavor": "Now you see me... actually, no you don't.",
        "color": "green",
    },
}

ALL_MUTATIONS: dict[str, dict[str, Any]] = {}
ALL_MUTATIONS.update(MUTATIONS_L3)
ALL_MUTATIONS.update(MUTATIONS_L6)
ALL_MUTATIONS.update(MUTATIONS_L9)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_pet(name: str, animal: str, hp: int, atk: int, spd: int, wil: int) -> dict:
    """Create a new pet. Stats must sum to 20, each >= 1."""
    if not name or not name.strip():
        raise ValueError("Pet name cannot be empty")
    if animal not in VALID_ANIMALS:
        raise ValueError(f"Invalid animal: {animal}. Must be one of {VALID_ANIMALS}")
    total = hp + atk + spd + wil
    if total != STAT_TOTAL:
        raise ValueError(f"Stats must sum to {STAT_TOTAL}, got {total}")
    for stat_name, val in [("hp", hp), ("atk", atk), ("spd", spd), ("wil", wil)]:
        if val < STAT_MIN:
            raise ValueError(f"{stat_name} must be >= {STAT_MIN}, got {val}")

    now = datetime.now(timezone.utc).isoformat()
    return {
        "name": name.strip(),
        "animal": animal,
        "level": 1,
        "xp": 0,
        "base_stats": {"hp": hp, "atk": atk, "spd": spd, "wil": wil},
        "mutations": [],
        "fights": [],
        "mood": "excited",
        "created_at": now,
    }


def _level_for_xp(xp: int) -> int:
    """Return level for given XP amount."""
    level = 1
    for lvl in sorted(LEVEL_THRESHOLDS.keys()):
        if xp >= LEVEL_THRESHOLDS[lvl]:
            level = lvl
    return level


def add_xp(pet: dict, amount: int) -> tuple[dict, bool]:
    """Add XP to pet. Returns (updated pet, leveled_up)."""
    pet = copy.deepcopy(pet)
    old_level = pet["level"]
    pet["xp"] += amount
    new_level = _level_for_xp(pet["xp"])
    if new_level > MAX_LEVEL:
        new_level = MAX_LEVEL
    pet["level"] = new_level
    leveled_up = new_level > old_level
    return pet, leveled_up


def get_available_mutations(pet: dict) -> list[dict]:
    """Return mutation options available to the pet right now."""
    level = pet["level"]
    mutations = pet.get("mutations", [])

    # Check which mutation levels are already chosen
    chosen_levels = set()
    for mid in mutations:
        m = ALL_MUTATIONS.get(mid)
        if m:
            chosen_levels.add(m["level"])

    # Level 3 mutations
    if level >= 3 and 3 not in chosen_levels:
        return list(MUTATIONS_L3.values())

    # Level 6 mutations — depends on L3 choice
    if level >= 6 and 6 not in chosen_levels and 3 in chosen_levels:
        l3_choice = mutations[0]  # First mutation is always L3
        return [m for m in MUTATIONS_L6.values() if m["parent"] == l3_choice]

    # Level 9 mutations — depends on L6 choice (automatic, single destiny)
    if level >= 9 and 9 not in chosen_levels and 6 in chosen_levels:
        l6_choice = mutations[1]  # Second mutation is L6
        return [m for m in MUTATIONS_L9.values() if m["parent"] == l6_choice]

    return []


def apply_mutation(pet: dict, mutation_id: str) -> dict:
    """Apply a mutation to the pet. Validates availability."""
    available = get_available_mutations(pet)
    available_ids = [m["id"] for m in available]
    if mutation_id not in available_ids:
        raise ValueError(
            f"Mutation '{mutation_id}' not available. "
            f"Available: {available_ids}"
        )

    pet = copy.deepcopy(pet)
    pet["mutations"].append(mutation_id)

    # Apply stat changes
    mutation = ALL_MUTATIONS[mutation_id]
    for stat, delta in mutation.get("stat_changes", {}).items():
        pet["base_stats"][stat] += delta

    return pet


def get_effective_stats(pet: dict) -> dict:
    """Get stats with all mutations applied. Returns a new dict."""
    stats = dict(pet["base_stats"])
    # Stat changes are already applied in base_stats via apply_mutation
    # This function provides a clean interface and could add computed fields
    stats["max_hp"] = 50 + stats["hp"] * 10
    stats["base_dmg"] = max(0, stats["atk"] - 1)
    stats["dodge_pct"] = stats["spd"] * 2.5
    stats["resist_pct"] = stats["wil"] * 3.3
    return stats


def get_mutation_tree() -> dict:
    """Return full mutation tree structure for UI rendering."""
    return {
        "level_3": list(MUTATIONS_L3.values()),
        "level_6": list(MUTATIONS_L6.values()),
        "level_9": list(MUTATIONS_L9.values()),
    }


# ---------------------------------------------------------------------------
# Apex Forms — Secret synergies
# ---------------------------------------------------------------------------

APEX_FORMS: list[dict[str, Any]] = [
    {
        "id": "spectral_stalker",
        "name": "Spectral Stalker",
        "animal": "tiger",
        "description": "Between one heartbeat and the next, the tiger ceases to exist — and reappears behind you.",
        "stat_bonus": {"atk": 3, "spd": 3},
        "ability": "Guaranteed critical strike from stealth. Cannot be targeted for 1 tick after a kill.",
    },
    {
        "id": "the_martyr",
        "name": "The Martyr",
        "animal": "bear",
        "description": "Every wound only makes it angrier. Every scar is a sermon. It will not fall.",
        "stat_bonus": {"hp": 5, "wil": 2},
        "ability": "When HP drops below 20%, gain massive damage reduction and heal allies on death.",
    },
    {
        "id": "phantom_fox",
        "name": "Phantom Fox",
        "animal": "fox",
        "description": "Its eyes see through walls, through lies, through time. Nothing hides from the Phantom.",
        "stat_bonus": {"spd": 3, "wil": 2},
        "ability": "Reveal all hidden enemies. Dodge chance doubled against abilities. Can see future attacks.",
    },
    {
        "id": "plague_bearer",
        "name": "Plague Bearer",
        "animal": "scorpion",
        "description": "The venom has evolved. It no longer kills — it converts. Everything it touches becomes poison.",
        "stat_bonus": {"atk": 2, "wil": 3},
        "ability": "All attacks apply cascading poison. Poison spreads to adjacent enemies each tick.",
    },
    {
        "id": "alpha",
        "name": "Alpha",
        "animal": "wolf",
        "description": "Not the biggest. Not the fastest. But every creature in the arena knows who leads.",
        "stat_bonus": {"atk": 2, "spd": 2, "wil": 2},
        "ability": "Aura: allies gain +10% all stats. Enemies within range suffer -5% ATK.",
    },
    {
        "id": "living_fortress",
        "name": "Living Fortress",
        "animal": "rhino",
        "description": "Walls of flesh and bone. It does not dodge. It does not retreat. It simply endures.",
        "stat_bonus": {"hp": 6, "atk": 1},
        "ability": "Immune to displacement. Reflect 25% melee damage. Cannot be one-shot.",
    },
    {
        "id": "storm_wing",
        "name": "Storm Wing",
        "animal": "eagle",
        "description": "It doesn't fly — it becomes the wind. Untouchable, inevitable, everywhere.",
        "stat_bonus": {"spd": 4, "atk": 2},
        "ability": "Always acts first. Ranged attacks cost 0 ticks. +50% damage from elevation.",
    },
    {
        "id": "primal_rage",
        "name": "Primal Rage",
        "animal": "boar",
        "description": "Pure fury given form. Rational thought is gone — only the charge remains.",
        "stat_bonus": {"atk": 5, "hp": 2},
        "ability": "Charge attack deals triple damage and stuns. ATK increases by 3% each tick.",
    },
    {
        "id": "void_walker",
        "name": "Void Walker",
        "animal": "panther",
        "description": "It stepped through the threshold and came back... different. Parts of it exist elsewhere now.",
        "stat_bonus": {"spd": 3, "atk": 2, "wil": 1},
        "ability": "Phase through attacks (30% chance). Teleport to any tile. Attacks ignore armor.",
    },
    {
        "id": "trickster_god",
        "name": "Trickster God",
        "animal": "monkey",
        "description": "Chaos incarnate. Every side effect is a gift. Every mutation is a punchline.",
        "stat_bonus": {"wil": 4, "spd": 2},
        "ability": "Randomize one enemy stat each tick. Side effects become beneficial. Immune to debuffs.",
    },
]


def _has_mutation_matching(pet: dict, *keywords: str) -> bool:
    """Check if pet has any mutation (standard, lab, or ultra) with id/name containing any keyword."""
    kws = [k.lower() for k in keywords]

    # Check standard mutations
    for mid in pet.get("mutations", []):
        mid_lower = mid.lower()
        if any(k in mid_lower for k in kws):
            return True

    # Check lab mutations
    lab = pet.get("lab_mutations") or {}
    for slot_key, mut in lab.items():
        if not mut:
            continue
        mut_id = (mut.get("id") or "").lower()
        mut_name = (mut.get("name") or "").lower()
        if any(k in mut_id or k in mut_name for k in kws):
            return True

    return False


def _count_lab_mutations(pet: dict) -> int:
    """Count filled lab mutation slots."""
    lab = pet.get("lab_mutations") or {}
    return sum(1 for v in lab.values() if v)


def _count_lab_tier3(pet: dict) -> int:
    """Count lab mutations from tier 3."""
    lab = pet.get("lab_mutations") or {}
    count = 0
    for v in lab.values():
        if not v:
            continue
        tier = v.get("tier")
        if tier == 3 or (isinstance(v.get("id"), str) and v["id"].startswith("t3_")):
            count += 1
    return count


def _has_side_effect_matching(pet: dict, *keywords: str) -> bool:
    """Check if pet has any side effect with name containing any keyword (case-insensitive)."""
    kws = [k.lower() for k in keywords]
    for se in pet.get("side_effects") or []:
        name = (se.get("name") or "").lower()
        if any(k in name for k in kws):
            return True
    return False


def _has_side_effect_category(pet: dict, category: str) -> bool:
    """Check if pet has any side effect with given category."""
    cat = category.lower()
    for se in pet.get("side_effects") or []:
        if (se.get("category") or "").lower() == cat:
            return True
    return False


def _count_side_effects(pet: dict) -> int:
    """Count all side effects."""
    return len(pet.get("side_effects") or [])


def _has_hp_boosting_mutations(pet: dict, min_count: int = 2) -> bool:
    """Check if pet has mutations that boost HP."""
    count = 0
    hp_keywords = ["hp", "tough", "hide", "battle_scars", "hardened", "survival", "heavy"]

    for mid in pet.get("mutations", []):
        if any(k in mid.lower() for k in hp_keywords):
            count += 1

    lab = pet.get("lab_mutations") or {}
    for v in lab.values():
        if not v:
            continue
        stats = v.get("stats") or {}
        if stats.get("hp", 0) > 0:
            count += 1
        mid = (v.get("id") or "").lower()
        if any(k in mid for k in hp_keywords):
            count += 1

    return count >= min_count


def _has_defensive_mutation(pet: dict) -> bool:
    """Check if pet has any defensive mutation."""
    def_keywords = ["fortress", "armor", "hide", "regenerat", "immortal", "juggernaut",
                    "unkillable", "absorber", "hardened", "symbiotic_armor", "shield"]
    return _has_mutation_matching(pet, *def_keywords)


def _get_stat(pet: dict, stat: str) -> int:
    """Get a stat value from the pet."""
    stats = pet.get("base_stats") or pet.get("stats") or {}
    return stats.get(stat, 0)


def check_apex_form(pet: dict) -> dict | None:
    """Check if a pet qualifies for an Apex Form.

    Returns the apex form dict (with id, name, animal, description, stat_bonus, ability)
    or None if no match.
    """
    animal = (pet.get("animal") or "").lower()

    for apex in APEX_FORMS:
        if apex["animal"] != animal:
            continue

        matched = False

        if apex["id"] == "spectral_stalker":
            # Tiger: shadow/twitch mutation + ambush mutation
            matched = (
                _has_mutation_matching(pet, "shadow", "twitch") and
                _has_mutation_matching(pet, "ambush")
            )

        elif apex["id"] == "the_martyr":
            # Bear: thick_hide/iron mutation + cascade side effect
            matched = (
                _has_mutation_matching(pet, "thick_hide", "iron") and
                _has_side_effect_category(pet, "cascade")
            )

        elif apex["id"] == "phantom_fox":
            # Fox: quick/speed/agile mutation + eye/vision/chromatic side effect
            matched = (
                _has_mutation_matching(pet, "quick", "speed", "agile") and
                _has_side_effect_matching(pet, "eye", "vision", "chromatic")
            )

        elif apex["id"] == "plague_bearer":
            # Scorpion: poison/venom/toxic mutation + cascade side effect
            matched = (
                _has_mutation_matching(pet, "poison", "venom", "toxic") and
                _has_side_effect_category(pet, "cascade")
            )

        elif apex["id"] == "alpha":
            # Wolf: 2+ tier 3 lab mutations
            matched = _count_lab_tier3(pet) >= 2

        elif apex["id"] == "living_fortress":
            # Rhino: 2+ HP-boosting mutations + defensive mutation
            matched = (
                _has_hp_boosting_mutations(pet, 2) and
                _has_defensive_mutation(pet)
            )

        elif apex["id"] == "storm_wing":
            # Eagle: SPD >= 12 + speed/wind/aerial mutation
            matched = (
                _get_stat(pet, "spd") >= 12 and
                _has_mutation_matching(pet, "speed", "wind", "aerial", "fleet", "swift")
            )

        elif apex["id"] == "primal_rage":
            # Boar: ATK >= 12 + charge/fury/rage mutation
            matched = (
                _get_stat(pet, "atk") >= 12 and
                _has_mutation_matching(pet, "charge", "fury", "rage", "frenzy", "berserker")
            )

        elif apex["id"] == "void_walker":
            # Panther: all 3 lab slots filled + instability >= 50
            matched = (
                _count_lab_mutations(pet) >= 3 and
                (pet.get("instability") or 0) >= 50
            )

        elif apex["id"] == "trickster_god":
            # Monkey: 3+ side effects
            matched = _count_side_effects(pet) >= 3

        if matched:
            return dict(apex)

    return None


def calculate_mood(pet: dict) -> str:
    """Calculate mood from recent fight history and state."""
    level = pet.get("level", 1)
    mutations = pet.get("mutations", [])
    fights = pet.get("fights", [])

    # Level 9+ → wise
    if level >= 9:
        return "confident"

    # Just mutated check — if mutations were recently applied
    # (We can't tell timing from data alone, so this is set externally)

    # Last 3 fights analysis
    recent = fights[-3:] if fights else []
    if len(recent) >= 3:
        results = [f["result"] for f in recent]
        if all(r == "win" for r in results):
            return "happy"
        if all(r == "loss" for r in results):
            return "angry"

    if not fights:
        return "tired"

    return "philosophical"


def xp_for_next_level(pet: dict) -> tuple[int, int]:
    """Return (current_xp_in_level, xp_needed_for_next_level).
    If max level, returns (current_xp - L10_threshold, 0).
    """
    level = pet["level"]
    xp = pet["xp"]
    if level >= MAX_LEVEL:
        return xp - LEVEL_THRESHOLDS[MAX_LEVEL], 0
    current_threshold = LEVEL_THRESHOLDS[level]
    next_threshold = LEVEL_THRESHOLDS[level + 1]
    return xp - current_threshold, next_threshold - current_threshold
