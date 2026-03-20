# Part B Agentic Ecology Roadmap — Final

Last updated: 2026-03-20
Status: Finalized after Round Table review
Owner: Codex acting as chief engineer
Supersedes:
- `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_DRAFT.md`
- `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_COUNCIL_READY.md`

Implementation status:
- `B1` complete
- `B1.5` complete
- `B2` complete
- `B3` complete
- `B4` complete
- `B5` complete
- next focus: `house-agent boundary enforcement + trust surfacing`

## Final Verdict

Part B is an approved expansion of Moreau Arena.

It is not:
- a side game
- a generic AI platform
- a vague persistent sandbox

It is:
- a persistent ecological benchmark for agent behavior

This means Moreau now has two intentional benchmark surfaces:

- `Part A`: controlled strategic benchmark
- `Part B`: persistent ecological benchmark

`A` keeps apples-to-apples rigor.
`B` measures long-horizon agent behavior under a named world contract.

---

## What Part B Is For

Part B exists to answer questions that Part A cannot answer well:

- does the agent survive?
- does it progress or stagnate?
- does it become brittle or resilient?
- does it over-optimize short-term rewards?
- does it allocate care, combat, and expedition effort intelligently over time?

Short form:

- `A` asks: can the model play well?
- `B` asks: can the agent endure, prioritize, and grow coherently over time?

---

## Human Role

Part B is not human-first.

The human role is:
- operator
- priority setter
- reviewer
- intervention source at selected moments

The human is not expected to:
- micromanage every action
- keep the system alive through constant manual input
- be online for progress to occur

Manual play may remain possible.
But it is not the center of mastery.

---

## First User

The first design-center user for Part B is:

- the technically curious operator who wants a delegated persistent world

Not first:
- the casual pet keeper
- the mass-market gamer
- the external agent developer

This matters because it clarifies both onboarding and product design:

- the value is not “easy game”
- the value is “my delegate keeps working while I sleep”

---

## Agent Product Decision

The first agent product for Part B is:

- the hosted house agent

Not first:
- BYO-agent API
- public agent marketplace

Reason:
- hosted agent is the shortest path to testing the operator fantasy
- BYO too early would add infrastructure and trust complexity before the world contract is stable

BYO remains explicitly out of scope for the first execution cycle.

---

## Benchmark Integrity Rule

Round Table forced one important correction:

- a benchmark with no participants is not a benchmark

Therefore the final rule is:

1. The house agent is excluded from the benchmark leaderboard until a public observation/action/scoring contract exists.
2. Once that contract exists, the house agent may participate in Part B benchmark seasons.
3. If the house agent participates, it must do so under the exact same published contract as any other valid run class.

After the 2026-03-20 synthesis pass, that rule is now interpreted more sharply:

- product richness may live above the contract
- benchmark legitimacy lives inside the contract
- separation should happen through labels and enforcement, not through empty parallel leaderboards

This resolves the earlier paradox:
- no premature contamination
- no empty benchmark season

---

## Run Classes

Part B must explicitly track run classes from the beginning.

Minimum taxonomy:

- `manual`
- `operator-assisted`
- `agent-only`

Leaderboards and analysis must always be scoped by run class.

Otherwise Part B will mix:
- human skill
- human+agent skill
- agent behavior

and the benchmark signal will collapse.

---

## Measurement Contract

Part B cannot expand further until B1 produces a real measurement contract.

At minimum it must define:

1. Observation contract
- what the agent can perceive

2. Action contract
- what the agent can do

3. Tick contract
- how often decisions happen

4. Call budget contract
- how much inference is allowed

5. Scoring contract
- how scores are computed

6. Season contract
- what counts as a season boundary

This should be treated as a versioned artifact, not hand-wavy prose.

---

## Score Families

The Round Table did not reject the score-family structure, but it changed how it should be used.

## Welfare

Still approved as a score family, but now with one hard requirement:

- it must include explicit decay

Without decay, a do-nothing or ultra-safe agent can dominate illegitimately.

Working requirement for B1:
- define a concrete welfare decay formula

Example shape:
- unattended health/morale/happiness decay per tick
- neglect penalties
- anti-hoarding or anti-idling pressure

## Combat

Approved.
This captures arena competence, reward capture, and recoverability.

## Expedition

Approved.
This captures risk calibration, extraction discipline, and route judgment.

## Composite

Deferred.

Composite score should not be the headline metric in the first measurement season.

Reason:
- it will absorb too much attention too early
- the weights will be arbitrary before welfare/combat/expedition are validated separately

So for the first season:
- publish family scores
- delay the composite as a secondary internal aggregation only

---

## Initial World Scope

Round Table cut the earlier three-zone plan down to two active zones.

Approved initial active zones:

1. `The Arena`
- baseline combat and combat-linked reward surface

2. `The Cave of Catharsis`
- push-your-luck expedition surface

Cut from first scope:

- `The Black Orchard`

Reason:
- two zones are enough to validate the ecological thesis
- a third zone creates scope pressure before the measurement contract is proven

The broader zone ladder remains design space only, not roadmap scope.

---

## Economy Constraint

Part B needs economy pressure, but the first version must stay narrow.

Working rule:
- only the minimum economy needed for two zones and core pet progression

Do not add:
- large item combinatorics
- relic explosions
- sprawling multi-currency systems

The world should become strategically hard through tradeoffs, not through accounting noise.

---

## Monetization Decision

The earlier flat-subscription idea is no longer the working default.

Current preferred model:

- hybrid access model

Working shape:

- subscription grants access to the world and operator layer
- inference actions for the hosted house agent consume a bounded credit budget
- the system can auto-pause when budget is exhausted

Why:
- flat subscription with unbounded inference is unsafe for a tiny team
- pure credits weakens the ongoing world-membership feeling
- hybrid aligns product access with cost control

This is still a hypothesis, but it is the leading one now.

---

## Hidden Prerequisite Confirmed

State migration is mandatory.

Part B cannot honestly support passive delegated progression while island state lives only in browser-local storage.

Therefore `B1.5` is not optional:

- move relevant Part B state server-side
- create a per-action log
- define conflict semantics
- make operator inspection possible

This is the prerequisite that all six models agreed on.

---

## Mock Operator Inspect UX

Round Table added one important product/measurement requirement:

- B1 must include a mock operator inspect UX

Reason:
- operator fantasy cannot stay abstract
- the benchmark needs a visible place where actions, causes, and consequences are legible

This does not mean full polished UI.
It means:

- one inspect/report surface
- one clear action history
- one clear explanation of what happened while the operator was away

---

## Final Execution Sequence

This is the standardized future route.

## B0 — Thesis Lock

Done when:
- this roadmap is accepted as source of truth

## B1 — Measurement Contract

Must produce:
- run class taxonomy
- welfare decay formula
- anti-degenerate baselines
- observation/action/tick/budget contracts
- mock operator inspect UX spec

If only one action is taken next, it must be B1.

## B1.5 — State Migration

Must produce:
- server-side persistence for relevant Part B state
- action log
- conflict semantics
- replay/report read path

Status:
- foundation implemented

Artifacts:
- `docs/PART_B_STATE_MIGRATION_B1_5.md`
- `docs/PART_B_STATE_MIGRATION_B1_5.json`
- `sql/PART_B_STATE_MIGRATION_B1_5.sql`
- `part_b_state.py`

## B2 — Manual Ecology Slice

Must produce:
- Arena
- Cave of Catharsis
- manual and operator-assisted flows

Status:
- implemented prototype slice

Artifacts:
- `docs/PART_B_MANUAL_ECOLOGY_SLICE_B2.md`
- `web/static/island/ecology.html`

Purpose:
- validate scoring and world pressure before passive agent loops

## B3 — Passive Queue

Must produce:
- FIFO queued actions
- bounded queue
- passive progression
- reporting

Important:
- FIFO remains approved
- do not upgrade to priority queue

## B4 — Hosted House Agent

Must produce:
- constrained house agent under public contract
- credit budgeting
- auto-pause behavior
- operator-facing controls

## B5 — First Measurement Season

Must produce:
- named Part B season
- family score leaderboards
- valid run-class separation
- house agent participation only under public contract

Composite headline score is still delayed at this stage.

---

## What Is Explicitly Cut or Delayed

Cut from first execution cycle:

- Black Orchard
- composite score as headline
- flat subscription commitment

Delayed:

- BYO-agent API
- marketplace
- broad zone expansion
- priority queue
- full economy complexity

---

## Final Non-Negotiables

1. `A` must preserve apples-to-apples rigor.
2. `B` must remain measurable, not just atmospheric.
3. State migration is a prerequisite, not a later cleanup.
4. Welfare must include explicit decay.
5. Run classes must be separated.
6. House agent may not receive hidden benchmark privileges once the public contract exists.

---

## Immediate Next Move

`B1` now exists as:

- `docs/PART_B_MEASUREMENT_CONTRACT_B1.md`
- `docs/PART_B_MEASUREMENT_CONTRACT_B1.json`
- `docs/PART_B_OPERATOR_INSPECT_UX_SPEC.md`

The next correct move is:

- execute `B1.5 — State Migration`

Not:
- build more zones
- build the house agent
- build BYO
- build economy layers

Everything now depends on moving the relevant Part B state and action log to a durable server-side model, because passive delegated progression cannot honestly exist on browser-local state.
