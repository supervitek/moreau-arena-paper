# Agentic Moreau Roadmap — Draft

Last updated: 2026-03-16
Status: Draft for Round Table review
Owner: Codex acting as chief engineer

## Executive Summary

Moreau Arena should not become a generic AI platform.

The correct expansion is narrower and stranger:
- humans remain the primary audience
- the narrative layer remains load-bearing
- agents are allowed only if they operate inside the same interpretive world as humans
- the first release should deepen human judgment, not replace it

The recommended direction is:
1. define an internal agent substrate first
2. build one internal diegetic advisory agent
3. measure whether that agent increases engagement, retention, and interpretive depth
4. only then consider limited external agent participation

This is a product expansion, not a replacement of Side A or Side B.

---

## Why This Exists

The current project has three unusual assets:
- a real benchmark with research credibility
- a theatrical world with mood, lore, and symbolic density
- a system already legible to agents in practice, even when it is cognitively heavy for humans

This creates an opening:
- complexity can be reframed from friction into moat
- agents can become participants in the Arena
- humans can become handlers, judges, witnesses, patrons, or interpreters rather than deprecated players

The risk is equally real:
- Moreau could collapse into "yet another AI tool"
- narrative could be reduced to skin over utility
- the team could drown in infra work before validating any new loop

This roadmap exists to prevent that.

---

## Product Thesis

### Core Thesis

Moreau Arena should support agentic participation only if agents are forced to experience the same interpretive labor as humans rather than bypassing it.

### Product Framing

Wrong framing:
- API platform
- model playground
- general-purpose agent framework

Correct framing:
- arena for strategic actors under strange constraints
- world in which human and agent actors are both legible within the fiction
- narrative benchmark where interpretation matters

### Strategic Goal

Create a third layer above the existing benchmark and Island:
- Side A: benchmark legitimacy
- Side B: world / game / engagement
- Side C: agentic participation mediated through Moreau's own logic

This Side C must strengthen both A and B instead of cannibalizing them.

---

## Non-Negotiable Principles

1. Narrative is load-bearing.
The project must never become a neutral shell wrapped around an agent product.

2. Agents do not bypass friction.
If a human must interpret a strange page, incomplete clue, or unstable signal, the agent should face the same shape of ambiguity.

3. Human agency must increase, not shrink.
The first agent feature should help a human decide, not decide on their behalf.

4. Public APIs come late.
A small team should not open a broad external surface before learning its own agent failure modes.

5. Agent content is constrained.
Agents should not flood the site with lore, posts, or generic synthetic sludge.

6. Instrument before scale.
Every new agentic capability must be observable with logs, replays, state traces, and explicit success/failure criteria.

7. Moreau remains weird.
If a proposed feature makes the product cleaner but less distinctive, default to preserving the weirdness.

---

## Non-Goals

The following are explicitly out of scope for the first roadmap:
- generic chatbot UX
- open public "bring any agent" API
- marketplace of third-party bots
- autonomous agent-vs-agent leagues at scale
- agent-generated lore as default site content
- billing-heavy enterprise platformization
- replacing the current benchmark with a tool product

---

## Recommended Product Path

## Path A: Internal Diegetic Advisory Agent

This is the recommended first prototype.

Working codename:
- Chronicler

Function:
- does not act for the player
- does not play the benchmark directly
- interprets state, surfaces patterns, whispers warnings, suggests options
- remains visibly fallible

Why this path first:
- lowest infra risk
- strongest fit with project identity
- does not require opening public APIs
- preserves human judgment
- lets us validate whether agents deepen the world or flatten it

### Example behaviors

- "Your panther dreams of speed but has lost three will-heavy fights."
- "The tides are wrong tonight. Mutation may grant power but carries a cost."
- "Track B punished greedier adaptations than expected. Reconsider the obvious counter."

### What it must not do

- auto-submit builds
- auto-play core public modes
- generate canonical lore
- become the optimal hidden path through the game

---

## Alternative Paths Considered

## Path B: BYO-Agent First

Pros:
- lean on external compute
- attractive to advanced users
- ecosystem upside

Cons:
- large auth, fairness, abuse, and support burden
- high chance of premature platformization
- likely too early for current bandwidth

Verdict:
- do not start here

## Path C: Hosted Champion First

Pros:
- easy story hook
- controlled outputs

Cons:
- can instantly make humans feel obsolete
- can push product toward optimization instead of interpretation
- risks becoming the "correct" way to play

Verdict:
- possible later, but not as phase 1

## Path D: Hidden Stagehand Agents

Pros:
- minimal UI disruption
- operationally clean

Cons:
- risk of making human experience opaque
- reduces legibility and trust if agent effects are invisible

Verdict:
- use only for internal systems, not as the first user-facing expression

---

## Technical Substrate First

Before any public-facing agent feature, we need a formal internal substrate.

## Substrate Questions

1. What state can an agent observe?
2. What actions can an agent take?
3. Which actions are advisory versus authoritative?
4. What are the success metrics?
5. What logging and replay guarantees exist?
6. What boundaries protect fairness, cost, and identity?

## Minimum Internal Spec

The first internal spec should define:

### 1. State Surfaces

- benchmark state
  - track metadata
  - leaderboard snapshots
  - matchup histories
  - public docs and measurement rules

- island state
  - pet dossier
  - mutation state
  - dream/confession/caretaker state
  - fight history
  - current page / scene context

- narrative state
  - visible copy the user sees
  - known uncertainty markers
  - permitted fictional framing
  - prohibited truth claims

### 2. Action Types

- advisory actions
  - suggest
  - warn
  - summarize
  - interpret
  - compare

- reversible low-risk actions
  - draft build
  - queue mutation option
  - draft note / dossier

- forbidden early actions
  - final submission without human review
  - destructive state changes
  - autonomous ladder play
  - narrative publishing into public site content

### 3. Observability

- every agent run gets a trace ID
- every prompt/context payload is loggable internally
- every output is replayable
- every advisory recommendation can be compared against human action and outcome

### 4. Runtime Constraints

- strict cost ceilings
- timeout ceilings
- prompt/context budgets
- explicit model choice by lane
- graceful fallback when external APIs are unavailable

### 5. Identity Constraints

- diegetic formatting rules
- allowed tone envelopes
- prohibited product-language leakage
- no "AI assistant" generic voice in live UX

---

## Product Architecture Roadmap

## Phase 0: Strategy Lock

Goal:
- settle product direction before writing infrastructure for the wrong problem

Deliverables:
- this roadmap reviewed by Round Table
- final decision memo
- first prototype choice locked
- success metrics locked

Exit criteria:
- explicit decision between advisory-first, champion-first, or BYO-first
- written non-goals approved

## Phase 1: Internal Substrate Spec

Goal:
- define the agent layer without exposing it publicly

Deliverables:
- `docs/AGENT_SUBSTRATE_SPEC.md`
- `docs/AGENT_GUARDRAILS.md`
- `docs/AGENT_EVENT_SCHEMA.md`
- inventory of state surfaces in `web/app.py`, Island pages, and benchmark pages

Execution:
- formalize advisory actions
- formalize forbidden actions
- enumerate state models and state-read adapters
- define replay / log requirements

Exit criteria:
- one clear spec for state, actions, logs, constraints

## Phase 2: Internal Runtime and Trace Layer

Goal:
- create safe internal plumbing for agent experiments

Deliverables:
- internal runner for agent tasks
- trace logging for all runs
- storage for agent transcripts and outcome metadata
- deterministic test harness for advisory prompts

Execution:
- implement internal-only routes or modules, not public APIs
- add model adapters for hosted internal agents
- add fail-safe fallback behavior
- add admin-only inspection surface

Exit criteria:
- advisory agent can run against fixture states and produce logged outputs

## Phase 3: Prototype 1 — Chronicler

Goal:
- validate whether a visible, flawed, diegetic advisory agent improves the Moreau experience

User story:
- a human can ask for interpretation or counsel
- the Chronicler offers a constrained reading of the current state
- the human still chooses

Capabilities:
- reads current pet / fight / benchmark context
- produces short, stylized, bounded advisory output
- can be wrong
- can disagree with obvious optimization
- cannot act directly

Initial placement options:
- Island dashboard sidebar
- pit / train pre-fight panel
- benchmark compare page advisory panel
- dossier annotation view

Success metrics:
- usage rate
- return usage rate
- does the human still take actions themselves
- subjective delight / weirdness retention
- no spike in confusion or bounce

Failure modes to watch:
- advice too useful and flattening
- advice too vague and ignored
- advice reads as generic LLM slop
- advice breaks world tone

Exit criteria:
- at least one surface where Chronicler clearly adds value without eroding identity

## Phase 4: Narrow External Pilot

Goal:
- test limited external participation without full public platform exposure

Form:
- invite-only trusted pilot
- 3 to 5 external builders
- constrained interface only

What is exposed:
- one narrow read-only or semi-structured submission interface
- no arbitrary execution
- no broad write access

Potential pilot modes:
- benchmark strategy submission draft
- replay interpretation assistant
- constrained "handler" input for one game mode

Exit criteria:
- real usage
- manageable abuse surface
- clear understanding of support burden

## Phase 5: Decide Public Direction

Only after phases 1-4.

Decision options:
- remain internal-only
- ship hosted advisory agent publicly
- ship invite-only BYO access
- ship hybrid
- kill the idea

The option to kill the idea must remain real.

---

## Workstreams

## Workstream A: Product

- choose first agent role
- define target human experience
- define where advice is welcome and where it is intrusive
- define "good weirdness" versus "confusing noise"

## Workstream B: Engineering

- substrate spec
- state adapters
- internal runtime
- replay / tracing
- cost control
- error fallback

## Workstream C: Design / UX

- how agent presence appears in-world
- visual language for whispers, warnings, and uncertainty
- how to signal "advisory only"
- how to keep humans in control

## Workstream D: Narrative

- name, persona, limits, flaws
- how the agent speaks
- what it cannot know
- how it fails in a Moreau-consistent way

## Workstream E: Measurement

- success metrics
- guardrail metrics
- replay review cadence
- go / no-go checkpoints

---

## Candidate Prototype Comparison

| Prototype | What it does | Why it is attractive | Main risk | Recommendation |
|-----------|--------------|----------------------|-----------|----------------|
| Chronicler | Advisory interpreter, flawed and visible | Strong identity fit, low infra risk, preserves human judgment | Can become gimmick or confusing | Recommended first |
| Champion | Hosted strong player | Easy story hook, measurable outcomes | Makes humans feel second-class | Later only |
| Invisible Stagehand | Backstage optimizer | Operationally neat | Low trust, low legibility | Internal only |
| BYO External Agent | External agent connects in | Ecosystem upside | Massive support and abuse burden | Not first |

---

## Monetization View

Monetization is not phase 1, but the roadmap should still note viable directions.

Best-aligned later options:
- patronage of a named entity
- premium advisory access
- tournament entry / premium league access
- agent seats for trusted advanced users

Low-alignment options:
- ads
- generic seat-based SaaS language
- selling raw API throughput as the identity of the product

---

## Risks

## Product Risks

- dilution of identity
- two half-products instead of one coherent product
- audience confusion over what Moreau is
- premature complexity

## Technical Risks

- brittle state extraction
- runaway API cost
- unbounded context windows
- poor observability
- abuse or exploit surface if exposed too early

## UX Risks

- humans feel displaced
- agent outputs feel too confident
- narrative becomes decorative instead of structural
- advice creates opacity rather than insight

## Mitigations

- keep first agent advisory-only
- log everything
- constrain outputs hard
- keep interfaces narrow
- do human review of representative transcripts
- refuse public API until failure modes are understood

---

## First Concrete Build Recommendation

Build:
- one internal advisory agent
- codename `Chronicler`

Do not build first:
- public BYO API
- autonomous arena champion
- agent marketplace
- agent-authored public feed

The first prototype should answer one question only:

Does a diegetic, fallible, advisory agent make Moreau Arena more compelling for humans?

If the answer is no, stop.

---

## Immediate Next Steps

1. Round Table critique on this roadmap draft.
2. Produce a final roadmap after critique.
3. Produce a final execution TODO with milestones and owners.
4. Start Phase 1 only after the strategic path is explicitly locked.

---

## Questions for Round Table

1. Is advisory-first still the correct sequence after reading this roadmap?
2. Should the first prototype be visible and flawed, or mostly backstage?
3. Is `Chronicler` the right first role, or should it be a different entity?
4. What part of the roadmap is overbuilt for a small team?
5. What part is still dangerously underspecified?
6. Which phase boundary is most likely to fail in practice?
7. What should be removed before execution starts?
