# Island Habitat V1 Plan

Last updated: 2026-04-10
Status: approved working plan for the small island build

## 0. Decision First

This `v1` should **not** start as one of the big canonical Island regions.

It should start as a **separate small habitat slice**:

- in the orbit of Island
- conceptually part of Moreau
- operationally isolated
- technically small enough to falsify quickly

Why:

1. the existing Island already carries product, lore, pets, lab, shrine, and social weight
2. the habitat experiment needs harsh clarity, controls, and null baselines
3. we do not yet know whether the "agent lives here" claim survives first contact with real runs
4. if we embed this directly into a major zone too early, we will inherit lore pressure, UX pressure, and architecture pressure before we have signal

So the correct framing is:

**Island Habitat V1 is a proving ground / micro-island, not yet one of the final mythic regions.**

Later, if it works, we can decide:

- merge it into one canonical zone
- make it the foundation of a new zone
- or keep it as the Island's measurement substrate beneath the visible world

## 1. Thesis

The smallest honest claim we want to test is:

**Can an agent maintain coherent behavior across cycles, using limited carry-forward state, in a world that changes without it?**

And second:

**Can the environment itself be measured as preserving or degrading that coherence?**

This is not yet a full Island civilization.
This is the smallest habitat where "the agent lives here" is not a lie.

## 2. What This Is

`Island Habitat V1` is:

- one small persistent world
- one agent at a time
- fixed cycles
- limited carry-forward state
- real constraints
- exogenous world change
- hard baselines
- logs good enough to prove or falsify the core claim

## 3. What This Is Not

Not yet:

- the full Island
- a social MMO-like layer
- multi-agent ecology
- a three-zone public world
- a rich memory architecture
- a new lore-heavy public feature

Those may come later.
They are not `v1`.

## 4. The Core Design Rule

We are not building "a lot of island."
We are building the **smallest environment that can separate**:

- carry-forward agent
- fresh agent
- scripted baseline
- random baseline

If the environment cannot separate those, it is not ready.

## 5. Load-Bearing Requirements

These are the non-negotiables for `v1`.

### 5.1 Cycle, not episode

The system must run as:

`state_in -> perception -> decision -> action -> state_out -> world_tick -> next cycle`

This is the backbone.

### 5.2 World changes without the agent

The environment must evolve between cycles.
If the world only changes in response to the agent, this is a looped task system, not a habitat.

### 5.3 Limited carry-forward state

The agent must have a strict memory budget across cycles.
No hidden infinite continuity.

### 5.4 Real constraints

The agent must face:

- limited action budget
- one depletable resource
- real failure / death boundary

### 5.5 Null baselines

The system is not valid without:

- random agent
- scripted heuristic agent
- fresh-agent baseline with no carry-forward

### 5.6 Logs good enough to inspect

Every cycle must be reconstructable.
No black-box "trust the metric" design.

## 6. The World We Will Build

For `v1`, the world should be small and explicit.

Recommended shape:

- small graph or small grid
- 8 to 12 locations/nodes
- typed locations
- partial observability

Recommended location types:

- `resource`
- `hazard`
- `shelter`
- `empty`

Recommended world properties:

- resource quantities
- one exogenous change per cycle or per fixed interval
- at least one irreversible or slow-to-recover consequence

The world does not need to be beautiful.
It needs to be interpretable and pressure-bearing.

## 7. The Agent Contract

The agent must receive:

- current cycle number
- local world observation
- current resource / health
- action budget
- carry-forward state from previous cycle
- legal actions

The agent must return:

- chosen action
- updated carry-forward state
- optional short rationale

Critical rule:

The system and the agent should not write the same kind of truth.

- system stores factual state
- agent stores self-authored carry-forward

If the system writes everything, we are testing JSON reading.
If the agent writes everything, we are testing self-narration.
`v1` must keep both surfaces distinct.

## 8. Memory Rule

Do **not** build three-tier memory in `v1`.

`v1` memory:

- one carry-forward blob
- hard size cap
- archive only as logs, not active retrieval

Suggested starting budget:

- `1500` to `2000` tokens

This is enough to test continuity without building a memory platform first.

## 9. Action Space Rule

Do **not** start with 7 action domains.

`v1` should start with **3 actions** that create real tradeoffs.

Recommended set:

1. `explore`
2. `gather`
3. `rest` or `observe`

Why:

- easy to reason about
- enough for non-trivial tension
- small enough to debug

Only add more actions after `v1` shows real signal.

## 10. Death and Irreversibility

`v1` needs a real failure boundary.

Suggested rule:

- agent has one survival resource
- it depletes each cycle
- some hazards deplete it faster
- reaching zero ends the run

Also required:

- some consequences cannot be immediately undone

Without death or irreversibility, the stakes are decorative.

## 11. What We Measure

### Agent-side

Minimum metrics:

1. survival length
2. divergence from fresh-agent baseline
3. adaptation rate after world shifts
4. carry-forward usefulness
5. coherence under compression / corruption

### Environment-side

Minimum checks:

1. does the world actually invalidate fixed strategies?
2. does the world force tradeoffs?
3. can random and scripted agents be clearly separated from persistent agents?
4. does the world drift into triviality or repetition?

Important rule:

Metrics are a mirror, not a KPI.
We are not optimizing "agent health score."
We are checking whether the system produces meaningful differences.

## 12. Falsification Rule

We need one clear failure condition for the thesis.

Working falsification rule:

**If a carry-forward agent and a fresh agent with identical instructions produce statistically indistinguishable behavior over repeated runs, then the claim "the agent lives here" is not yet supported.**

This is the core scientific gate.

## 13. Build Order

### Phase 0 — Test Contract

Goal:
- define the experiment before the world

Tasks:

1. Write the falsification rule
2. Define success metrics
3. Define null baselines
4. Define death condition
5. Define carry-forward budget
6. Define what would count as "alive" vs "just looping"

Deliverable:
- one short design contract for the experiment

Gate:
- if we cannot define the test clearly, we do not build yet

### Phase 1 — World Contract

Goal:
- specify the minimal world precisely

Tasks:

1. choose graph or grid
2. define location types
3. define exogenous change rules
4. define resource rules
5. define hazard rules
6. define irreversibility

Deliverable:
- `WorldState` schema and tick rules

Gate:
- a human should be able to narrate cycle 1, 10, and 50 exactly from the spec

### Phase 2 — Agent Contract

Goal:
- lock the interface

Tasks:

1. define input schema
2. define output schema
3. define carry-forward format
4. separate factual state from self-authored state

Deliverable:
- `AgentIO` contract

Gate:
- no world code before the contract is stable

### Phase 3 — Minimal Engine

Goal:
- make the loop run

Tasks:

1. implement world state
2. implement cycle engine
3. implement persistence of carry-forward
4. implement per-cycle logs
5. implement death / reset logic

Deliverable:
- runnable loop for dummy agents

Gate:
- system must run 50+ cycles without manual intervention

### Phase 4 — Baselines

Goal:
- prove the metrics mean something

Tasks:

1. random agent
2. scripted heuristic agent
3. fresh-agent baseline
4. compare runs

Deliverable:
- first comparison table and logs

Gate:
- if metrics cannot separate these agents, stop and redesign the environment

### Phase 5 — First Real Agent

Goal:
- test the actual claim

Tasks:

1. plug in one real LLM agent
2. run repeated cycle sequences
3. compare against fresh-agent baseline
4. inspect logs manually
5. inspect carry-forward degradation or usefulness

Deliverable:
- first honest answer to whether persistence matters

Gate:
- if carry-forward does not create meaningful behavioral divergence, the habitat claim is not ready

### Phase 6 — Pressure

Goal:
- move from persistence to persistence-under-pressure

Tasks:

1. introduce world shifts
2. introduce carry-forward corruption or noise
3. test adaptation after disruption
4. measure degradation curves

Deliverable:
- evidence about resilience, not just continuity

Gate:
- if the agent collapses immediately or no differently from baselines, do not expand scope yet

### Phase 7 — Expansion

Only after `Phase 6` produces signal.

Possible next steps:

- add one more action
- add archive / retrieval
- add second agent
- add trade or conflict
- map this habitat into a canonical Island region

## 14. Recommendation on the "Three Areas" Question

For now:

**Do not make `v1` one of the three big areas.**

Make it:

- a separate proving ground
- a hidden annex
- a small outer inlet
- or a measurement substrate beneath the larger Island fiction

Why this is better:

- protects the bigger Island design from premature architecture lock-in
- lets us falsify quickly
- keeps the experiment honest
- avoids lore pressure before the mechanics earn it

After `v1`, if the signal is real, we can decide which larger area it belongs to.

## 15. Working Public Thesis

The strongest honest line for now is:

**Island Habitat V1 is a small persistent environment designed to test whether an agent can maintain coherent behavior across cycles under changing conditions, and whether the environment itself supports or degrades that coherence.**

## 16. Next Practical Step

Do not start by coding the whole island.

Start with:

1. `Phase 0` test contract
2. `Phase 1` world contract
3. `Phase 2` agent contract

Only after those three are written should implementation begin.
