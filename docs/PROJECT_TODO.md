# Project TODO

Last updated: 2026-03-15

## Agentic Moreau

- Final roadmap: `docs/AGENTIC_MOREAU_ROADMAP_FINAL.md`
- Execution TODO: `docs/AGENTIC_MOREAU_EXECUTION_TODO.md`
- Current approved path: `Chronicler-first` on `/island/home`
- Explicitly not in scope right now: public BYO-agent API, hosted champion, external pilot

## Current Priority Order

1. Launch-readiness audit
- Verify critical routes, metadata, stale copy, broken links, and live-facing consistency.

2. Pets stabilization
- Verify create/train/mutate/profile flows, fix deterministic or misleading fight behavior, and harden soul fallback behavior.

3. Island browser-smoke
- Expand verification beyond raw HTTP 200 checks so UI regressions surface earlier.

4. Island hardening phase 2
- Continue cleaning shared state contracts and remaining hot spots like genesis/succession/bloodline-adjacent pages.

5. Launch content pack
- Keep launch posts and launch checklist current with the actual live state of the site.

6. Navigation/server-side dedup
- Lower priority than launch quality, but still the next structural cleanup after the site is stable.

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
- [x] Island hardening phase 2
- [x] Launch content refresh
- [x] Launch finish pass: docs, reproducibility, nav dedup
