# Part B Hosted House Agent — B4

Last updated: 2026-03-20
Status: Implemented
Owner: Codex acting as chief engineer

## Purpose

`B4` adds the first hosted agent that can operate inside Part B without breaking future benchmark claims.

The rule is unchanged:

- the house agent acts only through the published observation/action contract
- no hidden privileges
- no secret action surface

## What Exists

Runtime:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/part_b_state.py)

API:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py)

UI:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/ecology.html)

Verification:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/tests/test_part_b_state.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/tests/test_part_b_state.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_island.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/smoke_island.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/playtests/island_regression.js`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/playtests/island_regression.js)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/verify_part_b_gemini_live.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/verify_part_b_gemini_live.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_gemini_live_review.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_gemini_live_review.md)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_gemini_live_review.json`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/reports/part_b_gemini_live_review.json)

## Hosted-Agent Contract

Current B4 is intentionally narrow:

- only on `agent-only` runs
- only on the two-zone ecology slice
- only through the published verbs
- only with visible budget rails

The hosted agent can:
- preview the next action
- execute one action at a tick boundary
- leave a replayable action trace
- auto-pause when credits are exhausted

## Provider Path

Configured providers:
- `gemini`
- `anthropic`
- `fallback`

Runtime behavior:
- if `GOOGLE_API_KEY` or `GEMINI_API_KEY` is available and the run requests `gemini`, the house agent uses the Gemini path
- if `ANTHROPIC_API_KEY` and the `anthropic` package are available, the house agent uses the Anthropic path
- otherwise it falls back to a bounded heuristic planner

Current Gemini default:
- `gemini-2.5-flash-lite`

Compatibility note:
- the runtime normalizes older `gemini-2.0-*` aliases to current `gemini-2.5-*` replacements so stale env or UI values do not silently kill the product path

This keeps the product operational locally without faking a different contract.

## Hybrid Billing Rails

Current B4 implements the agreed hybrid rails conceptually:

- world access remains active per run
- hosted agent actions consume inference credits
- when credits reach `0`, the run auto-pauses

Visible fields:
- `billing_mode`
- `inference_budget_daily`
- `inference_budget_remaining`
- `world_access_active`
- `autopause_reason`

Current default mode:
- `hybrid`

## Operator Controls

The `ecology` surface now exposes:

- budget selection
- house-agent preview
- house-agent apply/update
- visible on/off state
- visible remaining credits

## Integrity Guardrails

The house agent currently preserves benchmark integrity because:

- it uses the same public verbs as everyone else
- it reads only the same observation contract
- every autonomous action is replayable
- budget exhaustion is visible
- the agent path is tied to `agent-only` run class

## Current Limits

B4 still does not include:

- external BYO-agent API
- marketplace logic
- hidden ladder privileges
- production billing processor
- composite leaderboard treatment

These remain out of scope for the first Part B execution cycle.

## API

Core B4 endpoints:

- `GET /api/v1/island/part-b/runs/{run_id}/house-agent/preview`
- `POST /api/v1/island/part-b/runs/{run_id}/house-agent`
- `POST /api/v1/island/part-b/runs/{run_id}/tick`

Operational verifier:
- `python3 scripts/verify_part_b_gemini_live.py --base-url https://moreauarena.com --ticks 3 --output reports/part_b_gemini_live_review.md --json-output reports/part_b_gemini_live_review.json`

Latest live result:
- a production `agent-only` run completed three ticks through the real Gemini path
- preview: `mode=model`, `provider=gemini`, `model=gemini-2.5-flash-lite`
- the sample run opened with `ENTER_ARENA`, inserted one `CARE`, then returned to `ENTER_ARENA`

## Exit Rule

`B4` is considered complete for the current execution cycle because:

- a constrained hosted house agent exists
- it acts through the public contract
- hybrid budget rails exist
- auto-pause exists
- the ecology UI can inspect and run it
- checked-in smoke/playtest tooling exercises it
