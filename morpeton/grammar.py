"""Morpeton v1.0 recursive descent parser.

Parses Morpeton source code into an AST (nested dicts/lists).
Implements partial-parse: broken WHEN blocks are skipped and logged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ParseError:
    line: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.message}"


@dataclass
class ParseResult:
    ast: dict | None
    errors: list[ParseError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.ast is not None and not self.errors

    @property
    def syntax_validity(self) -> float:
        """Fraction of WHEN blocks that parsed successfully."""
        if self.ast is None:
            return 0.0
        total = self.ast.get("_total_when_blocks", 0)
        valid = len(self.ast.get("when_blocks", []))
        if total == 0:
            return 1.0
        return valid / total


STANCES = {"aggressive", "defensive", "cautious", "mobile"}
ENGAGEMENTS = {"close_range", "mid_range", "kite"}
TERRAIN_GOALS = {"seek_high_ground", "use_cover", "control_choke", "open_field"}
DIRECTIONS = {"TOWARD", "AWAY_FROM", "TO"}
TARGETS = {"enemy", "nearest.cover", "nearest.high_ground", "enemy.last_seen"}
PROPERTIES = {"my.hp", "enemy.hp", "distance", "my.terrain"}
BOOLEAN_PROPS = {"enemy.visible"}
COMP_OPS = {"<", ">", "<=", ">=", "=", "!="}

_HEX_RE = re.compile(r"^[A-H][1-8]$")


class _Parser:
    """Recursive descent parser for Morpeton v1.0."""

    def __init__(self, source: str) -> None:
        self.lines = source.split("\n")
        self.pos = 0  # current line index
        self.errors: list[ParseError] = []

    @property
    def current_line(self) -> str | None:
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return None

    def peek(self) -> str:
        """Return current line stripped, or empty string if past end."""
        if self.pos < len(self.lines):
            return self.lines[self.pos].strip()
        return ""

    def peek_raw(self) -> str:
        """Return current line unstripped."""
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return ""

    def advance(self) -> str:
        """Consume and return current line (stripped)."""
        line = self.peek()
        self.pos += 1
        return line

    def skip_blank(self) -> None:
        """Skip blank lines."""
        while self.pos < len(self.lines) and self.lines[self.pos].strip() == "":
            self.pos += 1

    def error(self, msg: str) -> ParseError:
        e = ParseError(line=self.pos + 1, message=msg)
        self.errors.append(e)
        return e

    # ── Top-level ──

    def parse_program(self) -> dict:
        self.skip_blank()
        plan = self._parse_plan()
        self.skip_blank()
        when_blocks, default_block, total_when = self._parse_each_tick()
        return {
            "plan": plan,
            "when_blocks": when_blocks,
            "default": default_block,
            "_total_when_blocks": total_when,
        }

    # ── PLAN section ──

    def _parse_plan(self) -> dict:
        plan = {"stance": "defensive", "engage": "close_range", "terrain": "open_field"}
        if self.peek() != "PLAN:":
            return plan
        self.advance()  # consume PLAN:
        while self.pos < len(self.lines):
            raw = self.peek_raw()
            stripped = raw.strip()
            if stripped == "" or not raw.startswith("  "):
                break
            if stripped.startswith("STANCE "):
                val = stripped[7:].strip()
                if val in STANCES:
                    plan["stance"] = val
                else:
                    self.error(f"Invalid stance: {val}")
            elif stripped.startswith("ENGAGE "):
                val = stripped[7:].strip()
                if val in ENGAGEMENTS:
                    plan["engage"] = val
                else:
                    self.error(f"Invalid engagement: {val}")
            elif stripped.startswith("TERRAIN "):
                val = stripped[8:].strip()
                if val in TERRAIN_GOALS:
                    plan["terrain"] = val
                else:
                    self.error(f"Invalid terrain goal: {val}")
            else:
                self.error(f"Unknown PLAN field: {stripped}")
            self.advance()
        return plan

    # ── EACH TICK section ──

    def _parse_each_tick(self) -> tuple[list[dict], dict | None, int]:
        when_blocks: list[dict] = []
        default_block: dict | None = None
        total_when = 0

        if self.peek() != "EACH TICK:":
            if self.pos < len(self.lines):
                self.error(f"Expected 'EACH TICK:', got '{self.peek()}'")
            return when_blocks, default_block, total_when
        self.advance()  # consume EACH TICK:

        while self.pos < len(self.lines):
            self.skip_blank()
            if self.pos >= len(self.lines):
                break
            stripped = self.peek()
            if stripped.startswith("WHEN "):
                total_when += 1
                saved_pos = self.pos
                saved_errors = len(self.errors)
                try:
                    block = self._parse_when_block()
                    when_blocks.append(block)
                except _BlockParseError as e:
                    # Partial parse: skip this broken block
                    self.error(f"Skipping malformed WHEN block: {e}")
                    # Trim errors added inside the failed block
                    self.errors = self.errors[: saved_errors + 1]
                    # Skip lines until next WHEN/DEFAULT/end
                    self._skip_to_next_block()
            elif stripped == "DEFAULT:":
                default_block = self._parse_default_block()
            else:
                # Unknown line at top level of EACH TICK
                self.error(f"Unexpected line in EACH TICK: {stripped}")
                self.advance()

        return when_blocks, default_block, total_when

    def _parse_when_block(self) -> dict:
        line = self.peek()
        # Extract condition between WHEN and :
        if not line.startswith("WHEN ") or not line.endswith(":"):
            raise _BlockParseError(f"Bad WHEN syntax: {line}")

        cond_str = line[5:-1].strip()
        condition = self._parse_condition(cond_str)
        self.advance()

        actions: list[dict] = []
        while self.pos < len(self.lines):
            raw = self.peek_raw()
            stripped = raw.strip()
            if stripped == "":
                break
            # Check indentation — must be inside the WHEN block
            if not raw.startswith("    ") and not raw.startswith("\t"):
                break
            # Also break if we hit a new top-level keyword at 2-indent
            if raw.startswith("  ") and not raw.startswith("    "):
                break

            if stripped.startswith("IF "):
                actions.append(self._parse_if_line(stripped))
            elif stripped.startswith("DO "):
                action = self._parse_action(stripped[3:].strip())
                actions.append({"type": "do", "action": action})
            elif stripped.startswith("OTHERWISE DO "):
                # OTHERWISE should be handled inside _parse_if_line
                # but if we encounter it standalone, attach to previous IF
                if actions and actions[-1]["type"] == "if":
                    otherwise_action = self._parse_action(stripped[13:].strip())
                    actions[-1]["otherwise"] = otherwise_action
                else:
                    raise _BlockParseError(f"OTHERWISE without IF: {stripped}")
            else:
                raise _BlockParseError(f"Bad action line: {stripped}")
            self.advance()

        if not actions:
            raise _BlockParseError("WHEN block has no actions")

        return {"condition": condition, "actions": actions}

    def _parse_if_line(self, line: str) -> dict:
        # IF <condition> DO <action>
        # Find the DO keyword that separates condition from action
        do_idx = line.find(" DO ")
        if do_idx == -1:
            raise _BlockParseError(f"IF without DO: {line}")

        cond_str = line[3:do_idx].strip()
        action_str = line[do_idx + 4:].strip()

        condition = self._parse_condition(cond_str)
        action = self._parse_action(action_str)

        result: dict = {"type": "if", "condition": condition, "action": action}

        # Check next line for OTHERWISE
        if self.pos + 1 < len(self.lines):
            next_stripped = self.lines[self.pos + 1].strip()
            if next_stripped.startswith("OTHERWISE DO "):
                self.advance()
                otherwise_action = self._parse_action(next_stripped[13:].strip())
                result["otherwise"] = otherwise_action

        return result

    def _parse_default_block(self) -> dict:
        self.advance()  # consume DEFAULT:
        while self.pos < len(self.lines):
            stripped = self.peek().strip()
            if stripped == "":
                self.advance()
                continue
            if stripped.startswith("DO "):
                action = self._parse_action(stripped[3:].strip())
                self.advance()
                return action
            break
        self.error("DEFAULT block has no DO action")
        return {"type": "wait"}

    def _skip_to_next_block(self) -> None:
        """Skip lines until we hit the next WHEN/DEFAULT or end."""
        # Always advance at least one line to avoid infinite loops
        # when the WHEN line itself fails to parse
        self.advance()
        while self.pos < len(self.lines):
            stripped = self.peek()
            raw = self.peek_raw()
            # Stop at next WHEN or DEFAULT at the right indent level
            if stripped.startswith("WHEN ") and raw.startswith("  ") and not raw.startswith("    "):
                break
            if stripped == "DEFAULT:":
                break
            self.advance()

    # ── Condition parsing ──

    def _parse_condition(self, s: str) -> dict:
        s = s.strip()
        if not s:
            raise _BlockParseError("Empty condition")
        tokens = self._tokenize_condition(s)
        result, remaining = self._parse_or_expr(tokens)
        if remaining:
            raise _BlockParseError(f"Unexpected tokens in condition: {' '.join(remaining)}")
        return result

    def _tokenize_condition(self, s: str) -> list[str]:
        """Tokenize a condition string, keeping quoted strings as single tokens."""
        tokens: list[str] = []
        i = 0
        while i < len(s):
            if s[i] == " ":
                i += 1
                continue
            if s[i] == '"':
                j = s.index('"', i + 1)
                tokens.append(s[i : j + 1])
                i = j + 1
            elif s[i] in "()":
                tokens.append(s[i])
                i += 1
            elif s[i:i+2] in ("<=", ">=", "!="):
                tokens.append(s[i:i+2])
                i += 2
            elif s[i] in "<>=":
                tokens.append(s[i])
                i += 1
            else:
                j = i
                while j < len(s) and s[j] not in ' ()"' and s[j:j+2] not in ("<=", ">=", "!=") and s[j] not in "<>=":
                    j += 1
                tokens.append(s[i:j])
                i = j
        return tokens

    def _parse_or_expr(self, tokens: list[str]) -> tuple[dict, list[str]]:
        left, tokens = self._parse_and_expr(tokens)
        while tokens and tokens[0] == "OR":
            tokens = tokens[1:]  # consume OR
            right, tokens = self._parse_and_expr(tokens)
            left = {"type": "or", "left": left, "right": right}
        return left, tokens

    def _parse_and_expr(self, tokens: list[str]) -> tuple[dict, list[str]]:
        left, tokens = self._parse_not_expr(tokens)
        while tokens and tokens[0] == "AND":
            tokens = tokens[1:]  # consume AND
            right, tokens = self._parse_not_expr(tokens)
            left = {"type": "and", "left": left, "right": right}
        return left, tokens

    def _parse_not_expr(self, tokens: list[str]) -> tuple[dict, list[str]]:
        if tokens and tokens[0] == "NOT":
            tokens = tokens[1:]
            operand, tokens = self._parse_atom(tokens)
            return {"type": "not", "operand": operand}, tokens
        return self._parse_atom(tokens)

    def _parse_atom(self, tokens: list[str]) -> tuple[dict, list[str]]:
        if not tokens:
            raise _BlockParseError("Unexpected end of condition")

        # Parenthesized expression
        if tokens[0] == "(":
            tokens = tokens[1:]
            expr, tokens = self._parse_or_expr(tokens)
            if not tokens or tokens[0] != ")":
                raise _BlockParseError("Missing closing parenthesis")
            return expr, tokens[1:]

        # Boolean property: enemy.visible
        if tokens[0] == "enemy.visible":
            return {"type": "bool_prop", "prop": "enemy.visible"}, tokens[1:]

        # ability.ready "name"
        if tokens[0] == "ability.ready":
            if len(tokens) < 2 or not tokens[1].startswith('"'):
                raise _BlockParseError("ability.ready requires quoted ability name")
            return {"type": "ability_ready", "ability": tokens[1].strip('"')}, tokens[2:]

        # Comparison: property op value
        if tokens[0] in PROPERTIES:
            prop = tokens[0]
            if len(tokens) < 3:
                raise _BlockParseError(f"Incomplete comparison for {prop}")
            op = tokens[1]
            if op not in COMP_OPS:
                raise _BlockParseError(f"Invalid operator: {op}")
            val_str = tokens[2]
            value = self._parse_value(val_str)
            return {"type": "comparison", "prop": prop, "op": op, "value": value}, tokens[3:]

        raise _BlockParseError(f"Unexpected condition token: {tokens[0]}")

    def _parse_value(self, s: str) -> dict:
        if s.endswith("%"):
            try:
                return {"type": "percentage", "value": int(s[:-1])}
            except ValueError:
                raise _BlockParseError(f"Invalid percentage: {s}")
        if s.startswith('"') and s.endswith('"'):
            return {"type": "string", "value": s[1:-1]}
        try:
            return {"type": "number", "value": int(s)}
        except ValueError:
            raise _BlockParseError(f"Invalid value: {s}")

    # ── Action parsing ──

    def _parse_action(self, s: str) -> dict:
        s = s.strip()
        if s == "WAIT":
            return {"type": "wait"}

        if s.startswith("MOVE "):
            rest = s[5:]
            for d in sorted(DIRECTIONS, key=len, reverse=True):
                if rest.startswith(d + " "):
                    target = self._parse_target(rest[len(d) + 1:].strip())
                    return {"type": "move", "direction": d, "target": target}
            raise _BlockParseError(f"Invalid MOVE direction: {rest}")

        if s.startswith("ATTACK "):
            target = self._parse_target(s[7:].strip())
            return {"type": "attack", "target": target}

        if s.startswith("USE "):
            rest = s[4:].strip()
            if not rest.startswith('"'):
                raise _BlockParseError(f"USE requires quoted ability name: {rest}")
            end_quote = rest.index('"', 1)
            ability = rest[1:end_quote]
            remainder = rest[end_quote + 1:].strip()
            result: dict = {"type": "use", "ability": ability}
            if remainder:
                result["target"] = self._parse_target(remainder)
            return result

        if s.startswith("RETREAT "):
            target = self._parse_target(s[8:].strip())
            return {"type": "retreat", "target": target}

        if s.startswith("SCOUT TOWARD "):
            target = self._parse_target(s[13:].strip())
            return {"type": "scout", "target": target}

        raise _BlockParseError(f"Unknown action: {s}")

    def _parse_target(self, s: str) -> str:
        s = s.strip()
        if s in TARGETS:
            return s
        if _HEX_RE.match(s):
            return s
        raise _BlockParseError(f"Unknown target: {s}")


class _BlockParseError(Exception):
    """Raised when a single WHEN block fails to parse."""


def parse(source: str) -> ParseResult:
    """Parse Morpeton source code into an AST.

    Returns a ParseResult with the AST and any errors.
    Implements partial-parse: broken WHEN blocks are skipped.
    """
    source = source.strip()
    if not source:
        return ParseResult(
            ast={"plan": {"stance": "defensive", "engage": "close_range", "terrain": "open_field"},
                 "when_blocks": [], "default": None, "_total_when_blocks": 0},
            errors=[ParseError(line=1, message="Empty input")]
        )

    parser = _Parser(source)
    try:
        ast = parser.parse_program()
    except Exception as e:
        return ParseResult(ast=None, errors=[ParseError(line=parser.pos + 1, message=str(e))])

    return ParseResult(ast=ast, errors=parser.errors)
