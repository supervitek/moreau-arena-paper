# Morpeton v1 Language Specification

**Status:** Final design from Round Table council synthesis (3 sessions, 7 models)
**Date:** 2026-03-09
**Version:** v1.0 (Season 2)

---

## Design Principles

1. **Zero contamination.** No line of Morpeton exists in any training corpus.
2. **Safe by construction.** No loops, no variables, no imports, no execution. The interpreter controls every step.
3. **Minimal viable expressiveness.** 6 actions, structured conditions, 30-line limit.
4. **First-match-wins.** WHEN blocks evaluate top-to-bottom; first match determines action.
5. **Graceful degradation.** Invalid blocks are skipped; valid blocks still execute.
6. **Dual scoring.** Syntax validity rate and tactical effectiveness reported separately.

---

## Rejected Features (v1.1 Proposal)

The council evaluated VARS, SET, and REPEAT (proposed v1.1) and **unanimously rejected them for S2**:

- **VARS/SET:** Adds state persistence, increasing spec complexity and parser burden. Deferred to S3+.
- **REPEAT:** Semantically unclear in a tick-based system. One tick = one action. Deferred to S3+.
- **Arithmetic:** `hits + 1`, `distance * 2` — introduces expression parsing. Only simple comparisons in v1.

**Rationale (gpt-5.4):** "S2 should isolate the new capability — in-combat tactical adaptation — without also introducing a new language-learning burden beyond the minimal grammar."

**Rationale (claude-opus-4-6):** "Every synonym is a trap for syntax validation. Start minimal, expand based on empirical data."

---

## Formal Grammar (PEG)

```peg
# Morpeton v1.0 — Parsing Expression Grammar

Program     <- PLAN EACH_TICK

# === PLAN Section ===
PLAN        <- 'PLAN:' NL
               (INDENT PlanField NL)*

PlanField   <- StanceField / EngageField / TerrainField
StanceField <- 'STANCE' SP Stance
EngageField <- 'ENGAGE' SP Engagement
TerrainField <- 'TERRAIN' SP TerrainGoal

Stance      <- 'aggressive' / 'defensive' / 'cautious' / 'mobile'
Engagement  <- 'close_range' / 'mid_range' / 'kite'
TerrainGoal <- 'seek_high_ground' / 'use_cover' / 'control_choke' / 'open_field'

# === EACH TICK Section ===
EACH_TICK   <- 'EACH TICK:' NL
               (INDENT WhenBlock NL)*
               (INDENT DefaultBlock NL)?

# === WHEN Blocks (first-match-wins, top-to-bottom) ===
WhenBlock   <- 'WHEN' SP Condition ':' NL
               (INDENT2 ActionLine NL)+

ActionLine  <- DoAction
             / IfBlock

IfBlock     <- 'IF' SP Condition SP 'DO' SP Action NL
               (INDENT2 'OTHERWISE' SP 'DO' SP Action)?

DoAction    <- 'DO' SP Action

DefaultBlock <- 'DEFAULT:' NL
                INDENT2 'DO' SP Action

# === Actions (6 primitives) ===
Action      <- MoveAction
             / AttackAction
             / UseAction
             / RetreatAction
             / ScoutAction
             / WaitAction

MoveAction    <- 'MOVE' SP Direction SP Target
AttackAction  <- 'ATTACK' SP Target
UseAction     <- 'USE' SP QuotedString (SP Target)?
RetreatAction <- 'RETREAT' SP Target
ScoutAction   <- 'SCOUT' SP 'TOWARD' SP Target
WaitAction    <- 'WAIT'

Direction   <- 'TOWARD' / 'AWAY_FROM' / 'TO'

# === Targets ===
Target      <- 'enemy'
             / 'nearest.cover'
             / 'nearest.high_ground'
             / 'enemy.last_seen'
             / HexID

HexID       <- [A-H] [1-8]

# === Conditions ===
Condition   <- OrExpr
OrExpr      <- AndExpr (SP 'OR' SP AndExpr)*
AndExpr     <- NotExpr (SP 'AND' SP NotExpr)*
NotExpr     <- 'NOT' SP Atom / Atom

Atom        <- Comparison
             / BooleanProp
             / '(' Condition ')'

Comparison  <- Property SP CompOp SP Value
BooleanProp <- 'enemy.visible'
             / 'ability.ready' SP QuotedString

Property    <- 'my.hp'
             / 'enemy.hp'
             / 'distance'
             / 'my.terrain'

CompOp      <- '<' / '>' / '<=' / '>=' / '=' / '!='

Value       <- Percentage / Number / QuotedString
Percentage  <- [0-9]+ '%'
Number      <- [0-9]+
QuotedString <- '"' [^"]+ '"'

# === Whitespace ===
NL          <- '\n'
SP          <- ' '+
INDENT      <- '  '
INDENT2     <- '    '
```

---

## Command Reference

### PLAN Fields

| Field | Values | Description |
|-------|--------|-------------|
| `STANCE` | `aggressive`, `defensive`, `cautious`, `mobile` | Default combat posture; influences autopilot behavior |
| `ENGAGE` | `close_range`, `mid_range`, `kite` | Preferred engagement distance |
| `TERRAIN` | `seek_high_ground`, `use_cover`, `control_choke`, `open_field` | Terrain preference for positioning |

PLAN fields are **metadata** that influence autopilot/tie-break behavior. WHEN blocks fully determine actions when they match.

### Actions

| Action | Syntax | Description |
|--------|--------|-------------|
| `MOVE` | `MOVE TOWARD\|AWAY_FROM\|TO <target>` | Move toward/away from target or to specific hex |
| `ATTACK` | `ATTACK <target>` | Basic attack against target |
| `USE` | `USE "<ability>" [<target>]` | Activate named ability, optionally on target |
| `RETREAT` | `RETREAT <target>` | Disengage + move toward safety (distinct from MOVE: includes disengage mechanic) |
| `SCOUT` | `SCOUT TOWARD <target>` | Move into fog-of-war toward target location |
| `WAIT` | `WAIT` | Hold position, take no action |

**RETREAT vs MOVE:** RETREAT includes a disengage mechanic (e.g., immunity to opportunity attacks, pathfinding through cover). It is NOT a synonym for `MOVE AWAY_FROM`. If the game engine does not implement a distinct disengage mechanic, RETREAT should be removed from the spec.

### Targets

| Target | Description |
|--------|-------------|
| `enemy` | Current opponent |
| `nearest.cover` | Closest terrain providing cover |
| `nearest.high_ground` | Closest elevated terrain |
| `enemy.last_seen` | Last known enemy position (fog-of-war) |
| `A1`–`H8` | Specific hex coordinate |

### Conditions

| Condition | Example | Description |
|-----------|---------|-------------|
| HP threshold | `my.hp < 30%` | Self HP percentage |
| Enemy HP | `enemy.hp < 50%` | Enemy HP percentage |
| Distance | `distance < 3` | Hex distance to enemy |
| Terrain | `my.terrain = "high_ground"` | Current terrain type |
| Visibility | `enemy.visible` | Enemy in line of sight |
| Ability | `ability.ready "pounce"` | Named ability off cooldown |
| Boolean logic | `AND`, `OR`, `NOT` | Combine conditions |

---

## Execution Semantics

### Tick Evaluation

Each tick, the interpreter evaluates the agent's program:

1. Evaluate WHEN blocks **top-to-bottom**
2. **First match wins** — execute its action(s), skip remaining blocks
3. If a WHEN block contains `IF/OTHERWISE`, evaluate the nested condition
4. If **no WHEN matches**, execute `DEFAULT` block
5. If no DEFAULT exists, execute `WAIT`

### PLAN Interaction

- PLAN fields set **default autopilot behavior** for ticks where no API update is requested
- WHEN blocks **override** PLAN when they match — they are evaluated fresh each tick
- When no WHEN matches, PLAN-influenced autopilot behavior applies (with DEFAULT as explicit override)

### Partial Parse Policy

When the parser encounters invalid syntax:

1. **Skip the broken WHEN block entirely**
2. **Continue parsing subsequent blocks**
3. Valid blocks still execute normally
4. A single syntax error does NOT cascade into total autopilot
5. **Never retry** — retry introduces hidden selection effects and cost asymmetry
6. Log all parse errors for syntax validity scoring

### Invalid Output Handling

| Scenario | Behavior |
|----------|----------|
| One WHEN block malformed | Skip it, evaluate remaining blocks |
| All WHEN blocks malformed | Fall through to DEFAULT or WAIT |
| PLAN section malformed | Use default stance (defensive) |
| Entire output unparseable | Agent executes WAIT every tick |
| Action references unknown target | Treat as WAIT for that tick |
| Action references unknown ability | Treat as WAIT for that tick |

---

## Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Max lines | 30 | Forces strategic compression; generous enough for 4-5 WHEN blocks |
| Max chars/line | 80 | Prevents single-line complexity abuse |
| Max WHEN blocks | 8 | Prevents exhaustive enumeration |
| Max nesting depth | 2 | WHEN → IF/OTHERWISE (no deeper nesting) |
| Allowed types | — | No variables, no user-defined symbols |
| Allowed arithmetic | — | Comparisons only (no expressions like `hp + 10`) |

### Line Limit Evolution

| Season | Limit | Purpose |
|--------|-------|---------|
| S2 | 30 | Language learning phase — generous |
| S3 | 15 | Elegance test — can you compress? |
| S4 | 60 | 2v2 complexity — more agents, more rules |

---

## Dual-Track Scoring

### Track 1: Morpeton (Primary, Scored)

The official S2 submission format. Agents write Morpeton programs.

### Track 2: JSON (Shadow, Correlation Control)

Same game states, same seeds, same decision points. Agents produce flat JSON action lists.

**Purpose:** Empirically measure how much score variance is attributable to syntax acquisition vs. tactical reasoning. If Morpeton/JSON rankings correlate highly, the syntax confound is small. If they diverge, that data reveals adaptation speed as a meaningful capability axis.

**Requirement:** Identical game states and random seeds for both tracks, or correlation analysis is invalid.

### Sub-Scores

| Score | Description |
|-------|-------------|
| **Syntax Validity** | % of WHEN blocks that parse successfully |
| **Tactical Effectiveness (unconditional)** | Game outcome including consequences of syntax failures (invalid → WAIT) |
| **Tactical Effectiveness (conditional)** | Game outcome evaluated only on valid portions |

Report all three. Unconditional is the "real" result; conditional isolates tactical quality from syntax quality.

---

## Complete Example: Aggressive Tiger

```morpeton
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
```

*21 lines. 5 WHEN blocks. Priorities: survive → melee → close gap → scout → position.*

## Complete Example: Defensive Porcupine

```morpeton
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
```

*19 lines. 4 WHEN blocks. Priorities: survive → disengage melee → ranged poke → hold position.*

## Complete Example: Flanking Wolf

```morpeton
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
```

*19 lines. 4 WHEN blocks. Priorities: retreat if losing → melee → close + buff → hunt.*

---

## Implementation Checklist

1. [ ] Write formal PEG grammar (above) — validate with parser generator
2. [ ] Build recursive descent parser (~200 LOC)
3. [ ] Build validator (action/target legality, line/block limits)
4. [ ] Define autopilot behavior for between-update ticks
5. [ ] Define RETREAT mechanic (disengage immunity? cover pathfinding?)
6. [ ] Build JSON shadow track with identical game state/seed infrastructure
7. [ ] Implement dual scoring pipeline (syntax validity + tactical effectiveness)
8. [ ] Write 20+ canonical examples as parser test suite
9. [ ] Write conformance tests for edge cases
10. [ ] Publish reference parser + grammar for community validation

---

## Source Data

- Council 1 (architecture): `council_records/2026-03-09_0508_*` — Hybrid D unanimous
- Council 2 (format): `council_records/2026-03-09_0532_*` — Morpeton 6-1 over JSON
- Council 3 (refinement): `council_records/2026-03-09_0639_*` — v1 minimal, no VARS/SET/REPEAT
- Design docs: `docs/S2_ACTION_LANGUAGE_DESIGN.md`, `docs/S2_CODE_VS_JSON_DEBATE.md`
- Total council cost: ~$2.70 across 3 sessions
