"""Validator for Moreau Script DSL.

Checks parsed scripts for:
  - Max 50 rules
  - No forbidden constructs (eval, import, exec, open, os, sys, subprocess, socket)
  - Only allowed left-hand side references in conditions
  - Only allowed preference keys
  - Valid animal names in preferences
  - Stat values that are plausible (1-17)
"""

from __future__ import annotations

from moreau_script.parser import Rule, Condition, Comparison, Preference

# Valid animals from the Moreau Arena config (the 14 core animals)
VALID_ANIMALS = frozenset({
    "BEAR", "BUFFALO", "BOAR", "TIGER", "WOLF", "MONKEY",
    "CROCODILE", "EAGLE", "SNAKE", "RAVEN", "SHARK", "OWL",
    "FOX", "SCORPION",
})

# Allowed left-hand references in conditions
VALID_CONDITION_LHSS = frozenset({
    "opponent.animal",
    "opponent.last_build.hp",
    "opponent.last_build.atk",
    "opponent.last_build.spd",
    "opponent.last_build.wil",
    "my.hp_pct",
})

# Allowed preference keys
VALID_PREF_KEYS = frozenset({"animal", "hp", "atk", "spd", "wil"})

# Forbidden words in raw source (checked at source level)
FORBIDDEN_WORDS = frozenset({
    "eval", "exec", "import", "open", "os", "sys",
    "subprocess", "socket", "__", "compile", "globals",
    "locals", "getattr", "setattr", "delattr", "network",
})

MAX_RULES = 50


def validate(rules: list[Rule], source: str | None = None) -> list[str]:
    """Validate a parsed Moreau Script.

    Args:
        rules: The parsed list of Rule objects.
        source: Optional raw source text for additional safety checks.

    Returns:
        A list of error strings. Empty list means the script is valid.
    """
    errors: list[str] = []

    # Check rule count
    if len(rules) > MAX_RULES:
        errors.append(f"Too many rules: {len(rules)} (max {MAX_RULES})")

    # Check raw source for forbidden words
    if source is not None:
        source_lower = source.lower()
        for word in FORBIDDEN_WORDS:
            if word in source_lower:
                errors.append(f"Forbidden construct found in source: {word!r}")

    # Validate structure: first rule should be IF or ELSE
    if rules:
        first = rules[0]
        if first.rule_type not in ("IF", "ELSE"):
            errors.append(
                f"First rule must be IF or ELSE, got {first.rule_type}"
            )

    # Check each rule
    for idx, rule in enumerate(rules):
        rule_label = f"Rule {idx + 1} ({rule.rule_type})"

        # ELSE should not have a condition
        if rule.rule_type == "ELSE" and rule.condition is not None:
            errors.append(f"{rule_label}: ELSE should not have a condition")

        # IF/ELIF must have a condition
        if rule.rule_type in ("IF", "ELIF") and rule.condition is None:
            errors.append(f"{rule_label}: {rule.rule_type} requires a condition")

        # Validate condition references
        if rule.condition is not None:
            for comp in rule.condition.comparisons:
                if comp.left not in VALID_CONDITION_LHSS:
                    errors.append(
                        f"{rule_label}: Unknown condition reference: {comp.left!r}"
                    )

                # If comparing to a string, validate it looks like an animal
                if comp.left == "opponent.animal":
                    # Strip quotes for validation
                    val = comp.right.strip('"')
                    if val not in VALID_ANIMALS:
                        errors.append(
                            f"{rule_label}: Unknown animal in condition: {val!r}"
                        )

        # Validate preferences
        for pref in rule.preferences:
            if pref.key not in VALID_PREF_KEYS:
                errors.append(
                    f"{rule_label}: Unknown preference key: {pref.key!r}"
                )

            if pref.key == "animal":
                val = pref.value.strip('"')
                if val not in VALID_ANIMALS:
                    errors.append(
                        f"{rule_label}: Unknown animal: {val!r}"
                    )

            elif pref.key in ("hp", "atk", "spd", "wil"):
                if pref.value != "MAX":
                    try:
                        v = int(pref.value)
                        if v < 1 or v > 17:
                            errors.append(
                                f"{rule_label}: Stat {pref.key}={v} out of range (1-17)"
                            )
                    except ValueError:
                        errors.append(
                            f"{rule_label}: Invalid stat value for {pref.key}: {pref.value!r}"
                        )

    return errors
