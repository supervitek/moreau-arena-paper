"""Morpeton v1.0 — Domain-specific language for Moreau Arena Season 2.

Usage:
    from morpeton import parse, validate, execute

    result = parse(morpeton_code)
    errors = validate(result.ast, source=morpeton_code)
    action = execute(result.ast, game_state)
"""

from morpeton.grammar import parse, ParseResult, ParseError
from morpeton.interpreter import execute
from morpeton.validator import validate, ValidationError

__all__ = [
    "parse",
    "validate",
    "execute",
    "ParseResult",
    "ParseError",
    "ValidationError",
]
