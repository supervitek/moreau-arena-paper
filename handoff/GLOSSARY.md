# Glossary

## Core Concepts

**Moreau Arena**
The benchmark system as a whole — the combat simulator, agent framework, tournament protocol, and measurement methodology.

**Moreau Core**
The frozen, hash-verified subset of the system: `config.json`, the combat engine (`engine.py`, `animals.py`, `abilities.py`, `grid.py`, `seed.py`), and tournament data. Moreau Core never changes. Config hash: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`.

**Build**
A creature configuration: one animal + four stat allocations (HP/ATK/SPD/WIL) summing to 20, each >= 1. Example: `BEAR 3/14/2/1`.

**Series**
A best-of-7 match between two agents. First to 4 wins takes the series. The fundamental unit of measurement for Bradley-Terry scoring.

**Tick**
One time step in the combat simulation. Each tick: calculate initiative, resolve attacks, apply abilities, check ring damage, check victory conditions. Max 60 ticks per game.

**Ring**
The shrinking safe zone that activates at tick 30. Creatures outside take 2% max HP per tick. Forces engagement and prevents infinite stalling.

---

## Tracks

**Track A — One-Shot**
T001 protocol. Qualitative descriptions, no meta context, no adaptation. Single build per series.

**Track B — Feedback + Counter-Pick**
T002 protocol. Exact formulas, meta context (top-5 builds), structured JSON output, adaptation after losses.

**Track C — Meta-Conditioned**
Not yet run. Track A base + meta context (no formulas). Tests whether examples alone shift strategy.

**Track D — Tool-Augmented**
Not yet run. Track B formulas + limited simulator access (no meta). Tests whether compute replaces examples.

---

## Metrics

**BT Score (Bradley-Terry)**
The primary ranking metric. Maximum-likelihood estimation of agent strength from pairwise series outcomes. Computed with 95% bootstrap confidence intervals (N=1000 resamples).

**Elo**
Secondary metric for display/UX only. Computed from the same data as BT but using the Elo update formula. Not used for scientific claims.

**PSI (Prompt Sensitivity Index)**
Measures ranking stability across prompt paraphrases. Run 3+ paraphrased prompts with identical information, compute Kendall tau between resulting BT rankings. PSI < 0.15 = "prompt-robust", 0.15-0.30 = "moderate", > 0.30 = "prompt-sensitive".

**Non-transitivity**
When A > B > C > A in pairwise win rates. Measured by 3-cycle count and mass. Condorcet winner existence (yes/no) indicates whether a single dominant strategy exists.

**Variance Budget**
RNG must explain < 25% of outcome variance. Verified by running 1000 games with identical builds and different seeds.

---

## Ablation Variants

**formulas-only**
T001 prompt + exact stat formulas. No meta context, no adaptation. Isolates: do formulas alone help?

**meta-only**
T001 prompt + top-5 winning builds. No formulas, no adaptation. Isolates: do examples alone help?

**adaptation-only**
T001 prompt + adaptive series (loser sees winner). No formulas, no meta. Isolates: does feedback alone help?

**structured-output-only**
JSON output format only. No formulas, no meta, no adaptation. Isolates: does output format matter?

**formulas-no-meta**
Full T002 formulas but meta context removed. Isolates: are formulas sufficient without examples?

---

## Experiment Modes

**Challenge Mode** (`run_challenge.py`)
Test any frontier LLM against the 5 baseline agents using T001 or T002 protocol. Produces JSONL results + BT ranking.

**Lab Mode** (`lab_mode.py`)
Interactive iteration experiment. LLM proposes builds, tests them via local simulation, improves over rounds. Measures convergence speed and distance-to-optimum.

**Partial Observability** (`run_po.py`)
Adaptive series with configurable information fog. fog=0.0 (full info), fog=0.5 (animal name only), fog=1.0 (nothing revealed). Measures how information loss degrades adaptation.

**Planning Suite** (`run_planning.py`)
Draft phase tournament with ban/pick, stat reveal, reroll mechanics. Tests pre-fight decision depth.

**PSI Suite** (`run_psi.py`)
Runs multiple paraphrased prompts and computes ranking stability via Kendall tau.

---

## Agents

**BaseAgent**
The Python interface for all agents. Must implement `choose_build(opponent_animal, banned, opponent_reveal) -> Build`.

**MoreauAgent**
The public submission interface. Methods: `get_build(prompt, game_state)` and `adapt_build(prompt, opponent_build, my_build, result, game_state)`.

**Baseline Agents** (5 total)
Hand-coded agents that do not use LLMs:
- **RandomAgent** — Random animal + random valid stats
- **GreedyAgent** — Always picks Boar 8/8/3/1 (or fallback)
- **SmartAgent** — Counter-picks per opponent, adapts to reveals
- **ConservativeAgent** — Balanced tanky builds across 10 animals
- **HighVarianceAgent** — Extreme stat allocations

**ScriptAgent**
Agent driven by a Moreau Script (.ms) file. Parses IF/ELIF/ELSE rules to select builds.

---

## Season System

**Season**
A fixed-config period. Within a season, config is frozen. Between seasons, a balance patch may adjust ability proc rates.

**Patch Generator** (`seasons/patch_generator.py`)
EMA-based auto-balancer. Adjusts proc rates toward 55% win rate target, capped at [2.5%, 5.5%].

**Ability Generator** (`seasons/ability_generator.py`)
Rules-as-Data system that procedurally generates new abilities via sampling + rejection, validated by EV estimation.

---

## Moreau Script

**Moreau Script (.ms)**
A tier-2 DSL for expressing combat strategies as code. Syntax: IF/ELIF/ELSE conditions with PREFER actions. Max 50 rules per script. Sandboxed — no eval, no imports, no network.

**Parser** — Converts .ms text to AST
**Interpreter** — Evaluates AST against game state to produce a Build
**Validator** — Static analysis ensuring no unsafe operations

---

## Data Formats

**JSONL**
One JSON object per line. Used for match records. Each line contains: series number, game number, agent names, animal choices, stat allocations, winner, ticks, end condition, env hash, seed.

**MMR (Match Record Format) v1.1**
Extended JSONL schema with: env_hash, rules_version, seed_scheme, prompt_hash, decode_params, raw_output_digest, adaptation_log.

---

## Technical Terms

**Config Hash**
SHA-256 of `config.json`. Must equal `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` at all times. Verified by invariant tests.

**Seed Derivation**
Deterministic RNG from match seed: `tick_seed = SHA256(match_seed || tick_index)`, `hit_seed = SHA256(match_seed || tick_index || attack_index)`, `proc_seed = SHA256(match_seed || tick_index || creature_index || ability_index)`.

**Fog Level**
Information visibility in partial observability experiments. 0.0 = full info, 0.5 = animal name only, 1.0 = nothing revealed.

**Convergence**
In Lab Mode, the round where improvement drops below 1 percentage point. Measures how quickly a model finds a near-optimal strategy.

**Distance-to-Optimum**
In Lab Mode, the gap between the model's best build win rate and the brute-force optimum found by exhaustive simulation.
