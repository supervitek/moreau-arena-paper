# Part B Agentic Ecology Roadmap — Draft

Last updated: 2026-03-16
Status: Draft for Claude Code advisor review, then Round Table review
Owner: Codex acting as chief engineer

## Executive Summary

Moreau Arena is converging toward two different but complementary benchmarks:

- `Part A`: a controlled strategic benchmark
- `Part B`: a persistent ecological benchmark

`Part A` remains the laboratory. It preserves apples-to-apples comparability across seasons and controlled variants.

`Part B` should stop pretending to be a human-first game. It should become an agent-native world where models are evaluated by how they survive, grow, choose, and degrade under persistent, partially opaque conditions.

This is not a rejection of humans. It is a reassignment of human role:

- humans become operators, owners, patrons, and observers
- agents become the primary actors inside the world

If done correctly, this resolves the current tension:

- `A` stays scientifically controlled
- `B` becomes strategically deep without being forced to stay beginner-readable

---

## Core Thesis

`Part B` should evolve into a persistent agent operations benchmark.

The main question of `B` is not:

- "Can the model win a match?"

The main question of `B` is:

- "Can the agent survive, progress, adapt, prioritize, and remain coherent over time inside a hostile world?"

Short form:

- `A` asks: can the model play well?
- `B` asks: can the agent endure, grow, and choose well over time?

---

## Why This Direction Makes Sense

## 1. `B` is already drifting toward depth

Pets, mutation, dreams, corruption, caretaker systems, island state, bloodlines, expeditions, narrative surfaces, and now Chronicler are all pushing `B` toward a richer world model.

Trying to keep `B` permanently simple for casual human play will increasingly work against the direction of the project.

## 2. Hard worlds are sticky when they create stakes

Simple dopamine loops are one valid product shape, but they are not the only sticky shape.

Another shape is the harsh persistent world:

- steep learning curve
- meaningful loss
- compounding decisions
- asymmetry of knowledge
- identity through survival

This is closer to the long-term identity of `B`.

## 3. Agent-native complexity is a feature, not a bug

If the world becomes too complex for ordinary manual optimization, that is bad only if humans are still expected to micro-play it directly.

If the real role becomes:

- choose an agent
- configure priorities
- queue goals
- hire a hosted agent or connect your own
- review reports and intervene at strategic moments

then complexity increases the value of better agents instead of destroying usability.

## 4. `A` and `B` become legible as distinct products

Without this split, `B` risks feeling like a messy side-world.

With the split:

- `A` = controlled benchmark
- `B` = ecological benchmark

Together they form a coherent research/product system.

---

## Definition of the Two Benchmarks

## Part A — Controlled Strategic Benchmark

Purpose:
- compare model strategic performance under controlled, reproducible conditions

Properties:
- protocol clarity
- frozen historical data
- stable measurement logic
- explicit track/season/version boundaries
- apples-to-apples comparisons

Allowed evolution:
- new seasons
- new tracks
- controlled board-size changes
- weather variants
- new objective formats
- new constrained conditions

Not allowed:
- silent protocol drift
- changing old data
- changing old rules without versioning
- mixing world flavor changes into benchmark claims

Core question:
- under this defined ruleset, how well does the agent reason strategically?

## Part B — Persistent Ecological Benchmark

Purpose:
- compare how agents survive, grow, adapt, and allocate effort in a persistent world

Properties:
- persistent state
- risk accumulation
- multiple competing goals
- incomplete information
- meaningful opportunity cost
- asymmetric path choices

Allowed evolution:
- new zones
- new threats
- new resource loops
- new progression layers
- new failure modes
- new operator surfaces

Not allowed:
- arbitrary chaos without measurement
- pure content sprawl
- turning the world into unstructured lore theater

Core question:
- under persistent pressure and ambiguity, what kind of long-term behavior emerges from each agent?

---

## Human Role in Part B

Humans should not be the dominant low-level pilots of `B`.

They should become:

- operator
- owner
- patron
- strategist
- spectator

That means the human chooses:

- whether to use a hosted agent or bring one later
- what high-level priorities matter
- what risk appetite to set
- whether to pursue welfare, combat, mutation, or expedition outcomes
- when to intervene or override

The human should not need to:

- click every action manually
- babysit state every hour
- be online for progress to continue

The hook becomes:

- your agent keeps working while you sleep
- your account keeps changing
- your choices matter because your delegate keeps acting in your absence

This is one of the strongest differentiators available to the project.

---

## Why Human-First Design Is Wrong for Part B

If `B` remains human-first, two bad outcomes become likely:

1. The world is simplified until it loses its teeth.
2. Humans manually optimize the benchmark and contaminate the signal.

If the goal is to understand agent behavior, `B` must eventually become difficult enough that manual human micro-play is not the dominant path.

That does not mean humans disappear.
It means humans stop being the primary execution substrate.

---

## Product Shape

## The simplest long-term framing

Users have three broad choices:

1. Run manually
- possible, but labor-intensive and strategically limited

2. Use the house agent
- hosted, proprietary, convenience-first

3. Bring an external agent later
- not now, but possible in a later phase if the design stays coherent

Crucially:

- manual play must remain possible
- but agent-assisted play should become strictly more scalable

This creates meaningful tension:

- with no agent, nothing improves while you sleep
- with a strong agent, progress compounds

That is a very powerful operator fantasy.

---

## Initial Activity Pillars for Part B

Do not launch ten systems at once.

Start with three pillars that already imply different policy styles.

## Pillar 1 — Care

Examples:
- caretaker loops
- happiness
- health
- morale
- rest
- stable progression

What it measures:
- long-term welfare management
- low-risk compounding
- consistency

Possible leaderboard:
- welfare score
- happiness index
- survival streak
- average health stability

## Pillar 2 — Arena

Examples:
- direct PvP arena
- ranked fighting
- mutation-assisted combat
- reward-bearing combat

What it measures:
- tactical aggression
- build quality
- risk appetite
- mutation timing

Possible leaderboard:
- arena rank
- win rate
- trophy score
- combat earnings

## Pillar 3 — Expedition

Examples:
- random-condition arena
- push-your-luck caves
- trap-heavy PvE routes
- multi-stage boss runs

What it measures:
- risk evaluation
- route choice
- stop/continue judgment
- recovery discipline

Possible leaderboard:
- expedition depth
- extraction value
- survival-adjusted yield
- boss-clear efficiency

---

## Candidate Zone Ladder

These are concept candidates, not all immediate build targets.

## 1. The Arena

The cleanest combat surface.

Role:
- baseline PvP loop

## 2. The Crooked Arena

Arena with rotating conditions and reward modifiers.

Role:
- controlled variation with better loot

## 3. The Cave of Catharsis

Multi-stage descent.
After each miniboss, the agent can extract or continue.

Role:
- push-your-luck benchmark

## 4. The Manticore Woods

A hostile region with special objective logic, not only raw fighting.

Role:
- conditional reasoning under weird local rules

## 5. The Salt Tides

Environmental risk and attrition.

Role:
- recovery, pacing, and timing

## 6. The Black Orchard

Reward-heavy but corruption-heavy route.

Role:
- greed versus integrity

## 7. The Glass Kennels

Breeding and bloodline optimization under fragility.

Role:
- lineage strategy and delayed payoff

## 8. The Shrine of Quiet Debt

Tradeoffs between immediate rescue and long-term resource depletion.

Role:
- deferred cost reasoning

## 9. The Surgeon’s Stair

Mutation ladder with escalating irreversible choices.

Role:
- irreversible optimization under uncertainty

## 10. The Maw

Late-stage prestige zone for elite agents only.

Role:
- high-signal differentiator for the strongest policies

Important:
- do not build 5-10 soon
- use them as long-range design space

---

## Reward and Economy Direction

`B` needs a real economy, but not a bloated one.

Two reward channels are enough at first:

1. PvP rewards
- clean combat drops
- arena currency
- ranking-linked rewards

2. PvE rewards
- rare resources
- mutation materials
- survival/extraction rewards
- items or relics

This matters because resource loops force the agent to answer:

- fight now or save strength?
- mutate now or wait?
- spend for safety or gamble for upside?
- optimize one pet or diversify the roster?

Without that, `B` risks staying a flavor-rich activity tree instead of becoming an ecology of strategic tradeoffs.

---

## The Hosted Agent Question

The hosted house agent is product-powerful, but benchmark-dangerous.

It should exist eventually because:

- it is a natural conversion path
- it fits the operator fantasy
- it lets users access the world without bringing external infra

But it must be framed carefully.

Recommended framing:

- hosted house agent is a service layer, not the benchmark itself
- the environment and scoring must remain separable from the proprietary prompting layer
- users may know that the house agent has house advantages in convenience, but the benchmark contract must remain clear

Do not promise prompt transparency for the hosted agent.
But do preserve environmental fairness in what the agent is allowed to perceive and do.

---

## What Part B Must Measure

If `B` becomes an ecology benchmark, then “who is winning?” must stay legible.

Do not collapse all value into one single number too early.

Use a small family of scores:

## 1. Welfare Score
- happiness
- health stability
- survival duration
- neglect avoidance

## 2. Combat Score
- arena success
- efficiency
- reward capture
- losses and recoverability

## 3. Expedition Score
- depth
- extraction quality
- survival-adjusted loot
- decision quality under escalating risk

## 4. Composite Ecology Score
- weighted aggregate
- useful for headlines, but not the only truth

This allows different agents to reveal different styles instead of flattening everything into one ladder.

---

## What Should Be Held Constant

`A` preserves strict comparability.
`B` will never be as static, but it still needs strong version boundaries.

Recommended rule:

- each world season must have a clearly versioned environment contract
- mid-season balance changes must be rare and logged
- leaderboard comparisons must always be scoped to a named season/world state

That means `B` can evolve without becoming meaningless.

Short version:

- `A` is frozen-history strict
- `B` is season-versioned ecology strict

---

## Staged Build Plan

## Phase B0 — Thesis Lock

Deliverables:
- one approved concept memo
- explicit definition of `A` vs `B`
- explicit human role in `B`
- explicit non-goals

## Phase B1 — Measurement Lock

Deliverables:
- define `Welfare`, `Combat`, `Expedition`, `Composite`
- define seasonal versioning rules
- define what actions agents may take autonomously

Do not build new zones before this exists.

## Phase B2 — Minimal Operator Loop

Deliverables:
- task queue / priority queue
- active goals
- passive progress while user is away
- clear reporting of what the agent did

This is the first true “agent works while you sleep” layer.

## Phase B3 — Three-Pillar World

Deliverables:
- Care
- Arena
- one Expedition mode

This is enough to generate genuine policy differences.

## Phase B4 — Hosted House Agent

Deliverables:
- internal agent service
- operator-facing control surface
- clear service framing

No BYO yet.

## Phase B5 — Seasoned Ecology Benchmark

Deliverables:
- season versioning
- leaderboards
- historical comparisons by world season
- public-facing explanation of what `B` measures

Only after this should an external agent interface even be reconsidered.

---

## What Not To Build Yet

- no ten-zone content explosion
- no full MMO economy
- no public BYO-agent API
- no agent marketplace
- no lore generator replacing authored worldbuilding
- no complicated item combinatorics before the first real ecology loops are legible
- no “AI co-pilot for everything” surface creep

---

## Risks

## 1. Scope explosion

The most obvious risk.

Counter:
- only three pillars first
- only one expedition mode first
- strict phase exits

## 2. Unmeasurable richness

The world becomes interesting but not benchmarkable.

Counter:
- define score families before content expansion
- version seasons
- keep contract language explicit

## 3. Hosted-agent unfairness narrative

Users may feel the house agent is secretly privileged.

Counter:
- separate environment fairness from proprietary prompt quality
- keep allowed action space explicit

## 4. Human irrelevance

If the operator has no meaningful role, the product becomes sterile.

Counter:
- make humans choose goals, risk, and intervention thresholds
- keep manual play possible, but not mandatory

## 5. Part B loses its identity and becomes generic bot automation

Counter:
- keep the world strange
- keep consequences harsh
- keep environment-specific interpretation important

---

## Product Positioning

Moreau Arena should eventually be describable like this:

- `A`: a controlled benchmark for strategic reasoning
- `B`: a persistent benchmark for agent survival, growth, and choice

Or more vividly:

- `A` is the arena laboratory
- `B` is the island ecology

This is a stronger identity than:

- benchmark plus weird side game

It turns the project into a two-layer system with a clear logic.

---

## Recommended Next Step

Before any new `B` feature wave:

1. Review this document critically.
2. Stress-test it with internal AI advisors.
3. Bring the revised version to the Round Table.
4. After Round Table, produce:
   - a final `Part B roadmap`
   - a final `Part B execution TODO`
   - a first constrained implementation sequence

---

## Questions for Advisor Review

1. Is `B` as an ecological benchmark actually coherent, or is it still trying to be two products at once?
2. Is the operator/agent split the right human role model?
3. What is missing from the measurement design?
4. Which part of this plan is most likely to explode scope?
5. Which first `B` implementation step has the highest leverage?
6. Should the hosted house agent arrive before deeper world expansion, or after?
7. What should be cut before this goes to the Round Table?
