# KK Review Request — Self-Lab Boundary Fix

Please review the corrective pass that re-separated the public Island site from
the private self/OpenClaw layer.

Do not answer in chat.
Write the review directly in this file under `## KK Response`.

## Context

An earlier self-improvement pass did more than local OpenClaw work:

- it added public `/api/v1/self/*` endpoints
- it added public Island pages at `/island/mirror` and
  `/island/constitution`
- it added a `MIRROR` entry point on Island home

That created the wrong architecture:

- some self artifacts were local-only
- some self artifacts were tracked in git
- the public site became a half-live, half-empty exposure surface for private
  operational artifacts

## What was fixed

The corrective pass did this:

1. disabled `/api/v1/self/*` by default unless `MOREAU_ENABLE_SELF_LAB=1`
2. changed `/island/mirror` and `/island/constitution` to controlled
   placeholder pages unless the same local-lab opt-in is enabled
3. removed the `MIRROR` button from public Island home navigation
4. wrote the rule into project truth docs

## Files to inspect

- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/home.html`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/PROJECT_TRUTH.md`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/HANDOFF_FOR_CODEX.md`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/OPENCLAW_REPO_BOUNDARY.md`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/SELF_LAB_BOUNDARY_FIX_2026-04-10.md`

## What I want from you

Please answer these concretely:

1. Is this boundary fix architecturally correct?
2. Is the default-off web gating the right move?
3. Is the placeholder approach better than leaving a broken half-live dashboard?
4. Do you see any remaining public/private leak path?
5. What one thing should we be careful not to do next?

## Important

This is not a request to reopen the self-lab on the public site.
This is a request to review whether the separation is now honest and stable.

## KK Response

