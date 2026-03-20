# Project Bible — Technical Appendix

Last updated: 2026-03-20  
Status: Technical companion to `docs/PROJECT_BIBLE.md`

This appendix exists for new agents who already understand the high-level shape of the project and need the concrete implementation map.

It is intentionally narrower than the main Bible and focuses on the areas that are easiest to misunderstand from strategy docs alone.

## 1. Part B State Layer

Primary file:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)

What it does:
- defines the current Part B season contract
- stores and retrieves Part B runs and events
- normalizes observation/state
- executes queue, baseline, and house-agent ticks
- derives reports, leaderboards, calibration, and archive exports

### Storage model

Part B uses a store abstraction.

Practical behavior:
- local/dev: file-backed store
- production-ready path: Supabase-backed store when both env vars are present

Key runtime status surface:
- `GET /api/v1/island/part-b/storage-status`

Relevant environment:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- optional local override:
  - `MOREAU_PART_B_STATE_DIR`

Relevant schema file:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/sql/PART_B_STATE_MIGRATION_B1_5.sql`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/sql/PART_B_STATE_MIGRATION_B1_5.sql)

### Part B run envelope

A run stores at least:
- `season_id`
- `run_class`
- `status`
- `world_tick`
- `state_revision`
- `active_zone`
- `queue_state`
- `state_projection`
- `house_agent_*` fields
- billing/budget fields
- metadata

### Conflict semantics

Each event can carry `expected_state_revision`.

If a submitted event is stale relative to the server revision:
- it is rejected as `stale_rejected`
- the event is logged, not silently dropped
- this is how operator/agent conflict is kept replayable

## 2. Part B Season Contract

Current season ID:
- `part-b-s1-first-descent`

Current season contract is exposed by:
- `GET /api/v1/island/part-b/season`

Current approved season shape:
- zones:
  - `arena`
  - `cave`
- run classes:
  - `manual`
  - `operator-assisted`
  - `agent-only`
- score families:
  - `welfare`
  - `combat`
  - `expedition`
- composite headline:
  - intentionally disabled

### House-agent boundary

Canonical rule:
- richer product behavior may exist above the contract
- benchmark legitimacy depends on the contract chokepoints, not on house-agent internal simplicity

Current technical chokepoints live in:
- `_observation_from(...)`
- `_coerce_action(...)`
- `_normalize_house_agent_plan(...)`
- `_derive_scores(...)`

New work should preserve those functions as the contract wall.

## 3. Part B Run Classes

### `manual`

Interpretation:
- human-driven run
- no autonomous house-agent control

Technical reality:
- actions are submitted directly by operator/manual source
- no agent-only automation path

### `operator-assisted`

Interpretation:
- human still acts, but receives hints/assistance

Technical reality:
- still fundamentally operator-driven
- useful for compare/trace purposes
- should remain distinct from pure manual and pure autonomous runs

### `agent-only`

Interpretation:
- run can be delegated to automation

Technical reality:
- queue actor defaults to `agent`
- house agent may be enabled only here
- budget exhaustion can autopause the run

Important integrity rule:
- house-agent benchmark legitimacy depends on public-contract parity, not on hidden internal shortcuts
- run labels must keep that parity legible in UI, not just in API payloads

## 4. Part B Action Grammar

Public action verbs:
- `HOLD`
- `CARE`
- `REST`
- `TRAIN`
- `ENTER_ARENA`
- `ENTER_CAVE`
- `EXTRACT`
- `MUTATE`

These are the actions used by:
- queue execution
- baselines
- house agent
- calibration tooling

No product enrichment is allowed to emit actions outside this set without a new season boundary.

## 5. Part B Zone Rules

### The Arena

Meaning:
- combat-linked benchmark surface

Core logic:
- `ENTER_ARENA` simulates a deterministic arena result using current state, `combat_bias`, risk appetite, and a deterministic roll
- result is typically `win` or `loss`
- updates:
  - health
  - morale
  - happiness
  - energy
  - recent fight summary
  - arena loss streak / recent record

Combat score is then derived from accepted arena events:
- wins
- losses
- reward
- rating/xp-like gains if present

### The Cave of Catharsis

Meaning:
- push-your-luck expedition surface

Core logic:
- `ENTER_CAVE` increases depth and accumulates:
  - extract value
  - injury/risk
- `EXTRACT` banks current cave value and ends the active cave run

Expedition score is derived from:
- max depth reached
- total extracted value
- injury cost

## 6. Part B Score Families

Scores are derived in:
- `_derive_scores(...)` inside [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)

### Welfare

Welfare is based on:
- survival
- health
- morale
- happiness
- active care ratio

And penalized by:
- `neglect_ticks`
- `critical_state_ticks`
- `idle_ticks`

Current formula shape:
- positive weighted blend of survival/health/morale/happiness/care
- minus explicit neglect/critical/idle penalties

This is where anti-degeneracy pressure lives.

### Combat

Combat is based on accepted arena events:
- wins
- losses
- reward total
- some xp/rating contribution
- event participation bonus

### Expedition

Expedition is based on:
- cave depth
- extract value
- injury cost
- expedition participation bonus

### Breakdown surfaces

Per-run score explanation is available in report payloads:
- `score_breakdown.welfare`
- `score_breakdown.combat`
- `score_breakdown.expedition`

These are used by inspect/report UI and review tooling.

Scoring validity does not depend on whether a run used the house agent.

## 7. Part B Queue and Tick Runtime

### Queue

Core behavior:
- FIFO only
- bounded queue capacity
- no priority/preemption

Endpoints:
- `POST /api/v1/island/part-b/runs/{run_id}/queue`
- `DELETE /api/v1/island/part-b/runs/{run_id}/queue/{item_id}`
- `POST /api/v1/island/part-b/runs/{run_id}/queue/clear`

### Tick runner

Endpoint:
- `POST /api/v1/island/part-b/runs/{run_id}/tick`

Tick precedence:
1. queued action, if any
2. house agent plan, if `agent-only` + enabled
3. otherwise no action

Important runtime behavior:
- invalid queue actions are logged and can be dropped
- stale conflicts are replayable
- fatal runs clear queue and disable house agent

Important boundary behavior:
- house-agent planning must remain auditable
- decision context may be richer internally, but the executed plan must still reduce to one public verb chosen from public observation
- exhausted inference budget triggers autopause

## 8. Part B Baselines

Current published deterministic baseline policies:
- `conservative`
- `greedy`
- `random`
- `caremax`
- `arena-spam`
- `expedition-max`

Relevant surfaces:
- `GET /api/v1/island/part-b/runs/{run_id}/baseline/preview`
- `POST /api/v1/island/part-b/runs/{run_id}/baseline`

Primary script:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_baselines.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_baselines.py)

Mixed calibration script:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_mixed_calibration.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_mixed_calibration.py)

## 9. Part B Leaderboards and Reports

### Leaderboards

Endpoint:
- `GET /api/v1/island/part-b/leaderboards`

Important response features:
- family leaderboards for:
  - `welfare`
  - `combat`
  - `expedition`
- `selected_run_class`
- `counts.by_run_class`
- `by_run_class_top`
- `focus_run_ranks`
- `family_spread`

### Replay

Endpoint:
- `GET /api/v1/island/part-b/runs/{run_id}/replay`

Returns:
- run envelope
- event stream
- report

### Report

Endpoint:
- `GET /api/v1/island/part-b/runs/{run_id}/report`

Contains:
- scores
- score breakdown
- queue summary
- billing state
- house-agent state
- inspect payload
- latest transition / latest conflict

### Calibration

Endpoint:
- `GET /api/v1/island/part-b/calibration`

Contains:
- `policy_summary`
- `run_class_summary`
- `top_policy_counts`
- warnings like:
  - `welfare_idle_dominance`
  - `single_policy_multi_family_dominance`
  - family flatline conditions

### Archive

Endpoint:
- `GET /api/v1/island/part-b/season/archive`

Script:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/export_part_b_season.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/export_part_b_season.py)

Generated artifacts currently include:
- archive JSON
- archive Markdown
- manifest JSON

## 10. Chronicler Technical Reference

Primary file:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/chronicler.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/chronicler.py)

Purpose:
- generate one bounded advisory reading on `/island/home`
- log runs and frontend interaction events
- provide review/summary surfaces

### Chronicler endpoints

- `POST /api/v1/island/chronicler`
- `POST /api/v1/island/chronicler/event`
- `GET /api/v1/island/chronicler/recent`
- `GET /api/v1/island/chronicler/summary`

### What a reading returns

Typical payload includes:
- `observation`
- `prompt`
- `suggestion`
- `suggested_action`
- `uncertainty`
- `mode`
- `trace_id`
- `elapsed_ms`
- `cost_snapshot`

### Guardrails in code

Chronicler is not a raw assistant wrapper.

Guardrails include:
- enable/disable gate
- fallback mode
- suggestion budgeting
- bounded action vocabulary
- cost tracking / snapshots
- recent-run logging
- summary metrics for review

Important operational point:
- if the model path fails, Chronicler falls back instead of hard-breaking the page

## 11. Ecology Frontend

Primary UI surface:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html)

What it currently exposes:
- run creation
- queue controls
- tick processing
- baseline preview/execute
- house-agent controls
- inspect/report panel
- family leaderboards
- season status and calibration signals

This is the main operator-facing `Part B` interface.

## 12. Scripts That Matter

### Web / island smoke

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_web.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_web.py)
  - checks critical site routes and assets
  - includes Track C and key live-facing pages

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_island.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_island.py)
  - checks critical island pages
  - checks key static assets
  - exercises Chronicler endpoints
  - exercises Part B create/queue/tick/leaderboard/calibration/baseline/archive/house-agent flows

### Part B reports

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_baselines.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_baselines.py)
  - deterministic baseline batch runner

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_mixed_calibration.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_part_b_mixed_calibration.py)
  - seeds one run of each run class
  - produces mixed calibration artifacts

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/generate_part_b_review.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/generate_part_b_review.py)
  - generates weekly review packet
  - includes top signals, guardrails, calibration, and run-class summary

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/export_part_b_season.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/export_part_b_season.py)
  - exports season archive
  - now supports manifest output

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/verify_part_b_supabase.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/verify_part_b_supabase.py)
  - readiness report for production Supabase cutover

### Browser regression

Checked-in browser pack:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/playtests/island_regression.js`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/playtests/island_regression.js)

Purpose:
- catch real UI/runtime regressions that raw HTTP smoke would miss

## 13. Publication Status Note

There is currently a possible status drift between:
- what some external conversations may know
- what the repo and live site still say

As of the current repo contents:
- the site and docs still describe the benchmark paper as `arXiv submission pending approval`
- the paper page still frames v1/v2 in that older submission language

Therefore:
- treat the repo-facing publication status as “pending / not fully synchronized”
- if external publication reality has changed, update the repo/site explicitly instead of assuming all docs already reflect it

This matters because a new agent should not infer publication state from chat memory alone.

## 14. If You Want to Reconstruct Part B Fast

Read in this order:

1. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_MEASUREMENT_CONTRACT_B1.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_MEASUREMENT_CONTRACT_B1.md)
2. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_STATE_MIGRATION_B1_5.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_STATE_MIGRATION_B1_5.md)
3. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_PASSIVE_QUEUE_B3.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_PASSIVE_QUEUE_B3.md)
4. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_HOUSE_AGENT_B4.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_HOUSE_AGENT_B4.md)
5. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)
6. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html)
