# CODEX AUDIT REPORT 3

Fresh audit of the current repo state after the reported fixes.

Validation completed:
- `python3 -m pytest -q` → `164 passed`
- `python3 scripts/smoke_web.py` → passed for `/`, leaderboard, `track=C`, S1 pages, pets, Moreddit, key APIs, and `og-image.png`

Previous `CODEX_AUDIT_REPORT_2.md` critical findings were rechecked. The earlier key/API mismatches in `prophecy.html`, `caretaker.html`, `caretaker-letters.js`, `dreams-engine.js`, `caretaker-drift.js`, and `home.html` are fixed.

## Current Findings

- [C1] — `web/static/island/prophecy.html:1859` — `efficiency_decay` now reads the correct key, but compares a normalized efficiency value (`1.0`, `0.8`, `0.6`, etc.) against `80` instead of `0.8`. Once `moreau_caretaker_efficiency` exists, this prophecy resolves almost immediately because any stored value like `1` or `0.6` is `< 80`. — Suggested fix: compare against `0.8`, or convert the stored value to a percentage before comparing.

- [C1] — `web/static/island/prophecy.html:1871` — `letter_arrives` tracks `lettersState.visit_count`, not the number of unlocked/available letters. Because letters unlock every 3 visits in `caretaker-letters.js`, a prophecy created at visit 4 will resolve at visit 5 even though no new letter arrives until visit 6. — Suggested fix: derive the count from actual available letters, e.g. `Math.floor(visit_count / VISITS_PER_LETTER)` or a shared `getAvailableLetters()`-style helper.

- [W3] — `web/static/island/prophecy.html:1888` — `order_misfire` no longer checks standing orders or any misfire event. It resolves solely on `trust < 7`, so the prophecy can come true even when the player has zero standing orders configured. — Suggested fix: tie resolution to a real misfire signal in the standing-orders system, or remove this prophecy until misfires are actually tracked.

- [W10] — `web/static/island/prophecy.html:1764` — The prophecy page still performs unguarded `JSON.parse` on `moreau_oracle_history`, and again on `moreau_keeper_prophecies` at `1804`. A malformed localStorage value will break page initialization before the UI can recover. — Suggested fix: wrap both loads in `try/catch` with safe fallbacks (`[]`).

- [W2] — `web/static/island/home.html:3046` — Island playtime is accumulated independently on many pages (`home.html`, `train.html`, `pit.html`, `achievements.html`, `dreams.html`, `menagerie.html`, `graveyard.html`). Opening multiple tabs increments `moreau_island_time` in parallel, so the `Islander` achievement can be earned faster than real elapsed time. — Suggested fix: centralize time tracking to one heartbeat keyed by active visibility/focus, or gate increments with a shared timestamp lock in localStorage.
