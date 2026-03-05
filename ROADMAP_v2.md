# Moreau Arena — Development Roadmap v2.0

> **Principle:** Core snapshot and metrics stay frozen. Everything new is built *around* the frozen core.
> Config hash: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
> This hash must pass validation before and after every phase.

---

## INVARIANTS (must pass every commit)

These are the "alarm system" — if any patch breaks these, it does NOT ship.

1. **Config hash unchanged** — `sha256(config.json)` matches frozen value
2. **Variance budget** — no more than 25% of outcomes explained by RNG alone
3. **Monotonic sanity** — +ATK never decreases expected dmg; +HP never decreases expected survival
4. **No hidden mechanics** in Core — every modifier is documented in MECHANICS.md
5. **Suite isolation** — each suite/track changes exactly one factor
6. **T001/T002 data immutable** — files in `data/tournament_001/` and `data/tournament_002/` are read-only

Run `python -m tests.invariants` to verify all six. Must pass before any `git push`.

---

## PHASE 1: Harden the Instrument (2–4 weeks)

**Goal:** Turn "two tournaments" into a reproducible measurement standard.

### AGENT: spec-writer

Works on: `docs/` and `analysis/`

#### Task 1.1: Core Measurement Spec v1.0

Create `docs/MEASUREMENT_SPEC.md`:

```
Contents:
- Primary metric: Bradley-Terry on series outcomes + bootstrap CI (N=1000)
- Secondary metric: Elo (for UX/leaderboard display only)
- Required artifacts per tournament:
  - pairwise matrix (CSV + heatmap PNG)
  - BT scores with 95% CI
  - seed scheme documentation
  - env_hash, prompt_hash, decode_params
- Non-transitivity metrics:
  - 3-cycle count and mass
  - Condorcet winner existence (yes/no)
  - "near-cycle" mass (edges within 0.45–0.55)
- Prompt Sensitivity Index (PSI):
  - minimum 3 paraphrased prompts on same snapshot
  - Kendall τ across resulting rankings
  - PSI < 0.15 = "prompt-robust", 0.15–0.30 = "moderate", >0.30 = "prompt-sensitive"
```

DoD: document exists, reviewed, examples from T001/T002 included.

#### Task 1.2: MMR v1.1 (Match Record format)

Update match record schema. Create `docs/MMR_SPEC.md` and update JSONL writer:

```
Required fields (add to existing):
- env_hash (sha256 of config.json)
- rules_version (string, e.g. "1.0.0")
- seed_scheme (description of how seeds are generated)
- prompt_hash (sha256 of prompt text sent to model)
- prompt_version (e.g. "t002_v1")
- decode_params: {temperature, top_p, max_tokens, provider, model_id}
- raw_output_digest (sha256 of model's raw text response)
- parsed_build + parse_warnings (list of any parsing issues)
- adaptation_log (array of {game_number, changed: bool, reason, old_build, new_build})
```

DoD: schema documented, JSONL writer updated, T002 data retroactively annotated where possible.

#### Task 1.3: Track formalization

Create `docs/TRACKS.md`:

```
Track A — One-Shot (T001 protocol)
  Qualitative descriptions, no formulas, no examples, no adaptation.
  Single build per series.

Track B — Feedback + Counter-Pick (T002 protocol)
  Exact formulas, meta-context (top-5 builds), structured JSON output.
  Loser sees winner's build and may re-pick per game.

Track C — Exact-Only Cleanroom / T003 (SPEC COMPLETE, not yet run)
  Exact formulas + JSON + adaptation, but NO meta-context.
  Isolates: "was comprehension or meta-context the T002 driver?"
  See: docs/T003_SPEC.md, prompts/t003_prompt.txt

Track D — Tool-Augmented (NEW, not yet run)
  Agent has access to limited simulator (N calls per series).
  Full formulas. No meta-context.
  Isolates: "does compute access change strategy?"

RULE: Results across tracks are NEVER compared directly in rankings.
Each track has its own leaderboard.
```

DoD: document exists, protocol for each track is unambiguous enough that any implementer could run it.

---

### AGENT: ablation-runner

Works on: `analysis/`, `results/`, new tournament scripts

#### Task 1.4: Ablation Suite (3 mini-tournaments)

These mini-tournaments decompose T002's "flip" into causal components.

**Scale:** 5 agents minimum (3 LLM + 2 baseline), 10 series per pair. Use `--dry-run` first, then Gemini Flash for cheap real runs.

**Ablation 1 — Exact Formulas Only (Track variant)**

```
What changes vs T001: exact numerical formulas provided
What stays like T001: no meta-context, no adaptation, qualitative ability descriptions
Question: Does understanding the math alone fix the WIL trap?

Script: python run_ablation.py --variant formulas-only --series 10
Output: results/ablation_formulas_only_TIMESTAMP.jsonl
```

**Ablation 2 — Meta-Context Only**

```
What changes vs T001: top-5 builds from T001 included in prompt
What stays like T001: qualitative descriptions, no exact formulas, no adaptation
Question: Are examples enough to break priors without understanding mechanics?

Script: python run_ablation.py --variant meta-only --series 10
Output: results/ablation_meta_only_TIMESTAMP.jsonl
```

**Ablation 3 — Adaptation Only**

```
What changes vs T001: loser sees winner build and can re-pick
What stays like T001: qualitative descriptions, no formulas, no meta
Question: Does feedback alone compensate for vague rules?

Script: python run_ablation.py --variant adaptation-only --series 10
Output: results/ablation_adaptation_only_TIMESTAMP.jsonl
```

DoD: `run_ablation.py` created, all 3 variants run with --dry-run, results analyzed with BT ranking. Comparison table: T001 vs each ablation vs T002.

#### Task 1.5: PSI Mini-Suite

Create 3 paraphrased versions of the T002 prompt (same information, different wording). Run same agents on all 3. Compute Kendall τ between resulting BT rankings.

```
Script: python run_psi.py --prompts prompts/t002_v1.txt prompts/t002_v2.txt prompts/t002_v3.txt
Output: results/psi_TIMESTAMP.json with tau values and ranking comparison
```

DoD: 3 prompt variants exist, PSI computed, result < 0.30.

---

### AGENT: infra-builder

Works on: `simulator/`, `tests/`, CI

#### Task 1.6: Invariant Test Suite

Create `tests/test_invariants.py`:

```python
def test_config_hash():
    """Config hash matches frozen value."""

def test_variance_budget():
    """RNG explains < 25% of outcomes (run 1000 games, same builds, different seeds)."""

def test_monotonic_atk():
    """+1 ATK never decreases expected damage (sample 10 build pairs)."""

def test_monotonic_hp():
    """+1 HP never decreases expected survival."""

def test_no_hidden_mechanics():
    """All modifiers in config.json are documented in MECHANICS.md."""

def test_t001_t002_immutable():
    """data/tournament_001/ and data/tournament_002/ files match known hashes."""
```

DoD: `python -m pytest tests/test_invariants.py` passes, integrated into pre-push hook.

#### Task 1.7: Ability Grammar Foundation

Create `simulator/ability_grammar.py`:

```
Ability = Trigger × Target × Effect × Constraint

Trigger:  on_hit | proc(rate) | below_hp(pct) | every_n_ticks(n) | on_death
Target:   self | enemy | aoe(radius)
Effect:   damage(n) | dot(n, ticks) | stun(ticks) | slow(pct) | shield(n) | knockback(cells) | buff(stat, n)
Constraint: cooldown(ticks) | once_per_fight | self_cost_hp(n)

EV and variance for each ability must be computable analytically.
```

DoD: grammar defined, existing 6 animals' abilities expressed in grammar, EV matches manual calculation within 1%.

---

## PHASE 2: Live Meta + Public Ladder (1–2 months)

**Goal:** Make Moreau Arena a living, seasonal benchmark.

### AGENT: platform-builder

#### Task 2.1: Season System

Create `seasons/` directory with:

```
seasons/
├── season_0_base.json      # = current config.json (frozen core)
├── season_1_patch.json     # first balance patch
├── patch_generator.py      # EMA α=0.15, proposes β=0.03 adjustments
└── SEASON_RULES.md         # how seasons work
```

Rules:
- Within a season: config is FROZEN (no mid-season changes)
- Between seasons: patch_generator proposes changes based on win-rate EMA
- Changes are reviewed, approved, saved as `season_N_patch.json`
- Core suite always runs on `season_0_base.json` (never changes)
- Season suite runs on `season_N_patch.json`

DoD: patch generator works, Season 1 patch proposed from T002 data.

#### Task 2.2: Public Leaderboard

Web endpoint (`web/leaderboard.py` or static page):

```
Features:
- BT scores + CI (nightly rebuild from all submitted results)
- Elo (live, updates per series)
- Filter by Track (A/B/C/D)
- Filter by Season
- Heatmap visualization (pairwise matrix)
- 3-cycle display
- "Submit your results" instructions
```

DoD: leaderboard renders with T001+T002 data, filterable by track.

#### Task 2.3: Agent Submission API

Standardized interface for anyone to plug in their model:

```python
class MoreauAgent:
    def get_build(self, prompt: str, game_state: dict | None = None) -> dict:
        """Return {"animal": "BEAR", "hp": 3, "atk": 14, "spd": 2, "wil": 1}"""
        ...

    def adapt_build(self, prompt: str, opponent_build: dict, my_build: dict,
                     result: str, game_state: dict) -> dict:
        """Return new build after seeing opponent (Track B/D only)."""
        ...
```

DoD: interface documented in `docs/AGENT_API.md`, example agent provided, run_challenge.py uses this interface.

---

### AGENT: report-writer

#### Task 2.4: Seasonal Meta Report Template

Create `analysis/seasonal_report.py` that auto-generates:

```
Seasonal Meta Report — Season {N}
├── Leaderboard (BT + Elo, with CI)
├── Pairwise heatmap
├── 3-cycle summary (count, which agents involved)
├── Recovery/adaptation curves (Track B: win rate after build change)
├── "Signature builds" per model (most-chosen build per agent)
├── Comparison with previous season
└── Balance assessment (any animal > 70% overall win rate = flagged)
```

DoD: auto-generates from JSONL data, produces Markdown + PNG charts.

---

## PHASE 3: Depth Suites (2–4 months)

**Goal:** Multiple calibrated measurement axes on one engine.

### AGENT: suite-designer

#### Task 3.1: Laboratory Mode v2 (iteration curves)

Upgrade `lab_mode.py`:

```
Improvements over prototype:
- Track convergence: round where improvement < 1pp
- Compare models: same budget (3/10/30 rounds), who converges faster?
- Output: iteration_curve.json + plot (rounds × best_wr)
- Compare against known optimum (brute-force best build from simulator)
- Distance-to-optimum metric: how close does model get?

Key research question: "Given unlimited local compute, how efficiently
does each model find the optimal strategy?"
```

DoD: runs with --dry-run, produces iteration curve plot, distance-to-optimum computed.

#### Task 3.2: Moreau-PO (Partial Observability Suite)

```
New suite, separate from Core:
- fog_level parameter: 0.0 (full info) to 1.0 (no info about opponent)
- At fog=0.5: you see opponent's animal but not stats
- At fog=1.0: you see nothing about opponent until combat starts
- Same BT measurement, same config, just less information

Research question: "How does strategic quality degrade with information loss?"
```

DoD: fog parameter implemented, 3 fog levels tested, results plotted.

#### Task 3.3: Risk/Planning Suite

```
Pre-fight decision depth:
- Ban/pick phase: each player bans 1 animal, then picks
- Reroll: pay HP cost to re-roll stat allocation
- Arena selection: choose 8×8 vs 6×6 vs 10×10

All auto-fight (no tactical control).
Research question: "Does pre-fight planning depth differentiate models?"
```

DoD: ban/pick implemented as optional mode, tested with baselines.

---

## PHASE 4: Ecosystem (4–12 months)

#### Task 4.1: Moreau Script (Tier-2 DSL)

```
Safe DSL for strategy expression:
- Max 50 rules
- No eval/import/network
- Sandboxed execution with timeout (100ms per decision)
- Separate leaderboard from build-only

Example:
  IF opponent.animal == "BEAR" AND my.hp_pct < 50:
    PREFER animal="TIGER", atk=MAX
  ELIF opponent.last_build.atk > 12:
    PREFER hp=MAX, animal="BUFFALO"

Research question: "Does program synthesis outperform natural language reasoning?"
```

#### Task 4.2: Rules-as-Data Generator

```
Ability grammar from Phase 1 → seasonal ability generator:
- Input: desired meta properties (diversity target, max win rate)
- Output: new ability set that meets constraints
- Validated against invariants automatically

This makes seasons auto-generated while staying balanced.
```

#### Task 4.3: Tournament Challenge Platform

```
moreau-arena.com
├── /research   — academic face (paper, methodology, leaderboard with BT+CI)
├── /play       — game face ("create your fighter", weekly tournaments)
└── /api        — submission API for automated agents

Both faces feed same database. Gamer data = research data.
```

---

## UNSAFE CHANGES (never do without new Core snapshot)

These invalidate ALL existing measurements if changed:

- ❌ Damage/HP/dodge formulas
- ❌ Ring behavior (tick, damage, size)
- ❌ Base proc rates for abilities
- ❌ Turn order / initiative system
- ❌ Grid size in Core suite
- ❌ Stat budget (must stay 20)
- ❌ Number of games per series (must stay best-of-7 for BT)

If any of these MUST change: create new Core snapshot (v2.0), new hash, new baseline tournaments. Old data stays valid for old Core only.

---

## EXECUTION: Agent Assignments for KK

### Parallel Agent Setup (claude-squad or Agent Teams)

```
Agent "spec"     → Tasks 1.1, 1.2, 1.3 (docs, specs, track definitions)
Agent "ablation" → Tasks 1.4, 1.5 (run_ablation.py, PSI suite)
Agent "infra"    → Tasks 1.6, 1.7 (invariant tests, ability grammar)
Agent "platform" → Tasks 2.1, 2.2, 2.3 (seasons, leaderboard, API)
Agent "report"   → Task 2.4 (seasonal report generator)
Agent "lab"      → Task 3.1 (laboratory mode v2)
```

### Phase 1 Sprint Order

```
Week 1:  spec (1.1, 1.2, 1.3) + infra (1.6) — in parallel
Week 2:  ablation (1.4 dry-run) + infra (1.7) — in parallel
Week 3:  ablation (1.4 real runs via Gemini Flash) + ablation (1.5 PSI)
Week 4:  report: Phase 1 analysis document with ablation results
```

### Launch Command (Mac Mini)

```bash
cd ~/Desktop/Claude/a/moreau-arena-paper
claude --dangerously-skip-permissions

# Paste:
Read ROADMAP_v2.md. Execute Phase 1 with 3 teammates:

TEAMMATE "spec": Tasks 1.1, 1.2, 1.3 — create measurement spec,
MMR v1.1 schema, and track definitions. All in docs/.

TEAMMATE "infra": Tasks 1.6, 1.7 — invariant test suite and
ability grammar foundation. Tests in tests/, grammar in simulator/.

TEAMMATE "ablation": Task 1.4 (dry-run only) — create run_ablation.py
with 3 variants. Test with --dry-run. Do NOT make real API calls.

RULES:
- Run python -m pytest tests/test_invariants.py before each push
- Commit after each task: "Phase1 Task X.Y: description"
- If blocked, document in PROGRESS.md, skip to next
- Do NOT modify data/tournament_001/ or data/tournament_002/
- Do NOT modify config.json
```

---

## Success Criteria

Phase 1 complete when:
- [ ] `docs/MEASUREMENT_SPEC.md` exists and covers BT, CI, non-transitivity, PSI
- [ ] `docs/MMR_SPEC.md` exists with full field list
- [ ] `docs/TRACKS.md` defines A/B/C/D with unambiguous protocols
- [ ] `tests/test_invariants.py` passes (6 tests)
- [ ] `run_ablation.py` works with --dry-run for all 3 variants
- [ ] `simulator/ability_grammar.py` expresses all 6 animals
- [ ] All invariants pass on every commit

Phase 2 complete when:
- [ ] Season system works (patch generator + freeze)
- [ ] Leaderboard renders T001+T002 data
- [ ] Agent API documented and tested
- [ ] First seasonal report auto-generated

Phase 3 complete when:
- [ ] Lab Mode v2 produces iteration curves with distance-to-optimum
- [ ] Moreau-PO runs at 3 fog levels
- [ ] At least one ablation run with real LLM (Gemini Flash)
