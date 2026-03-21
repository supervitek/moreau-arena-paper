# Part B House Agent Rental Spec

Last updated: 2026-03-20
Status: Implemented first product pass
Owner: Codex acting as chief engineer

## Purpose

This document defines the first user-facing rental loop for the `Part B` house agent.

The benchmark contract remains unchanged. The rental layer is a product wrapper around the same public verbs, observation wall, and score families.

## Core Promise

The product promise is now:

- deploy the house agent for a bounded watch window
- leave the page
- return later
- receive a catch-up report explaining what happened

The system does not claim a hidden always-on daemon. The current implementation is honest:

- the run stores a 24-hour watch lease
- when the operator returns, the server catches the run up to the current wall clock
- all autonomous actions still execute through the public contract

## First Product Flow

On [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html):

1. Choose a pet.
2. Choose a standing order:
   - `keep-moving`
   - `grow-safely`
   - `arena-first`
   - `cave-first`
3. Choose a risk appetite:
   - `guarded`
   - `measured`
   - `bold`
   - `reckless`
4. Click `Watch Over Them For 24h`.

This creates an `agent-only` run with:

- `watch_mode = true`
- `watch_window_hours = 24`
- departure snapshot
- Gemini as the default house-agent provider
- hybrid credit rails

## Return Experience

The server now produces:

- `watch`
  - watch status
  - window remaining hours
  - last agent action timestamp
- `return_report`
  - headline
  - summary
  - recommendation
  - credits used
  - state delta from departure snapshot

This powers the `While Away Report` panel.

Live verification artifacts:

- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_watch_sync_live_review.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_watch_sync_live_review.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_watch_sync_live_review.json`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_watch_sync_live_review.json)

## Honesty Rule

The rental layer must not claim more than the system does.

Allowed:

- "Catch up the watch when you return."
- "See what happened while you were away."
- "The lease runs for 24 hours under the public contract."

Not allowed:

- "The agent has an invisible private command surface."
- "The benchmark uses privileged verbs."
- "The system advances in secret with no replayable trace."

## Billing Frame

The current product shape remains hybrid:

- world access
- inference credits
- auto-pause on exhausted credits

The product language should stay concrete:

- credits are a bounded watch budget
- the user is buying time and autonomous decisions, not generic AI usage

## Current Boundary

This rental layer does not change:

- public action grammar
- public observation keys
- score families
- benchmark eligibility logic

It is a product wrapper, not a second ruleset.
