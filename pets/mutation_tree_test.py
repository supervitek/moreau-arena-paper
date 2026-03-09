"""Tests for the Moreau Pets mutation tree system."""

import pytest
from pets.mutation_tree import (
    create_pet,
    add_xp,
    get_available_mutations,
    apply_mutation,
    get_effective_stats,
    get_mutation_tree,
    calculate_mood,
    xp_for_next_level,
    LEVEL_THRESHOLDS,
)


# ---- create_pet ----

def test_create_pet_valid():
    pet = create_pet("Shadow", "fox", 5, 7, 6, 2)
    assert pet["name"] == "Shadow"
    assert pet["animal"] == "fox"
    assert pet["level"] == 1
    assert pet["xp"] == 0
    assert pet["base_stats"] == {"hp": 5, "atk": 7, "spd": 6, "wil": 2}
    assert pet["mutations"] == []
    assert pet["fights"] == []


def test_create_pet_invalid_stats_sum():
    with pytest.raises(ValueError, match="Stats must sum to 20"):
        create_pet("Bad", "bear", 5, 5, 5, 6)


def test_create_pet_stat_below_minimum():
    with pytest.raises(ValueError, match="must be >= 1"):
        create_pet("Bad", "bear", 0, 8, 6, 6)


def test_create_pet_invalid_animal():
    with pytest.raises(ValueError, match="Invalid animal"):
        create_pet("Bad", "dragon", 5, 5, 5, 5)


def test_create_pet_empty_name():
    with pytest.raises(ValueError, match="cannot be empty"):
        create_pet("", "fox", 5, 5, 5, 5)


# ---- add_xp ----

def test_add_xp_level_up_at_threshold():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    pet, leveled = add_xp(pet, 100)  # L3 threshold
    assert pet["level"] == 3
    assert pet["xp"] == 100
    assert leveled is True


def test_add_xp_no_level_up():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    pet, leveled = add_xp(pet, 30)
    assert pet["level"] == 1
    assert leveled is False


def test_add_xp_incremental():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 50)  # L2
    assert pet["level"] == 2
    pet, leveled = add_xp(pet, 50)  # L3
    assert pet["level"] == 3
    assert leveled is True


# ---- get_available_mutations ----

def test_mutations_at_l3():
    pet = create_pet("Test", "tiger", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 100)
    muts = get_available_mutations(pet)
    assert len(muts) == 3
    ids = {m["id"] for m in muts}
    assert ids == {"blood_rage", "thick_hide", "quick_feet"}


def test_mutations_at_l6_after_bloodrage():
    pet = create_pet("Test", "tiger", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 300)
    pet = apply_mutation(pet, "blood_rage")
    muts = get_available_mutations(pet)
    assert len(muts) == 2
    ids = {m["id"] for m in muts}
    assert ids == {"frenzy", "intimidate"}


def test_mutations_at_l6_after_thick_hide():
    pet = create_pet("Test", "wolf", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 300)
    pet = apply_mutation(pet, "thick_hide")
    muts = get_available_mutations(pet)
    ids = {m["id"] for m in muts}
    assert ids == {"regeneration", "fortress"}


def test_mutations_at_l6_after_quick_feet():
    pet = create_pet("Test", "eagle", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 300)
    pet = apply_mutation(pet, "quick_feet")
    muts = get_available_mutations(pet)
    ids = {m["id"] for m in muts}
    assert ids == {"ambush", "evasion"}


def test_no_mutations_below_l3():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 50)
    assert get_available_mutations(pet) == []


def test_cant_apply_unavailable_mutation():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 100)
    with pytest.raises(ValueError, match="not available"):
        apply_mutation(pet, "frenzy")  # L6 mutation at L3


def test_cant_apply_same_mutation_twice():
    pet = create_pet("Test", "tiger", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 300)
    pet = apply_mutation(pet, "blood_rage")
    with pytest.raises(ValueError, match="not available"):
        apply_mutation(pet, "blood_rage")


# ---- full path L3 → L6 → L9 ----

def test_full_mutation_path():
    pet = create_pet("Fury", "bear", 5, 7, 5, 3)
    pet, _ = add_xp(pet, 600)  # L9
    # L3
    pet = apply_mutation(pet, "blood_rage")
    assert pet["mutations"] == ["blood_rage"]
    assert pet["base_stats"]["atk"] == 9  # 7 + 2
    assert pet["base_stats"]["spd"] == 4  # 5 - 1
    # L6
    pet = apply_mutation(pet, "frenzy")
    assert pet["mutations"] == ["blood_rage", "frenzy"]
    # L9 — destiny (only one option)
    muts = get_available_mutations(pet)
    assert len(muts) == 1
    assert muts[0]["id"] == "berserker"
    pet = apply_mutation(pet, "berserker")
    assert pet["mutations"] == ["blood_rage", "frenzy", "berserker"]
    # No more mutations available
    assert get_available_mutations(pet) == []


# ---- get_effective_stats ----

def test_effective_stats():
    pet = create_pet("Test", "fox", 5, 7, 6, 2)
    stats = get_effective_stats(pet)
    assert stats["max_hp"] == 100  # 50 + 5*10
    assert stats["base_dmg"] == 6  # 7 - 1
    assert stats["dodge_pct"] == 15.0  # 6 * 2.5
    assert abs(stats["resist_pct"] - 6.6) < 0.1  # 2 * 3.3


def test_effective_stats_after_mutation():
    pet = create_pet("Test", "fox", 5, 7, 6, 2)
    pet, _ = add_xp(pet, 100)
    pet = apply_mutation(pet, "blood_rage")
    stats = get_effective_stats(pet)
    assert stats["base_dmg"] == 8  # (7+2) - 1
    assert stats["dodge_pct"] == 12.5  # (6-1) * 2.5


# ---- mood calculation ----

def test_mood_3_wins():
    pet = create_pet("Test", "tiger", 5, 5, 5, 5)
    pet["fights"] = [
        {"opponent": "A", "result": "win", "ticks": 30},
        {"opponent": "B", "result": "win", "ticks": 25},
        {"opponent": "C", "result": "win", "ticks": 20},
    ]
    assert calculate_mood(pet) == "happy"


def test_mood_3_losses():
    pet = create_pet("Test", "tiger", 5, 5, 5, 5)
    pet["fights"] = [
        {"opponent": "A", "result": "loss", "ticks": 30},
        {"opponent": "B", "result": "loss", "ticks": 25},
        {"opponent": "C", "result": "loss", "ticks": 20},
    ]
    assert calculate_mood(pet) == "angry"


def test_mood_no_fights():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    assert calculate_mood(pet) == "tired"


def test_mood_level_9():
    pet = create_pet("Test", "fox", 5, 5, 5, 5)
    pet["level"] = 9
    assert calculate_mood(pet) == "confident"


# ---- mutation tree structure ----

def test_mutation_tree_structure():
    tree = get_mutation_tree()
    assert len(tree["level_3"]) == 3
    assert len(tree["level_6"]) == 6
    assert len(tree["level_9"]) == 6


# ---- xp_for_next_level ----

def test_xp_for_next_level():
    pet = create_pet("Test", "bear", 5, 5, 5, 5)
    pet, _ = add_xp(pet, 60)  # L2
    current, needed = xp_for_next_level(pet)
    assert current == 10  # 60 - 50
    assert needed == 50  # 100 - 50
