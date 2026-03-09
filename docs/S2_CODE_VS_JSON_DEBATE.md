# Season 2 Output Format: Code vs JSON vs Morpeton

**Status:** Design recommendation from Round Table council session
**Date:** 2026-03-09
**Councils:** 2 panels, 7 responding models, $0.72 total cost
**Previous:** [S2_ACTION_LANGUAGE_DESIGN.md](S2_ACTION_LANGUAGE_DESIGN.md) — established Hybrid D architecture (unanimous)

## Council Composition

| Panel | Models | Moderator | Cost |
|-------|--------|-----------|------|
| API | claude-opus-4-6, claude-sonnet-4-6, gpt-5.4, gpt-5.2 | claude-opus-4-6 | $0.72 |
| Ollama | kimi-k2.5, qwen3-80b, cogito-671b | kimi-k2.5 | $0.00 |

---

## Result: Morpeton Wins (6-1)

**6 models** chose Morpeton as the primary S2 format:
claude-opus-4-6, claude-sonnet-4-6, gpt-5.2, kimi-k2.5, qwen3-80b, cogito-671b

**1 model** chose JSON primary + Morpeton shadow track:
gpt-5.4

**0 models** chose Python. Python was unanimously eliminated.

---

## Consensus Points (All 7 Models Agree)

1. **Python is eliminated.** Tests coding fluency, not tactics. Massive contamination (GitHub corpus). Sandbox is a security nightmare. Unanimous, uncontested.

2. **Morpeton is the philosophically correct format.** Even gpt-5.4 (the sole JSON advocate) agrees Morpeton is the eventual destination and superior on contamination, safety, readability, and evolution.

3. **JSON cannot express conditional tactical logic cleanly.** Adding conditionals to JSON effectively recreates a DSL with worse ergonomics. JSON tests serialization compliance, not reasoning.

4. **Morpeton's parser is tractable.** ~200 lines of recursive descent / PEG. Far simpler than Python sandboxing, only moderately harder than JSON schema validation.

5. **The spec must be complete and unambiguous.** Morpeton's success is contingent on grammar quality. A sloppy definition would invalidate benchmark results.

6. **WHEN blocks: top-to-bottom, first-match-wins.** Explicit priority ordering is simplest to parse and tests whether models understand rule prioritization.

7. **v1 command set must be deliberately small.** Rich vocabulary (COORDINATE, SUPPRESS) belongs in later seasons.

---

## The Central Debate: Timing

### For Morpeton Primary in S2 (6 models)

> "Contamination resistance is not an optimization — it is the benchmark's raison d'être. Launching S2 with JSON and promising Morpeton 'next season' weakens Moreau's competitive positioning."
> — claude-opus-4-6 (synthesis)

> "Learning a novel formalism from a spec *is* a reasoning capability, and one directly relevant to real-world agent deployment. It's not confounding; it's additional signal."
> — claude-opus-4-6

> "Lower initial syntax accuracy is a feature, not a bug. Forcing models to acquire a novel grammar from the prompt alone isolates true reasoning capability from memorized patterns."
> — kimi-k2.5

### For JSON Primary + Morpeton Shadow Track (gpt-5.4)

> "S2 already changes the benchmark substantially with tactical updates, fog, terrain, and movement. Adding a brand-new DSL at the same time risks measuring prompt-language acquisition + syntax obedience more than tactical reasoning."
> — gpt-5.4

> "If a model ranks low, is it bad at tactics or bad at learning Morpeton? Clean attribution matters for benchmark credibility."
> — gpt-5.4

### Resolution (Opus synthesis)

Run **Morpeton as primary scored format** with **JSON as parallel secondary track**. This lets the community empirically measure how much score variance is attributable to syntax acquisition vs. tactical reasoning. If correlation between tracks is high, the confound is small. If low, that itself is valuable data.

Report **two sub-scores**: syntax validity rate + tactical effectiveness. This separates the axes cleanly.

---

## Line Limit for S2

| Model | Proposed Limit |
|-------|---------------|
| claude-opus-4-6 | 30 |
| gpt-5.2 | 30 |
| kimi-k2.5 | 30 |
| qwen3-80b | 30 |
| cogito-671b | 30 |
| claude-sonnet-4-6 | 25 |
| gpt-5.4 | 24 |

**Consensus: 30 lines for S2.** Generous enough for 4-5 WHEN blocks with nested IF/OTHERWISE. Forces strategic compression without punishing formatting inefficiency during language learning phase.

**Evolution path:** S2=30, S3=15 (elegance test), S4=60 (2v2 complexity).

---

## Morpeton v1 Core Specification

### Structure
```morpeton
PLAN:
  STANCE <stance>
  ENGAGE <engagement>
  TERRAIN <terrain_goal>

EACH TICK:
  WHEN <condition>:
    IF <condition> DO <action>
    OTHERWISE DO <action>

  WHEN <condition>:
    DO <action>

  DEFAULT:
    DO <action>
```

### Stances (enumerated)
`aggressive` | `defensive` | `cautious` | `mobile`

### Engagement (enumerated)
`close_range` | `mid_range` | `kite`

### Actions (enumerated)
| Command | Syntax | Description |
|---------|--------|-------------|
| MOVE | `MOVE TOWARD/AWAY_FROM/TO <target>` | Hex movement |
| ATTACK | `ATTACK <target>` | Basic attack |
| USE | `USE "<ability>" [<target>]` | Use named ability |
| RETREAT | `RETREAT <location>` | Disengage toward safety |
| SCOUT | `SCOUT TOWARD <location>` | Explore fog-of-war |
| WAIT | `WAIT` | Hold position, no action |

### Targets / Selectors
`enemy` | `nearest.cover` | `nearest.high_ground` | `enemy.last_seen` | `<hex_id>`

### Conditions
| Condition | Example |
|-----------|---------|
| HP threshold | `my.hp < 30%` |
| Enemy visibility | `enemy.visible` / `NOT enemy.visible` |
| Distance | `distance < 3` |
| Ability ready | `ability.ready "pounce"` |
| Terrain | `my.terrain = "high_ground"` |
| Boolean logic | `AND` / `OR` / `NOT` |

### Control Flow
- `WHEN <condition>:` — top-level rule (first-match-wins, top-to-bottom)
- `IF <condition> DO <action>` — nested conditional
- `OTHERWISE DO <action>` — else branch
- `DEFAULT:` — fallback if no WHEN matches

### Constraints
- Max 30 lines per submission (S2)
- No loops, no variables, no imports, no arithmetic beyond comparisons
- No user-defined symbols
- All action keywords and targets are from enumerated vocabulary
- Invalid output → graceful degradation (partial parse: accept valid WHEN blocks, default stance for broken ones)

---

## Disagreement: Advanced Commands

| Command | Advocates | Opponents |
|---------|-----------|-----------|
| OVERWATCH | kimi-k2.5 (area denial primitive) | cogito-671b (composite from WAIT+ATTACK) |
| FLANK | kimi-k2.5 (positional maneuvering) | cogito-671b (composite from MOVE) |

**Resolution:** Defer OVERWATCH/FLANK to S3. Keep v1 minimal with 6 core actions. Season vocabulary expansion is a feature of the format.

---

## Comparison Summary

| Criterion | JSON | Python | Morpeton |
|-----------|------|--------|----------|
| Syntax accuracy | Best (~95%+) | Good | Medium-high (improving) |
| Contamination risk | Medium | **Severe** | **Zero** |
| Reasoning tested | Serialization | Coding fluency | Tactical logic + language learning |
| Conditional logic | Poor (needs DSL) | Excellent | Good (WHEN/IF/DO) |
| Safety | Safe | **Dangerous** | **Safe by construction** |
| Parser complexity | Low | **High** (sandbox) | Low-Medium (~200 LOC) |
| Replay readability | Medium | Medium | **Best** |
| Evolution potential | Schema versioning pain | Drift to code benchmark | **Excellent** (seasonal vocabulary) |
| **Council vote** | **1** | **0** | **6** |

---

## Implementation Plan

1. **Write Morpeton v1 grammar spec** — formal, unambiguous, with examples
2. **Build parser** — recursive descent, ~200 lines, compiles to decision tree
3. **Build validator** — check syntax + action/target legality
4. **Define fallback policy** — partial parse with default stance for broken blocks
5. **Add JSON shadow track** — same game state, JSON schema output, for correlation analysis
6. **Report dual scores** — syntax validity rate + tactical effectiveness
7. **Integrate with Hybrid D architecture** — plan call (Morpeton) + event-driven updates (Morpeton)

---

## Source Data

- API council: `council_records/2026-03-09_0532_season_2_of_moreau_arena_adds_a_hex_grid_with_terr.*`
- Ollama council: same timestamp, separate panel in same files
- All raw responses/critiques/votes: `council_records/raw/2026-03-09_0532_*`
- API vote tally: Props 1-7,9,12 unanimous AGREE; Prop 8 (Morpeton primary) 2 agree 1 disagree; Props 10-11 split
- Ollama vote tally: All 5 propositions unanimous AGREE (3-0)
