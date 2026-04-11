# Self-Lab Boundary Fix — 2026-04-10

## Why this fix was necessary

A self/OpenClaw improvement pass crossed the boundary between:

- the private local self-system
- and the public Island site

Specifically, it added:

- public Island navigation to `MIRROR`
- public web pages for `/island/mirror` and `/island/constitution`
- public `/api/v1/self/*` endpoints

That created the wrong shape:

- part of the self-system was still local-only
- part of the self-system was already tracked in git
- the public site therefore became a half-live, half-empty exposure surface for
  private operational artifacts

This did not necessarily crash the site, but it violated the intended project
boundary.

## Principle

The public Island and the private self/OpenClaw layer are related, but they are
not the same audience or surface.

The correct default is:

- public Island stays public/product-facing
- self/OpenClaw stays local/operational
- explicit local lab exposure must be opt-in, not the default

## What was changed

### Web boundary

- `/api/v1/self/*` endpoints are now disabled by default unless
  `MOREAU_ENABLE_SELF_LAB=1`
- the self API is grouped under a dedicated gated router, so future
  `/api/v1/self/*` additions inherit the boundary automatically
- `/island/mirror` and `/island/constitution` now render a controlled local-lab
  placeholder unless that same explicit opt-in is enabled
- the real lab HTML for mirror/constitution was moved out of `web/static/` into
  `web/lab/`, so the templates are no longer reachable through the public
  static file mount
- the `MIRROR` button was removed from public Island home navigation

### Truth docs

The rule was written into:

- `PROJECT_TRUTH.md`
- `HANDOFF_FOR_CODEX.md`
- `docs/OPENCLAW_REPO_BOUNDARY.md`

## Why this is the right fix

This is not a rejection of self-lab work.

It is a separation fix.

The self/OpenClaw layer can still evolve locally and can still have lab pages,
dashboards, and APIs. But those surfaces should not appear on the public site
by accident or by default.

## Operational rule going forward

If a feature reads from `self/`, `~/.openclaw/`, live continuity files, or
private local telemetry, then one of these must be true before it is surfaced
publicly:

1. the feature has an explicit public-safe payload and UX
2. the feature is lab-gated behind an explicit opt-in
3. the feature stays local-only

Do not ship half-live private telemetry into the public Island UX.
