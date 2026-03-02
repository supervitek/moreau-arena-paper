"""Parser for the Moreau Script DSL.

Parses .ms files into an AST of Rule objects. The grammar is:

    IF condition:
      PREFER key=value, key=value
    ELIF condition:
      PREFER key=value, key=value
    ELSE:
      PREFER key=value

Conditions support:
  - opponent.animal == "BEAR"
  - my.hp_pct < 50
  - opponent.last_build.atk > 12
  - AND / OR connectors

PREFER supports:
  - animal="TIGER"
  - atk=MAX, hp=MAX
  - hp=8, atk=6, spd=4, wil=2
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Comparison:
    """A single comparison: e.g. opponent.animal == "BEAR" or my.hp_pct < 50."""
    left: str       # e.g. "opponent.animal", "my.hp_pct", "opponent.last_build.atk"
    operator: str   # "==", "!=", "<", ">", "<=", ">="
    right: str      # e.g. '"BEAR"', '50', '"TIGER"'


@dataclass(frozen=True)
class Condition:
    """A condition that may be a single comparison or a compound (AND/OR).

    For compound conditions, comparisons are joined by the same connector.
    Mixed AND/OR is not supported (keeps the DSL simple).
    """
    comparisons: list[Comparison]
    connector: Literal["AND", "OR", "NONE"] = "NONE"  # NONE = single comparison


@dataclass(frozen=True)
class Preference:
    """A single key=value preference, e.g. animal="TIGER" or atk=MAX."""
    key: str    # "animal", "hp", "atk", "spd", "wil"
    value: str  # '"TIGER"', "MAX", "8"


@dataclass
class Rule:
    """A single IF/ELIF/ELSE block with its condition and preferences."""
    rule_type: Literal["IF", "ELIF", "ELSE"]
    condition: Condition | None  # None for ELSE
    preferences: list[Preference]


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

_COMPARISON_RE = re.compile(
    r'([\w.]+)\s*(==|!=|<=|>=|<|>)\s*("[^"]*"|\d+(?:\.\d+)?)'
)

_PREFER_ITEM_RE = re.compile(
    r'(\w+)\s*=\s*("[^"]*"|MAX|\d+(?:\.\d+)?)'
)

_VALID_OPERATORS = {"==", "!=", "<", ">", "<=", ">="}


def _parse_condition(text: str) -> Condition:
    """Parse a condition string into a Condition AST node."""
    text = text.strip()

    # Detect connector
    if " AND " in text:
        parts = text.split(" AND ")
        connector: Literal["AND", "OR", "NONE"] = "AND"
    elif " OR " in text:
        parts = text.split(" OR ")
        connector = "OR"
    else:
        parts = [text]
        connector = "NONE"

    comparisons: list[Comparison] = []
    for part in parts:
        part = part.strip()
        m = _COMPARISON_RE.match(part)
        if not m:
            raise SyntaxError(f"Invalid condition: {part!r}")
        left, op, right = m.group(1), m.group(2), m.group(3)
        comparisons.append(Comparison(left=left, operator=op, right=right))

    return Condition(comparisons=comparisons, connector=connector)


def _parse_preferences(text: str) -> list[Preference]:
    """Parse a PREFER line into a list of Preference objects."""
    text = text.strip()
    prefs: list[Preference] = []
    for m in _PREFER_ITEM_RE.finditer(text):
        key, value = m.group(1), m.group(2)
        prefs.append(Preference(key=key, value=value))
    if not prefs:
        raise SyntaxError(f"No valid preferences in: {text!r}")
    return prefs


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse(source: str) -> list[Rule]:
    """Parse a Moreau Script source string into a list of Rule objects.

    Args:
        source: The full text of a .ms file.

    Returns:
        A list of Rule objects representing the AST.

    Raises:
        SyntaxError: If the script has invalid syntax.
    """
    rules: list[Rule] = []
    lines = source.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            i += 1
            continue

        # Parse IF/ELIF/ELSE
        if line.startswith("IF ") and line.endswith(":"):
            condition_text = line[3:-1].strip()
            condition = _parse_condition(condition_text)
            rule_type: Literal["IF", "ELIF", "ELSE"] = "IF"
        elif line.startswith("ELIF ") and line.endswith(":"):
            condition_text = line[5:-1].strip()
            condition = _parse_condition(condition_text)
            rule_type = "ELIF"
        elif line.strip() == "ELSE:":
            condition = None
            rule_type = "ELSE"
        else:
            raise SyntaxError(f"Unexpected line (expected IF/ELIF/ELSE): {line!r}")

        # Next line must be PREFER
        i += 1
        while i < len(lines):
            pline = lines[i].strip()
            if not pline or pline.startswith("#"):
                i += 1
                continue
            break
        else:
            raise SyntaxError(f"Expected PREFER after {rule_type}, got end of file")

        if not pline.startswith("PREFER "):
            raise SyntaxError(f"Expected PREFER line, got: {pline!r}")

        prefer_text = pline[7:]  # after "PREFER "
        preferences = _parse_preferences(prefer_text)

        rules.append(Rule(
            rule_type=rule_type,
            condition=condition,
            preferences=preferences,
        ))

        i += 1

    return rules


def parse_file(path: str) -> list[Rule]:
    """Parse a .ms file from disk.

    Args:
        path: Path to the .ms file.

    Returns:
        A list of Rule objects.
    """
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return parse(source)
