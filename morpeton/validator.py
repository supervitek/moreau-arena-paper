"""Morpeton v1.0 validator.

Checks structural constraints: line limits, block counts, nesting depth.
Runs on source text and/or parsed AST.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationError:
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# Constraint defaults (Season 2)
MAX_LINES = 30
MAX_CHARS_PER_LINE = 80
MAX_WHEN_BLOCKS = 8
MAX_NESTING_DEPTH = 2  # WHEN -> IF/OTHERWISE


def validate(
    ast: dict | None = None,
    source: str | None = None,
    *,
    max_lines: int = MAX_LINES,
    max_chars: int = MAX_CHARS_PER_LINE,
    max_when: int = MAX_WHEN_BLOCKS,
) -> list[ValidationError]:
    """Validate Morpeton source and/or AST against constraints.

    Args:
        ast: Parsed AST from grammar.parse().
        source: Raw Morpeton source text.
        max_lines: Maximum allowed lines (default: 30 for S2).
        max_chars: Maximum chars per line (default: 80).
        max_when: Maximum WHEN blocks (default: 8).

    Returns:
        List of ValidationError. Empty list means valid.
    """
    errors: list[ValidationError] = []

    # Source-level checks
    if source is not None:
        lines = source.split("\n")
        # Strip trailing empty lines for line count
        while lines and lines[-1].strip() == "":
            lines.pop()

        if len(lines) > max_lines:
            errors.append(ValidationError(
                "MAX_LINES",
                f"Program has {len(lines)} lines (max {max_lines})"
            ))

        for i, line in enumerate(lines, 1):
            if len(line) > max_chars:
                errors.append(ValidationError(
                    "MAX_CHARS",
                    f"Line {i} has {len(line)} chars (max {max_chars})"
                ))

    # AST-level checks
    if ast is not None:
        when_blocks = ast.get("when_blocks", [])

        total = ast.get("_total_when_blocks", len(when_blocks))
        if total > max_when:
            errors.append(ValidationError(
                "MAX_WHEN_BLOCKS",
                f"Program has {total} WHEN blocks (max {max_when})"
            ))

        # Check nesting depth
        for i, block in enumerate(when_blocks):
            depth = _max_depth(block)
            if depth > MAX_NESTING_DEPTH:
                errors.append(ValidationError(
                    "MAX_NESTING",
                    f"WHEN block {i+1} has nesting depth {depth} (max {MAX_NESTING_DEPTH})"
                ))

    return errors


def _max_depth(block: dict) -> int:
    """Calculate maximum nesting depth of a WHEN block.

    WHEN is depth 1, IF/OTHERWISE inside is depth 2.
    """
    actions = block.get("actions", [])
    max_d = 1
    for action in actions:
        if action.get("type") == "if":
            max_d = max(max_d, 2)
    return max_d
