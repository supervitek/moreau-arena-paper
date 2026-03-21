# Live Site Follow-Up Audit
**Date:** 2026-03-21
**Auditor:** Codex
**Target:** [https://moreauarena.com](https://moreauarena.com)
**Focus:** Ecology/watch flow after the product-seam fixes and live cave-first verification

## What Was Rechecked

- `GET /island/ecology`
- `GET /island/home`
- `GET /island/train`
- `GET /island/pit`
- `GET /island/rivals`
- `GET /island/caretaker`
- `GET /island/nonexistent`
- Live Part B run creation, house-agent preview, cave-first watch/sync, and return report

## Confirmed Improvements

- The main Ecology surface now reads like a product:
  - `Watch Over Them For 24h`
  - `Catch Up Now`
  - `Complete Active Run`
  - credit explainer copy
- Invalid island routes now return a styled human 404 page instead of raw JSON.
- A real production `cave-first` Gemini run is live and viable:
  - preview action: `ENTER_CAVE`
  - observed actions: `ENTER_CAVE -> EXTRACT -> ENTER_CAVE -> EXTRACT`
  - expedition score now rises in production instead of staying flat at `0`
- Provider/model controls are still available, but they are no longer front-and-center in the main product path.

## New Finding Closed

### F1. Completed watch return report could still show a future `next_due_at`
- **Severity:** Low
- **What happened:** A completed 24-hour watch could return a report with `0h left` and `0 ticks left`, but still expose a future `next_due_at`. The recommendation text also stayed too “live” for a finished lease.
- **Why it matters:** This weakens the morning-report fantasy. A user should not see “next due” semantics after a run has already closed.
- **Status:** Fixed locally in code and covered by test. The fix will become visible on production after Render deploys the latest commit.

## Remaining UX Friction

### U1. Ecology is still information-dense
- The page is much better than before, but it still compresses product flow, advanced controls, replay, inspect, and leaderboards into one surface.
- This is now a polish issue, not a product-breaker.

### U2. Advanced tooling is still visibly technical
- `Agent Tuning`, baselines, and some inspect/season language still read like internal instrumentation.
- Acceptable for now, but still the clearest place where Ecology feels more “operator console” than “mass product”.

### U3. Manual mode remains operationally underrepresented
- Production continues to skew toward `agent-only` and `operator-assisted`.
- Not a bug, but it means manual users still have weak social proof in ranked views.

## Verdict

The large product seams from the previous audit are no longer the story.

What changed:
- Expedition is alive.
- 404s are human.
- credits are explained.
- runs can close cleanly.
- provider/model noise is mostly pushed out of the main path.

What remains:
- density
- advanced-tool feel
- more real operator traces

Current state:

**The Ecology now feels like a real product surface with research instrumentation still attached, not a research tool pretending to be a product.**
