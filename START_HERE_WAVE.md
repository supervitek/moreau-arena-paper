# Start Here — Wave

Use this file if you are a new AI thread or a fresh agent wave entering the repo.

First read:

- [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)

Then continue here.

## Your Job

Do not reconstruct the whole project from vibes.
Enter the correct layer, use the right truth source, and avoid inventing architecture that is no longer live.

## The Four Layers

1. `Part A` — frozen benchmark
2. world / site / Island — public-facing layer
3. `Part B` — persistent ecology benchmark
4. `OpenClaw / self` — local continuity and operational layer

Most confusion comes from answering a question about one layer with assumptions from another.

## Rules That Save Time

### Rule 1: Do not improvise the truth source

If the task is about live OpenClaw behavior:

- live truth = `~/.openclaw/openclaw.json`
- repo `openclaw.json` = reference only

### Rule 2: Do not clean up frozen artifacts

Frozen benchmark data and config are load-bearing.
Do not “improve” them because they look old.

### Rule 3: Do not merge public and private layers by instinct

The public Moreau repo and the private self/OpenClaw layer are connected, but not identical.

### Rule 4: Do not read ten docs before locating the task

Pick the owning layer first.

## Good Reading Order

### If the task is broad or unclear

1. [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)
2. [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)
3. the task-specific file

### If the task is about OpenClaw / self

1. [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)
2. [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md)
3. [`HANDOFF_FOR_CODEX.md`](./HANDOFF_FOR_CODEX.md)

### If the task is about benchmark / site / Part B

1. [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)
2. [`docs/PROJECT_BIBLE.md`](./docs/PROJECT_BIBLE.md)

## What Not To Hallucinate

- that repo `openclaw.json` drives the live daemon
- that all docs are equally current
- that `Part A`, Island, `Part B`, and OpenClaw are one flat system
- that frozen benchmark files are normal refactor targets

## The Fastest Useful First Move

After reading the truth file, say internally:

1. which layer owns this task
2. what the source of truth is for that layer
3. what file or command would verify reality before editing

If you cannot answer those three, you are still orienting.

## If You Are Handling Self / OpenClaw

Use this order:

1. `~/.openclaw/openclaw.json`
2. `openclaw health`
3. `openclaw gateway health`
4. repo docs and scripts

Do not invert that order.

## Desired Behavior

- stay narrow
- verify before editing
- prefer the live truth over elegant theory
- keep the project’s layers distinct while preserving their relationship
