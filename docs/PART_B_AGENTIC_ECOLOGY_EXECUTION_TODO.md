# Part B Agentic Ecology Execution TODO

Last updated: 2026-03-17
Status: Active
Source of truth: `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`

## Mission

Turn Part B into a valid ecological benchmark without blowing scope or losing benchmark integrity.

The next mandatory focus is:

- `B1 — Measurement Contract`

---

## Phase B0 — Lock

- [x] Finalize Part B roadmap after Round Table review.
- [x] Lock A/B split language.
- [x] Lock house-agent integrity rule.
- [x] Lock initial scope cuts:
  - no Black Orchard
  - no composite headline score
  - no flat subscription commitment

Exit rule:
- no ambiguity remains about the approved Part B direction

---

## Phase B1 — Measurement Contract

- [ ] Define run class taxonomy:
  - `manual`
  - `operator-assisted`
  - `agent-only`
- [ ] Define observation contract.
- [ ] Define action contract.
- [ ] Define tick cadence.
- [ ] Define inference/call budget contract.
- [ ] Define season boundary rules.
- [ ] Define family score formulas:
  - Welfare
  - Combat
  - Expedition
- [ ] Add explicit welfare decay formula.
- [ ] Add anti-degenerate baseline tests:
  - trivially conservative
  - trivially greedy
  - trivially random
- [ ] Write mock operator inspect UX spec.
- [ ] Decide what evidence is shown to the operator after offline progression.

Exit rule:
- Part B has a versionable measurement contract, not just ideas

---

## Phase B1.5 — State Migration

- [ ] Identify the minimum Part B state that must leave localStorage.
- [ ] Design server-side persistence for that state.
- [ ] Add per-action event log.
- [ ] Define human vs agent conflict semantics.
- [ ] Define replay/report read path for operator inspection.

Exit rule:
- passive delegated progression is technically possible without fake persistence

---

## Phase B2 — Manual Ecology Slice

- [ ] Build `The Arena` as initial combat surface.
- [ ] Build `The Cave of Catharsis` as initial expedition surface.
- [ ] Connect both surfaces to family scores.
- [ ] Support manual runs.
- [ ] Support operator-assisted runs.
- [ ] Do not add a third active zone.

Exit rule:
- the two-zone world exists and the score families can be exercised in reality

---

## Phase B3 — Passive Queue

- [ ] Implement FIFO queued action list.
- [ ] Add queue length cap.
- [ ] Add passive tick execution.
- [ ] Add operator report for completed actions.
- [ ] Explicitly avoid priority/preemption logic.

Exit rule:
- “works while you sleep” exists in bounded form

---

## Phase B4 — Hosted House Agent

- [ ] Add constrained hosted house agent under public contract.
- [ ] Add hybrid billing logic concept:
  - world access
  - inference credits
  - auto-pause on exhausted budget
- [ ] Add operator controls for house agent.
- [ ] Ensure house agent acts only through published action grammar.

Exit rule:
- house agent can run without invalidating future benchmark claims

---

## Phase B5 — First Measurement Season

- [ ] Name first Part B season.
- [ ] Freeze season contract.
- [ ] Publish family score leaderboards.
- [ ] Separate leaderboard views by run class.
- [ ] Permit house agent in benchmark season only if it is using the public contract.
- [ ] Keep composite score out of headline presentation.

Exit rule:
- Part B has a real first measurement season

---

## Explicit Red Lines

- [ ] No BYO-agent API in the first execution cycle
- [ ] No Black Orchard in the first execution cycle
- [ ] No composite headline score in the first measurement season
- [ ] No priority queue
- [ ] No broad economy expansion before the two-zone slice works
- [ ] No hidden house-agent privileges once the public contract exists
