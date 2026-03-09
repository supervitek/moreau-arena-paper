"""Morpeton v1.0 interpreter.

Takes a parsed AST + game state → returns an action for the current tick.
First-match-wins for WHEN blocks. Graceful degradation on errors.
"""

from __future__ import annotations

WAIT_ACTION = {"type": "wait"}


def execute(ast: dict, game_state: dict) -> dict:
    """Execute a Morpeton AST against the current game state.

    Args:
        ast: Parsed Morpeton program (from grammar.parse()).
        game_state: Dict with keys like:
            - my_hp: int (0-100, percentage)
            - enemy_hp: int (0-100, percentage)
            - enemy_visible: bool
            - distance: int (hex distance to enemy)
            - my_terrain: str ("high_ground", "cover", "open", etc.)
            - abilities: dict[str, bool] (ability_name -> is_ready)

    Returns:
        Action dict, e.g. {"type": "attack", "target": "enemy"}
        Falls back to WAIT on any error.
    """
    if ast is None:
        return WAIT_ACTION

    when_blocks = ast.get("when_blocks", [])
    default = ast.get("default")

    # First-match-wins: evaluate WHEN blocks top-to-bottom
    for block in when_blocks:
        try:
            if _eval_condition(block["condition"], game_state):
                return _eval_actions(block["actions"], game_state)
        except Exception:
            # Skip broken block at runtime too
            continue

    # No WHEN matched — fall through to DEFAULT
    if default is not None:
        return default

    return WAIT_ACTION


def _eval_condition(cond: dict, state: dict) -> bool:
    """Evaluate a condition AST node against game state."""
    ctype = cond["type"]

    if ctype == "and":
        return _eval_condition(cond["left"], state) and _eval_condition(cond["right"], state)

    if ctype == "or":
        return _eval_condition(cond["left"], state) or _eval_condition(cond["right"], state)

    if ctype == "not":
        return not _eval_condition(cond["operand"], state)

    if ctype == "bool_prop":
        prop = cond["prop"]
        if prop == "enemy.visible":
            return bool(state.get("enemy_visible", False))
        return False

    if ctype == "ability_ready":
        abilities = state.get("abilities", {})
        return bool(abilities.get(cond["ability"], False))

    if ctype == "comparison":
        return _eval_comparison(cond, state)

    return False


def _eval_comparison(cond: dict, state: dict) -> bool:
    """Evaluate a comparison condition."""
    prop = cond["prop"]
    op = cond["op"]
    value = cond["value"]

    # Resolve property value from game state
    prop_val = _resolve_property(prop, state)
    if prop_val is None:
        return False

    # Resolve comparison value
    cmp_val = _resolve_value(value)
    if cmp_val is None:
        return False

    # String comparison
    if isinstance(prop_val, str) or isinstance(cmp_val, str):
        if op == "=":
            return str(prop_val) == str(cmp_val)
        if op == "!=":
            return str(prop_val) != str(cmp_val)
        return False

    # Numeric comparison
    if op == "<":
        return prop_val < cmp_val
    if op == ">":
        return prop_val > cmp_val
    if op == "<=":
        return prop_val <= cmp_val
    if op == ">=":
        return prop_val >= cmp_val
    if op == "=":
        return prop_val == cmp_val
    if op == "!=":
        return prop_val != cmp_val
    return False


def _resolve_property(prop: str, state: dict) -> int | str | None:
    """Resolve a property name to its value from game state."""
    if prop == "my.hp":
        return state.get("my_hp")
    if prop == "enemy.hp":
        return state.get("enemy_hp")
    if prop == "distance":
        return state.get("distance")
    if prop == "my.terrain":
        return state.get("my_terrain")
    return None


def _resolve_value(value: dict) -> int | str | None:
    """Resolve a parsed value node."""
    vtype = value["type"]
    if vtype == "percentage":
        return value["value"]
    if vtype == "number":
        return value["value"]
    if vtype == "string":
        return value["value"]
    return None


def _eval_actions(actions: list[dict], state: dict) -> dict:
    """Evaluate action lines within a matched WHEN block.

    For IF/OTHERWISE, evaluate the nested condition.
    For DO, return the action directly.
    Returns the first resolved action.
    """
    for action_line in actions:
        atype = action_line["type"]

        if atype == "do":
            return action_line["action"]

        if atype == "if":
            if _eval_condition(action_line["condition"], state):
                return action_line["action"]
            elif "otherwise" in action_line:
                return action_line["otherwise"]
            # IF didn't match and no OTHERWISE — continue to next action line
            continue

    return WAIT_ACTION
