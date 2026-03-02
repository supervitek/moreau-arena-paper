"""Sandboxed interpreter for Moreau Script DSL.

Takes parsed rules + game context and produces a build dict.
Uses iteration count limit (not threading) for safety.

Game context provides:
  - opponent.animal: str or None
  - opponent.last_build: dict with hp/atk/spd/wil or None
  - my.hp_pct: int (always 100 at start of game)

Usage:
    python -m moreau_script.interpreter moreau_script/examples/counter_pick.ms
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from typing import Any

from moreau_script.parser import Rule, Condition, Comparison, parse_file
from moreau_script.validator import VALID_ANIMALS

# Max iterations to prevent infinite loops (100ms-equivalent safety)
MAX_ITERATIONS = 10_000

# Default build when nothing matches
DEFAULT_ANIMAL = "BEAR"
DEFAULT_STATS = {"hp": 5, "atk": 5, "spd": 5, "wil": 5}

# Valid animals list for random selection
_ANIMALS_LIST = sorted(VALID_ANIMALS)


@dataclass
class GameContext:
    """Context passed to the interpreter for condition evaluation."""
    opponent_animal: str | None = None
    opponent_last_build: dict[str, int] | None = None
    my_hp_pct: int = 100


def _resolve_ref(ref: str, ctx: GameContext) -> Any:
    """Resolve a dotted reference (e.g. 'opponent.animal') against the context."""
    if ref == "opponent.animal":
        return ctx.opponent_animal
    elif ref == "my.hp_pct":
        return ctx.my_hp_pct
    elif ref.startswith("opponent.last_build."):
        stat = ref.split(".")[-1]
        if ctx.opponent_last_build is None:
            return None
        return ctx.opponent_last_build.get(stat)
    return None


def _coerce_value(raw: str) -> Any:
    """Coerce a right-hand value from the AST to a Python value."""
    # Quoted string -> strip quotes, upper
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].upper()
    # Numeric
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _eval_comparison(comp: Comparison, ctx: GameContext) -> bool:
    """Evaluate a single comparison against the game context."""
    left_val = _resolve_ref(comp.left, ctx)
    right_val = _coerce_value(comp.right)

    # If left is None (e.g. no opponent info), comparison fails
    if left_val is None:
        return False

    # Normalize animal names to uppercase for comparison
    if isinstance(left_val, str):
        left_val = left_val.upper()

    op = comp.operator
    if op == "==":
        return left_val == right_val
    elif op == "!=":
        return left_val != right_val
    elif op == "<":
        return left_val < right_val
    elif op == ">":
        return left_val > right_val
    elif op == "<=":
        return left_val <= right_val
    elif op == ">=":
        return left_val >= right_val

    return False


def _eval_condition(cond: Condition, ctx: GameContext) -> bool:
    """Evaluate a compound condition against the game context."""
    if cond.connector == "AND":
        return all(_eval_comparison(c, ctx) for c in cond.comparisons)
    elif cond.connector == "OR":
        return any(_eval_comparison(c, ctx) for c in cond.comparisons)
    else:  # NONE — single comparison
        if not cond.comparisons:
            return False
        return _eval_comparison(cond.comparisons[0], ctx)


def _apply_preferences(
    preferences: list,
) -> dict[str, Any]:
    """Convert a list of Preference objects into a build dict.

    Handles:
      - animal="TIGER" -> pick that animal
      - atk=MAX -> allocate max points to atk after minimums
      - hp=8 -> set hp to 8
    """
    build: dict[str, Any] = {}
    max_stats: list[str] = []

    for pref in preferences:
        if pref.key == "animal":
            build["animal"] = pref.value.strip('"').upper()
        elif pref.value == "MAX":
            max_stats.append(pref.key)
        else:
            try:
                build[pref.key] = int(pref.value)
            except ValueError:
                pass  # skip invalid

    # Default animal if not specified
    if "animal" not in build:
        build["animal"] = random.choice(_ANIMALS_LIST)

    # Allocate stats
    stat_names = ["hp", "atk", "spd", "wil"]

    # Start with minimums for unspecified stats
    for s in stat_names:
        if s not in build and s not in max_stats:
            build[s] = 1

    # Calculate remaining points
    total = 20
    used = sum(build.get(s, 0) for s in stat_names if s in build)
    remaining = total - used

    if max_stats:
        # Distribute remaining equally among MAX stats, last one gets remainder
        per_stat = remaining // len(max_stats)
        leftover = remaining - per_stat * len(max_stats)
        for i, s in enumerate(max_stats):
            if i == len(max_stats) - 1:
                build[s] = max(1, per_stat + leftover)
            else:
                build[s] = max(1, per_stat)
    else:
        # If stats don't sum to 20, adjust the last unspecified stat
        current_total = sum(build.get(s, 1) for s in stat_names)
        if current_total != 20:
            # Find a stat we can adjust (prefer one that wasn't explicitly set)
            diff = 20 - current_total
            # Try to add to wil first, then spd, then hp, then atk
            for adjust_stat in ["wil", "spd", "hp", "atk"]:
                new_val = build.get(adjust_stat, 1) + diff
                if new_val >= 1:
                    build[adjust_stat] = new_val
                    break

    return build


def interpret(
    rules: list[Rule],
    ctx: GameContext | None = None,
) -> dict[str, Any]:
    """Execute parsed rules against a game context and produce a build dict.

    Args:
        rules: Parsed list of Rule objects.
        ctx: Game context for condition evaluation. Defaults to empty context.

    Returns:
        A build dict with keys: animal, hp, atk, spd, wil.
    """
    if ctx is None:
        ctx = GameContext()

    iterations = 0

    for rule in rules:
        iterations += 1
        if iterations > MAX_ITERATIONS:
            break

        if rule.rule_type == "ELSE":
            # ELSE always matches
            return _apply_preferences(rule.preferences)
        elif rule.condition is not None:
            if _eval_condition(rule.condition, ctx):
                return _apply_preferences(rule.preferences)

    # No rule matched — return default
    return {
        "animal": random.choice(_ANIMALS_LIST),
        "hp": 5,
        "atk": 5,
        "spd": 5,
        "wil": 5,
    }


def interpret_file(
    path: str,
    ctx: GameContext | None = None,
) -> dict[str, Any]:
    """Parse and interpret a .ms file.

    Args:
        path: Path to the .ms file.
        ctx: Game context. Defaults to empty context.

    Returns:
        A build dict.
    """
    rules = parse_file(path)
    return interpret(rules, ctx)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m moreau_script.interpreter <script.ms>")
        print("       python -m moreau_script.interpreter script.ms [opponent_animal]")
        sys.exit(1)

    script_path = sys.argv[1]
    opponent_animal = sys.argv[2].upper() if len(sys.argv) > 2 else None

    ctx = GameContext(opponent_animal=opponent_animal)
    build = interpret_file(script_path, ctx)
    print(f"Build: {build}")
