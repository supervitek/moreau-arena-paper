# Part B Agentic Ecology Execution TODO

Last updated: 2026-03-20
Status: Active
Source of truth: `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`

## Mission

Turn Part B into a valid ecological benchmark without blowing scope or losing benchmark integrity.

The next mandatory focus is:

- `House-agent boundary enforcement and trust surfacing`

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

- [x] Define run class taxonomy:
  - `manual`
  - `operator-assisted`
  - `agent-only`
- [x] Define observation contract.
- [x] Define action contract.
- [x] Define tick cadence.
- [x] Define inference/call budget contract.
- [x] Define season boundary rules.
- [x] Define family score formulas:
  - Welfare
  - Combat
  - Expedition
- [x] Add explicit welfare decay formula.
- [x] Add anti-degenerate baseline tests:
  - trivially conservative
  - trivially greedy
  - trivially random
- [x] Write mock operator inspect UX spec.
- [x] Decide what evidence is shown to the operator after offline progression.

Artifacts:
- `docs/PART_B_MEASUREMENT_CONTRACT_B1.md`
- `docs/PART_B_MEASUREMENT_CONTRACT_B1.json`
- `docs/PART_B_OPERATOR_INSPECT_UX_SPEC.md`

Exit rule:
- Part B has a versionable measurement contract, not just ideas

---

## Phase B1.5 — State Migration

- [x] Identify the minimum Part B state that must leave localStorage.
- [x] Design server-side persistence for that state.
- [x] Add per-action event log.
- [x] Define human vs agent conflict semantics.
- [x] Define replay/report read path for operator inspection.

Artifacts:
- `docs/PART_B_STATE_MIGRATION_B1_5.md`
- `docs/PART_B_STATE_MIGRATION_B1_5.json`
- `sql/PART_B_STATE_MIGRATION_B1_5.sql`
- `part_b_state.py`

Exit rule:
- passive delegated progression is technically possible without fake persistence

---

## Phase B2 — Manual Ecology Slice

- [x] Build `The Arena` as initial combat surface.
- [x] Build `The Cave of Catharsis` as initial expedition surface.
- [x] Connect both surfaces to family scores.
- [x] Support manual runs.
- [x] Support operator-assisted runs.
- [x] Do not add a third active zone.

Artifacts:
- `docs/PART_B_MANUAL_ECOLOGY_SLICE_B2.md`
- `web/static/island/ecology.html`

Exit rule:
- the two-zone world exists and the score families can be exercised in reality

---

## Phase B3 — Passive Queue

- [x] Implement FIFO queued action list.
- [x] Add queue length cap.
- [x] Add passive tick execution.
- [x] Add operator report for completed actions.
- [x] Explicitly avoid priority/preemption logic.

Artifacts:
- `docs/PART_B_PASSIVE_QUEUE_B3.md`
- `part_b_state.py`
- `web/static/island/ecology.html`

Exit rule:
- “works while you sleep” exists in bounded form

---

## Phase B4 — Hosted House Agent

- [x] Add constrained hosted house agent under public contract.
- [x] Add hybrid billing logic concept:
  - world access
  - inference credits
  - auto-pause on exhausted budget
- [x] Add operator controls for house agent.
- [x] Ensure house agent acts only through published action grammar.
- [x] Verify a live Gemini house-agent run on production.
- [x] Verify a live watch-sync catch-up run on production.

Artifacts:
- `docs/PART_B_HOUSE_AGENT_B4.md`
- `part_b_state.py`
- `web/static/island/ecology.html`
- `scripts/verify_part_b_gemini_live.py`
- `reports/part_b_gemini_live_review.md`
- `reports/part_b_watch_sync_live_review.md`

Exit rule:
- house agent can run without invalidating future benchmark claims

---

## Phase B5 — First Measurement Season

- [x] Name first Part B season.
- [x] Freeze season contract.
- [x] Publish family score leaderboards.
- [x] Separate leaderboard views by run class.
- [x] Permit house agent in benchmark season only if it is using the public contract.
- [x] Keep composite score out of headline presentation.

Artifacts:
- `docs/PART_B_FIRST_MEASUREMENT_SEASON_B5.md`
- `docs/PART_B_SCORE_CALIBRATION.md`
- `docs/PART_B_SEASON_ARCHIVE_FORMAT.md`
- `docs/PART_B_SUPABASE_PRODUCTION_READINESS.md`
- `reports/part_b_b5_baselines.md`
- `reports/part_b_b5_archive.md`
- `reports/part_b_weekly_review.md`

Exit rule:
- Part B has a real first measurement season

---

## 10-Point Follow-Up Package

- [x] Live calibration pass, closed locally via baselines plus mixed run-class seeded traces.
- [x] Baseline expansion.
- [x] Leaderboard polish.
- [x] Inspect/report UI phase 3.
- [x] Queue/tick hardening phase 3.
- [x] Automated season review tooling.
- [x] Archive/export hardening.
- [x] Frontend/product polish for ecology.
- [x] KK/local review loop completed to shipping threshold.
- [~] Preparatory Supabase productionization completed up to the external production boundary.

Artifact:
- `docs/PART_B_10_POINT_COMPLETION_CHECKLIST.md`

---

## Next Runtime Focus

- [ ] Accumulate real operator traces beyond seeded local calibration runs.
- [x] Apply Part B SQL on production Supabase.
- [x] Verify `storage-status` returns `supabase` in production.
- [ ] Start the first live review cadence against real operator behavior.
- [x] Close the house-agent boundary package from `docs/PART_B_HOUSE_AGENT_BOUNDARY_EXECUTION_TODO.md`.

---

## Explicit Red Lines

- [x] No BYO-agent API in the first execution cycle
- [x] No Black Orchard in the first execution cycle
- [x] No composite headline score in the first measurement season
- [x] No priority queue
- [x] No broad economy expansion before the two-zone slice works
- [x] No hidden house-agent privileges once the public contract exists
