# Part B State Migration — B1.5

Last updated: 2026-03-17  
Status: Active foundation implemented  
Source roadmap: `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`  
Companion contract: `docs/PART_B_MEASUREMENT_CONTRACT_B1.md`  
SQL schema: `sql/PART_B_STATE_MIGRATION_B1_5.sql`

## Purpose

Phase `B1.5` exists to move the minimum viable Part B benchmark state out of browser-only persistence.

Without this phase:
- delegated progression is fake
- operator inspection is partial
- human vs agent conflicts are invisible
- “works while you sleep” cannot become a valid benchmark claim

With this phase:
- the run envelope lives on the server
- the event log is replayable
- operator interventions have revision semantics
- B3 queue execution and B4 hosted agent can build on a real state path

---

## What Must Leave localStorage

The minimum state that must stop being browser-only is:

1. `run envelope`
- season id
- run class
- active zone
- world tick
- status
- revision number

2. `operator policy`
- priority profile
- risk appetite
- care threshold
- combat bias
- expedition bias

3. `queue state`
- FIFO queued actions
- queue capacity context
- budget remaining

4. `state projection`
- latest server-trusted snapshot needed to continue the run
- not every island secret
- only the published public contract + current run state

5. `event log`
- who acted
- what action was attempted
- under which revision
- what outcome happened
- whether the action was accepted or rejected

These five pieces are sufficient to make passive progression technically real without migrating the entire Island at once.

---

## What Stays Out of Scope in B1.5

Still not part of this phase:

- full Island-wide server migration
- BYO-agent infrastructure
- public benchmark season UI
- economy expansion
- privileged hidden agent actions
- third zone

`B1.5` is a substrate phase, not a feature-completeness phase.

---

## Storage Model

Two canonical server objects now exist:

## `part_b_runs`

One row per ecological run.

Purpose:
- hold the latest server-trusted projection
- define the current revision
- define the operator’s declared priorities
- serve as the anchor record for replay and reporting

Key fields:
- `id`
- `season_id`
- `run_class`
- `status`
- `subject_pet_*`
- `active_zone`
- `world_tick`
- `state_revision`
- `queue_state`
- `state_projection`
- `inference_budget_remaining`
- `conflict_policy`

## `part_b_events`

Append-only event log per run.

Purpose:
- preserve replayability
- preserve actor provenance
- preserve conflict outcomes
- power operator inspection reports

Key fields:
- `run_id`
- `sequence`
- `world_tick`
- `actor_type`
- `event_type`
- `action_verb`
- `expected_state_revision`
- `applied_state_revision`
- `conflict_status`
- `accepted`
- `observation`
- `outcome`
- `details`
- `state_after`

---

## Conflict Semantics

Part B now uses explicit revision semantics.

## Rule

Every run has `state_revision`.

When an agent or system event is submitted:
- it may include `expected_state_revision`
- if that revision is stale relative to the server run record, the event is rejected as `stale_rejected`

This encodes the approved principle:
- operator changes must be visible
- autonomous execution cannot silently overwrite newer human intent

## Working policy in B1.5

Default conflict policy:
- `operator_wins_before_execution`

Interpretation:
- operator updates that land before agent execution invalidate stale agent actions
- stale agent actions are logged, not silently dropped
- replay must show that the action existed and why it did not apply

This is enough for the first benchmark-safe passive loop.

---

## Replay and Report Path

The read path for operator inspection is now standardized:

1. load run envelope
2. load ordered event stream
3. derive compact report

Canonical endpoints:
- `GET /api/v1/island/part-b/storage-status`
- `POST /api/v1/island/part-b/runs`
- `GET /api/v1/island/part-b/runs`
- `GET /api/v1/island/part-b/runs/{run_id}`
- `PATCH /api/v1/island/part-b/runs/{run_id}`
- `POST /api/v1/island/part-b/runs/{run_id}/events`
- `GET /api/v1/island/part-b/runs/{run_id}/replay`
- `GET /api/v1/island/part-b/runs/{run_id}/report`

This read path is enough for:
- mock inspect UX
- weekly benchmark review
- debugging queue behavior
- later hosted-agent supervision

---

## Backend Modes

Two backend modes are intentionally supported:

## `supabase`

Production-intended mode.

Requirements:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- SQL in `sql/PART_B_STATE_MIGRATION_B1_5.sql`

Use:
- real persistence
- real replay history
- real delegated progression

## `file`

Development fallback.

Use:
- local prototyping
- tests
- isolated browser playtests

Important:
- file mode is acceptable for development
- it is not sufficient for a real benchmark season claim

---

## Exit Criteria for B1.5

`B1.5` counts as complete because the following are now true:

- the minimum run state has a server-side home
- operator policy and queue state can be stored outside the browser
- per-action events are replayable
- human vs agent conflicts are defined and enforceable
- operator replay/report read paths exist
- a Supabase-ready production path exists
- a file-backed dev path exists for local execution and tests

---

## What This Unlocks Next

This phase unlocks:

1. `B2`
- two-zone manual ecology slice can target a real run envelope

2. `B3`
- FIFO queue can execute against revisioned server state

3. `B4`
- hosted house agent can act through logged, replayable events

Without `B1.5`, those later phases would either drift back to localStorage or become benchmark theater.
