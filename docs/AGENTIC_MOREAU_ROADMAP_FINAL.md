# Agentic Moreau Roadmap — Final

Last updated: 2026-03-16
Status: Approved working roadmap after Round Table review
Owner: Codex acting as chief engineer

## Decision

Moreau Arena will explore agentic participation, but only in a narrow, diegetic, human-strengthening form.

This is an expansion, not a pivot away from the benchmark or the world.

The first and only approved prototype path is:
- build `Chronicler`
- make it advisory, visible, bounded, and fallible
- keep the human as decision-maker
- measure whether it deepens interpretation or weakens it

Everything else is out of scope until this is proven.

---

## What We Are Actually Building

We are not building:
- a public agent API
- a hosted champion that plays instead of people
- a marketplace of bots
- a generic AI assistant layer
- an infrastructure platform

We are building:
- one internal advisory entity
- on one surface
- with one tightly bounded role
- under hard identity and behavior constraints

This entity is called `Chronicler`.

---

## Core Thesis

Agents belong in Moreau only if they experience the same interpretive labor as humans and increase human agency instead of replacing it.

If Chronicler makes the project feel like a helpful AI assistant, the experiment has failed.

If Chronicler shortens or bypasses the strange, interpretive, atmospheric parts of Moreau, the experiment has failed.

---

## Non-Negotiable Principles

1. Narrative is load-bearing.
The world is not wrapping paper around a utility product.

2. Agents do not bypass friction.
They must move through the same ambiguity, partiality, and ritual texture that humans face.

3. The human remains the chooser.
Chronicler may interpret, frame, warn, and suggest. It may not decide.

4. Scope stays narrow.
One entity. One surface. One experiment.

5. Public platformization is explicitly deferred.
No BYO-agent pilot is part of the current roadmap.

6. Identity beats convenience.
If a feature is efficient but de-Moreaus the product, it loses.

7. Observability is mandatory.
Every Chronicler interaction must be measurable enough to judge success or failure.

---

## What Changed After Round Table Review

The Round Table critiques materially changed the plan:

- removed the external pilot from the roadmap
- collapsed formal pre-work into a build-first path
- added hard kill criteria
- elevated voice/tone lock and fallibility design to first-class requirements
- reduced metrics to three core measures

The main lesson was simple:
do not build scaffolding for months and never reach the experiment.

---

## First Prototype

## Entity

`Chronicler`

## Product Role

A diegetic advisory presence that reads a player's current state and offers a bounded interpretive response.

## Allowed Behaviors

- point out patterns
- raise warnings
- ask sharp questions
- offer bounded, uncertain suggestions
- direct attention toward overlooked parts of state

## Disallowed Behaviors

- speaking like a generic assistant
- giving optimal or dominant "correct" answers
- acting on behalf of the user
- auto-submitting, auto-mutating, or auto-playing
- generating canonical lore for the site

## Fallibility Model

Chronicler must be fallible through character limits, not random error injection.

Allowed fallibility:
- incomplete knowledge
- bias toward omens or symbols
- over-reading some signals
- under-trusting some obvious optimizations
- conflicting interpretations under uncertainty

Disallowed fallibility:
- arbitrary nonsense
- random wrongness for flavor
- broken or inconsistent world logic

---

## First Surface

The first and only approved surface for Prototype 1 is:
- `/island/home`

Why this surface:
- it is central
- it touches pet state, mood, fight history, dreams, mutations, and corruption
- it lets Chronicler deepen interpretation rather than optimize a single tactical choice
- it avoids immediately turning the system into a combat copilot

What Chronicler does on `/island/home`:
- reads the active pet state
- reads recent fight history
- reads dream / confession / mutation / corruption context if present
- emits one short advisory block

Advisory block shape:
- one observation
- one question or warning
- optionally one bounded suggestion with explicit uncertainty

Example shape:
- "Three victories, but all against brittle foes."
- "Why is the wolf dreaming of still water after a speed-heavy run?"
- "You may want to delay mutation tonight, though I would not swear to it."

---

## Metrics

Only three metrics govern the experiment.

## 1. Usage Metric

Question:
- do people meaningfully engage with Chronicler?

Measure:
- Chronicler open/use rate on `/island/home`

Success signal:
- repeat use by the same users across sessions

## 2. Guardrail Metric

Question:
- is Chronicler becoming too authoritative?

Measure:
- human override rate

Failure threshold:
- if human override rate drops below 50%, Chronicler is too directive

## 3. Identity Metric

Question:
- does Chronicler deepen interpretation or replace it?

Measures:
- bounce rate delta after exposure
- time on interpretive pages after exposure
- qualitative transcript review

Failure thresholds:
- bounce rate increases by more than 5%
- Chronicler usage correlates with reduced time on interpretive pages
- transcript review says "this feels like a helpful AI assistant"

---

## Hard Kill Criteria

The experiment must stop if any of the following happen:

1. Users follow Chronicler advice unmodified more than 30% of the time.
That means the system is acting too much like an authority.

2. Human override rate falls below 50%.
That means humans are defaulting to the agent instead of interpreting for themselves.

3. Bounce rate on the affected flow rises by more than 5%.
That means the feature is harming experience.

4. Chronicler usage correlates with lower time spent on interpretive pages.
That means it is compressing or bypassing the very texture we are trying to preserve.

5. Internal transcript review concludes: "this feels like a helpful AI assistant."
This is immediate kill.

6. Runtime cost exceeds a hard ceiling of $5/day during the prototype.
This is a small-team constraint, not a nice-to-have.

---

## Voice Lock

Before implementation begins, Chronicler needs a voice lock.

This is not a long prose bible. It is a compact operational set:
- 10 golden examples of acceptable output
- 10 anti-examples of unacceptable output
- explicit forbidden tones
- explicit uncertainty markers
- explicit no-go phrases that sound like SaaS assistant language

Examples of forbidden drift:
- "Here are three recommendations"
- "Based on your current stats"
- "I suggest optimizing"
- "You should definitely"
- "Let's improve your performance"

The goal is to stop assistant-voice contamination before code ships.

---

## Minimal Technical Shape

We are not producing five formal preparatory specs before coding.

Instead, the implementation itself becomes the working spec, supported by one concise contract section in this roadmap and by tests.

Minimum engineering shape:

- one Chronicler context builder for `/island/home`
- one bounded response renderer
- one trace/log record per run
- one configuration layer for model/cost cap/fallback
- one reviewable transcript sample set

No external API surface is part of this phase.

---

## Roadmap Phases

## Phase 0: Strategy Lock

Duration:
- 1 week

Goal:
- freeze the decision and remove ambiguity

Deliverables:
- this final roadmap
- final execution TODO
- explicit decision that current path is `Chronicler-first`

Exit criteria:
- no unresolved debate about BYO, champion, or stagehand-first

## Phase 1: Build Chronicler

Duration:
- 6 weeks target

Goal:
- build the smallest real version of Chronicler on `/island/home`

Required components:
- voice lock
- fallibility design
- context builder
- bounded UI surface
- trace logging
- cost cap
- kill-criteria instrumentation

Exit criteria:
- live internal prototype exists
- transcripts are reviewable
- kill criteria are measurable

## Phase 2: Measure and Decide

Duration:
- 4 weeks target

Goal:
- determine continue / revise / kill

Questions:
- are people using it?
- are they still interpreting?
- is it preserving identity?
- is it cheap enough?

Exit criteria:
- one written decision memo:
  - continue
  - pivot
  - kill

## Phase 3: Decide Future Direction

This phase exists only if Phase 2 passes.

It does not pre-approve any public API.

Possible outcomes:
- expand Chronicler to a second surface
- keep it internal-only
- create a public advisory layer
- revisit a much narrower external interface later
- kill the line of work entirely

---

## Out of Scope for This Roadmap

The following are not part of the approved plan:

- BYO-agent pilot
- external trusted agent program
- public agent API
- hosted champion
- autonomous agent leagues
- agent-authored Moreddit or lore content
- full platform instrumentation for hypothetical future products

These are separate future decisions, not latent commitments.

---

## Decision Rules

Use these rules while implementing:

1. If a feature helps Chronicler sound smarter but less strange, reject it.
2. If a feature improves convenience by shortening interpretation, reject it.
3. If a feature requires a second user-facing surface before the first is validated, reject it.
4. If a feature cannot be measured against the three metrics, delay it.
5. If a feature invites platformization, cut it.

---

## Final Recommendation

Build exactly one thing:
a bounded, visible, fallible Chronicler on `/island/home`.

Do it fast enough to reach the real experiment.
Do it carefully enough to preserve Moreau's identity.
Do not let future-platform fantasies leak into phase 1.

If Chronicler deepens human judgment and preserves the weirdness, continue.
If it starts feeling like a competent assistant, kill it.
