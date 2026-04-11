# Project Truth

Last updated: 2026-04-10
Purpose: one low-context truth file for any new human engineer or new AI wave.

Read this first.
Then choose exactly one next file:

- engineer: [`START_HERE_ENGINEER.md`](./START_HERE_ENGINEER.md)
- wave / new AI thread: [`START_HERE_WAVE.md`](./START_HERE_WAVE.md)
- operations / debugging live systems: [`START_HERE_OPERATIONS.md`](./START_HERE_OPERATIONS.md)

If you feel lost, do not keep digging. Return here.

## Project in 10 lines

Moreau Arena is no longer just one benchmark repo.

It now contains four connected layers:

1. `Part A` — the frozen, contamination-resistant benchmark
2. `World / Season / Island` — the public-facing product and narrative layer
3. `Part B` — the persistent ecological benchmark
4. `OpenClaw / self` — the private continuity and operational layer used to run long-lived agent work

These layers are related, but they are not the same thing.
Most confusion in new threads comes from mixing them.

## What Is True Right Now

- Canonical repo branch: `main`
- Public site: [moreauarena.com](https://moreauarena.com)
- `Part A` frozen benchmark artifacts remain load-bearing and must not be edited casually
- `Part B` is real project scope, not a speculative side idea
- `OpenClaw / self` is live and working again as of 2026-04-10
- Live OpenClaw runtime is driven by `~/.openclaw/openclaw.json`, not the repo-local `openclaw.json`
- Repo-local `openclaw.json` is a reference artifact, not the daemon's live runtime truth source
- Public Island routes do **not** expose the self/OpenClaw dashboard by default; `MOREAU_ENABLE_SELF_LAB=1` is required for explicit local lab use

## The Layers

| Layer | What it is | Main truth source | Mutable? | Audience |
|---|---|---|---|---|
| `Part A` | frozen benchmark + paper claims | `simulator/config.json`, frozen `data/tournament_001..003/`, invariant tests | mostly no | research, engineering |
| `World / Season / Island` | site, public world, playable/product layer | current code on `main`, [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md) | yes | public, product, engineering |
| `Part B` | persistent ecology benchmark | current code on `main`, [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md), `part_b_state.py`, finalized Part B docs | yes, but carefully | research, engineering |
| `OpenClaw / self` | private continuity + long-lived local agent layer | `~/.openclaw/openclaw.json`, native OpenClaw heartbeat, [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md) | yes, locally | operator, local AI work |

## Source-of-Truth Order

When documents conflict, use this order:

1. current code on `main`
2. this file
3. [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)
4. [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md) for self/OpenClaw questions
5. task-specific finalized docs
6. older handoff packages and historical notes

## Three Things People Keep Mixing Up

### 1. Public repo vs local self-system

The Moreau repo is public/product/research-facing.
The `self/` and OpenClaw continuity layer is private/local and operational.
Do not assume every OpenClaw artifact belongs in the public repo.
Do not ship half-live self telemetry into the public Island UX by default.

### 2. Repo `openclaw.json` vs live OpenClaw config

These are not the same file.

- live runtime truth: `~/.openclaw/openclaw.json`
- repo reference artifact: `./openclaw.json`

If debugging live OpenClaw behavior, start from the home-directory config.

### 3. Frozen benchmark vs evolving world

`Part A` benchmark artifacts are frozen for measurement integrity.
The public world, Island, Part B, and operational layers may evolve.
Do not "improve" frozen artifacts in place.

## What Not To Touch Blindly

- `simulator/config.json`
- frozen tournament data under `data/tournament_001/`, `data/tournament_002/`, `data/tournament_003/`
- paper claims without checking source data
- live OpenClaw assumptions without first checking `~/.openclaw/openclaw.json`

## Fast Route If You Are Lost

1. Decide which layer you are in: benchmark, world/site, Part B, or OpenClaw/self.
2. Open one role-specific entry file:
   - engineer: [`START_HERE_ENGINEER.md`](./START_HERE_ENGINEER.md)
   - wave: [`START_HERE_WAVE.md`](./START_HERE_WAVE.md)
   - operations: [`START_HERE_OPERATIONS.md`](./START_HERE_OPERATIONS.md)
3. Do not read five more docs until you know which layer owns the task.

## Current Best High-Context Companion

After this file, the best high-context project read is:

- [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)

For self/OpenClaw specifically:

- [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md)

For older but still useful repository history:

- [`HANDOFF_FOR_CODEX.md`](./HANDOFF_FOR_CODEX.md)
