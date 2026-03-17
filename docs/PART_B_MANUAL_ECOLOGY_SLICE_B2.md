# Part B Manual Ecology Slice — B2

Last updated: 2026-03-17  
Status: Implemented prototype slice  
Source contract: `docs/PART_B_MEASUREMENT_CONTRACT_B1.md`  
Prerequisite: `docs/PART_B_STATE_MIGRATION_B1_5.md`

## Purpose

`B2` turns Part B from pure contract/spec work into a real, playable two-zone benchmark slice.

This phase intentionally does not try to ship the full Island as a benchmark world.
It does one narrower thing:

- prove that a persistent Part B run can exercise two distinct ecological pressures with replayable actions and family scores

---

## Active Surfaces

The implemented B2 slice lives at:

- `/island/ecology`

It contains exactly two active zones:

1. `The Arena`
- baseline combat pressure
- uses the published `ENTER_ARENA` action
- logs combat outcomes into the server-backed Part B run

2. `The Cave of Catharsis`
- push-your-luck expedition pressure
- uses `ENTER_CAVE` and `EXTRACT`
- preserves depth, held value, and injury pressure in the run state

No third active zone was added.

---

## Run Classes Supported

The B2 slice supports:

- `manual`
- `operator-assisted`

It does not yet support:

- `agent-only`

That remains blocked on later phases (`B3` queue execution and `B4` hosted house agent).

---

## What Is Real in B2

This is not a mockup.
The slice now has:

- server-backed Part B run creation
- per-action event logging
- replay history
- report summary
- family score output
- two distinct zone loops

The family scores now reflect:

- `Welfare`
  - current health, morale, happiness, neglect pressure, alive status

- `Combat`
  - accepted arena actions, wins/losses, combat-linked reward signal

- `Expedition`
  - cave depth reached, value extracted, injury tax

---

## Operator Model

The B2 page already encodes the approved human role:

- choose the pet
- choose run class
- choose priority profile
- act as operator
- inspect replay and scores

In `operator-assisted` mode the page also surfaces bounded hints.

Important:
- the hints do not act autonomously
- they do not bypass the public action grammar
- they exist only to establish the operator-assisted loop before hosted automation arrives

---

## Technical Shape

Primary files:

- `web/static/island/ecology.html`
- `part_b_state.py`
- `web/app.py`
- `sql/PART_B_STATE_MIGRATION_B1_5.sql`

Validation/support:

- `tests/test_part_b_state.py`
- `scripts/smoke_island.py`

Home entry point:

- `web/static/island/home.html`

---

## What B2 Deliberately Does Not Do

Still out of scope:

- BYO-agent API
- third zone
- broad economy
- composite headline score
- passive queue
- hosted autonomous execution

This phase is about benchmark validity and slice realism, not feature breadth.

---

## Exit Condition

`B2` is considered complete because:

- the two-zone world exists
- both zones feed family scores
- manual runs work
- operator-assisted runs work
- replay/report surfaces are real
- no third active zone was introduced

---

## Next Move

The next required phase is:

- `B3 — Passive Queue`

That is the phase that turns this slice from “operator acts on a persistent run” into “the run can keep moving while the operator sleeps.”
