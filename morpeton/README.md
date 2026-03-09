# Morpeton v1.0

Domain-specific language for Moreau Arena Season 2.

Zero training data contamination. Safe by construction. Designed by an 8-model Round Table council.

## Quick Start

```python
from morpeton import parse, validate, execute

code = """
PLAN:
  STANCE aggressive
  ENGAGE close_range
  TERRAIN seek_high_ground

EACH TICK:
  WHEN my.hp < 20%:
    DO RETREAT nearest.cover

  WHEN enemy.visible AND distance < 2:
    DO ATTACK enemy

  DEFAULT:
    DO MOVE TOWARD enemy
"""

# Parse
result = parse(code)
print(result.ok)          # True
print(result.errors)      # []
print(result.syntax_validity)  # 1.0

# Validate constraints
errors = validate(result.ast, source=code)
print(errors)  # []

# Execute against game state
game_state = {
    "my_hp": 80,
    "enemy_hp": 60,
    "enemy_visible": True,
    "distance": 1,
    "my_terrain": "open",
    "abilities": {},
}
action = execute(result.ast, game_state)
print(action)  # {"type": "attack", "target": "enemy"}
```

## API Reference

### `parse(source: str) -> ParseResult`

Parse Morpeton source code into an AST.

- Returns `ParseResult` with `.ast` (dict), `.errors` (list), `.ok` (bool), `.syntax_validity` (float)
- Implements partial parse: broken WHEN blocks are skipped, valid ones kept

### `validate(ast, source, *, max_lines=30, max_chars=80, max_when=8) -> list[ValidationError]`

Check structural constraints.

- `MAX_LINES` — too many lines (default 30)
- `MAX_CHARS` — line too long (default 80)
- `MAX_WHEN_BLOCKS` — too many WHEN blocks (default 8)
- `MAX_NESTING` — nesting too deep (max 2: WHEN → IF/OTHERWISE)

### `execute(ast: dict, game_state: dict) -> dict`

Execute one tick. Returns an action dict.

**Game state keys:**

| Key | Type | Description |
|-----|------|-------------|
| `my_hp` | int (0-100) | Self HP percentage |
| `enemy_hp` | int (0-100) | Enemy HP percentage |
| `enemy_visible` | bool | Enemy in line of sight |
| `distance` | int | Hex distance to enemy |
| `my_terrain` | str | Current terrain type |
| `abilities` | dict[str, bool] | Ability name → is ready |

**Action types returned:**

| Action | Fields |
|--------|--------|
| `wait` | `{"type": "wait"}` |
| `move` | `{"type": "move", "direction": "TOWARD", "target": "enemy"}` |
| `attack` | `{"type": "attack", "target": "enemy"}` |
| `use` | `{"type": "use", "ability": "pounce", "target": "enemy"}` |
| `retreat` | `{"type": "retreat", "target": "nearest.cover"}` |
| `scout` | `{"type": "scout", "target": "enemy.last_seen"}` |

## Running Tests

```bash
python -m pytest morpeton/test_morpeton.py -v
```

## Language Reference

See [docs/MORPETON_V1_SPEC.md](../docs/MORPETON_V1_SPEC.md) for the full specification including formal PEG grammar, execution semantics, and design rationale.
