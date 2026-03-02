"""Moreau Script DSL — a safe domain-specific language for creature combat strategies.

Parse, validate, and execute .ms scripts that produce Moreau Arena builds.
"""

__all__ = ["parse", "validate", "interpret", "Rule", "Condition", "Preference"]


def __getattr__(name: str):  # noqa: ANN001
    """Lazy imports to avoid circular / runpy warnings."""
    if name in ("parse", "Rule", "Condition", "Preference"):
        from moreau_script.parser import parse, Rule, Condition, Preference
        return {"parse": parse, "Rule": Rule, "Condition": Condition, "Preference": Preference}[name]
    if name == "validate":
        from moreau_script.validator import validate
        return validate
    if name == "interpret":
        from moreau_script.interpreter import interpret
        return interpret
    raise AttributeError(f"module 'moreau_script' has no attribute {name!r}")
