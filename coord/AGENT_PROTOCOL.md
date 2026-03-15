# Agent Coordination Protocol

This repo can now delegate Claude Code work directly from the terminal through `scripts/kk_dispatch.py`.

## Layout

- `coord/inbox/`: queued task files
- `coord/claims/`: machine-readable task claim/status records
- `coord/outbox/`: captured worker results
- `coord/archive/`: completed or failed task files
- `coord/status/`: worker session registry

## Default Worker

- `kk`: Claude Code CLI worker, invoked with:
  - `claude -p`
  - `--dangerously-skip-permissions`
  - `--permission-mode bypassPermissions`

The dispatcher automatically reuses the worker's last Claude session unless `--fresh` is passed.

## Task Lifecycle

1. Create a task file in `coord/inbox/`
2. Run `python3 scripts/kk_dispatch.py run`
3. Dispatcher creates a claim record in `coord/claims/`
4. Worker executes the task in this repo
5. Dispatcher stores the raw response in `coord/outbox/`
6. Original task file is moved to `coord/archive/`

## Task Format

Use the template in [`coord/TASK_TEMPLATE.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/coord/TASK_TEMPLATE.md) or create tasks with:

```bash
python3 scripts/kk_dispatch.py submit \
  --title "Fix homepage bug" \
  --assignee kk \
  --body "Investigate homepage nav mismatch and fix it."
```

Each task should stay narrow:

- one clear objective
- exact paths when known
- expected deliverable
- whether code changes are allowed

## Useful Commands

```bash
python3 scripts/kk_dispatch.py status
python3 scripts/kk_dispatch.py submit --title "..." --body "..."
python3 scripts/kk_dispatch.py run
python3 scripts/kk_dispatch.py ask --prompt "Summarize current git status"
```

## Notes

- The dispatcher captures Claude's outer JSON payload and the human-readable result separately.
- `coord/status/kk_sessions.json` stores the latest worker session IDs.
- This is intended as a local orchestration layer, not a replacement for Git history or backups.
