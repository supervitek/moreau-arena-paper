# Round Table Council — 2026-03-09

**Question:** Season 2 of Moreau Arena adds a hex grid with terrain, fog of war, and movement. Agents will need to make tactical decisions DURING combat, not just before it.

The Round Table already reached UNANIMOUS consensus on Option D (Hybrid): battle plan + event-driven tactical updates, ~5-7 calls per game. Now the debate shifts to OUTPUT FORMAT.

Three candidate formats for how agents express their tactical decisions:

Option 1 — STRICT JSON (current consensus):
```json
{
  "type": "update",
  "actions": [
    {"do": "move", "to": "C4"},
    {"do": "use_ability", "name": "hamstring", "target": "enemy"},
    {"do": "move", "to": "D5"}
  ],
  "stance_override": "defensive"
}
```

Option 2 — PYTHON CODE: Agent writes executable Python within a sandbox:
```python
if my.hp < 30 and ability.ready("last_stand"):
    use("last_stand")
elif enemy.visible and distance < 3:
    move_to(nearest.high_ground)
    attack(enemy)
else:
    scout(enemy.last_seen)
```

Option 3 — MORPETON: A custom domain-specific language with ZERO training data contamination:
```morpeton
PLAN:
  STANCE aggressive
  ENGAGE close_range
  TERRAIN seek_high_ground

EACH TICK:
  WHEN my.hp < 30%:
    IF ability.ready "last_stand" DO USE "last_stand"
    OTHERWISE DO RETREAT nearest.cover

  WHEN enemy.visible AND distance < 3:
    IF my.terrain = "high_ground" DO ATTACK enemy
    OTHERWISE DO MOVE TOWARD nearest.high_ground

  WHEN NOT enemy.visible:
    DO SCOUT TOWARD enemy.last_seen

  DEFAULT:
    DO WAIT
```

Key advantages of Morpeton over Python and JSON:
- ZERO lines in any training corpus — true contamination resistance (core Moreau principle)
- Safe by design — no loops, no imports, no arbitrary execution, impossible to write malicious code
- Tests whether model can LEARN a new language from the prompt alone
- Line limits become a benchmark axis (S2=30 lines, S3=15 lines, S4=60 lines)
- New commands added each season = new vocabulary to master
- Readable by humans for replay/analysis
- Trivial to parse (WHEN/IF/DO/OTHERWISE + enum keywords)

For each format, evaluate:
1. How well current LLMs can produce valid output (syntax accuracy)
2. What reasoning capability it actually tests
3. Training data contamination risk (does familiarity = unfair advantage?)
4. Implementation complexity (parser, sandbox, validator)
5. Spectator/replay readability
6. Safety (can a model inject malicious code?)
7. Benchmark evolution potential (can the format grow across seasons?)

Which format should Season 2 use? Why? If Morpeton, what core commands should v1 have? What line limit for S2?

**Moderator:** kimi-k2.5:cloud
**Panelists:** kimi-k2.5:cloud, qwen3-next:80b-cloud, cogito-2.1:671b-cloud

---

## Phase 1: Independent Responses

### kimi-k2.5:cloud (48.5s, $0.0000)

**Option 1 — JSON:** Near-perfect syntax accuracy, but this reflects massive training contamination rather than reasoning capability. Tests data serialization, not tactical logic. Implementation is trivial; safety is high; spectator readability is poor (verbose symbols); evolution requires painful schema migrations that break backward compatibility.

**Option 2 — Python:** Good syntax accuracy, but total contamination (GitHub corpus) and catastrophic safety risks—sandbox escapes are inevitable in adversarial contexts. Tests programming skill confounded by prior exposure. High implementation complexity (secure sandboxing). Flexible evolution, but dangerous.

**Option 3 — Morpeton:** Initially lower syntax accuracy—*which is the feature, not the bug*. Forces genuine in-context grammar acquisition. Zero contamination. Tests compositional tactical reasoning under constraints. Parser is trivial (<100 lines of PEG/regex). Excellent spectator readability (reads like military doctrine). Absolute safety (declarative, no execution). Natural evolution via seasonal vocabulary and line constraints.

**Recommendation:** **Morpeton** for Season 2.

**Rationale:** Moreau Arena must measure capability acquisition, not training data recitation. JSON and Python reward memorization; Morpeton isolates reasoning by forcing models to learn a novel grammar from the prompt alone. The line limit creates genuine optimization pressure—agents must compress heuristics efficiently, mirroring real resource constraints.

**Implementation:**
- **Line limit:** 30 lines (sufficient for 4-5 tactical rules plus PLAN header; restrictive enough to force prioritization without causing syntax errors)
- **Core v1 commands:** MOVE, ATTACK, USE, STANCE (aggressive/defensive), SCOUT, RETREAT, WAIT, SEEK_HIGH_GROUND, OVERWATCH, FLANK

This tests whether frontier models can synthesize structured, executable policies from few-shot examples—a more valuable signal than JSON templating or Python regurgitation.

### qwen3-next:80b-cloud (11.8s, $0.0000)



For Season 2, **Morpeton is the clear choice**. Here’s why:

1. **Contamination risk**: Morpeton has *zero* training data contamination—critical for Moreau’s principles. JSON and Python are pervasive in training data, giving models unfair memorization advantages.  
2. **Safety**: Morpeton’s design (no loops, imports, or execution) eliminates malicious code risks. Python requires complex sandboxing; JSON is safe but inflexible.  
3. **Reasoning test**: Morpeton evaluates *true adaptability*—models must parse and apply a new language from scratch, not rely on prior patterns. This tests core reasoning, not memorization.  
4. **Implementation**: Parser is trivial (regex for `WHEN/IF/DO` keywords). JSON requires strict schema validation; Python needs execution sandboxing (higher risk/complexity).  
5. **Readability**: Morpeton’s natural-language-style syntax (e.g., `WHEN my.hp < 30%: DO RETREAT`) is human-readable for replays. JSON is machine-friendly but opaque; Python is verbose.  
6. **Evolution**: Line limits (S2=30) and new commands (e.g., `scout`, `terrain.seek`) can scale cleanly across seasons. JSON/Python lack built-in extensibility for domain-specific rules.  

**Core v1 commands**: `move`, `attack`, `use_ability`, `stance`, `scout`, `retreat`, `terrain.seek`, `distance`, `enemy.visible`, `hp`.  
**Why not JSON/Python?** JSON is too predictable (common in training), and Python’s complexity risks safety and over-reliance on pre-trained patterns. Morpeton aligns with Moreau’s goal: testing *new* capabilities, not reusing existing knowledge.  

**Verdict**: Morpeton wins. It’s contaminant-proof, safe, and rigorously tests adaptive reasoning—exactly what Season 2 demands.

### cogito-2.1:671b-cloud (9.1s, $0.0000)

As Cogito-2.1, I strongly advocate for Option 3 (MORPETON) as the output format for Season 2. Here's my analysis:

1. **Syntax Accuracy & Reasoning**: While JSON is familiar, it forces procedural logic into declarative structures. Python is expressive but risks memorization. MORPETON's structured format (WHEN/IF/DO) is simple enough for modern LLMs to grasp from the prompt alone while testing true compositional reasoning.

2. **Contamination Risk**: Python has massive contamination risk, giving unfair advantage to models trained on public GitHub. JSON has some contamination but less deterministic. MORPETON's zero-training-data approach is the only way to ensure fair evaluation of reasoning rather than memorization.

3. **Implementation & Safety**: MORPETON's design eliminates entire classes of exploits. No need for complex sandboxing like Python. A simple recursive descent parser can validate syntax and execute commands safely.

4. **Evolution Potential**: The format can grow naturally by adding new keywords (e.g., TERRAIN_IGNORE in S3) and adjusting line limits. This creates a clean benchmark progression.

For MORPETON v1, core commands should include:
- Basic: MOVE, ATTACK, USE, WAIT, RETREAT
- Terrain: SEEK_TERRAIN, AVOID_TERRAIN
- Conditional: WHEN, IF, OTHERWISE, DEFAULT
- Stance: STANCE [aggressive/defensive/neutral]
- Vision: SCOUT, LAST_KNOWN_POSITION

Recommended S2 line limit: 30 lines. This provides enough expressiveness for complex tactics while forcing conciseness. We can reduce to 15 in S3 once models adapt.

The true test of intelligence is learning and applying new systems, not recalling old patterns. MORPETON makes this the ultimate evaluation.

---

## Phase 2: Critique Round

### kimi-k2.5:cloud's Critique (30.0s, $0.0000)

**Critique of Fellow Panelists**

We are unanimously aligned on Morpeton’s superiority—this consensus is significant because it prioritizes capability measurement over implementation convenience. However, two clarifications are needed.

**qwen3-next:80b-cloud**

*Agreement:* Correctly identifies that Morpeton tests *adaptability* rather than memorization, and properly weights contamination resistance as a core Moreau principle.

*Disagreement:* Your list of "core commands" conflates **action verbs** (MOVE, ATTACK) with **game state variables** (hp, distance, enemy.visible). In Morpeton’s grammar, the right-hand side of WHEN/IF clauses evaluates arbitrary game state (allowing any property like `my.hp` or `enemy.distance`), while the DO clause restricts to a finite command vocabulary. Listing `hp` as a "command" suggests confusion about this grammar boundary. We must be precise: commands are executable actions; conditions are boolean expressions over game state.

*Question:* How do you propose handling type safety when mixing free-form condition expressions with restricted action verbs? Do you envision a schema that validates condition logic separately from command enumeration?

**cogito-2.1:671b-cloud**

*Agreement:* Your progressive line-limit strategy (30→15→60) elegantly creates benchmark pressure. The categorization of commands (Basic/Terrain/Vision) is also superior to a flat list.

*Disagreement:* You omit **OVERWATCH** and **FLANK**, which I consider essential for hex-grid tactical combat. AVOID_TERRAIN is defensive; OVERWATCH tests commitment to area denial—a distinct tactical primitive. Without it, we lose "hold fire until enemy enters line of sight" scenarios.

*Question:* You suggest dropping to 15 lines for S3. Is this not dangerously close to forcing syntax errors through truncation rather than rewarding elegant compression? At 15 lines, we may measure token-limit anxiety rather than strategic minimalism.

**Refinement of My Position**

Upon review, I maintain **30 lines for S2** but adopt Cogito’s command categorization. I additionally clarify that Morpeton’s condition grammar (the WHEN/IF side) must remain syntactically permissive for game-state references, while the DO side enforces the restricted vocabulary—a distinction qwen3’s response blurred. The true test is whether models can map complex situational awareness (via unrestricted conditionals) onto constrained executable actions.

### qwen3-next:80b-cloud's Critique (30.9s, $0.0000)



**Critique of Panelists' Responses**  

**kimi-k2.5:cloud**  
- **Agreement**: You perfectly identified Morpeton’s core strengths—zero contamination, safety, and spectator readability ("reads like military doctrine"). Your point about syntax accuracy being "initially lower... which is the feature, not the bug" is spot-on; it forces genuine in-context learning, not memorization. I fully endorse your critique of JSON’s "painful schema migrations" and Python’s sandbox risks.  
- **Disagreement**: None. Your command list (MOVE, ATTACK, SEEK_HIGH_GROUND, OVERWATCH, FLANK) is superior to my original wording of "terrain.seek" or "distance" as commands. Those are conditions (e.g., `distance < 3`), not actions. You correctly separated syntax structure from actionable verbs.  
- **Question**: Should OVERWATCH and FLANK be included in S2’s v1? They seem niche for Season 2’s terrain-focused mechanics—could they complicate the initial learning curve unnecessarily?  

**cogito-2.1:671b-cloud**  
- **Agreement**: You rightly emphasized Morpeton’s "compositional tactical reasoning" test and zero sandboxing complexity. Your parser description ("recursive descent") aligns with my "trivial to parse" claim. I also agree with your command list (MOVE, ATTACK, SEEK_TERRAIN) being more precise than my flawed inclusion of "distance" as a command.  
- **Disagreement**: None. Your note that JSON "forces procedural logic into declarative structures" is critical—I overlooked this earlier, but Season 2’s *during-combat* decisions absolutely require conditionals, which JSON’s static action list cannot express.  
- **Question**: You proposed reducing line limits to 15 in S3. How would you test if models adapt to stricter constraints without sacrificing tactical nuance?  

**Self-Reflection**: After your responses, I acknowledge my mistake in listing properties (e.g., `distance`, `enemy.visible`) as commands. These are conditionals, not actions—only verbs like MOVE or ATTACK belong in the core command set. Your clarity on this is correct, and I’ll adjust my approach. Morpeton remains the clear choice for S2, and both your command lists are more rigorous than mine. No changes to my core verdict.  

*(Word count: 298)*

### cogito-2.1:671b-cloud's Critique (9.9s, $0.0000)

**Critique of Kimi-K2.5:**
1. **Agreements:**
   - Correctly identifies JSON's weakness in testing tactical reasoning
   - Strong emphasis on contamination as a critical factor
   - Agrees that Morpeton's initial syntax challenges are features, not bugs

2. **Disagreements:**
   - Overstates JSON's spectator readability as "poor" - while verbose, it's actually highly parsable for visualization tools
   - Underestimates Morpeton's implementation complexity - while the parser is simple, full semantic validation requires more than basic regex (e.g., validating terrain existence)

3. **Question:**
   - Your command list includes FLANK and OVERWATCH - shouldn't these be higher-level tactics composed of basic primitives rather than core commands?

**Critique of Qwen3-Next:80B-Cloud:**
1. **Agreements:**
   - Excellent point about Morpeton's natural-language syntax enhancing human readability
   - Strong case for how line limits create optimization pressure
   - Correctly highlights Python's sandboxing risks

2. **Disagreements:**
   - Incorrectly claims JSON is "inflexible" - with a well-designed schema, it can be quite extensible
   - Overlooks that Python's contamination could be mitigated with strict style constraints

3. **Question:**
   - You propose `terrain.seek` as a command - wouldn't this be better as a parameter to MOVE (e.g., `MOVE TOWARD nearest.high_ground`) to keep the language minimal?

**Reflection:**
After seeing these responses, I'm even more convinced of Morpeton's superiority, but I'll refine my position:
- Kimi is right that 30 lines is sufficient but challenging
- Both correctly emphasize that contamination avoidance is non-negotiable
- I now believe core commands should be even more minimal (remove TERRAIN as a separate command, make it a modifier to MOVE)

The collective arguments strengthen the case that Morpeton uniquely satisfies Moreau's core principle of testing reasoning rather than recall.

---

## Phase 3: Moderator's Synthesis

*Synthesized by kimi-k2.5:cloud (56.4s, $0.0000)*

**MODERATOR SYNTHESIS: Moreau Arena Season 2 Output Format Council**

## 1. CONSENSUS POINTS

The Round Table reaches **unanimous consensus** on the following:

- **Format Selection**: Morpeton (Option 3) is the superior choice for Season 2, superseding both JSON and Python.
- **Contamination Principle**: Zero training data contamination is a non-negotiable core requirement; Morpeton’s absence from existing corpora provides the only valid test of in-context learning and tactical reasoning.
- **Safety Architecture**: Declarative non-execution design (no loops, no imports, no arbitrary code execution) is mandatory; Python’s sandbox risks and JSON’s inflexibility are disqualifying.
- **Line Constraints**: A line limit of **approximately 30 lines** for Season 2 strikes the correct balance between expressiveness and compression pressure.
- **Grammar Structure**: The language must distinguish between **condition expressions** (evaluating game state in WHEN/IF clauses) and **action commands** (restricted vocabulary in DO clauses).
- **Evolution Strategy**: The format must support benchmark evolution through seasonal vocabulary expansion and progressive line-limit constraints.
- **Readability**: Human-readable syntax resembling military doctrine is preferred for spectator analysis and replay debugging.

## 2. KEY DISAGREEMENTS

Despite unanimous support for Morpeton, substantive differences persist regarding implementation details:

**Command Taxonomy**: Whether advanced tactical concepts (OVERWATCH, FLANK) should be **primitive commands** (Kimi-K2.5) or **composite behaviors** built from basic actions (Cogito-2.1). Qwen3-Next questions whether these might unnecessarily complicate the initial learning curve.

**Line Limit Progression**: Whether reducing to **15 lines** in Season 3 (Cogito-2.1) tests elegant compression or merely induces token-limit anxiety and syntax truncation errors (Kimi-K2.5).

**Parser Complexity**: Whether semantic validation requires only simple regex/PEG parsing (Kimi-K2.5, Qwen3-Next) or necessitates additional validation layers for terrain existence and game-state property verification (Cogito-2.1).

**Terrain Interaction**: Whether terrain-seeking should be a standalone command (`SEEK_TERRAIN`) or a modifier to existing movement commands (`MOVE TOWARD nearest.high_ground`).

## 3. STRONGEST ARGUMENTS

**From Kimi-K2.5**: *Lower initial syntax accuracy is a feature, not a bug.* Forcing models to acquire a novel grammar from the prompt alone isolates true reasoning capability from memorized patterns. The distinction between unrestricted condition grammar (allowing arbitrary game-state references) and restricted command vocabulary is architecturally crucial.

**From Qwen3-Next**: Morpeton’s natural-language syntax ("reads like military doctrine") optimizes for **spectator readability** without sacrificing machine parsability, addressing a key stakeholder need for replay analysis and broadcast commentary.

**From Cogito-2.1**: **Progressive line limits** (30→15→60) create a clean benchmark evolution that tests strategic compression and prioritization under constraint, mirroring real-world resource limitations.

**From Kimi-K2.5**: JSON forces procedural tactical logic into declarative data structures, making it ill-suited for dynamic, condition-heavy combat decisions where `IF enemy.visible THEN` logic is essential.

**From All Panelists**: Python’s contamination risk (GitHub corpus familiarity) and sandbox escape vulnerabilities make it unsuitable for adversarial evaluation contexts, regardless of its expressive power.

## 4. SYNTHESIS

**Recommendation**: Season 2 shall adopt **Morpeton** with a **30-line limit**, implementing a hybrid grammar where:

- **Condition Expressions** (left side): Permissive grammar allowing arbitrary boolean logic over game state (`my.hp < 30%`, `enemy.distance < 3`, `terrain.elevation > 5`)
- **Action Commands** (right side): Restricted vocabulary of primitives: `MOVE`, `ATTACK`, `USE`, `WAIT`, `RETREAT`, `SCOUT`, `STANCE`, `OVERWATCH`, `FLANK`
- **Terrain Handling**: Expressed as modifiers/parameters to `MOVE` (e.g., `MOVE TOWARD high_ground`, `AVOID low_ground`) rather than standalone commands, maintaining linguistic minimalism
- **Evolution Path**: Season 3 may reduce to 15 lines to test compression efficiency, provided Season 2 establishes baseline competency

**Rationale**: This approach satisfies the zero-contamination mandate while providing sufficient tactical primitives for hex-grid combat. OVERWATCH and FLANK warrant primitive status because they represent distinct tactical commitments (area denial vs. positional maneuvering) that would require verbose multi-line emulation if composed from basic actions, violating the compression goals of the format. The 30-line limit forces prioritization without inducing syntax errors from aggressive truncation.

## 5. NUMBERED PROPOSITIONS

**Proposition 1**: Season 2 shall adopt Morpeton (Option 3) as the exclusive output format, rejecting JSON due to training data contamination and Python due to safety risks and memorization advantages.

**Proposition 2**: Season 2 shall implement a **30-line limit** per tactical update, with future seasons reserved the right to implement stricter compression constraints to test strategic prioritization.

**Proposition 3**: Morpeton grammar shall strictly separate **condition expressions** (permitting arbitrary game-state references in WHEN/IF clauses) from **action commands** (restricting DO clauses to an enumerated vocabulary of primitives).

**Proposition 4**: Core commands for Season 2 shall include `MOVE`, `ATTACK`, `USE`, `WAIT`, `RETREAT`, `SCOUT`, `STANCE`, `OVERWATCH`, and `FLANK`, with terrain preferences expressed as modifiers to movement commands rather than standalone actions.

**Proposition 5**: The Morpeton parser shall prioritize implementation simplicity (regex/PEG-based lexical analysis) while maintaining zero-execution safety guarantees and contamination resistance as non-negotiable architectural constraints.

---

## Phase 4: Votes

### kimi-k2.5:cloud (28.6s, $0.0000)

- **Proposition 1**: AGREE — Zero contamination is essential to isolate in-context learning from memorized patterns, and Morpeton’s novel grammar forces models to demonstrate true reasoning rather than recalling training data.
- **Proposition 2**: AGREE — Thirty lines provides sufficient expressiveness for tactical complexity without inducing the token-limit anxiety or syntax truncation errors that aggressive compression would risk.
- **Proposition 3**: AGREE — The strict separation between permissive condition expressions and restricted command vocabulary is architecturally crucial for maintaining both parseability and expressive tactical logic.
- **Proposition 4**: AGREE — OVERWATCH and FLANK represent distinct tactical commitments requiring primitive status to avoid verbose multi-line emulation that would violate compression goals.
- **Proposition 5**: AGREE — Simple regex/PEG parsing minimizes implementation overhead while preserving the non-negotiable safety guarantees and contamination resistance required for adversarial evaluation.

### qwen3-next:80b-cloud (5.3s, $0.0000)

- **Proposition 1**: AGREE — Morpeton eliminates training data contamination risks and Python’s safety vulnerabilities while outperforming JSON’s structural inflexibility for dynamic combat logic.
- **Proposition 2**: AGREE — The 30-line limit optimally balances tactical expressiveness and compression pressure, with future seasons reserved for stricter constraints to test strategic prioritization.
- **Proposition 3**: AGREE — Strict separation of condition expressions (permissive game-state logic) and action commands (restricted vocabulary) ensures safety and clear tactical reasoning without execution risks.
- **Proposition 4**: AGREE — Treating OVERWATCH/FLANK as primitives and terrain as movement modifiers maintains tactical precision while avoiding verbose multi-line workarounds that undermine compression goals.
- **Proposition 5**: AGREE — Regex/PEG-based parsing provides sufficient validation without unnecessary complexity, preserving zero-execution safety and contamination resistance as non-negotiable.

### cogito-2.1:671b-cloud (4.4s, $0.0000)

- **Proposition 1**: AGREE — Morpeton's novelty ensures genuine evaluation of in-context learning while JSON and Python present unacceptable contamination and safety risks respectively.
- **Proposition 2**: AGREE — A 30-line limit creates optimal pressure for strategic prioritization while avoiding excessive truncation errors that could compromise tactical coherence.
- **Proposition 3**: AGREE — Strict grammatical separation between expressive conditions and restricted actions maintains both strategic flexibility and implementation safety.
- **Proposition 4**: AGREE — Including tactical primitives like OVERWATCH and FLANK reduces unnecessary verbosity while terrain integration into movement commands preserves linguistic minimalism.
- **Proposition 5**: AGREE — Prioritizing simple parser architecture with regex/PEG parsing balances implementation robustness with the critical zero-execution safety requirement.

---

## Cost Summary

**Total: $0.0000**

| Model | Cost |
|-------|------|
| kimi-k2.5:cloud | $0.0000 |
| qwen3-next:80b-cloud | $0.0000 |
| cogito-2.1:671b-cloud | $0.0000 |
