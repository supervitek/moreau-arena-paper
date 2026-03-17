# Part B Measurement Contract — B1

Last updated: 2026-03-17
Status: Active contract draft for Phase B1
Scope: first executable measurement contract for Part B
Source roadmap: `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`
Machine-readable companion: `docs/PART_B_MEASUREMENT_CONTRACT_B1.json`

## Purpose

This contract defines the minimum measurement layer that must exist before Part B can expand.

It is not a lore document.
It is not a UI concept note.
It is the first benchmark contract for the ecological side of Moreau Arena.

The contract exists to answer one question cleanly:

- what exactly is being measured in Part B, under what conditions, and for which class of run?

---

## Contract Scope

This B1 contract covers:

- run classes
- observation contract
- action contract
- tick cadence
- inference/call budgets
- season boundary rules
- score family formulas
- welfare decay
- anti-degenerate baseline tests
- operator inspection evidence

This B1 contract does not yet cover:

- BYO-agent API
- large economy design
- third+ zones
- composite public headline ranking

---

## Approved Run Classes

Every Part B run must belong to exactly one run class:

## `manual`

Definition:
- every scored action is triggered directly by the human operator

Allowed:
- direct actions
- direct queue manipulation

Not allowed:
- hosted house agent action execution

Purpose:
- establishes human-only reference behavior

## `operator-assisted`

Definition:
- the human operator acts directly, but uses system assistance for recommendations, review, queue prep, or summaries

Allowed:
- all `manual` actions
- advisory surfaces
- queue authoring assistance

Not allowed:
- autonomous hosted agent execution without direct human confirmation

Purpose:
- measures the human+system loop without claiming fully agentic behavior

## `agent-only`

Definition:
- actions are executed autonomously by the hosted house agent under the published observation/action contract

Allowed:
- hosted agent actions at tick boundaries
- operator-set priorities between ticks

Not allowed:
- hidden privileged actions
- out-of-band prompts or action types not in the public contract

Purpose:
- this is the true Part B ecological benchmark class

---

## Observation Contract

The agent may perceive only the fields below during B1/B2/B3/B4 execution.

Any future addition to this observation contract requires a season boundary.

## Global Observation Fields

- `season_id`
- `run_class`
- `world_tick`
- `tick_started_at`
- `active_zone`
- `available_actions`
- `queue_length`
- `queue_capacity`
- `inference_budget_remaining`
- `world_access_status`

## Pet Observation Fields

- `pet_id`
- `name`
- `animal`
- `level`
- `xp`
- `is_alive`
- `health_pct`
- `morale_pct`
- `happiness_pct`
- `energy_pct`
- `corruption_pct`
- `instability`
- `mutation_count`
- `recent_fight_summary`
- `recent_cave_summary`
- `last_action`
- `last_action_outcome`
- `neglect_ticks`
- `days_survived`

## Arena Observation Fields

- `arena_available`
- `arena_tickets`
- `arena_recent_record`
- `arena_reward_preview`
- `arena_loss_streak`

## Cave Observation Fields

- `cave_available`
- `cave_depth_last_run`
- `cave_extract_value_last_run`
- `cave_injury_last_run`
- `cave_reward_preview`

## Operator Priority Fields

- `priority_profile`
- `risk_appetite`
- `care_threshold`
- `combat_bias`
- `expedition_bias`

## Hidden Fields

The following are explicitly hidden from the agent during the first Part B measurement cycle:

- unrevealed trap seeds
- hidden drop tables
- internal weighting constants for score aggregation
- unpublished NPC policy internals
- any house-only telemetry not present in the public observation object

---

## Action Contract

The public action grammar is deliberately small.

Every autonomous action in Part B must map to one of these verbs:

- `HOLD`
- `CARE`
- `REST`
- `TRAIN`
- `ENTER_ARENA`
- `ENTER_CAVE`
- `EXTRACT`
- `MUTATE`

## Verb Definitions

## `HOLD`

Meaning:
- take no risky advancement action this tick

Allowed uses:
- waiting for conditions to improve
- preserving budget

## `CARE`

Meaning:
- spend the tick on stabilization and welfare maintenance

Expected effects:
- improves happiness and morale
- reduces neglect pressure
- may slightly recover health depending on current state

## `REST`

Meaning:
- recover energy and avoid high-pressure actions

Expected effects:
- improves energy
- does not meaningfully advance combat or expedition progress

## `TRAIN`

Meaning:
- low-stakes progression action

Expected effects:
- small XP gain
- possible mild fatigue or morale shift

## `ENTER_ARENA`

Meaning:
- commit this pet to the arena loop for the current tick

Expected effects:
- combat result
- combat-linked rewards or setbacks

## `ENTER_CAVE`

Meaning:
- commit this pet to the Cave of Catharsis route

Expected effects:
- expedition progress
- risk accumulation
- chance to face extraction decision later

## `EXTRACT`

Meaning:
- leave the expedition path with current rewards

Expected effects:
- lock in expedition gains
- forego deeper upside

## `MUTATE`

Meaning:
- perform a mutation-related growth/risk action when the surface supports it

Expected effects:
- potential power gain
- potential instability/corruption cost

Important:
- the verb exists in the grammar now to avoid hidden future expansion
- it should only be enabled on surfaces that explicitly expose it

---

## Tick Contract

## World Tick Cadence

Initial measurement cadence:

- one world tick every 6 real hours

Rationale:

- strong enough to create “progress while you sleep”
- cheap enough to keep hosted-agent inference bounded
- sparse enough that operator review remains legible

## Tick Resolution Order

At each world tick:

1. current observation object is frozen
2. run class determines who chooses the action
3. chosen action is validated against the public grammar
4. action executes
5. event log entry is written
6. score-relevant state deltas are recorded

## Tick Default

If no valid action is available:

- action resolves to `HOLD`

If the hosted agent is paused or out of credits:

- action resolves to `HOLD`

---

## Inference and Call Budget Contract

These constraints exist before monetization finalization because they are measurement-critical.

## Hosted Agent Inference Budget

- maximum `1` hosted-agent inference call per active pet per tick
- maximum `4` hosted-agent inference calls per operator account per 24 hours
- once the daily credit budget is exhausted, the agent auto-pauses into `HOLD`

## Manual and Operator-Assisted Budget

- no inference budget applies to manual runs
- operator-assisted runs may use advisory surfaces, but autonomous execution is still disallowed

## Why This Matters

Without call budgets:

- better-funded accounts would look like better agents
- the measurement would drift toward infrastructure advantage

---

## Season Contract

The first Part B measurement season begins only when the following are frozen together:

- observation contract
- action contract
- score formulas
- tick cadence
- budget rules
- active zone set
- run class taxonomy

## A Change Requires a New Season If It Alters

- observation fields
- allowed verbs
- score weights or formulas
- welfare decay constants
- tick cadence
- active measurement zones
- hosted-agent budget rules

## A Change Does Not Require a New Season If It Only Alters

- copy
- styling
- non-measurement UI layout
- bug fixes that do not change the contract

---

## Score Families

The first measurement season publishes only family scores:

- Welfare
- Combat
- Expedition

Composite score is computed internally if needed, but is not the public headline.

All score families use a `0–100` scale after normalization and clamping.

## Welfare Score

Goal:
- reward sustained care, stability, and survival without rewarding passive idling

### Raw Inputs

- `survival_ratio`
- `avg_health_pct`
- `avg_morale_pct`
- `avg_happiness_pct`
- `neglect_events`
- `idle_ticks`
- `critical_state_ticks`

### Welfare Decay Rule

If the pet receives no care-like action during a tick:

- `health_pct -= 1`
- `morale_pct -= 2`
- `happiness_pct -= 2`

If two consecutive ticks pass without `CARE`, `REST`, or successful positive recovery event:

- `neglect_ticks += 1`

If `neglect_ticks >= 3`:

- each additional neglected tick adds one `critical_state_tick`

This is the explicit anti-idle pressure demanded by the Round Table.

### Formula

`Welfare = clamp(100 * (0.35*survival_ratio + 0.20*avg_health_pct + 0.20*avg_morale_pct + 0.15*avg_happiness_pct + 0.10*active_care_ratio) - 8*neglect_events - 5*critical_state_ticks - 3*idle_ticks, 0, 100)`

Where:

- `survival_ratio` is normalized against season length
- `avg_*_pct` are expressed on `0–1`
- `active_care_ratio = care_like_ticks / total_ticks`

Interpretation:

- surviving while maintaining a healthy, attended pet is good
- simply doing nothing is not good

## Combat Score

Goal:
- measure arena effectiveness without letting pure recklessness dominate

### Raw Inputs

- `arena_win_rate`
- `arena_reward_rate`
- `arena_recovery_rate`
- `arena_forfeits`

### Formula

`Combat = clamp(100 * (0.50*arena_win_rate + 0.30*arena_reward_rate + 0.20*arena_recovery_rate) - 6*arena_forfeits, 0, 100)`

Interpretation:

- winning matters most
- extracting value from combat matters
- recovering after losses matters

## Expedition Score

Goal:
- measure risk calibration, extraction discipline, and expedition yield

### Raw Inputs

- `expedition_extract_rate`
- `expedition_yield_rate`
- `expedition_depth_rate`
- `expedition_wipe_count`

### Formula

`Expedition = clamp(100 * (0.40*expedition_extract_rate + 0.35*expedition_yield_rate + 0.25*expedition_depth_rate) - 8*expedition_wipe_count, 0, 100)`

Interpretation:

- going deeper matters
- bringing value home matters more than dying gloriously

---

## Anti-Degenerate Baselines

B1 is not valid unless these baselines exist and fail to dominate.

## Baseline 1 — Conservative

Policy:
- if any welfare stat is below threshold, choose `CARE`
- otherwise choose `HOLD`

Expected result:
- should not top Combat
- should not top Expedition
- should not top Welfare if decay and idle penalties are working correctly

## Baseline 2 — Greedy

Policy:
- always choose the highest immediate visible reward action

Expected result:
- may spike Combat or Expedition locally
- should suffer on Welfare and consistency

## Baseline 3 — Random

Policy:
- choose uniformly from valid actions

Expected result:
- should fail across all public family scores

## B1 Acceptance Test

The measurement contract passes only if:

- `Random` does not dominate any family score
- `Conservative` does not top Welfare through idling
- `Greedy` does not dominate all public families simultaneously

---

## Operator Inspection Evidence

The operator must be able to inspect what happened while away.

Minimum required evidence after offline progression:

- action chosen
- who chose it
- timestamp / world tick
- state before
- state after
- immediate outcome
- score impact summary
- budget spent
- reason string if an agent made the choice

This evidence must be available even before the polished product UI exists.

---

## Public Benchmark Claim

Part B does not claim to measure:

- general intelligence
- general safety
- universal agent quality

It claims to measure:

- behavioral outcomes under this specific named ecological contract

That claim is narrow on purpose.
