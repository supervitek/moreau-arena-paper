"""Morpeton v1.0 test suite — 25+ tests covering parser, interpreter, validator."""

import pytest
from morpeton.grammar import parse
from morpeton.interpreter import execute
from morpeton.validator import validate

# ═══════════════════════════════════════════════════════
# Example programs from the spec
# ═══════════════════════════════════════════════════════

TIGER = """\
PLAN:
  STANCE aggressive
  ENGAGE close_range
  TERRAIN seek_high_ground

EACH TICK:
  WHEN my.hp < 20%:
    IF ability.ready "last_stand" DO USE "last_stand"
    OTHERWISE DO RETREAT nearest.cover

  WHEN enemy.visible AND distance < 2:
    IF ability.ready "pounce" DO USE "pounce" enemy
    OTHERWISE DO ATTACK enemy

  WHEN enemy.visible AND distance >= 2:
    DO MOVE TOWARD enemy

  WHEN NOT enemy.visible:
    DO SCOUT TOWARD enemy.last_seen

  DEFAULT:
    DO MOVE TOWARD nearest.high_ground
"""

PORCUPINE = """\
PLAN:
  STANCE defensive
  ENGAGE mid_range
  TERRAIN use_cover

EACH TICK:
  WHEN my.hp < 30%:
    DO RETREAT nearest.cover

  WHEN enemy.visible AND distance < 2:
    IF ability.ready "quill_burst" DO USE "quill_burst"
    OTHERWISE DO MOVE AWAY_FROM enemy

  WHEN enemy.visible AND distance < 4:
    DO ATTACK enemy

  WHEN NOT enemy.visible:
    DO WAIT

  DEFAULT:
    DO MOVE TOWARD nearest.cover
"""

WOLF = """\
PLAN:
  STANCE mobile
  ENGAGE close_range
  TERRAIN open_field

EACH TICK:
  WHEN my.hp < 25% AND enemy.hp > 50%:
    DO RETREAT nearest.cover

  WHEN enemy.visible AND distance < 2:
    DO ATTACK enemy

  WHEN enemy.visible AND distance >= 2:
    IF ability.ready "howl" DO USE "howl"
    OTHERWISE DO MOVE TOWARD enemy

  WHEN NOT enemy.visible:
    DO SCOUT TOWARD enemy.last_seen

  DEFAULT:
    DO MOVE TOWARD enemy.last_seen
"""


# ═══════════════════════════════════════════════════════
# PARSER TESTS
# ═══════════════════════════════════════════════════════

class TestParserExamples:
    """Spec examples must parse without errors."""

    def test_tiger_parses(self):
        result = parse(TIGER)
        assert result.ast is not None
        assert len(result.errors) == 0
        assert result.ast["plan"]["stance"] == "aggressive"
        assert len(result.ast["when_blocks"]) == 4
        assert result.ast["default"] is not None

    def test_porcupine_parses(self):
        result = parse(PORCUPINE)
        assert result.ast is not None
        assert len(result.errors) == 0
        assert result.ast["plan"]["stance"] == "defensive"
        assert len(result.ast["when_blocks"]) == 4

    def test_wolf_parses(self):
        result = parse(WOLF)
        assert result.ast is not None
        assert len(result.errors) == 0
        assert result.ast["plan"]["stance"] == "mobile"
        assert len(result.ast["when_blocks"]) == 4


class TestParserPlan:
    """PLAN section parsing."""

    def test_plan_fields(self):
        result = parse(TIGER)
        plan = result.ast["plan"]
        assert plan["stance"] == "aggressive"
        assert plan["engage"] == "close_range"
        assert plan["terrain"] == "seek_high_ground"

    def test_missing_plan_defaults(self):
        code = "EACH TICK:\n  WHEN enemy.visible:\n    DO ATTACK enemy"
        result = parse(code)
        assert result.ast is not None
        assert result.ast["plan"]["stance"] == "defensive"

    def test_invalid_stance(self):
        code = "PLAN:\n  STANCE berserk\n\nEACH TICK:\n  DEFAULT:\n    DO WAIT"
        result = parse(code)
        assert any("stance" in e.message.lower() for e in result.errors)


class TestParserConditions:
    """Condition parsing."""

    def test_simple_comparison(self):
        code = "PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN my.hp < 30%:\n    DO RETREAT nearest.cover"
        result = parse(code)
        cond = result.ast["when_blocks"][0]["condition"]
        assert cond["type"] == "comparison"
        assert cond["prop"] == "my.hp"
        assert cond["op"] == "<"
        assert cond["value"] == {"type": "percentage", "value": 30}

    def test_and_condition(self):
        code = "PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN enemy.visible AND distance < 3:\n    DO ATTACK enemy"
        result = parse(code)
        cond = result.ast["when_blocks"][0]["condition"]
        assert cond["type"] == "and"
        assert cond["left"]["type"] == "bool_prop"
        assert cond["right"]["type"] == "comparison"

    def test_not_condition(self):
        code = "PLAN:\n  STANCE defensive\n\nEACH TICK:\n  WHEN NOT enemy.visible:\n    DO WAIT"
        result = parse(code)
        cond = result.ast["when_blocks"][0]["condition"]
        assert cond["type"] == "not"
        assert cond["operand"]["type"] == "bool_prop"

    def test_ability_ready(self):
        code = 'PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN ability.ready "fury":\n    DO USE "fury"'
        result = parse(code)
        cond = result.ast["when_blocks"][0]["condition"]
        assert cond["type"] == "ability_ready"
        assert cond["ability"] == "fury"

    def test_complex_and_or(self):
        code = "PLAN:\n  STANCE mobile\n\nEACH TICK:\n  WHEN my.hp < 25% AND enemy.hp > 50%:\n    DO RETREAT nearest.cover"
        result = parse(code)
        cond = result.ast["when_blocks"][0]["condition"]
        assert cond["type"] == "and"


class TestParserActions:
    """Action parsing."""

    def test_move_toward(self):
        code = "PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN enemy.visible:\n    DO MOVE TOWARD enemy"
        result = parse(code)
        action = result.ast["when_blocks"][0]["actions"][0]["action"]
        assert action["type"] == "move"
        assert action["direction"] == "TOWARD"
        assert action["target"] == "enemy"

    def test_move_away_from(self):
        code = "PLAN:\n  STANCE defensive\n\nEACH TICK:\n  WHEN enemy.visible:\n    DO MOVE AWAY_FROM enemy"
        result = parse(code)
        action = result.ast["when_blocks"][0]["actions"][0]["action"]
        assert action["direction"] == "AWAY_FROM"

    def test_use_with_target(self):
        code = 'PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN enemy.visible:\n    DO USE "pounce" enemy'
        result = parse(code)
        action = result.ast["when_blocks"][0]["actions"][0]["action"]
        assert action["type"] == "use"
        assert action["ability"] == "pounce"
        assert action["target"] == "enemy"

    def test_use_without_target(self):
        code = 'PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN enemy.visible:\n    DO USE "howl"'
        result = parse(code)
        action = result.ast["when_blocks"][0]["actions"][0]["action"]
        assert action["type"] == "use"
        assert action["ability"] == "howl"
        assert "target" not in action

    def test_hex_target(self):
        code = "PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN enemy.visible:\n    DO MOVE TO C4"
        result = parse(code)
        action = result.ast["when_blocks"][0]["actions"][0]["action"]
        assert action["target"] == "C4"

    def test_scout_toward(self):
        code = "PLAN:\n  STANCE aggressive\n\nEACH TICK:\n  WHEN NOT enemy.visible:\n    DO SCOUT TOWARD enemy.last_seen"
        result = parse(code)
        action = result.ast["when_blocks"][0]["actions"][0]["action"]
        assert action["type"] == "scout"
        assert action["target"] == "enemy.last_seen"


class TestParserPartialParse:
    """Partial parse: broken blocks skipped, valid ones kept."""

    def test_broken_block_skipped(self):
        code = """\
PLAN:
  STANCE aggressive

EACH TICK:
  WHEN my.hp < 20%:
    DO RETREAT nearest.cover

  WHEN GARBAGE INVALID SYNTAX:
    DO SOMETHING WRONG

  WHEN enemy.visible:
    DO ATTACK enemy
"""
        result = parse(code)
        assert result.ast is not None
        assert len(result.errors) > 0
        # Should have 2 valid blocks (first and third), skipping the broken one
        assert len(result.ast["when_blocks"]) == 2

    def test_all_blocks_broken(self):
        code = """\
PLAN:
  STANCE aggressive

EACH TICK:
  WHEN INVALID:
    DO NONSENSE

  DEFAULT:
    DO WAIT
"""
        result = parse(code)
        assert result.ast is not None
        assert len(result.ast["when_blocks"]) == 0
        assert result.ast["default"] == {"type": "wait"}

    def test_syntax_validity_metric(self):
        code = """\
PLAN:
  STANCE aggressive

EACH TICK:
  WHEN my.hp < 20%:
    DO RETREAT nearest.cover

  WHEN BROKEN JUNK:
    DO FAIL

  WHEN enemy.visible:
    DO ATTACK enemy
"""
        result = parse(code)
        # 2 of 3 blocks valid
        assert abs(result.syntax_validity - 2 / 3) < 0.01


class TestParserEdgeCases:
    """Edge cases."""

    def test_empty_input(self):
        result = parse("")
        assert result.ast is not None
        assert len(result.ast["when_blocks"]) == 0
        assert len(result.errors) > 0

    def test_only_plan(self):
        code = "PLAN:\n  STANCE aggressive"
        result = parse(code)
        # No EACH TICK section — valid but degenerates to WAIT every tick
        assert result.ast is not None
        assert len(result.ast["when_blocks"]) == 0
        assert result.ast["plan"]["stance"] == "aggressive"

    def test_if_otherwise(self):
        code = """\
PLAN:
  STANCE aggressive

EACH TICK:
  WHEN my.hp < 20%:
    IF ability.ready "last_stand" DO USE "last_stand"
    OTHERWISE DO RETREAT nearest.cover
"""
        result = parse(code)
        assert result.ast is not None
        assert len(result.errors) == 0
        block = result.ast["when_blocks"][0]
        assert block["actions"][0]["type"] == "if"
        assert "otherwise" in block["actions"][0]


# ═══════════════════════════════════════════════════════
# INTERPRETER TESTS
# ═══════════════════════════════════════════════════════

class TestInterpreter:
    """Interpreter: first-match-wins, condition evaluation."""

    def _state(self, **kwargs) -> dict:
        defaults = {
            "my_hp": 100,
            "enemy_hp": 100,
            "enemy_visible": True,
            "distance": 5,
            "my_terrain": "open",
            "abilities": {},
        }
        defaults.update(kwargs)
        return defaults

    def test_first_match_wins(self):
        """First matching WHEN block determines the action."""
        result = parse(TIGER)
        # Tiger at full HP, enemy visible at distance 1 → second WHEN matches
        state = self._state(my_hp=100, enemy_visible=True, distance=1)
        action = execute(result.ast, state)
        # Should ATTACK (no pounce ready)
        assert action["type"] == "attack"

    def test_hp_threshold(self):
        """Low HP triggers retreat."""
        result = parse(TIGER)
        state = self._state(my_hp=15, enemy_visible=True, distance=1)
        action = execute(result.ast, state)
        # First WHEN: my.hp < 20% → IF ability.ready "last_stand"
        # No ability ready → OTHERWISE RETREAT
        assert action["type"] == "retreat"

    def test_ability_ready_if(self):
        """IF branch taken when ability is ready."""
        result = parse(TIGER)
        state = self._state(my_hp=15, abilities={"last_stand": True})
        action = execute(result.ast, state)
        assert action["type"] == "use"
        assert action["ability"] == "last_stand"

    def test_not_visible_scout(self):
        """NOT enemy.visible → SCOUT."""
        result = parse(TIGER)
        state = self._state(enemy_visible=False)
        action = execute(result.ast, state)
        assert action["type"] == "scout"

    def test_default_fallback(self):
        """When no WHEN matches, DEFAULT fires."""
        result = parse(TIGER)
        # Enemy visible but distance >= 2 → third WHEN matches → MOVE TOWARD
        # Actually with Tiger, distance >= 2 AND enemy.visible → third block matches
        # Let's use a state where enemy is visible but no blocks match
        # For tiger, all enemy.visible cases are covered, so use not visible
        # Actually NOT enemy.visible matches 4th block. Let's test DEFAULT differently.
        code = """\
PLAN:
  STANCE defensive

EACH TICK:
  WHEN my.hp < 10%:
    DO WAIT

  DEFAULT:
    DO MOVE TOWARD nearest.cover
"""
        r = parse(code)
        state = self._state(my_hp=50)
        action = execute(r.ast, state)
        assert action["type"] == "move"
        assert action["target"] == "nearest.cover"

    def test_no_match_no_default_waits(self):
        """No WHEN match and no DEFAULT → WAIT."""
        code = "PLAN:\n  STANCE defensive\n\nEACH TICK:\n  WHEN my.hp < 10%:\n    DO RETREAT nearest.cover"
        result = parse(code)
        state = self._state(my_hp=50)
        action = execute(result.ast, state)
        assert action["type"] == "wait"

    def test_empty_ast_waits(self):
        """Empty input → WAIT."""
        result = parse("")
        state = self._state()
        action = execute(result.ast, state)
        assert action["type"] == "wait"

    def test_none_ast_waits(self):
        """None AST → WAIT."""
        action = execute(None, {})
        assert action["type"] == "wait"

    def test_porcupine_kiting(self):
        """Porcupine at close range without quill_burst → MOVE AWAY_FROM."""
        result = parse(PORCUPINE)
        state = self._state(my_hp=80, enemy_visible=True, distance=1)
        action = execute(result.ast, state)
        assert action["type"] == "move"
        assert action["direction"] == "AWAY_FROM"

    def test_porcupine_ranged(self):
        """Porcupine at mid range → ATTACK."""
        result = parse(PORCUPINE)
        state = self._state(my_hp=80, enemy_visible=True, distance=3)
        action = execute(result.ast, state)
        assert action["type"] == "attack"

    def test_wolf_retreat_condition(self):
        """Wolf retreats only when losing (low HP AND enemy > 50%)."""
        result = parse(WOLF)
        # Low HP but enemy also low → doesn't retreat (AND condition fails)
        state = self._state(my_hp=20, enemy_hp=30, enemy_visible=True, distance=1)
        action = execute(result.ast, state)
        # enemy.hp > 50% is false, so first WHEN doesn't match
        # distance < 2 and visible → ATTACK
        assert action["type"] == "attack"

    def test_wolf_retreats_when_losing(self):
        """Wolf retreats when HP low and enemy healthy."""
        result = parse(WOLF)
        state = self._state(my_hp=20, enemy_hp=80, enemy_visible=True, distance=1)
        action = execute(result.ast, state)
        assert action["type"] == "retreat"

    def test_terrain_comparison(self):
        code = """\
PLAN:
  STANCE defensive

EACH TICK:
  WHEN my.terrain = "high_ground":
    DO ATTACK enemy

  DEFAULT:
    DO MOVE TOWARD nearest.high_ground
"""
        result = parse(code)
        state = self._state(my_terrain="high_ground")
        action = execute(result.ast, state)
        assert action["type"] == "attack"

        state2 = self._state(my_terrain="open")
        action2 = execute(result.ast, state2)
        assert action2["type"] == "move"

    def test_distance_gte(self):
        """Test >= operator."""
        result = parse(TIGER)
        state = self._state(enemy_visible=True, distance=5)
        action = execute(result.ast, state)
        # distance >= 2 → MOVE TOWARD enemy
        assert action["type"] == "move"
        assert action["direction"] == "TOWARD"


# ═══════════════════════════════════════════════════════
# VALIDATOR TESTS
# ═══════════════════════════════════════════════════════

class TestValidator:
    """Constraint validation."""

    def test_valid_program(self):
        result = parse(TIGER)
        errors = validate(result.ast, source=TIGER)
        assert errors == []

    def test_too_many_lines(self):
        lines = ["PLAN:", "  STANCE aggressive", "", "EACH TICK:"]
        for i in range(28):
            lines.append(f"  WHEN my.hp < {i}%:")
            lines.append("    DO WAIT")
        source = "\n".join(lines)
        result = parse(source)
        errors = validate(result.ast, source=source)
        assert any(e.code == "MAX_LINES" for e in errors)

    def test_line_too_long(self):
        long_line = "  WHEN " + "enemy.visible AND " * 10 + "distance < 3:"
        source = f"PLAN:\n  STANCE aggressive\n\nEACH TICK:\n{long_line}\n    DO WAIT"
        result = parse(source)
        errors = validate(result.ast, source=source)
        assert any(e.code == "MAX_CHARS" for e in errors)

    def test_too_many_when_blocks(self):
        lines = ["PLAN:", "  STANCE aggressive", "", "EACH TICK:"]
        for i in range(10):
            lines.append(f"  WHEN my.hp < {i + 1}%:")
            lines.append("    DO WAIT")
        source = "\n".join(lines)
        result = parse(source)
        errors = validate(result.ast, source=source)
        assert any(e.code == "MAX_WHEN_BLOCKS" for e in errors)

    def test_custom_limits(self):
        errors = validate(ast=None, source=TIGER, max_lines=10)
        assert any(e.code == "MAX_LINES" for e in errors)

    def test_all_examples_valid(self):
        for name, code in [("Tiger", TIGER), ("Porcupine", PORCUPINE), ("Wolf", WOLF)]:
            result = parse(code)
            errors = validate(result.ast, source=code)
            assert errors == [], f"{name} failed validation: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
