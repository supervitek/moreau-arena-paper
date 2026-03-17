# Project TODO

Last updated: 2026-03-17

## Agentic Moreau

- Final roadmap: `docs/AGENTIC_MOREAU_ROADMAP_FINAL.md`
- Execution TODO: `docs/AGENTIC_MOREAU_EXECUTION_TODO.md`
- Current approved path: `Chronicler-first` on `/island/home`
- Explicitly not in scope right now: public BYO-agent API, hosted champion, external pilot

## Part B Ecology

- Final roadmap: `docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`
- Execution TODO: `docs/PART_B_AGENTIC_ECOLOGY_EXECUTION_TODO.md`
- Measurement contract: `docs/PART_B_MEASUREMENT_CONTRACT_B1.md`
- Operator inspect UX spec: `docs/PART_B_OPERATOR_INSPECT_UX_SPEC.md`
- State migration foundation: `docs/PART_B_STATE_MIGRATION_B1_5.md`
- Manual ecology slice: `docs/PART_B_MANUAL_ECOLOGY_SLICE_B2.md`
- Passive queue: `docs/PART_B_PASSIVE_QUEUE_B3.md`
- Hosted house agent: `docs/PART_B_HOUSE_AGENT_B4.md`
- Current next move: `B5 — First Measurement Season`

## Current Priority Order

1. Launch-readiness audit
- Verify critical routes, metadata, stale copy, broken links, and live-facing consistency.

2. Pets stabilization
- Verify create/train/mutate/profile flows, fix deterministic or misleading fight behavior, and harden soul fallback behavior.

3. Island browser-smoke
- Maintain the checked-in Playwright regression pack so UI regressions surface earlier than raw HTTP smoke.

4. Island hardening phase 2
- Continue cleaning shared state contracts and remaining hot spots like genesis/succession/bloodline-adjacent pages.

5. Launch content pack
- Keep launch posts and launch checklist current with the actual live state of the site.

6. Navigation/server-side dedup
- Lower priority than launch quality, but still the next structural cleanup after the site is stable.

7. Paper adaptation derivation cleanup
- Keep the committed T002 derivation script and verification docs aligned if the paper changes again.

## Execution Notes

- Frozen forever: `data/tournament_001-003/`, `data/season1_tournament/`, `simulator/config.json`
- Canonical repo: `main`
- Render auto-deploys from `main`
- Prefer small validated changes with smoke checks before push
- Multi-worker lanes available through `scripts/kk_dispatch.py`

## Progress

- [x] Multi-worker Claude orchestration
- [x] Track C backend fix
- [x] Homepage/nav/preview cleanup pass
- [x] Initial island stabilization pass
- [x] Launch-readiness audit refresh
- [x] Pets stabilization pass
- [x] Browser-smoke expansion
- [x] Checked-in island browser regression pack (`scripts/playtests/island_regression.js`)
- [x] Second-wave island browser audit and runtime fixes
- [x] Island hardening phase 2
- [x] Launch content refresh
- [x] Launch finish pass: docs, reproducibility, nav dedup
- [x] Chronicler weekly review/reporting template and provisional verdict flow
- [x] Committed T002 adaptation derivation script
- [x] Paper adaptation table re-derived from canonical JSONL
- [x] Part B B1.5 state migration foundation
- [x] Part B B2 manual ecology slice
- [x] Part B B3 passive queue
- [x] Part B B4 hosted house agent
