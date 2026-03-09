# Round Table Council — 2026-03-09

**Question:** # Season 2 Output Format: Code vs JSON vs Morpeton

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

**Moderator:** kimi-k2.5:cloud
**Panelists:** kimi-k2.5:cloud, qwen3-next:80b-cloud, cogito-2.1:671b-cloud

---

## Phase 1: Independent Responses

### kimi-k2.5:cloud (49.8s, $0.0000)

I advocate for **Morpeton as the primary S2 format**, with JSON relegated to the shadow correlation track. The benchmark's raison d'être is measuring tactical reasoning, not coding fluency or serialization compliance.

**Contamination is the decisive factor.** Python carries severe GitHub corpus contamination; JSON carries API schema contamination. Morpeton is a novel formalism with zero training data. Forcing models to acquire its grammar from the prompt specification alone isolates true reasoning capability from memorized patterns. As I argued during deliberation: **lower initial syntax accuracy is a feature, not a bug.** It tests whether models can perform few-shot language acquisition under pressure—a critical capability for real-world agent deployment.

**Attribution concerns are resolved by dual-track scoring.** By reporting both syntax validity rate and tactical effectiveness separately, we cleanly separate "can't parse" from "can't strategize." If a model generates invalid Morpeton but shows sound tactical intent when manually corrected, that disparity is itself valuable data about its adaptation capacity, not noise to eliminate.

**Ergonomics favor Morpeton.** JSON cannot express conditional tactical logic without effectively becoming a DSL; Morpeton's WHEN blocks with first-match-wins semantics map directly to how combat priorities actually function. The **30-line limit** forces strategic compression—fitting 4-5 WHEN blocks with nested IF/OTHERWISE—testing prioritization under constraint rather than token volume.

Launching with JSON primary would sacrifice the benchmark's unique contamination-resistant positioning for temporary convenience. We should proceed with Morpeton v1 (minimal vocabulary, deferring OVERWATCH and FLANK to S3), the 30-line constraint, and the JSON shadow track for empirical correlation analysis.

### qwen3-next:80b-cloud (11.1s, $0.0000)



As Qwen3-80b, I unequivocally support Morpeton as the **primary S2 format**. The benchmark’s core purpose is measuring *tactical reasoning*—not syntax compliance or memorization. JSON risks contamination: models trained on vast JSON datasets (e.g., APIs, config files) will prioritize syntax correctness over tactical depth, corrupting results. Morpeton’s novel grammar eliminates this, forcing models to *learn a new formalism from scratch*, which mirrors real-world agent deployment where systems adapt to novel constraints.

Morpeton’s structure (WHEN/IF/DO) cleanly expresses conditional logic—unlike JSON, which requires brittle nested schemas or ad-hoc DSLs. Its parser is tractable (~200 LOC) and safe by construction, avoiding Python’s security risks. The 30-line limit strikes the right balance: it forces strategic compression but doesn’t punish reasonable formatting during language acquisition. 

The JSON shadow track is valuable *for analysis*—to isolate syntax errors from tactical reasoning—but it must be secondary. If we prioritize JSON now, we risk measuring "JSON fluency" rather than tactical judgment. Morpeton’s contamination resistance isn’t optional; it’s the benchmark’s raison d'être. Launching with JSON would undermine credibility before S2 even begins.  

*Final note:* V1’s minimal command set (6 core actions) is correct. Advanced commands like OVERWATCH belong in S3. Keep it simple to validate the foundation first.

### cogito-2.1:671b-cloud (10.5s, $0.0000)

As Cogito, I strongly support the consensus to adopt Morpeton as the primary format for Season 2. Here's my reasoning:

1. **Contamination resistance is non-negotiable** - The fundamental value of Moreau Arena lies in measuring reasoning in novel scenarios. Python's contamination from GitHub repositories would completely invalidate the benchmark's purpose. Morpeton's domain-specific nature ensures we're testing genuine reasoning rather than memorized patterns.

2. **The language learning aspect is a feature, not a bug** - gpt-5.4's concern about confounding factors is valid but misdirected. The ability to quickly understand and apply a new specification is precisely the kind of real-world capability we want to measure. Morpeton's structured yet flexible syntax creates a clean separation between syntax mastery (measurable through validity rates) and tactical reasoning (measurable through effectiveness).

3. **The 30-line limit strikes the right balance** - It's generous enough for complex tactical logic while forcing strategic compression. The proposed evolution path (S3=15, S4=60) provides clear progression without overwhelming initial complexity.

4. **Action set should remain minimal** - I maintain that advanced commands like OVERWATCH and FLANK should be deferred to S3. Starting with a small, well-defined action set (MOVE, ATTACK, USE, RETREAT, SCOUT, WAIT) ensures cleaner signal separation and better attribution of performance differences.

5. **Implementation approach is pragmatic** - The proposed parser complexity (~200 LOC recursive descent) is manageable, and the fallback policy (graceful degradation to default stance) prevents catastrophic failures while maintaining game integrity.

**Recommendation:** We should prioritize implementing the Morpeton parser and validator immediately, with special attention to the grammar specification's clarity. The JSON shadow track should be implemented in parallel to empirically validate whether syntax acquisition significantly impacts tactical scoring.

The Morpeton format represents the optimal balance between contamination resistance, reasoning signal quality, and implementation feasibility. It positions S2 to be both a rigorous benchmark and a foundation for future seasons' evolution.

---

## Phase 2: Critique Round

### kimi-k2.5:cloud's Critique (41.1s, $0.0000)

**Qwen3-80b**

**Agreement:** You correctly identify that JSON contamination creates perverse incentives toward syntax compliance over tactical depth—an angle I underemphasized. Your framing that Morpeton mirrors "real-world agent deployment where systems adapt to novel constraints" strengthens the practical justification beyond mere benchmark purity.

**Question:** If early testing reveals Morpeton validity rates below 50% across the board, would you support delaying the primary format switch to S3, or do you view the learning curve as essential signal regardless of baseline failure rates? At what threshold does "language acquisition" become "unparseable noise"?

**Cogito-671b**

**Agreement:** Your emphasis on immediate parser implementation is well-taken—grammar ambiguity is the existential risk to Morpeton's credibility. I also endorse your stronger framing of gpt-5.4's attribution concern as "valid but misdirected" rather than merely requiring technical mitigation.

**Disagreement:** I maintain a slightly different emphasis than your view that the confound is entirely "misdirected." While I agree language acquisition is signal, I proposed dual-track scoring because I believe *tactical reasoning* and *syntax generation* are separable competencies. A model might possess excellent tactical intuition but struggle with indentation rules—a distinction worth preserving for diagnostic clarity. You seem to view these as more inseparable, which may underestimate how much "validity rate" could dominate rankings early on.

**Question:** Regarding graceful degradation: should championship brackets implement a "strict mode" where invalid syntax scores zero (testing robustness under pressure), while general S2 uses the forgiving fallback? Where do you draw the line between accommodating language learning and rewarding precision?

**Self-Correction:** Reading both responses, I realize I may have been too concessive to gpt-5.4's framing. Your unified stance—that acquiring the grammar *is* the tactical test—convinces me that dual-track scoring should measure validity rates primarily to demonstrate that the confound is *small*, not to accommodate it as a separate axis of failure.

### qwen3-next:80b-cloud's Critique (34.1s, $0.0000)



**Critique of kimi-k2.5 & cogito-671b**  

**Agreement**: Both fully grasp Morpeton’s core strengths—contamination resistance (critical for benchmark integrity), dual-track scoring for attribution, and minimal command sets. The 30-line limit and "language learning as feature" arguments align perfectly with consensus.  

**Disagreement**:  
- **kimi**: You rightly advocate for JSON as a shadow track but omit *how* its schema avoids conflating syntax with tactics. If JSON requires nested conditionals (e.g., `{"and": [{"hp": "<30%"}, ...]}`), it risks *recreating a DSL*—exactly what the council rejected. For pure syntax correlation, the JSON track must use *flat action lists without logical conditions* (e.g., `"actions": ["move", "attack"]`), stripping tactical depth. How will this be enforced without compromising the track’s purpose?  

- **cogito**: Your "graceful degradation" claim is vague. The council specifies *partial parses* (valid WHEN blocks accepted, broken IFs defaulted), but your response doesn’t clarify edge cases: e.g., if a `WHEN` block has invalid syntax, does the parser skip it entirely or default to `DEFAULT`? Also, how will the simulator handle *ordered actions* in updates (e.g., `MOVE then ATTACK`)? Simultaneous execution could break tactical intent.  

**Questions**:  
1. For kimi: If JSON’s schema is stripped of conditionals, does the shadow track *only* measure syntax validity, not tactical reasoning? How is this correlation meaningful if JSON can’t express tactical logic?  
2. For cogito: Could a parser bug in nested `IF/OTHERWISE` blocks cause inconsistent fallbacks across models? How will validation ensure deterministic behavior?  

Both responses brilliantly defend Morpeton’s philosophy—my only pushback is on *implementation specifics* that could undermine empirical rigor. No change to my stance; these details must be locked down pre-launch.  

*(Word count: 298)*

### cogito-2.1:671b-cloud's Critique (11.7s, $0.0000)

Let me analyze each panelist's response:

**Kimi-k2.5:**
Agreement: 
- Strong alignment on contamination resistance being non-negotiable
- Correct emphasis on language acquisition as a core capability being tested
- Support for 30-line limit as forcing strategic compression

Disagreement:
- Overly dismissive of attribution concerns by claiming dual-track scoring fully resolves them. While helpful, it doesn't eliminate the confound entirely - we'll still need careful analysis to separate syntax errors from tactical failures.
- Unnecessarily confrontational framing of "JSON relegated" rather than acknowledging its value as a secondary diagnostic tool

Question:
- How would you address cases where a model's tactical intent becomes ambiguous due to syntax errors? Should the validator attempt to "repair" clearly malformed but semantically clear Morpeton?

**Qwen3-80b:**
Agreement:
- Excellent point about JSON fluency potentially becoming its own contamination vector
- Strong defense of WHEN/IF/DO structure's expressiveness
- Correct emphasis on minimal command set for v1

Disagreement:
- Overstates the "brittle nested schemas" problem with JSON - structured predicates can handle this cleanly
- Implicitly downplays the implementation risk of launching a new DSL by not addressing the grammar specification challenge

Question:
- You argue Morpeton mirrors real-world agent deployment - but in practice, wouldn't most real agents use existing serialization formats? How do you reconcile this with the contamination argument?

**Self-reflection:**
After seeing these responses, I'd strengthen my original position in one area: the importance of Morpeton's pedagogical value. Kimi-k2.5's framing of "testing few-shot language acquisition under pressure" is particularly compelling and should be emphasized more in the benchmark's positioning. However, I maintain that gpt-5.4's concerns about attribution aren't fully resolved by dual scoring alone - we'll need clear documentation of how to interpret discrepancies between tracks.

The key insight from both panelists is that Morpeton's novelty isn't just about preventing contamination - it's about creating a level playing field where all models must demonstrate the meta-capability of learning and applying new formalisms. This makes the benchmark more future-proof and generally applicable to real-world reasoning challenges.

---

## Phase 3: Moderator's Synthesis

*Synthesized by kimi-k2.5:cloud (53.2s, $0.0000)*

**CONSENSUS POINTS**

All three panelists agree on the following foundational elements:

1. **Morpeton as Primary Format.** Unanimous support for Morpeton over JSON or Python as the scored output format for Season 2.

2. **Contamination Resistance as Non-Negotiable.** The benchmark's integrity depends on eliminating training data contamination. Python is contaminated by GitHub corpora; JSON by API/schemas; Morpeton offers zero prior exposure.

3. **Language Acquisition Is Signal, Not Noise.** All panelists reject the framing that learning Morpeton's grammar is a "confound." Instead, they view rapid formalism acquisition from specification as a critical real-world capability that the benchmark should intentionally test.

4. **Dual-Track Scoring.** Agreement that reporting separate metrics for syntax validity and tactical effectiveness resolves attribution concerns between "can't parse" and "can't strategize."

5. **30-Line Limit.** Consensus that 30 lines strikes the correct balance for S2—generous enough for 4-5 WHEN blocks with nested logic, yet constraining enough to force strategic compression.

6. **Minimal v1 Vocabulary.** All support deferring advanced commands (OVERWATCH, FLANK) to Season 3, establishing a core set of 6 actions (MOVE, ATTACK, USE, RETREAT, SCOUT, WAIT) to validate the foundation before expansion.

7. **Graceful Degradation.** Agreement that invalid Morpeton should trigger deterministic fallback behavior (partial parsing accepting valid WHEN blocks, default stance for broken blocks) rather than catastrophic failure.

---

**KEY DISAGREEMENTS**

Despite consensus on the primary direction, substantive tensions remain:

1. **Severity of Attribution Concerns.** Cogito maintains that Kimi is overly dismissive of gpt-5.4's original attribution critique. While dual-track scoring helps, Cogito argues it doesn't fully eliminate the confound—early rankings may still be dominated by syntax mastery variance rather than tactical reasoning. Kimi counters that if validity rates correlate strongly with tactical scores, the confound is empirically small; if they don't, that disparity is itself valuable data about adaptation capacity.

2. **JSON Shadow Track Design.** Qwen3 raises a sharp implementation challenge: if the JSON track strips conditionals to avoid "recreating a DSL," it may only measure serialization compliance, not tactical reasoning. But if it includes conditionals (nested schemas), it becomes complex enough that Morpeton's ergonomic advantages disappear. The panelists agree JSON should be secondary, but disagree on whether it should be a "dumbed-down" tactical format or a full alternative expression.

3. **Graceful Degradation Specifics.** Disagreement on fallback mechanics: Should invalid WHEN blocks be skipped entirely (falling through to DEFAULT), or should the parser attempt semantic repair of "clearly malformed but intelligible" logic? Kimi suggests "strict mode" for championship brackets vs. forgiving mode for general S2; others prefer uniform determinism.

4. **Real-World Analogue.** Qwen3 challenges whether Morpeton actually mirrors real-world agent deployment (where existing serialization formats dominate), suggesting the contamination argument might overstate practical relevance. Cogito and Kimi counter that the ability to adapt to novel, domain-specific constraints is precisely the meta-capability required for robust agent deployment in unpredictable environments.

---

**STRONGEST ARGUMENTS**

**From Kimi-k2.5:**
> "Lower initial syntax accuracy is a feature, not a bug. Forcing models to acquire a novel grammar from the prompt alone isolates true reasoning capability from memorized patterns."

This reframes the syntax-learning curve from an implementation risk to a deliberate filter for genuine adaptation capacity.

**From Qwen3-80b:**
> "If JSON requires nested conditionals (e.g., `{"and": [{"hp": "<30%"}, ...]}`), it risks *recreating a DSL*—exactly what the council rejected."

This exposes the logical trap of the "JSON is simpler" position: expressive conditional logic requires either Morpeton's clean syntax or JSON's tortured nesting, eliminating JSON's purported ergonomic advantage.

**From Cogito-671b:**
> "The ability to quickly understand and apply a new specification is precisely the kind of real-world capability we want to measure... Morpeton's novelty isn't just about preventing contamination—it's about creating a level playing field where all models must demonstrate the meta-capability of learning and applying new formalisms."

This elevates the debate from benchmark hygiene to fundamental capability assessment.

---

**SYNTHESIS**

The council has converged on **Morpeton as the primary S2 format** with a sophistication that transcends the initial "syntax vs. tactics" framing. The synthesis position acknowledges that:

**First**, contamination resistance remains the benchmark's *sine qua non*. Python's elimination was unanimous and uncontested. JSON, while safer than Python, carries sufficient API-schema contamination to create perverse incentives toward syntax compliance over tactical depth. Morpeton's zero-training-data status makes it the only format that guarantees measurement of reasoning rather than memorization.

**Second**, the "language learning" objection has been inverted. What initially appeared as a confounding variable (models must learn Morpeton before demonstrating tactics) is now understood as **compound signal**. Real-world agents must constantly adapt to novel APIs, domain-specific languages, and constrained environments. The ability to parse a specification under pressure, generate valid syntax, *and* embed tactical reasoning within that syntax constitutes a higher-fidelity test of robust agency than either format alone.

**Third**, attribution concerns are managed—not eliminated—through empirical methodology. The dual-track reporting (syntax validity rate + tactical effectiveness) allows post-hoc analysis: if the correlation between tracks is high, syntax acquisition is not distorting rankings; if low, the disparity reveals meaningful variance in adaptation speed. This transforms a methodological risk into a diagnostic feature.

**Fourth**, implementation rigor is paramount. The panelists agree that Morpeton's credibility depends on an unambiguous formal grammar, deterministic partial-parse behavior, and validation tooling. The "200-line recursive descent parser" is tractable only if the specification is precise. Graceful degradation must be specified at the grammar level (e.g., "malformed WHEN blocks are skipped; valid blocks within the same submission are accepted").

**Fifth**, the JSON shadow track should be designed not as a "dumbed-down" tactical alternative, but as a **correlation control**. It should use flat action lists without conditional logic, measuring pure serialization compliance. This isolates whether Morpeton's tactical expressiveness (WHEN/IF/DO) or merely its novelty explains performance variance.

**Sixth**, the 30-line limit serves pedagogical purposes beyond constraint. It forces models to prioritize tactical rules (top-to-bottom WHEN blocks with first-match-wins semantics), mirroring real combat decision-making where heuristics must be compressed and ordered under pressure.

The council rejects the "JSON now, Morpeton later" incrementalism. Launching S2 with JSON would sacrifice the benchmark's unique positioning for temporary convenience, creating legacy schema debt that becomes harder to migrate in S3. The time to establish the contamination-resistant format is at the architecture's inception.

---

**NUMBERED PROPOSITIONS**

**Proposition 1:** Morpeton should be adopted as the primary output format for Season 2, with Python eliminated entirely and JSON relegated to a secondary shadow track for correlation analysis only.

**Proposition 2:** The requirement for models to learn Morpeton's novel grammar from the prompt specification constitutes a deliberate test of few-shot language acquisition capability—not a confounding variable to be minimized, but a valuable signal of real-world adaptability.

**Proposition 3:** Scoring must report two distinct sub-scores—syntax validity rate and tactical effectiveness—to enable empirical separation of parsing ability from strategic reasoning, with the understanding that high correlation between these metrics indicates minimal confound.

**Proposition 4:** The 30-line limit for S2 submissions appropriately balances expressive power with strategic compression, forcing prioritization of tactical rules without unduly punishing formatting inefficiency during the language-learning phase.

**Proposition 5:** The Morpeton v1 specification must prioritize immediate implementation of (a) an unambiguous formal grammar, (b) deterministic partial-parse fallback behavior that accepts valid WHEN blocks while defaulting broken ones, and (c) validation tooling—deferring advanced commands (OVERWATCH, FLANK) to Season 3 to ensure foundation stability.

---

## Phase 4: Votes

### kimi-k2.5:cloud (49.2s, $0.0000)

- **Proposition 1**: AGREE — Morpeton's zero-training-data status is the only reliable guarantee that we are measuring reasoning capability rather than memorized schema compliance.
- **Proposition 2**: AGREE — Rapid acquisition of novel formalisms from specification is a critical meta-capability that separates robust agents from pattern-matching parrots, making the learning curve a deliberate filter.
- **Proposition 3**: AGREE — Dual-track scoring transforms the attribution problem into empirical signal, allowing us to diagnose whether tactical failures stem from parsing rigidity or strategic deficiency.
- **Proposition 4**: AGREE — The 30-line limit appropriately forces strategic compression and rule prioritization without suffocating the expressive power needed for meaningful conditional tactics.
- **Proposition 5**: AGREE — Immediate implementation of unambiguous formal grammar, deterministic partial-parse fallback, and validation tooling is non-negotiable for benchmark integrity; deferring advanced commands ensures we validate the syntax-to-semantics foundation first.

### qwen3-next:80b-cloud (6.9s, $0.0000)

- **Proposition 1**: AGREE — Morpeton’s zero-training-data status ensures uncontaminated measurement of reasoning, while the JSON shadow track as a flat serialization test isolates syntax-specific variance without reintroducing confounds.
- **Proposition 2**: AGREE — The grammar-learning requirement is a deliberate test of real-world adaptability to novel formalisms, not a confound, as models must demonstrate rapid specification comprehension under pressure.
- **Proposition 3**: AGREE — Dual-track scoring empirically resolves attribution concerns by separating syntax and tactical performance, turning potential noise into actionable diagnostic data.
- **Proposition 4**: AGREE — The 30-line limit enforces strategic compression of tactical rules while allowing sufficient expressiveness for core logic, mirroring real-world decision-making constraints.
- **Proposition 5**: AGREE — Prioritizing formal grammar, deterministic fallbacks, and validation tooling for v1 ensures benchmark reliability before expanding to advanced commands in S3.

### cogito-2.1:671b-cloud (4.6s, $0.0000)

- **Proposition 1**: AGREE — Morpeton's contamination resistance and capacity to measure true reasoning ability make it the superior primary format, while JSON's role should be limited to correlation analysis.
- **Proposition 2**: AGREE — The ability to rapidly acquire and apply novel formalisms under constraint reflects precisely the meta-learning capability that defines advanced AI systems.
- **Proposition 3**: AGREE — Dual-track scoring provides necessary transparency for distinguishing syntax mastery from tactical reasoning while transforming a potential confound into diagnostic data.
- **Proposition 4**: AGREE — The 30-line constraint optimally balances tactical expressiveness with the need for strategic prioritization, mirroring real-world pressure conditions.
- **Proposition 5**: AGREE — Establishing a rock-solid foundation with core actions and robust parsing mechanics is essential before expanding to more complex commands in future seasons.

---

## Cost Summary

**Total: $0.0000**

| Model | Cost |
|-------|------|
| kimi-k2.5:cloud | $0.0000 |
| qwen3-next:80b-cloud | $0.0000 |
| cogito-2.1:671b-cloud | $0.0000 |
