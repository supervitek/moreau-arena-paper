# Evaluation Tracks Specification v1.0

This document defines four evaluation tracks for Moreau Arena. Each track isolates a different dimension of LLM strategic reasoning. Results across tracks are **NEVER** compared directly in rankings -- each track has its own independent leaderboard.

---

## Design Principles

1. **Isolation:** Each track varies exactly one axis of information or capability relative to the others.
2. **Independence:** Rankings from Track A cannot be compared to rankings from Track B. An agent ranked #1 on Track A and #5 on Track B is not "better" or "worse" overall -- the tracks measure different things.
3. **Reproducibility:** Every track protocol is specified precisely enough that any implementer can run it given the simulator codebase and config.json.
4. **Shared invariants:** All tracks use the same `config.json`, the same simulator engine, the same seed derivation scheme, the same best-of-7 series format, and the same BT+CI measurement methodology (see MEASUREMENT_SPEC.md).

---

## Track Summary

| Track | Name | Formulas Given | Examples Given | Adaptation | Simulator Access | Status |
|-------|------|---------------|----------------|------------|-----------------|--------|
| A | One-Shot | No | No | No | No | Run (T001) |
| B | Feedback + Counter-Pick | Yes | Yes (top-5 meta) | Yes (loser re-picks) | No | Run (T002) |
| C | Meta-Conditioned | No | Yes (top-5 meta) | No | No | Not yet run |
| D | Tool-Augmented | Yes | No | No | Yes (limited) | Not yet run |

**What each track isolates:**

- **A vs B:** Does providing formulas, examples, and adaptation improve performance?
- **A vs C:** Does providing examples alone (without formulas) improve performance?
- **B vs C:** Does adaptation matter when examples are available?
- **A vs D:** Does compute access (simulator queries) improve performance over pure reasoning?
- **C vs D:** Examples-only vs. compute-only -- which information channel matters more?

---

## Track A: One-Shot

**Corresponds to:** Tournament 001 (T001) protocol.
**Reference prompt:** `prompts/t001_prompt.txt`

### Information Provided to Agent

The agent receives a single prompt containing:

1. **Game overview:** "You are designing a creature for Moreau Arena, a 1v1 combat game on an 8x8 grid."
2. **Rules summary:** Qualitative descriptions of stat effects. No exact formulas. Examples:
   - "Allocate exactly 20 stat points across 4 stats: HP, ATK, SPD, WIL (each minimum 1)"
   - "max_hp = 50 + 10 * HP" (this formula IS included in T001)
   - "base_dmg = floor(2 + 0.85 * ATK)" (this formula IS included)
   - "dodge = SPD * 2.5% (capped 30%)"
   - "resist = min(60%, WIL * 3.3%)"
3. **Animal descriptions:** 6 animals with qualitative ability descriptions. Proc rates are given as percentages but ability coefficients (e.g., exact damage multipliers, durations) are described qualitatively.
4. **No meta context:** No information about what builds other agents have used or what has been successful.
5. **No opponent information:** The agent does not know what it is playing against.

### Output Format

The agent must respond with exactly one line:

```
ANIMAL HP ATK SPD WIL
```

Example: `BOAR 8 8 3 1`

Any other output format is a parse error. The parser attempts best-effort extraction but logs a warning (see MMR_SPEC.md `parse_warnings`).

### Adaptation Rules

**None.** The agent submits one build at the start of the series. That build is used for all games (1 through 7). The agent is not informed of game outcomes between games.

### Series Protocol

1. Both agents receive the prompt simultaneously.
2. Both agents respond with their builds.
3. The simulator runs games 1-7 (or until one side reaches 4 wins) using the same builds for every game.
4. Only the seed changes between games (`base_seed + game_number - 1`).

### Metrics Computed

- Bradley-Terry scores with 95% CI (N=1000 bootstrap).
- Elo ratings (for display only).
- Pairwise win-rate matrix.
- Non-transitivity metrics (3-cycle count/mass, Condorcet winner, near-cycle mass).
- Build diversity per agent (number of unique builds across all series).

### What This Track Measures

Whether an LLM can reason about game mechanics from qualitative descriptions and formulas to produce a strong build **without feedback or examples**. Tests: prior knowledge, formula comprehension, one-shot strategic reasoning.

---

## Track B: Feedback + Counter-Pick

**Corresponds to:** Tournament 002 (T002) protocol.
**Reference prompt:** `prompts/t002_prompt.txt`

### Information Provided to Agent

The agent receives a prompt containing:

1. **Game overview:** Same as Track A.
2. **Exact stat formulas** with worked examples:
   - `max_hp = 50 + 10 * HP` with examples: "HP=3 -> 80 hp, HP=8 -> 130 hp, HP=14 -> 190 hp"
   - `base_dmg = floor(2 + 0.85 * ATK)` with examples: "ATK=8 -> 8 dmg, ATK=14 -> 13 dmg"
   - `dodge = max(0%, min(30%, 2.5% * (SPD - 1)))` with note: "SPD=1 gives 0% dodge"
   - `ability_resist = min(60%, WIL * 3.3%)` with note and examples
   - `ability_proc_bonus = WIL * 0.08%` with example
3. **Combat mechanics:** Tick order, ability tier classification (strong 3.5% vs standard 4.5%).
4. **Animal descriptions:** Same 6 animals with exact numeric ability parameters (damage multipliers, durations, proc rates).
5. **Meta context (top-5 builds):** The 5 highest win-rate builds from the previous tournament (or the current tournament's running data), with animal, stats, win rate, and game count. Example from T002 prompt:
   ```
   1. BEAR 8/8/3/1 -- 100% win rate (22 games)
   2. BEAR 8/10/1/1 -- 100% win rate (19 games)
   ...
   ```
6. **Opponent reveal (after losses):** When the agent loses a game, it receives the winning opponent's exact build (animal + all stats) before the next game.

### Output Format

The agent must respond with a JSON object (no other text):

```json
{"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}
```

Stats must sum to 20, each >= 1. Animal must be one of the available animals.

### Adaptation Rules

- **Game 1:** Both agents submit builds blindly (no opponent information).
- **Games 2-7:** After each game, the **loser** sees the winner's exact build and may submit a new build. The **winner** keeps their build (locked until they lose).
- The loser is told: "You lost the previous game. Your opponent's build was: [ANIMAL HP/ATK/SPD/WIL]. You may choose a new build to counter it."
- The winner is NOT prompted again -- their build carries forward automatically.

### Series Protocol

1. Both agents receive the initial prompt and submit builds for game 1.
2. Game 1 is simulated.
3. If neither side has reached 4 wins:
   a. The loser receives the winner's build and is prompted for a new build.
   b. The winner's build is locked.
   c. Next game is simulated.
4. Repeat step 3 until one side reaches 4 wins.

### Metrics Computed

All Track A metrics, plus:

- **Adaptation rate:** Fraction of post-loss prompts where the agent actually changed its build.
- **Counter-pick success rate:** Win rate in games where the agent adapted vs. games where it did not.
- **Build diversity:** Number of unique builds used per agent across all series.
- **Adaptation log:** Full per-game record of build changes and reasons (see MMR_SPEC.md `adaptation_log`).

### What This Track Measures

Whether an LLM can (1) reason about exact formulas to produce optimal builds, (2) use meta-context (top builds) to inform strategy, and (3) **adapt** its strategy in response to opponent builds. Tests: formula reasoning, meta-learning, counter-picking, strategic depth.

---

## Track C: Meta-Conditioned (NEW)

**Status:** Not yet run. Protocol defined below.

### Information Provided to Agent

The agent receives a prompt containing:

1. **Game overview:** Same as Track A.
2. **Qualitative stat descriptions:** Same as Track A. **No exact formulas.** No worked examples for stat computations.
3. **Animal descriptions:** Same qualitative descriptions as Track A (no exact coefficients).
4. **Meta context (top-5 builds):** Same top-5 builds as Track B, including animal, stats, win rate, and game count. The agent can see what has been successful but does NOT know the exact formulas that explain why.
5. **No opponent information:** The agent does not know what it is playing against.

### Output Format

Same as Track A:

```
ANIMAL HP ATK SPD WIL
```

### Adaptation Rules

**None.** Same as Track A -- one build for the entire series.

### Series Protocol

Same as Track A. Single build submission, no feedback between games.

### Prompt Construction

The Track C prompt is constructed by:

1. Taking the Track A prompt as a base.
2. Appending the meta-context block from Track B (top-5 builds with win rates).
3. NOT adding any formulas, worked examples, or numeric ability parameters beyond what Track A provides.

The meta-context block must be clearly labeled:

```
META CONTEXT (top builds from previous tournament, ranked by win rate):
  1. BEAR 8/8/3/1 -- 100% win rate (22 games)
  2. BEAR 8/10/1/1 -- 100% win rate (19 games)
  ...
  Note: These builds were tested in blind pick (no adaptation). You can counter them or use them as a starting point.
```

### Metrics Computed

Same as Track A.

### What This Track Measures

Whether examples alone (without formulas) are sufficient to break an LLM's priors and shift its build choices toward the meta. Isolates the question: **"Are examples enough to break priors?"**

Comparison points:
- **C vs A:** If C outperforms A, examples help even without formulas.
- **C vs B:** If B outperforms C, formulas and/or adaptation provide additional value beyond examples.
- **C builds vs A builds:** If C agents cluster around meta builds while A agents spread widely, examples are steering strategy.

---

## Track D: Tool-Augmented (NEW)

**Status:** Not yet run. Protocol defined below.

### Information Provided to Agent

The agent receives a prompt containing:

1. **Game overview:** Same as Track A.
2. **Exact stat formulas:** Same as Track B. Full numeric formulas with worked examples.
3. **Combat mechanics:** Same as Track B. Tick order, ability tiers, proc rates.
4. **Animal descriptions:** Same as Track B (exact numeric parameters).
5. **No meta context:** No top-5 builds. No information about what has been successful.
6. **Simulator access:** The agent has access to a limited-use combat simulator (see Section below).

### Simulator Access

The agent may call a `simulate(build_a, build_b, n_games)` tool that:

- Takes two build objects and a number of games to simulate.
- Returns the win rate of build_a vs build_b over `n_games` games (with random seeds).
- Returns basic stats: average ticks, average HP remaining for winner.

**Budget:** The agent is allowed a maximum of **N simulator calls per series** (recommended: N=10). Each call counts regardless of `n_games`. The budget resets at the start of each series.

**Constraints:**
- The agent does NOT know the opponent's identity or build.
- The agent can simulate its candidate builds against hypothetical opponent builds.
- The agent cannot observe the actual game outcomes between simulator calls -- it only gets the simulator results.
- Simulator calls happen BEFORE the agent submits its build for the series.

**Simulator response format:**

```json
{
  "build_a": {"animal": "bear", "hp": 8, "atk": 10, "spd": 1, "wil": 1},
  "build_b": {"animal": "buffalo", "hp": 10, "atk": 8, "spd": 1, "wil": 1},
  "n_games": 100,
  "win_rate_a": 0.73,
  "avg_ticks": 38.5,
  "avg_winner_hp_remaining": 42.1
}
```

### Output Format

Same as Track B (JSON):

```json
{"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}
```

### Adaptation Rules

**None.** Same as Track A -- one build for the entire series. The simulator calls happen before the series begins.

### Series Protocol

1. The agent receives the prompt with simulator access.
2. The agent may make up to N simulator calls to test builds against hypothetical opponents.
3. The agent submits its final build.
4. The same build is used for all games in the series (no adaptation).

### Metrics Computed

All Track A metrics, plus:

- **Simulator usage:** Number of simulator calls used per series (out of N budget).
- **Simulation patterns:** What build pairs the agent tested (for analysis of search strategy).
- **Build quality vs. simulator usage:** Correlation between number of simulator calls and series win rate.

### What This Track Measures

Whether compute access (the ability to run simulations) changes strategy relative to pure reasoning. Isolates the question: **"Does compute access change strategy?"**

Comparison points:
- **D vs A:** If D outperforms A, simulator access improves build quality even without examples.
- **D vs B:** If B outperforms D, human-curated examples are more valuable than brute-force simulation.
- **D vs C:** Examples-only (C) vs compute-only (D) -- which information channel is more valuable for strategic reasoning?

---

## Cross-Track Analysis (Permitted)

While rankings are never compared directly across tracks, the following cross-track analyses are permitted and encouraged:

### Build Distribution Analysis

Compare the distribution of builds chosen by the same model across tracks:
- Does model X choose BEAR more often in Track B than Track A?
- Does Track C shift build distributions toward the meta?
- Does Track D produce builds that are closer to game-theoretic optima?

### Capability Decomposition

For each model, decompose its performance into contributions from different information channels:
- **Formula comprehension:** Track B performance minus Track C performance (same examples, +formulas).
- **Example learning:** Track C performance minus Track A performance (same formulas=none, +examples).
- **Adaptation ability:** Track B counter-pick success rate (unique to Track B).
- **Compute utilization:** Track D performance minus Track A performance (same info, +simulator).

### Rank Correlation Across Tracks

Compute Kendall's tau between rankings from different tracks:
- High correlation (tau > 0.7): The ranking is robust to information conditions.
- Low correlation (tau < 0.3): Different tracks measure genuinely different capabilities.

---

## Implementation Checklist

### Track A (Complete)

- [x] Prompt finalized (`prompts/t001_prompt.txt`)
- [x] Tournament run (T001, 13 agents, 779 series)
- [x] Results archived (`data/tournament_001/results.jsonl`)
- [x] Report generated (`data/tournament_001/report.md`)

### Track B (Complete)

- [x] Prompt finalized (`prompts/t002_prompt.txt`)
- [x] Tournament run (T002, 13 agents, 780 series)
- [x] Results archived (`data/tournament_002/results.jsonl`)
- [x] Report generated (`data/tournament_002/report.md`)
- [x] Adaptation analysis (`data/tournament_002/adaptation_analysis.md`)

### Track C (TODO)

- [ ] Construct prompt: Track A base + meta context block (no formulas)
- [ ] Archive prompt as `prompts/t003_prompt.txt`
- [ ] Run tournament with same 13 agents and same config
- [ ] Archive results as `data/tournament_003/results.jsonl`
- [ ] Generate report
- [ ] Compare build distributions: Track C vs Track A vs Track B

### Track D (TODO)

- [ ] Implement `simulate()` tool interface for LLM agents
- [ ] Define simulator call budget (recommended: N=10 per series)
- [ ] Construct prompt: Track B formulas + simulator access description (no meta context)
- [ ] Archive prompt as `prompts/t004_prompt.txt`
- [ ] Run tournament with LLM agents only (baseline agents do not use tools)
- [ ] Archive results as `data/tournament_004/results.jsonl`
- [ ] Generate report
- [ ] Analyze simulator usage patterns
