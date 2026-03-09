# Season 2 Action Language Design

**Status:** Design recommendation from Round Table council session
**Date:** 2026-03-09
**Council:** 8 models across 2 panels (API + Ollama)

## Council Composition

| Panel | Models | Moderator | Cost |
|-------|--------|-----------|------|
| API | claude-opus-4-6, claude-sonnet-4-6, gpt-5.4, gpt-5.2 | claude-opus-4-6 | $1.05 |
| Ollama | kimi-k2.5, qwen3-80b, cogito-671b, deepseek-v3.2* | deepseek-v3.2 | $0.00 |

*DeepSeek-v3.2 returned empty responses (thinking model token issue).

---

## Unanimous Recommendation: Option D — Event-Driven Hybrid

All 8 models (7 responding) independently chose **Option D (Hybrid)**: an initial battle plan plus mid-combat tactical updates. No model advocated for Options A, B, C, or E as the primary approach.

---

## Consensus Points (All Models Agree)

1. **Hybrid architecture is correct.** Plan + corrections best balances cost, reasoning signal, and implementation feasibility.

2. **Strict JSON, not DSL.** Every model rejected free-form DSL parsing (Option B). Constrained JSON schemas with enumerated fields eliminate syntax errors as a confounder.

3. **Graceful degradation.** Invalid or malformed agent output degrades to no-op/default behavior, never crashes the game. Informed by S1 data showing frozen models and formatting brittleness.

4. **~5-8 API calls per game per agent.** 1 plan call + 4-7 tactical updates. Sustainable at tournament scale (91+ series x 7 games) while still testing adaptation.

5. **Must test situated tactical reasoning.** Option C's "describe your strategy" approach is explicitly rejected — it collapses into S1-style pre-combat planning. The point of S2 is in-combat decision-making.

6. **Replay readability.** Plan + discrete decision points creates natural narrative: "Agent opened with flank plan, switched to retreat at tick 18 after taking quill damage."

---

## Key Disagreements

### 1. Trigger Model: Event-Driven vs. Fixed Interval

| Model | Proposal | Post-Critique Position |
|-------|----------|----------------------|
| claude-opus-4-6 | Fixed every 5 ticks | Updated toward event-driven |
| claude-sonnet-4-6 | HP thresholds (75/50/25%) | Acknowledged event-driven superiority |
| gpt-5.2 | Event-driven decision points | Held position (most influential argument) |
| gpt-5.4 | Every 4 ticks OR event trigger | Updated toward "primarily event-driven + max silent interval" |
| Kimi-k2.5 | Every 5 ticks or on event | Hybrid cadence |
| Qwen3-80b | Key ticks (time-driven) | Mixed |
| Cogito-671b | Fixed every 5 ticks | Held position |

**Resolution:** Consensus drifted heavily toward **event-driven as primary mechanism** with a **backstop cadence** (forced update if no event fires in N ticks).

### 2. Call Budget Floor

- claude-sonnet-4-6 proposed 2-5 calls — criticized by 3 other models as too sparse
- Majority position: **6-8 calls minimum** for meaningful tactical agency
- gpt-5.4: "at 2-5 calls, many important tactical moments won't be model-controlled"

### 3. Condition Syntax

- Multiple proposals included string-based conditions (`"hp_enemy < 50% AND adjacent"`) — criticized as "DSL bleeding into JSON"
- **Unresolved tension:** how to express conditional logic without inventing a mini-expression language or limiting agents to impoverished predicates
- Opus synthesis proposed structured predicate objects (AST-like JSON) as the resolution

### 4. Action Granularity

- gpt-5.4 specified per-tick actions (`"tick": 9, "type": "move"`) — criticized as reintroducing Option A
- Alternative: ordered action lists without tick assignments, simulator schedules execution
- Trade-off: precision vs. robustness

### 5. Autopilot Intelligence

- All agree simulator needs autopilot between decision points
- Nobody fully specifies how smart it should be
- gpt-5.4: "if autopilot is too smart, benchmark measures simulator policy quality more than model reasoning"
- **Recommendation:** deliberately minimal, deterministic autopilot

---

## Strongest Arguments (from Opus synthesis)

1. **gpt-5.2: Event-driven interrupts are strictly superior to fixed intervals.** Most influential single argument — caused 2 panelists to update positions. Fixed intervals waste calls during low-information stretches and miss critical moments between intervals.

2. **gpt-5.4: "Only allow enumerated actions, predicates, and objectives."** Eliminates an entire class of failure modes. Zero disagreement across all critiques.

3. **claude-opus-4-6: 3-4 action limit per update call.** Prevents token bloat, forces prioritization, makes validation trivial.

4. **gpt-5.4: Backstop cadence ("max silent interval").** Pure event-driven has a failure mode if trigger set is imperfect. Maximum gap rule (e.g., 5 ticks) is a simple safeguard.

5. **claude-sonnet-4-6: Phase labels for replay narrative.** Label decision points as phase transitions (opening/mid/finisher) for spectator readability. Costs nothing to implement.

---

## Recommended Architecture

### Call Type 1: BATTLE PLAN (1 call, pre-combat)

Agent receives: hex map layout, terrain, fog-of-war rules, own build, opponent's animal (not stats).

```json
{
  "type": "plan",
  "stance": "flanking",
  "engagement": "mid_range",
  "terrain_goal": "seek_high_ground",
  "fog_behavior": "scout_forward",
  "ability_priority": ["pounce", "hamstring", "roar"],
  "rules": [
    {
      "condition": {"stat": "hp_self_pct", "op": "lt", "value": 25},
      "action": "retreat_to_cover"
    },
    {
      "condition": {
        "type": "and",
        "clauses": [
          {"stat": "enemy_visible", "op": "eq", "value": true},
          {"stat": "distance", "op": "lte", "value": 2}
        ]
      },
      "action": "use_ability",
      "ability": "pounce"
    }
  ]
}
```

**Key fields (all enumerated):**
- `stance`: aggressive | balanced | defensive | flanking | ambush
- `engagement`: close_range | mid_range | kite
- `terrain_goal`: seek_high_ground | use_cover | control_choke | open_field
- `fog_behavior`: scout_forward | hold_position | ambush_wait
- `rules`: structured predicates (no string parsing)

### Call Type 2: TACTICAL UPDATE (event-driven, ~5-7 per game)

**Trigger events** (simulator fires when any occurs):
- Enemy enters/exits fog-of-war vision
- Adjacency change (enter/leave melee range)
- HP threshold crossed (60%, 40%, 20%)
- Ability becomes available (cooldown ready)
- Path blocked by terrain or positioning
- **Backstop: no event in 5 ticks** → forced update

Agent receives: compact board state (own position, HP, buffs/debuffs, visible enemy info, terrain within vision, active cooldowns).

```json
{
  "type": "update",
  "phase": "mid",
  "actions": [
    {"do": "move", "to": "C4"},
    {"do": "use_ability", "name": "hamstring", "target": "enemy"},
    {"do": "move", "to": "D5"}
  ],
  "stance_override": "defensive",
  "comment": "Enemy flanking from south, retreating to high ground"
}
```

**Constraints:**
- Max 4 actions per update
- Actions are ordered intents, not per-tick assignments — simulator schedules execution
- `comment` field is for replay/spectator only, never parsed
- All action types and targets are enumerated, no free text in executable fields
- Invalid output → no-op (graceful degradation)

---

## Cost Estimate

| Component | Calls | Tokens/call | Total tokens |
|-----------|-------|-------------|-------------|
| Battle plan | 1 | ~400-600 | ~500 |
| Tactical updates | 5-7 | ~200-400 | ~1,500 |
| Board state (input) | 5-7 | ~300 | ~1,800 |
| **Total per game** | **6-8** | — | **~4,000** |
| **Per series (best-of-7)** | **~50** | — | **~28,000** |

At current API prices, this is ~$0.03-0.10 per game per agent depending on model.

---

## Open Questions for Implementation

1. **Autopilot policy:** How smart should between-update behavior be? Must be deterministic and documented so it doesn't become a hidden confounder.

2. **Condition predicate vocabulary:** Exact set of stats, operators, and compound logic supported. Start minimal, expand based on testing.

3. **Fog-of-war information budget:** How much of the board state to reveal per update? Too much reduces fog's impact; too little makes decisions random.

4. **Adaptive format integration:** S1 uses best-of-7 with build adaptation. S2 needs to decide if plans can reference previous game outcomes.

5. **Validation strictness:** How strict is schema validation? Options: reject-and-retry (costly), warn-and-default (forgiving), silent-default (simplest).

---

## Source Data

- API council synthesis: `council_records/raw/2026-03-09_0508_*synthesis_claude-opus-4-6.json`
- Ollama individual responses: `council_records/raw/2026-03-09_0508_*response_{kimi,qwen3,cogito}*.json`
- All raw responses and critiques: `council_records/raw/2026-03-09_0508_*`
- API council votes: unanimous AGREE on all 12-13 propositions (gpt-5.4, gpt-5.2)
- Ollama council votes: degraded (empty DeepSeek synthesis → Kimi abstained, Cogito voted on wrong propositions)
