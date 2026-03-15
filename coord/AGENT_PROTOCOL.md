# Agent Coordination Protocol

This repo can now delegate Claude Code work directly from the terminal through `scripts/kk_dispatch.py`.

It supports multiple named worker lanes so Codex can fan out narrow tasks to separate Claude Code sessions without manual copy-paste.

## Layout

- `coord/inbox/`: queued task files
- `coord/claims/`: machine-readable task claim/status records
- `coord/outbox/`: captured worker results
- `coord/archive/`: completed or failed task files
- `coord/status/`: worker session registry

## Worker Lanes

- `kk`: default general worker
- `kk-audit`: read-only audits, diff review, repo scans
- `kk-frontend`: HTML/CSS/UI-only tasks
- `kk-state`: state contract, storage, engine logic
- `kk-tests`: tests, smoke checks, verification scripts
- `kk-content`: copy, docs, handoff, reports

All workers use Claude Code CLI, invoked with:
  - `claude -p`
  - `--dangerously-skip-permissions`
  - `--permission-mode bypassPermissions`

The dispatcher automatically reuses each worker's last Claude session unless `--fresh` is passed.

Worker names are just lanes. Add more when needed, but keep names stable so session history stays useful.

## Task Lifecycle

1. Create a task file in `coord/inbox/`
2. Run either:
   - `python3 scripts/kk_dispatch.py run`
   - `python3 scripts/kk_dispatch.py run-all --parallel 4`
3. Dispatcher creates a claim record in `coord/claims/`
4. Worker executes the task in this repo
5. Dispatcher stores the raw response in `coord/outbox/`
6. Original task file is moved to `coord/archive/`

## Task Format

Use the template in [`coord/TASK_TEMPLATE.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/coord/TASK_TEMPLATE.md) or create tasks with:

```bash
python3 scripts/kk_dispatch.py submit \
  --title "Fix homepage bug" \
  --assignee kk-frontend \
  --body "Investigate homepage nav mismatch and fix it."
```

Each task should stay narrow:

- one clear objective
- exact paths when known
- expected deliverable
- whether code changes are allowed

Prefer one worker per concern. `run-all` only dispatches one queued task per worker lane in a single pass, which avoids concurrent reuse of the same Claude session.

## Useful Commands

```bash
python3 scripts/kk_dispatch.py status
python3 scripts/kk_dispatch.py status --json
python3 scripts/kk_dispatch.py submit --title "..." --body "..."
python3 scripts/kk_dispatch.py run
python3 scripts/kk_dispatch.py run-all --parallel 4
python3 scripts/kk_dispatch.py ask --prompt "Summarize current git status"
python3 scripts/kk_dispatch.py ask-many --workers kk-audit,kk-tests --prompt "Summarize the current queue"
```

## Safe Parallelism

- Safe:
  - audits, scans, reports, tests, docs
  - code edits on disjoint files or clearly separated subsystems
- Unsafe:
  - two workers editing the same file family at once
  - one worker refactoring shared helpers while another edits dependents

Codex should use multiple workers mainly for audit, research, verification, and clearly separated edit lanes.

## Notes

- The dispatcher captures Claude's outer JSON payload and the human-readable result separately.
- `coord/status/kk_sessions.json` stores the latest worker session IDs by lane.
- `coord/claims/*.json` and `coord/outbox/*` include the worker lane in the filename.
- This is intended as a local orchestration layer, not a replacement for Git history or backups.
