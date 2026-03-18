# Project Bible — Moreau Arena

Last updated: 2026-03-17  
Status: Canonical high-context handoff for new agents and new accounts

This file is the fastest way to bring a new coding agent up to the real current state of the project.

It is intentionally opinionated. When this file conflicts with older agent docs, prefer this file plus the current code on `main`.

## 1. Project in One Page

Moreau Arena is no longer just one thing.

It is now a project with three connected layers:

1. `Part A` — the controlled benchmark
2. `World / Season / Island` — the narrative and product layer
3. `Part B` — the persistent ecological benchmark

Short version:

- `Part A` asks: can the model play well under controlled, reproducible conditions?
- `World / Season / Island` makes the project legible, strange, memorable, and interactive.
- `Part B` asks: can an agent endure, prioritize, and grow coherently over time in a persistent world?

The project must preserve measurement integrity without collapsing into a generic AI platform.

## 2. Canonical Principles

These principles are load-bearing.

1. `Part A` must remain apples-to-apples comparable across seasons and variants.
2. Frozen benchmark artifacts are not to be edited casually.
3. New measurement changes belong in clearly versioned tracks or seasons, not silent drift.
4. Narrative is load-bearing. It is not cosmetic wrapping.
5. Agents must not bypass the interpretive weirdness of Moreau.
6. `Part B` is operator-first and agent-native, not casual-human-first.
7. Small-team pragmatism matters more than platform ambition.

## 3. Source-of-Truth Order

When context conflicts, use this order:

1. Current code on `main`
2. This file
3. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_TODO.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_TODO.md)
4. The current finalized roadmap docs
5. Older handoff docs like [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/HANDOFF_FOR_CODEX.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/HANDOFF_FOR_CODEX.md)
6. Legacy agent rules that no longer match actual workflow

Important: some older docs say “never push to `main` directly.”  
Actual working reality on this project is different:

- canonical branch: `main`
- Render deploys from `main`
- local commits on `main` are normal
- `git pull --rebase` before push remains the correct hygiene rule

## 4. Frozen / High-Risk Areas

These are the strongest guardrails in the repo.

### Frozen forever

- `data/tournament_001/`
- `data/tournament_002/`
- `data/tournament_003/`
- `data/season1_tournament/`
- `simulator/config.json`

### Treat as high-risk

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/paper/moreau_arena.tex`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/paper/moreau_arena.tex)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)
- `season1/engine_s1.py`
- `simulator/engine.py`

Rule:
- freeze benchmark data
- version new measurement behavior
- do not “quietly improve” old benchmark regimes

## 5. Current Product Shape

### Part A — Controlled benchmark

This is the research benchmark side.

Current benchmark history:

- `T001`
- `T002`
- `T003`

The intention going forward is:
- continue making new benchmark seasons/tracks
- keep old measured regimes interpretable
- preserve apples-to-apples comparisons where promised
- introduce major rule shifts only as new named tracks or seasons

### World / Season / Island

This is the public-facing world and product layer:

- homepage
- leaderboards
- fighter pages
- quick fights
- Moreddit
- pets
- island
- Chronicler

Season 1 is already live and should be treated as published history, not preview content.

### Part B — Persistent ecological benchmark

This is now an approved expansion, not a speculative side idea.

`Part B` measures:
- persistence
- prioritization
- adaptation
- survival/growth tradeoffs
- operator/agent dynamics over time

Current approved structure:
- two active zones only:
  - `The Arena`
  - `The Cave of Catharsis`
- run classes:
  - `manual`
  - `operator-assisted`
  - `agent-only`
- family scores:
  - `welfare`
  - `combat`
  - `expedition`
- `composite` is intentionally not the headline score in the first season

## 6. Current Strategic Decisions

### Agentic Moreau decision

The approved narrow agentic experiment is:
- `Chronicler`
- advisory, bounded, visible, fallible by character
- on one surface first:
  - `/island/home`

Not approved right now:
- public BYO-agent API
- hosted champion
- external pilot
- generic AI assistant layer

### Part B decision

The approved `Part B` direction is:
- persistent ecological benchmark
- operator-first
- hosted house agent first
- BYO-agent later, if ever, and only after public contract maturity

House agent benchmark integrity rule:
- house agent may not enjoy hidden privileges
- benchmark participation only counts once the public contract exists and parity is real

## 7. What Has Already Been Done

This section is here so a new agent does not redo settled work.

### Site stabilization

Already done:
- homepage/nav cleanup
- preview badge removal
- Track C backend fix
- pets bug fixes
- launch-readiness pass
- social/metadata hardening
- browser-smoke and island regression pack

### Chronicler

Already done:
- voice lock
- product contract
- backend runtime
- frontend on `/island/home`
- bounded advisory logic
- reporting and summary endpoints
- tests and smoke coverage

Primary files:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/chronicler.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/chronicler.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/chronicler.js`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/chronicler.js)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_ROADMAP_FINAL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_ROADMAP_FINAL.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_EXECUTION_TODO.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_EXECUTION_TODO.md)

### Part B

Already done:
- `B1` measurement contract
- `B1.5` state migration foundation
- `B2` manual ecology slice
- `B3` passive queue
- `B4` hosted house agent
- `B5` first measurement season
- 10-point follow-up package, closed locally except live Supabase enablement

Primary files:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_EXECUTION_TODO.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_EXECUTION_TODO.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_10_POINT_COMPLETION_CHECKLIST.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_10_POINT_COMPLETION_CHECKLIST.md)

## 8. Actual Current State

### What is live and working

- benchmark site
- Season 1 pages
- fighter pages
- pets flow
- island
- Chronicler on `/island/home`
- Part B ecology surface
- Part B queue and hosted house agent logic
- Part B season leaderboards and report/archive tooling

### What remains not fully complete

Mostly external/operational, not conceptual:

1. real live operator traces for Part B
2. production Supabase enablement for Part B persistence
3. confirmation that production `storage-status` switches to `supabase`
4. real recurring review cadence based on live use

### Practical truth

The codebase is much more mature than the old handoff suggests.  
The main unfinished edge is no longer “build the thing,” but “run the thing with real persistence and real usage.”

## 9. Key Files a New Agent Should Read First

If a fresh agent has limited context window, this is the reading order.

1. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_BIBLE.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_BIBLE.md)
2. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_TODO.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_TODO.md)
3. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_ROADMAP_FINAL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_ROADMAP_FINAL.md)
4. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md)
5. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_EXECUTION_TODO.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_EXECUTION_TODO.md)
6. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py)
7. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)
8. [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/chronicler.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/chronicler.py)

## 10. Runtime and Commands

### Core test command

```bash
python3 -m pytest -q
```

### Local web

```bash
python3 -m uvicorn web.app:app --reload --port 8000
```

### Island smoke

```bash
python3 scripts/smoke_island.py
```

### Web smoke

```bash
python3 scripts/smoke_web.py
```

### Browser regression

```bash
cd scripts/playtests && npm run island-regression -- --base-url http://127.0.0.1:8000
```

### Part B reports

```bash
python3 scripts/run_part_b_baselines.py --output reports/part_b_b5_baselines.md
python3 scripts/run_part_b_mixed_calibration.py --json-output reports/part_b_mixed_calibration.json --md-output reports/part_b_mixed_calibration.md
python3 scripts/generate_part_b_review.py --output reports/part_b_weekly_review.md
python3 scripts/export_part_b_season.py --json-output reports/part_b_b5_archive.json --md-output reports/part_b_b5_archive.md --manifest-output reports/part_b_b5_manifest.json
python3 scripts/verify_part_b_supabase.py --output reports/part_b_supabase_readiness.json
```

## 11. Workflow Rules That Matter in Practice

These reflect actual working practice, not stale generic policy.

1. Work from `main`.
2. Before push: run relevant tests or smoke.
3. Before push: `git pull --rebase`.
4. Push directly to `main` when the change is validated and intentional.
5. Do not revert unrelated untracked or user-created files.
6. Do not touch `council_records/` unless the task is specifically about Round Table outputs.

## 12. Claude Code / KK Orchestration

This machine has working local KK orchestration.

Key facts:

- dispatcher: [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/kk_dispatch.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/kk_dispatch.py)
- protocol: [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/coord/AGENT_PROTOCOL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/coord/AGENT_PROTOCOL.md)
- KK should run through Claude Max auth, not accidental API-key billing
- dispatcher already strips `ANTHROPIC_API_KEY` unless explicitly overridden

Use KK when it creates leverage:
- parallel critique
- focused audits
- secondary reviews

Do not rely on KK for the primary truth over tests and code.

## 13. Current Highest-Value Next Steps

If a new agent takes over now, the next best moves are:

1. enable real Supabase persistence for Part B in production
2. confirm live `storage-status = supabase`
3. accumulate real operator traces
4. run the first live Part B review cadence
5. calibrate Part B scores against real traces, not only seeded ones

## 14. What Not to Waste Time On

Do not restart solved debates unless there is new evidence.

Not the right next move:
- making BYO-agent API now
- broadening Part B to many more zones immediately
- adding composite score as the main Part B headline
- making Chronicler into a generic helper
- reworking old benchmark history
- “cleaning up” frozen tournament data

## 15. If This File Is Used on Another Account

Tell the new agent:

1. Read this file first.
2. Assume the code on `main` is canonical.
3. Treat `Part A`, `Chronicler`, and `Part B` as already real, not speculative.
4. Do not spend time rediscovering settled architecture.
5. Start from the next unfinished operational edge:
   - production persistence
   - live traces
   - real calibration

Short prompt to pair with this file:

> Read [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_BIBLE.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_BIBLE.md) first. Treat it as the high-context source of truth unless the current code on `main` contradicts it. Then inspect the current code and continue from the highest-value unfinished operational work without re-litigating settled design decisions.

## 16. Companion Documents

These are the most relevant companion docs.

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_TODO.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PROJECT_TODO.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/LAUNCH_CHECKLIST.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/LAUNCH_CHECKLIST.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PAPER_VERIFICATION_REPORT.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PAPER_VERIFICATION_REPORT.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_ROADMAP_FINAL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/AGENTIC_MOREAU_ROADMAP_FINAL.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_AGENTIC_ECOLOGY_ROADMAP_FINAL.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_10_POINT_COMPLETION_CHECKLIST.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/PART_B_10_POINT_COMPLETION_CHECKLIST.md)
