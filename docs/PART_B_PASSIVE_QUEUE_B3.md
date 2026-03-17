# Part B Passive Queue — B3

Last updated: 2026-03-17
Status: Implemented
Owner: Codex acting as chief engineer

## Purpose

`B3` is the first bounded answer to the operator fantasy:

- queue work
- sleep
- return to a replayable trace

This is not a priority scheduler.
It is not a background MMO economy.
It is a strict FIFO queue running against the published Part B action grammar.

## What Exists

Server runtime:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)

Web/API surfaces:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html)

Verification:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/tests/test_part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/tests/test_part_b_state.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_island.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_island.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/playtests/island_regression.js`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/playtests/island_regression.js)

## Queue Contract

Queue semantics are intentionally narrow:

- FIFO only
- no priority
- no preemption
- bounded capacity
- one executed action per tick

Default capacity:
- `6` queued actions per run

Allowed queued verbs:
- `HOLD`
- `CARE`
- `REST`
- `TRAIN`
- `ENTER_ARENA`
- `ENTER_CAVE`
- `EXTRACT`
- `MUTATE`

## Tick Execution

Passive execution now runs through server state, not client-only localStorage.

Each processed tick:
- reads the current run envelope
- consumes the first queued action if present
- executes the public action contract
- appends a replayable event
- updates state projection
- updates queue state
- updates report surfaces

If no queue item exists:
- manual/operator-assisted runs stop cleanly
- `agent-only` runs may fall through to the hosted house agent

## Invalid Action Handling

Invalid queued actions do not silently mutate state.

Current bounded outcomes:
- `pet_not_alive`
- `arena_unavailable`
- `cave_unavailable`
- `nothing_to_extract`
- `mutation_cap_reached`

These are logged as replayable `tick_skipped` events rather than disappearing.

## Operator Report

The replay/report layer now exposes:

- pending queue items
- queue capacity
- recent completed passive actions
- accepted/rejected tick outcomes
- score deltas through the normal report path

The `ecology` page also renders a “While Away Report” block for these events.

## API

Core B3 endpoints:

- `POST /api/v1/island/part-b/runs/{run_id}/queue`
- `DELETE /api/v1/island/part-b/runs/{run_id}/queue/{item_id}`
- `POST /api/v1/island/part-b/runs/{run_id}/queue/clear`
- `POST /api/v1/island/part-b/runs/{run_id}/tick`

## Explicit Non-Goals

B3 still does not include:

- priority scheduling
- branching job graphs
- resource crafting economy
- offline cron runner
- hidden system actions outside the public grammar

## Exit Rule

`B3` is considered complete because:

- a FIFO queue exists
- it executes bounded ticks
- it emits replayable reports
- it does not introduce priority/preemption logic
- it works in the live `ecology` surface and in checked-in regression tooling
