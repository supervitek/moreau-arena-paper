"""Entry point for running Moreau Script files.

Usage:
    python -m moreau_script <script.ms> [opponent_animal]

Examples:
    python -m moreau_script moreau_script/examples/counter_pick.ms
    python -m moreau_script moreau_script/examples/counter_pick.ms BEAR
    python -m moreau_script moreau_script/examples/stat_optimizer.ms
"""

from __future__ import annotations

import json
import sys

from moreau_script.parser import parse_file
from moreau_script.validator import validate
from moreau_script.interpreter import interpret, GameContext


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m moreau_script <script.ms> [opponent_animal]")
        print()
        print("Options:")
        print("  opponent_animal   Optional: the opponent's animal (e.g. BEAR)")
        sys.exit(1)

    script_path = sys.argv[1]
    opponent_animal = sys.argv[2].upper() if len(sys.argv) > 2 else None

    # Parse
    try:
        rules = parse_file(script_path)
    except (SyntaxError, FileNotFoundError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    # Read raw source for validation
    with open(script_path, "r", encoding="utf-8") as f:
        source = f.read()

    # Validate
    errors = validate(rules, source)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    # Interpret
    ctx = GameContext(opponent_animal=opponent_animal)
    build = interpret(rules, ctx)

    # Verify stats sum to 20
    stat_total = build["hp"] + build["atk"] + build["spd"] + build["wil"]
    if stat_total != 20:
        print(f"Warning: stats sum to {stat_total}, not 20", file=sys.stderr)

    # Print result
    print(json.dumps(build, indent=2))


if __name__ == "__main__":
    main()
