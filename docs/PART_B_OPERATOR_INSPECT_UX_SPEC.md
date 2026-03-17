# Part B Operator Inspect UX Spec

Last updated: 2026-03-17
Status: B1 mock UX spec
Related contract: `docs/PART_B_MEASUREMENT_CONTRACT_B1.md`

## Purpose

The inspect surface is the operator’s answer to one question:

- what happened while I was away, and why?

This is not a dashboard of everything.
It is a legible post-hoc review surface for delegated activity.

---

## Core UX Goal

The operator should be able to open one surface and immediately learn:

1. what the pet or account did
2. whether it helped or hurt
3. what the hosted agent thought it was doing
4. whether intervention is needed now

---

## Information Blocks

## 1. Session Header

Must show:

- `season_id`
- `run_class`
- `world_tick`
- `time_since_last_inspect`
- `active pet`
- `active zone`

Purpose:
- orient the operator instantly

## 2. Status Delta Card

Must show:

- previous health / current health
- previous morale / current morale
- previous happiness / current happiness
- previous corruption / current corruption
- score family deltas

Purpose:
- summarize whether the system is trending better or worse

## 3. Action Ledger

Minimum row fields:

- tick
- actor
- action
- reason
- outcome
- cost
- zone

Purpose:
- explain what the delegate actually did

This is the single most important evidence block.

## 4. Score Impact Block

Must show:

- Welfare delta
- Combat delta
- Expedition delta

Composite score is not shown as the primary headline in the first season.

Purpose:
- keep the operator oriented around public score families

## 5. Intervention Prompt

Must answer:

- do I need to intervene now?

Example intervention states:

- `Care immediately`
- `Stop arena exposure`
- `Extract next cave run`
- `Agent paused on budget`
- `No intervention needed`

Purpose:
- convert logs into operator actionability

---

## Evidence Rules

The inspect surface must not rely on vibes or narrative summary alone.

Every displayed recommendation or warning must be traceable to:

- one or more concrete action log entries
- one or more concrete state deltas

The inspect surface can be atmospheric in tone.
It cannot be epistemically vague.

---

## First Mock Layout

Top to bottom:

1. Session Header
2. Status Delta Card
3. Most Recent 5 Actions
4. Score Impact Block
5. Intervention Prompt

This is enough for B1.

No need yet for:

- deep charts
- comparative history explorer
- multi-pet heatmaps
- replay visualizations

---

## Example Operator Questions the Surface Must Answer

- Why did my welfare score drop?
- Why did the agent choose the cave instead of care?
- Did the pet actually gain anything from the arena run?
- Is corruption getting out of hand?
- Am I budget-paused?
- Should I step in now or let the queue continue?

If the surface cannot answer these quickly, it is not good enough for Phase B1.
