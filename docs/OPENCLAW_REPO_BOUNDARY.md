# OpenClaw Repo Boundary

This repo now separates the OpenClaw/self system into two layers:

## Main repo: live operational scaffolding

The main repo keeps the code and stable scaffolding that the live OpenClaw/self
runtime depends on directly:

- `openclaw.json`
- `ai-gateway/`
- `HEARTBEAT.md`
- stable `self/` prompts and scripts
- canonical operational files that still live at the same paths

## Sibling vault: heavy research memory

The sibling vault at:

- `/Users/cc/Desktop/Claude/a/moreau-self-vault`

holds the heavier research layer and archive surfaces:

- `self/thinking/`
- `self/logs/`
- `self/graveyard/`
- `self/docs/`
- `self/experiments/`
- `self/.learnings/`
- `self/session_markers/`
- `self/predictions.csv`
- additional local research sidecars moved under `repo_sidecar/`

These are surfaced back into `self/` via symlinks, so the live system keeps the
same paths while the main repo stays lighter.

## Git hygiene rule

We version stable scaffolding and code in the main repo. We do **not** version
volatile OpenClaw runtime state here (for example `self/state.json`,
`self/questions.md`, `self/dialogues.md`, `self/mirror.md`, local backup logs,
or `.openclaw/workspace-state.json`).

That keeps the working tree clean without tearing apart the live self/OpenClaw
ecosystem.
