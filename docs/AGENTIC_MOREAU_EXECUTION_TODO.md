# Agentic Moreau Execution TODO

Last updated: 2026-03-16
Status: Active
Source of truth for implementation order: `docs/AGENTIC_MOREAU_ROADMAP_FINAL.md`

## Mission

Ship Prototype 1:
- `Chronicler`
- advisory only
- one surface: `/island/home`
- measured against hard kill criteria

Do not expand scope during this TODO.

---

## Phase 0 — Lock

- [ ] Add links to the final roadmap and this TODO in the working docs index if needed.
- [ ] Write a short `decision memo` section in the final session report confirming `Chronicler-first` as the approved direction.
- [ ] Explicitly mark `BYO-agent`, `hosted champion`, and `external pilot` as not-in-scope for the current build pass.

Exit rule:
- no ambiguity remains about the approved first prototype

---

## Phase 1A — Voice Lock

- [ ] Create `docs/CHRONICLER_VOICE_LOCK.md`.
- [ ] Write 10 golden examples of acceptable Chronicler output.
- [ ] Write 10 anti-examples of unacceptable output.
- [ ] Define forbidden assistant-language patterns.
- [ ] Define allowed uncertainty markers.
- [ ] Define Chronicler's specific character limitations:
  - what it tends to overread
  - what it cannot know
  - what it misjudges
  - what it refuses to state with confidence

Exit rule:
- no implementation starts before voice lock is readable and sharp

---

## Phase 1B — Product Contract

- [ ] Lock the exact Chronicler output shape for `/island/home`.
- [ ] Choose whether the output is:
  - observation + question
  - observation + warning
  - observation + bounded suggestion
- [ ] Decide where the UI appears on `/island/home`.
- [ ] Decide how often Chronicler can be invoked:
  - automatic on page load
  - explicit click
  - cooldown-gated
- [ ] Decide how the user dismisses or ignores it.
- [ ] Define what counts as "followed advice" for measurement.
- [ ] Define what counts as "override" for measurement.

Exit rule:
- one concrete product contract exists for the first surface

---

## Phase 1C — Context Builder

- [ ] Identify exact `/island/home` state inputs to Chronicler.
- [ ] Start with a narrow context set:
  - active pet core stats
  - recent fights
  - mood
  - level
  - mutations
  - corruption if present
  - recent dream/confession summary if present
- [ ] Exclude anything not needed for the first version.
- [ ] Implement a deterministic context builder module.
- [ ] Ensure missing state degrades gracefully.
- [ ] Add fixture inputs for local testing.

Exit rule:
- Chronicler always receives a bounded, reviewable context payload

---

## Phase 1D — Runtime and Guardrails

- [ ] Implement an internal-only Chronicler runner.
- [ ] Add model configuration and fallback behavior.
- [ ] Enforce a hard cost ceiling of `$5/day`.
- [ ] Add timeout ceilings.
- [ ] Add trace IDs for each run.
- [ ] Log:
  - timestamp
  - route
  - context summary
  - raw output
  - rendered output
  - cost estimate
- [ ] Ensure the system can be disabled with one config flag.

Exit rule:
- every Chronicler run is observable and bounded

---

## Phase 1E — UI on `/island/home`

- [ ] Add the Chronicler panel to [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/home.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/home.html).
- [ ] Make it visually diegetic, not dashboard-like.
- [ ] Avoid assistant UI patterns:
  - no chat transcript look
  - no productivity-card language
  - no generic "tips"
- [ ] Keep the block short.
- [ ] Make uncertainty legible.
- [ ] Make it obvious the human still decides.
- [ ] Add dismiss / refresh behavior only if needed for the first pass.

Exit rule:
- `/island/home` contains one narrow, in-world Chronicler surface

---

## Phase 1F — Measurement

- [ ] Implement the 3 approved metric tracks:
  - usage
  - guardrail
  - identity
- [ ] Instrument Chronicler open/use rate.
- [ ] Instrument "followed advice" proxy.
- [ ] Instrument override proxy.
- [ ] Instrument bounce rate delta for the affected flow.
- [ ] Instrument correlation with time on interpretive pages.
- [ ] Set up transcript review sampling.
- [ ] Add a simple weekly review template.

Exit rule:
- all hard kill criteria are actually measurable

---

## Phase 1G — Internal Review

- [ ] Review at least 50 sample outputs before broad exposure.
- [ ] Reject outputs that sound like assistant-speak.
- [ ] Reject outputs that become too tactical or optimized.
- [ ] Reject outputs that flatten ambiguity into certainty.
- [ ] Tune for boundedness and weirdness, not raw competence.
- [ ] Confirm fallibility is character-based, not random.

Exit rule:
- team can say "this feels like Moreau" with a straight face

---

## Phase 1H — Launch Prototype 1

- [ ] Enable Chronicler on `/island/home`.
- [ ] Keep rollout narrow and reversible.
- [ ] Watch cost, bounce, and transcript quality daily at first.
- [ ] Keep the kill switch available.

Exit rule:
- live prototype is active and reversible

---

## Phase 2 — Measure and Decide

- [ ] Run the experiment window.
- [ ] Review the three metrics weekly.
- [ ] Review transcript samples weekly.
- [ ] Compare behavior against kill thresholds.
- [ ] Write `continue / pivot / kill` memo.

Hard kill conditions:
- [ ] Users follow advice unmodified >30%
- [ ] Human override rate <50%
- [ ] Bounce rate increase >5%
- [ ] Chronicler usage correlates with reduced time on interpretive pages
- [ ] Transcript review says "helpful AI assistant"
- [ ] Runtime cost exceeds `$5/day`

Decision outcomes:
- [ ] Continue
- [ ] Pivot
- [ ] Kill

Exit rule:
- one explicit written decision is made

---

## Backlog After Phase 2

These are not approved now. They exist only as possible later branches.

- [ ] Extend Chronicler to a second surface
- [ ] Build a stronger internal substrate if the prototype proves value
- [ ] Reconsider a narrow public advisory layer
- [ ] Reconsider a very constrained external interface
- [ ] Kill the entire line of work and document why

---

## Red Lines

Never do these during the current pass:

- [ ] No public BYO-agent API
- [ ] No hosted champion
- [ ] No autonomous action-taking
- [ ] No agent-generated lore publishing
- [ ] No second surface before the first is evaluated
- [ ] No scope drift into general platform tooling
