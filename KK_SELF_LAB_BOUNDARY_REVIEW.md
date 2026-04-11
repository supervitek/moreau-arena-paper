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
4. moved the real mirror/constitution templates out of `web/static/` into
   `web/lab/`
5. moved self endpoints under a dedicated gated router
6. wrote the rule into project truth docs

## Files to inspect

- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/app.py`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/static/island/home.html`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/lab/mirror.html`
- `/Users/cc/Desktop/Claude/a/moreau-arena-paper/web/lab/constitution.html`
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

**Reviewer:** Claude Opus 4.6 (KK), 2026-04-10
**Scope:** boundary review only, not feature review

---

### 1. Is this boundary fix architecturally correct?

**Yes.** The fix addresses exactly the right problem in exactly the right way.

The gating mechanism is clean:
- Single env var `MOREAU_ENABLE_SELF_LAB` read once at startup into `SELF_LAB_PUBLIC_ENABLED`
- One guard function `_require_self_lab_enabled()` returning 404 — not 403 (correct: don't even acknowledge the route exists)
- Page-level gating in `island_page()` at line 2357: `if page in {"mirror", "constitution"} and not SELF_LAB_PUBLIC_ENABLED` → returns a styled placeholder, not a broken page
- All 7 API endpoints (`/api/v1/self/{state,hypotheses,thinking,provenance,predictions,daily-log,constitution}`) each call `_require_self_lab_enabled()` as first line

The env var is not set on Render (checked: not in `render.yaml`), so the default on prod is **off**. The lab surfaces only exist when explicitly enabled locally. This is the right default direction.

### 2. Is the default-off web gating the right move?

**Yes, and for the right reason.** The alternative (removing the code entirely) would mean losing the lab pages for local use. The alternative (leaving them on) would expose empty/broken dashboards on prod. Default-off with opt-in is the only shape that serves both the public site and the local lab.

One design note I approve of: the placeholder returns HTTP 200 with a styled page, not 404. This is correct — a 404 on `/island/mirror` would leak that the route "doesn't exist" (which isn't true — it exists but is gated). A 200 with explanation is more honest than a 404 that pretends ignorance.

### 3. Is the placeholder approach better than a broken half-live dashboard?

**Significantly better.** The placeholder:
- Explains the boundary ("The Island site is public. The OpenClaw/self layer is private, operational, and local-first.")
- Tells you how to enable it locally (`MOREAU_ENABLE_SELF_LAB=1`)
- Links back to island home and Project Bible
- Uses consistent styling (dark theme, accent colors)

A broken half-live dashboard would create the worst possible impression: "this project is incomplete." The placeholder creates the right impression: "this exists, it's intentionally private, here's why."

### 4. Do you see any remaining public/private leak path?

**I checked the following and found no remaining leaks:**

- **Static file mount:** `app.mount("/static", ...)` serves only `web/static/`, not `self/`. The HTML files `mirror.html` and `constitution.html` are in `web/static/island/` but they only render when the gate is open. When the gate is closed, the placeholder HTML is served directly from the Python function, so the static files are never reached. **No leak.**

- **`mirror.html` and `constitution.html` are still in `web/static/island/`:** In theory, someone could request `/static/island/mirror.html` directly and get the raw HTML. However, the HTML page itself tries to `fetch('/api/v1/self/state')` etc. — all of which return 404 when the gate is off. So the page loads but shows nothing / errors. **Cosmetic leak only** — the HTML template is visible but no data flows. Low severity, but worth noting.

  **Recommendation if you want to close this:** Move `mirror.html` and `constitution.html` out of `web/static/island/` into a non-served directory (e.g., `web/lab/`), and serve them from `_serve_html()` reading from the non-static path. This way the raw HTML files are not accessible via the `/static/` mount. This is optional — the current state leaks no data, only an empty template.

- **`MIRROR` button on island home:** Confirmed removed — `grep -i mirror web/static/island/home.html` returns no matches. **Clean.**

- **`self/provenance.json` in git:** This file is committed to the repo and visible on GitHub. It contains the thinking graph structure (node names, question IDs, edge types). It does not contain thinking file content, but it does reveal the intellectual structure. **This is a minor information leak via the public GitHub repo, not via the website.** If the self-system's intellectual structure should be private, consider adding `self/provenance.json` to `.gitignore`. If the structure is fine to be public (it's metadata, not content), leave it.

- **`MASTER_PLAN.md` in git:** This file is committed and public on GitHub. It describes the full self-improvement architecture in detail. **Same consideration as above** — it's not a website leak but a repo visibility question.

### 5. What one thing should we be careful not to do next?

**Do not add "just one more" self endpoint without the gate.**

The current gate works because every self endpoint calls `_require_self_lab_enabled()`. If someone adds a new endpoint — say `/api/v1/self/drift` for embedding drift results — and forgets the gate, it creates a silent leak. The pattern is manual (each handler calls the guard), not structural (no middleware-level block on the `/api/v1/self/` prefix).

**Concrete mitigation:** Consider moving all self endpoints to a separate `APIRouter` with a dependency that enforces the gate:

```python
self_router = APIRouter(prefix="/api/v1/self", dependencies=[Depends(_require_self_lab_enabled_dep)])
```

This makes the gate structural — any new endpoint on the router is automatically gated. Currently it's per-function, which is correct but fragile against future additions.

---

### Summary

| Question | Answer |
|----------|--------|
| Boundary fix correct? | Yes |
| Default-off right? | Yes |
| Placeholder better? | Yes |
| Remaining leak paths? | One cosmetic (raw HTML via `/static/`), two repo-level (`provenance.json`, `MASTER_PLAN.md` on GitHub). No data leaks via web. |
| One thing to watch? | Gate is per-function, not per-router. Future endpoints need manual discipline or router-level refactor. |

The separation is now honest and stable.
