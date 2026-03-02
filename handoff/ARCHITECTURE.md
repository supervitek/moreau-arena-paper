# Architecture — How Everything Connects

## High-Level Data Flow

```
                              ┌──────────────────────────────────┐
                              │         config.json (FROZEN)      │
                              │  Stats, animals, abilities, grid  │
                              └──────────┬───────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │  Simulator   │   │   Seasons    │   │  Invariant   │
            │   Engine     │   │   System     │   │   Tests      │
            │ (engine.py)  │   │ (patches)    │   │ (89 tests)   │
            └──────┬───────┘   └──────────────┘   └──────────────┘
                   │
        ┌──────────┼──────────────┬──────────────┐
        │          │              │              │
        ▼          ▼              ▼              ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ Baseline │ │   LLM    │ │  Script  │ │  Gemini  │
  │ Agents   │ │  Agents  │ │  Agent   │ │  Agent   │
  │ (5)      │ │ (v1, v2) │ │  (DSL)   │ │          │
  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
       │             │            │             │
       └──────┬──────┘────────────┘─────────────┘
              │
              ▼
  ┌───────────────────────────────────────────────┐
  │              Experiment Runners                │
  │  run_challenge.py  run_ablation.py  lab_mode  │
  │  run_psi.py  run_planning.py  run_po.py       │
  └──────────────────────┬────────────────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │   Results (JSONL)   │
              │  results/*.jsonl    │
              └──────────┬─────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        ┌──────────┐ ┌────────┐ ┌──────────┐
        │ BT/Elo   │ │Pairwise│ │ Seasonal │
        │ Ranking  │ │ Matrix │ │  Report  │
        └────┬─────┘ └───┬────┘ └────┬─────┘
             │           │           │
             └─────┬─────┘───────────┘
                   │
                   ▼
          ┌──────────────────┐
          │    Web UI         │
          │  (FastAPI app)    │
          │  /leaderboard     │
          │  /play  /research │
          │  /api/v1/*        │
          └──────────────────┘
```

---

## Component Details

### 1. Combat Simulator

The simulator is the deterministic core. Given two builds and a seed, it produces an identical outcome every time.

```
simulator/
├── config.json      ← All parameters (FROZEN)
├── engine.py        ← Tick loop: initiative → attacks → abilities → ring → victory check
├── animals.py       ← Animal enum, stat blocks, passive/ability definitions
├── abilities.py     ← Ability proc resolution, effect application
├── grid.py          ← 8x8 grid, Chebyshev pathfinding, ring zone calculation
├── seed.py          ← SHA-256 seeded RNG (tick/hit/proc seeds)
└── __main__.py      ← CLI: --build1/--build2, --round-robin, --series
```

**Tick loop (engine.py):**
```
for tick in 1..60:
    1. Calculate initiative: SPD + seeded_random(0, 0.49)
    2. Determine attack order (higher initiative goes first)
    3. Apply passive modifiers (Fury, Charge, Ambush, etc.)
    4. Roll ability procs: proc_rate × (1 + WIL_bonus) vs resist
    5. Calculate physical damage: base_dmg × ability_mods × RNG_variance
    6. Apply active effects (buffs, DoTs, debuffs)
    7. Apply ring damage if tick >= 30 and creature outside safe zone
    8. Advance status effect durations
    9. Check: HP <= 0 → death; tick = 60 → timeout (compare remaining HP)
```

**Stat formulas:**
```python
max_hp    = 50 + 10 * HP          # HP stat → hit points
base_dmg  = floor(2 + 0.85 * ATK) # ATK stat → damage per hit
dodge     = max(0%, min(30%, 2.5% * (SPD - 1)))  # SPD stat → dodge chance
resist    = min(60%, WIL * 3.3%)   # WIL stat → ability resist
```

### 2. Agent System

All agents implement the `BaseAgent` interface:

```python
class BaseAgent:
    def choose_build(
        self,
        opponent_animal: Animal | None,  # Known in Track B after game 1
        banned: list[Animal],            # Banned animals (planning suite)
        opponent_reveal: dict | None     # Winner's build (Track B, after loss)
    ) -> Build:
        """Return animal + 4 stats summing to 20"""
```

For public submissions, the `MoreauAgent` interface adds:

```python
class MoreauAgent:
    def get_build(self, prompt: str, game_state: dict | None) -> dict
    def adapt_build(self, prompt, opponent_build, my_build, result, game_state) -> dict
```

**Agent hierarchy:**
```
BaseAgent (interface)
├── RandomAgent        ← Random everything
├── GreedyAgent        ← Fixed best known build
├── SmartAgent         ← Counter-pick table + reveal adaptation
├── ConservativeAgent  ← Balanced tanky builds
├── HighVarianceAgent  ← Extreme stat allocations
├── ScriptAgent        ← Driven by Moreau Script (.ms) file
└── LLM Agents
    ├── LLMAgent (v1)  ← T001 protocol, plain text, regex parsing
    ├── LLMAgentV2     ← T002 protocol, JSON output, meta context
    └── GeminiAgent    ← Google Gemini wrapper for ablations
```

### 3. Experiment Runners

Each runner script is self-contained and produces JSONL output:

```
run_challenge.py     ── LLM vs 5 baselines, T001 or T002 protocol
                        Supports: anthropic, openai, google, xai providers
                        Output: results/challenge_<model>_<timestamp>.jsonl

run_ablation.py      ── 5 variants isolating T002 components
                        formulas-only, meta-only, adaptation-only,
                        structured-output-only, formulas-no-meta
                        Output: results/ablation_<variant>_<timestamp>.jsonl

lab_mode.py          ── Interactive iteration experiment
                        LLM proposes N builds per round, tests via local sim
                        Tracks convergence and distance-to-optimum
                        Output: results/lab_<model>_<timestamp>.json

run_psi.py           ── Prompt sensitivity measurement
                        3+ paraphrased prompts, Kendall tau between rankings
                        Output: results/psi_<timestamp>.json

run_planning.py      ── Ban/pick draft phase tournament
                        Ban 3 animals, pick 1, build, optional reroll
                        Output: results/planning_<timestamp>.jsonl

run_po.py            ── Partial observability experiment
                        fog=0.0 (full), 0.5 (animal only), 1.0 (nothing)
                        Output: results/po_fog<N>_<model>_<timestamp>.jsonl
```

All runners support `--dry-run` (replaces API calls with random builds).

### 4. Analysis Pipeline

```
JSONL data ──→ bt_ranking.py ──→ BT scores + 95% CI + Elo ratings
             │
             ├→ pairwise_matrix.py ──→ Win-rate CSV + heatmap PNG
             │
             └→ seasonal_report.py ──→ Markdown report + charts
                                       (BT, Elo, heatmap, 3-cycles,
                                        signature builds, balance check)
```

**BT computation:**
1. Load series outcomes from JSONL
2. Build pairwise win/loss counts
3. Iterative MLE: maximize P(outcomes | ratings)
4. Bootstrap CI: resample N=1000, recompute ratings
5. Output: sorted rankings with confidence intervals

### 5. Web Leaderboard

```
web/
├── app.py              ← FastAPI application
│   ├── GET /           ← Index page
│   ├── GET /leaderboard ← BT/Elo leaderboard + heatmap
│   ├── GET /play       ← Create-your-fighter form
│   ├── GET /research   ← Academic face
│   ├── POST /api/v1/fight    ← Run 1 game
│   ├── POST /api/v1/series   ← Run best-of-7
│   ├── GET  /api/v1/leaderboard/bt      ← JSON BT scores
│   ├── GET  /api/v1/leaderboard/pairwise ← JSON pairwise matrix
│   ├── GET  /api/v1/leaderboard/cycles   ← JSON 3-cycle detection
│   └── POST /api/v1/submit   ← Agent submission
└── static/
    ├── index.html      ← Navigation hub
    ├── leaderboard.html ← BT tables, heatmap, 3-cycle display
    ├── play.html       ← Stat sliders with budget enforcement
    └── research.html   ← Methodology summary + BT leaderboard
```

Data flow: JSONL files → analysis scripts → JSON API → HTML frontend.

### 6. Season System

```
seasons/
├── season_0_base.json     ← Copy of frozen config.json
├── season_1_patch.json    ← Adjusted ability proc rates
├── patch_generator.py     ← EMA-based auto-balancer
├── ability_generator.py   ← Procedural ability generation
└── SEASON_RULES.md        ← How seasons work

Patch generation flow:
1. Load JSONL match data
2. Compute per-ability win rates (EMA, window=500)
3. Target: 55% win rate (neutral=50%)
4. Adjust proc rates: rate += damping * (target - actual)
5. Clamp to [2.5%, 5.5%]
6. Save as season_N_patch.json
```

Within a season, config is frozen. Between seasons, patches adjust balance. Core suite always runs on `season_0_base.json`.

### 7. Moreau Script DSL

```
moreau_script/
├── parser.py          ← Text → AST (IF/ELIF/ELSE + PREFER)
├── interpreter.py     ← AST × GameState → Build
├── validator.py       ← Static analysis (no eval/exec/import)
├── script_agent.py    ← ScriptAgent wraps parser + interpreter
└── examples/
    ├── random_strategy.ms
    ├── counter_pick.ms
    └── stat_optimizer.ms

Data flow:
.ms file → parser → AST → validator → interpreter(game_state) → Build
```

**Grammar:**
```
Script := Rule+ EOF
Rule := IF Condition THEN Preference+ [ELIF Condition THEN Preference+]* [ELSE Preference+]*
Condition := stat_comparison (AND stat_comparison)*
Preference := PREFER animal [with hp=X atk=Y spd=Z wil=W]
```

Max 50 rules per script. Iteration limit: 1000 steps. No eval, no imports, no network.

### 8. Lab Mode Architecture

```
┌─────────────────────────────────────────────┐
│                 LLM Provider                 │
│  (Anthropic / OpenAI / Google / xAI)         │
└──────────────────┬──────────────────────────┘
                   │ Proposes N builds
                   ▼
┌──────────────────────────────────────────────┐
│              Lab Mode Controller              │
│  1. Parse builds from LLM response            │
│  2. Run local round-robin (N×N×games_per_pair) │
│  3. Rank builds by win rate                    │
│  4. Compute distance-to-optimum               │
│  5. Send results back to LLM for next round   │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│         Iteration Curve Output                │
│  {round, best_build, best_wr, all_builds}     │
│  Convergence: first round < 1pp improvement   │
│  Distance: best_wr vs brute-force optimum     │
└──────────────────────────────────────────────┘
```

### 9. Test Architecture

```
tests/test_invariants.py (89 tests)
│
├── Config Integrity (4 tests)
│   └── Hash match, required keys, version, arena params
│
├── Determinism (3 tests)
│   └── Same seed → same result (5 seeds), different seeds → different results
│
├── Seed Derivation (5 tests)
│   └── Tick/hit/proc seeds deterministic, range checks
│
├── Stat System (6 tests)
│   └── Constraints, derived formulas, size thresholds, ability completeness
│
├── Combat Invariants (7 tests)
│   └── Termination, winner validity, end condition, HP checks, log length
│
├── Grid Invariants (3 tests)
│   └── Dimensions, starting positions, distance metric
│
├── Proc Rates (3 tests)
│   └── Tier rates correct, code matches config, bounds respected
│
├── Tournament Data Immutability (3 tests)
│   └── SHA-256 hashes for all 10 frozen files
│
├── Regression Tests (2 tests)
│   └── Known outcomes for specific matchups, all animals can fight
│
├── Variance Budget (1 test)
│   └── RNG < 25% of outcome variance (1000 games)
│
├── Monotonic ATK (1 test, 10 parameterized pairs)
│   └── +1 ATK never decreases expected damage (200 games each)
│
├── Monotonic HP (1 test, 10 parameterized pairs)
│   └── +1 HP never decreases expected survival (200 games each)
│
├── No Hidden Mechanics (1 test)
│   └── All config keys documented in MECHANICS.md
│
└── Symmetry (1 test)
    └── Mirror match: no >70/30 systematic bias (200 games)
```
