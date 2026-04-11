# Start Here — Engineer

Use this file if you are a human engineer or coding agent trying to make a change safely.

Before anything else, read:

- [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)

Then use this file to choose the right part of the repo.

## The First Question

Which layer owns your task?

1. `Part A` benchmark
2. public world / site / Island
3. `Part B` persistent ecology
4. `OpenClaw / self` local operational layer

Do not start editing until you know which layer you are touching.

## Safe Mental Model

- `Part A` is the measurement anchor
- world / site / Island is the public-facing product layer
- `Part B` is the persistent ecological benchmark
- `OpenClaw / self` is the local continuity and operator-facing agent layer

The repo contains all four, but they do not obey the same change rules.

## What Is Frozen

Treat these as frozen unless the task explicitly says otherwise:

- `simulator/config.json`
- `data/tournament_001/`
- `data/tournament_002/`
- `data/tournament_003/`

If a task seems to require editing those directly, pause and verify the intent.

## Where To Read Next By Task Type

### Benchmark / paper integrity

Read:

1. [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)
2. [`README.md`](./README.md)
3. older handoff package only if needed:
   - [`handoff/README_START_HERE.md`](./handoff/README_START_HERE.md)

Useful files:

- `simulator/`
- `agents/`
- `analysis/`
- `prompts/`
- `tests/test_invariants.py`

### Public site / world / Island work

Read:

1. [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)
2. [`README.md`](./README.md)

Useful files:

- `web/`
- `docs/ISLAND_STATUS.md`
- `docs/ISLAND_ROADMAP.md`
- `roundtable/`

### Part B work

Read:

1. [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)
2. the finalized Part B docs referenced there

Useful files:

- `part_b_state.py`
- `docs/PART_B_*`

### OpenClaw / self work

Read:

1. [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md)
2. [`HANDOFF_FOR_CODEX.md`](./HANDOFF_FOR_CODEX.md)

Important truth:

- live OpenClaw config: `~/.openclaw/openclaw.json`
- repo `openclaw.json`: reference only

Useful repo paths:

- `self/`
- `self/scripts/`
- `ai-gateway/`

## Commands Engineers Commonly Need

### Repo health

```bash
git status --short
python -m pytest tests/test_invariants.py -q
```

### Web dev

```bash
uvicorn web.app:app --reload --port 8000
```

### OpenClaw runtime checks

```bash
openclaw health
openclaw gateway health
python3 -m json.tool ~/.openclaw/openclaw.json >/dev/null
```

## Common Failure Modes

### Editing frozen benchmark assets by accident

This silently damages measurement integrity.

### Treating repo `openclaw.json` as live runtime config

It is not.
Use `~/.openclaw/openclaw.json` for live debugging.

### Mixing public docs and private self-state

`self/` is operational and local-first.
Do not assume a public-repo cleanup should absorb that layer.

### Trying to simplify the project by collapsing layers

The project is intentionally multi-layered.
The right simplification is better orientation, not flattening the design.

## If You Only Have Five Minutes

1. Read [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)
2. Identify the layer
3. Read one deeper doc:
   - project-wide: [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)
   - OpenClaw/self: [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md)
4. Touch the smallest surface that solves the task
