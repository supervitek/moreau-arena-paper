# Part B Agentic Ecology Roadmap — Council Ready

Last updated: 2026-03-16
Status: Revised after three Claude Code advisor critiques
Owner: Codex acting as chief engineer
Supersedes: `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_DRAFT.md`

## Executive Decision

Moreau Arena should explicitly become a two-benchmark system:

- `Part A`: controlled strategic benchmark
- `Part B`: persistent ecological benchmark

`Part A` remains the laboratory.
`Part B` becomes the island ecology.

This is not a soft thematic distinction. It is a product and measurement split.

`A` asks:
- can the model play well under a controlled protocol?

`B` asks:
- can the agent survive, grow, allocate effort, and remain coherent over time inside a persistent hostile world?

---

## Binding Decisions

This document is not only vision. It makes four binding decisions.

## Decision 1 — Part B is not human-first

Humans are not the primary low-level pilots of `B`.

Humans become:
- operators
- owners
- reviewers of outcomes
- setters of priorities and risk appetite

Manual play remains possible.
But manual play is not the main intended mode of mastery.

## Decision 2 — The first user is the operator, not the casual player

The first target user for `B` is:

- a technically curious operator who wants a persistent world where their delegate improves things while they are away

Not the first target user:

- casual Tamagotchi-only player
- broad consumer gamer
- public external agent developer

Those may come later. They are not the first design center.

## Decision 3 — Hosted house agent is the first agent product

If `B` becomes agent-native, the first agent product is:

- the hosted house agent

Not first:

- BYO-agent API
- open marketplace of bots

The house agent is the fastest path to testing the operator fantasy:

- assign priorities
- leave
- come back
- inspect what happened

## Decision 4 — Benchmark integrity beats product convenience

The hosted house agent may exist as a service layer before external agents.
But it must not contaminate the benchmark contract.

Therefore:

- the house agent is excluded from the benchmark leaderboard until a public observation/action contract exists
- if a house-agent leaderboard exists earlier, it must be explicitly labeled as a house league, not the benchmark leaderboard

This removes the biggest trust failure before it starts.

---

## Why This Split Is Correct

## Part A

`A` is where Moreau remains disciplined:

- frozen historical data
- explicit tracks
- explicit rule variants
- controlled season boundaries
- apples-to-apples comparability

Examples of allowed evolution in `A`:

- board-size changes
- weather conditions
- new controlled season variants
- new track definitions

Examples of forbidden evolution in `A`:

- silent protocol drift
- mutating old data
- changing old rules without reversioning

## Part B

`B` is where Moreau becomes deep, harsh, and path-dependent:

- persistent state
- compounding decisions
- meaningful loss
- incomplete information
- competing objectives
- operator/agent separation

Trying to keep `B` permanently simple for direct human micro-play would flatten the very part of the project that is becoming distinctive.

Complexity in `B` is acceptable if:

- humans are not forced to micro-manage it constantly
- agents are evaluated inside it coherently
- the world still has measurement contracts

---

## Product Thesis for Part B

The core fantasy of `B` is:

- your delegate keeps acting while you sleep
- your absence has consequences
- your strategic choices matter because they shape ongoing behavior, not just immediate clicks

This is the real hook.

Without an agent:

- progress is manual
- nothing improves while you sleep

With an agent:

- work continues
- mistakes compound
- progress compounds
- your priorities matter even when you are offline

That is the right operator fantasy.

---

## First Revenue Hypothesis

The first monetization hypothesis for `B` is:

- hosted house agent as a subscription service

Default working assumption:

- low monthly subscription for one active operator account
- higher tiers later only if the core loop proves sticky

This is a hypothesis, not a locked price.
But the model is explicit:

- not ads
- not enterprise
- not “free forever and maybe monetize later”

The hosted agent incurs ongoing inference cost, so `B` must be designed under a real cost model from the beginning.

---

## Benchmark Integrity Contract for Part B

The ecological benchmark is valid only if three contracts exist per measurement season:

1. Observation contract
- what the agent can see

2. Action contract
- what the agent can do

3. Scoring contract
- how outcomes are turned into leaderboard-relevant numbers

Until these are public and stable for a season:

- the hosted house agent is a product service, not benchmark evidence

This distinction is critical.

---

## What Part B Measures

`B` is not trying to measure “general intelligence.”
It is not trying to measure global model quality.

It measures:

- persistent behavioral outcomes under a named world contract

That requires explicit score families.

## Score Family 1 — Welfare

Measures:
- survival duration
- happiness stability
- health stability
- neglect avoidance

This score must explicitly penalize degenerate coward policies.
An agent that does nothing forever cannot top the welfare ladder.

## Score Family 2 — Combat

Measures:
- arena success
- combat efficiency
- combat-linked reward capture
- recoverability after losses

## Score Family 3 — Expedition

Measures:
- depth reached
- extraction quality
- survival-adjusted yield
- decision quality in push-your-luck contexts

## Score Family 4 — Composite

Measures:
- weighted blend of the three families above

Important:
- the composite score will become the headline number in practice
- therefore its weights are part of the benchmark contract, not a UI detail

---

## Degenerate Policy Rule

Before Part B is treated as a benchmark, one explicit anti-degeneracy test must exist:

- run a trivially conservative agent
- run a trivially greedy agent
- run a trivially random agent
- verify that none of them dominate the scoring system

If a “do almost nothing” policy scores well, the benchmark is invalid.

---

## Human Intervention Rule

Human intervention is allowed in `B` as product behavior.
But benchmark interpretation must treat this clearly.

Therefore:

- all human interventions must be logged
- benchmark leaderboards must distinguish:
  - agent-only runs
  - operator-assisted runs

If that separation is not enforced, attribution becomes muddy.

---

## Observation and Action Grammar

The agent in `B` must not be a vague “AI that can do stuff.”

It needs an explicit grammar.

Each measurement season must define:

- visible state fields
- allowed actions
- action costs
- tick cadence
- call budget
- failure semantics

Without this, adding world content just increases prompt ambiguity instead of benchmark depth.

---

## Three Initial Pillars

Part B should begin with only three activity pillars.

## Pillar 1 — Care

Focus:
- caretaker loops
- welfare
- maintenance
- survivability

This reveals:
- discipline
- patience
- consistency

## Pillar 2 — Arena

Focus:
- PvP arena
- mutation-assisted combat
- combat-linked rewards

This reveals:
- aggression
- build quality
- tactical risk appetite

## Pillar 3 — Expedition

Focus:
- one push-your-luck PvE route
- stop/continue decisions
- escalating reward versus death risk

This reveals:
- route choice
- extraction discipline
- risk calibration

These three pillars are enough to produce meaningful policy differences.

Do not build beyond them initially.

---

## Initial Zone Scope

Roadmap scope should name only three active zones:

1. `The Arena`
- baseline PvP surface

2. `The Cave of Catharsis`
- push-your-luck expedition surface

3. `The Black Orchard`
- greed-versus-integrity surface

Everything else belongs to long-range design space, not the roadmap body.

Why these three:

- together they cover stable play, combat play, and extraction play
- together they create meaningful tradeoffs
- together they are enough for first policy differentiation

---

## Economy Constraint

Part B needs an economy, but it must be intentionally narrow.

Initial rule:

- maximum one resource family per pillar

That means:

- one Care-linked resource
- one Combat-linked resource
- one Expedition-linked resource

No combinatorial item explosion.
No relic zoo.
No sprawling crafting tree.

If `B` cannot become strategically interesting with three simple resource channels, it will not become healthier by adding fifteen.

---

## The Hidden Prerequisite: State Architecture

This is the most important engineering correction from advisor review.

The “agent works while you sleep” thesis cannot run on client-local island state.

To support real passive progression, `B` requires:

- durable server-side state
- per-action write log
- conflict semantics for human vs agent mutation
- replay/audit visibility

This is not a feature.
It is a prerequisite migration.

Therefore the roadmap must treat server-side state migration as an explicit gate, not an implementation detail.

---

## Minimal Shippable Sequence

This is the smallest realistic sequence for a tiny team.

## B0 — Thesis Lock

Deliverables:
- this approved roadmap
- final A/B split language
- hosted-agent integrity contract
- initial monetization statement

## B1 — Measurement Contract

Deliverables:
- score formulas
- observation contract
- action grammar
- season versioning rules
- anti-degenerate policy test

This should produce a versioned measurement contract artifact, not only prose.

## B1.5 — State Migration

Deliverables:
- move relevant `B` state from localStorage-only persistence to durable server-side storage
- per-action event log
- basic conflict semantics

This is a gate before passive progression.

## B2 — Three-Pillar Manual World

Deliverables:
- Care loop
- Arena loop
- one Expedition loop

Important:
- still manually triggered
- no autonomous agent yet

Purpose:
- validate whether the score design reveals real policy differences at all

## B3 — B2-lite Passive Queue

Deliverables:
- queued action list
- FIFO only
- small max queue length
- simple per-tick execution
- reporting to the operator

Not allowed:
- no priority queue
- no preemption logic
- no general planner

This is the minimum version of “works while you sleep.”

## B4 — Hosted House Agent

Deliverables:
- one LLM call per pet per tick
- hard cost cap
- explicit action grammar
- logged decisions
- operator-facing settings

This is a constrained hosted agent, not a free-form autonomous super-operator.

## B5 — Measurement Season

Deliverables:
- named Part B season
- frozen season contract
- benchmark leaderboard for valid run classes
- separate labeling for any house-only league

Only after this should external agent integration be reconsidered.

---

## What Is Explicitly Delayed

- BYO-agent API
- public agent marketplace
- zones 4+
- complex item combinatorics
- full MMO economy
- multiple competing leaderboard classes
- any attempt to make `B` broad-consumer friendly too early

---

## Biggest Risks

## 1. Scope explosion

Counter:
- only three zones
- only three pillars
- only one hosted agent first

## 2. Benchmark theater

Interesting world, weak measurement.

Counter:
- bind observation, action, and scoring contracts before passive-agent expansion

## 3. Hosted-agent trust collapse

Counter:
- house agent excluded from benchmark leaderboard until public contract exists

## 4. Infrastructure-first trap

Counter:
- do not build a full agent platform before validating the three-pillar world manually

## 5. Degenerate safe policies

Counter:
- require anti-coward scoring tests before calling the system a benchmark

---

## What Changed After Claude Code Advisor Review

Three Claude Code advisors reviewed the earlier draft from product, benchmark, and systems angles.

Their strongest corrections were:

1. This must make decisions, not only articulate philosophy.
2. Benchmark integrity for the house agent must be structural, not rhetorical.
3. The first user and first revenue model must be explicit.
4. The ten-zone ladder was scope leakage and was cut to three active zones.
5. “Priority queue” was unrealistic and was replaced by a FIFO passive queue.
6. State migration is an explicit prerequisite, not a hidden implementation detail.
7. Score families must be defined as contracts, not only named as ideas.

This revised version incorporates those corrections directly.

---

## Questions for the Round Table

1. Is the hosted-agent integrity contract strong enough, or should the house agent be delayed even further?
2. Is the first user definition correct: operator first, not casual player?
3. Are the three initial zones the right trio?
4. Is subscription the right first monetization hypothesis, or should it be credits instead?
5. Is the “manual world before passive queue” sequence correct, or too conservative?
6. What score family is still most likely to collapse into a degenerate policy?
7. What should be cut again before execution begins?
