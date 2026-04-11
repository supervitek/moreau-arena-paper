# Start Here — Operations

Use this file when the job is to debug, verify, or restore live project behavior.

First read:

- [`PROJECT_TRUTH.md`](./PROJECT_TRUTH.md)

Then follow this file as the operator path.

## What Counts As Operations Here

- site or API health
- OpenClaw / self runtime health
- gateway health
- daemon cadence, logs, and recovery
- “is the system really working right now?”

## Split The Problem First

There are two very different operational surfaces:

1. Moreau repo app/runtime
2. OpenClaw / self runtime

Do not debug one through the assumptions of the other.

## OpenClaw: Live Truth

For OpenClaw, the live runtime truth source is:

- `~/.openclaw/openclaw.json`

Not:

- `./openclaw.json`

The live loop is the native OpenClaw heartbeat.
Repo scripts are safety and fallback tools around that loop.

## OpenClaw Debug Order

Use this order every time:

1. `python3 -m json.tool ~/.openclaw/openclaw.json >/dev/null`
2. `openclaw health`
3. `openclaw gateway health`
4. inspect `~/.openclaw/cron/jobs.json`
5. inspect `self/logs/daily/`
6. only then inspect repo scripts under `self/scripts/`

Supporting doc:

- [`docs/OPENCLAW_REPO_BOUNDARY.md`](./docs/OPENCLAW_REPO_BOUNDARY.md)

## Moreau App / Repo Debug Order

1. `git status --short`
2. relevant tests
3. local server or script run
4. targeted file inspection

For web:

```bash
uvicorn web.app:app --reload --port 8000
```

For frozen benchmark integrity:

```bash
python -m pytest tests/test_invariants.py -q
```

## Current OpenClaw Reality

As of 2026-04-10:

- the missing constitution hash stop was fixed
- `self/state.json` was repaired and is valid JSON again
- heartbeat resumed producing real LLM cycles
- the working daemon is still the native OpenClaw loop

This matters because older docs or assumptions may imply the repo-local shell-hook model is primary. It is not.

## Good Operator Questions

- what is the live truth source for this surface?
- what is the smallest command that verifies it?
- is the problem a live runtime failure, a stale doc, or a split-brain between them?

## Bad Operator Moves

- debugging live OpenClaw from repo `openclaw.json`
- editing reference docs before confirming runtime reality
- assuming lack of one log entry means the daemon never ran
- changing frozen benchmark assets during operational work

## If You Only Need One Short Checklist

### OpenClaw

```bash
python3 -m json.tool ~/.openclaw/openclaw.json >/dev/null
openclaw health
openclaw gateway health
```

Then inspect:

- `~/.openclaw/cron/jobs.json`
- `self/logs/daily/`

### Repo app

```bash
git status --short
python -m pytest tests/test_invariants.py -q
```

Then run the smallest relevant local entrypoint.
