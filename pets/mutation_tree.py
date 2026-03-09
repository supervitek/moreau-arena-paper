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
