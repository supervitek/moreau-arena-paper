# Task Title

- task_id: replace_me
- assignee: kk
- created_at: 2026-03-14T00:00:00Z
- cwd: /Users/cc/Desktop/Claude/a/moreau-arena-paper

## Objective

Describe the single main goal.

## Context

List relevant files, routes, docs, or constraints.

## Deliverable

Describe what the worker should return or change.

## Guardrails

- say if edits are allowed
- say if tests are required
- say if frozen files must not be touched

## Lane Notes

- Recommended assignees:
  - `kk-audit` for analysis and review
  - `kk-frontend` for UI-only edits
  - `kk-state` for storage/engine/state work
  - `kk-tests` for tests and verification
  - `kk-content` for docs and copy
- Keep one task per worker narrow enough that `run-all` can dispatch several lanes safely.
