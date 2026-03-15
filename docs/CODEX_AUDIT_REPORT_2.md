# CODEX AUDIT REPORT 2

Audited `web/static/island/` (`*.html` + `*.js`), 45 files total.

No issues found for `C2` (script tag dependencies), `W4` (M-engine encrypted notes vs sleep dialect lexicon), `W6` (genesis preserved keys vs weight key), or `W8` (achievements object/order consistency).

## Findings

- [C1] — `web/static/island/prophecy.html:1864` — `new_dialect` prophecies read `moreau_sleep_dialects`, but the canonical dialect store is `moreau_sleep_dialect` in `sleep-dialect.js`. These prophecies never observe real dialect progress and will not resolve correctly. — Suggested fix: read the singular key and count `words_discovered` from the stored dialect state.

- [C1] — `web/static/island/prophecy.html:1870` — `letter_arrives` prophecies read `moreau_caretaker_letters` as an array, but `caretaker-letters.js` stores state under `moreau_caretaker_letters_state` with `{ visit_count, letters_read, last_visit }`. `letters.length` is therefore disconnected from the real system and can never reflect incoming letters. — Suggested fix: read `moreau_caretaker_letters_state` and derive progress from the stored state shape.

- [C1] — `web/static/island/prophecy.html:1859` — `efficiency_decay` prophecies read `moreau_caretaker_state.efficiency`, but the actual efficiency system uses `moreau_caretaker_efficiency` in `caretaker-price.js`. This prophecy path is wired to a nonexistent storage object and will stay false unless unrelated code creates that key. — Suggested fix: read the real efficiency key or call a shared CaretakerPrice/CaretakerEngine accessor.

- [C3] — `web/static/island/caretaker.html:1812` — The caretaker page calls `CaretakerEngine.decayNeeds(pet)`, but `caretaker-engine.js` exposes `initNeeds`, `decay`, and `decayAll`, not `decayNeeds`. The guard prevents a crash, but needs decay never runs through the intended page-specific path. — Suggested fix: replace this call with the real public API, most likely `CaretakerEngine.decay(pet)`.

- [C3] — `web/static/island/caretaker-letters.js:504` — Caretaker dismissal calls `CaretakerEngine.clearStandingOrders()`, but no such public method exists in `caretaker-engine.js`. The “clear standing orders” side effect is silently skipped after dismissal. — Suggested fix: either add a real public method for clearing orders or call the `StandingOrders` API directly.

- [C4] — `web/static/island/dreams-engine.js:328` — Dream generation treats pets as dead only when `pet.deceased` is set, ignoring the parallel `is_alive === false` convention used across the island pages. Pets imported or normalized through the DB-style field can be missed by haunting and convergence logic. — Suggested fix: standardize death checks on `pet.deceased || pet.is_alive === false` everywhere dreams look for deceased pets.

- [C4] — `web/static/island/caretaker-drift.js:109` — Caretaker Drift’s `isAlive()` returns true for any pet without `deceased`, ignoring `is_alive === false`. That makes drift/favorite selection inconsistent with the rest of the island’s pet model. — Suggested fix: use the shared dead/alive convention `!pet.deceased && pet.is_alive !== false`.

- [W1] — `web/static/island/prophecy.html:1876` — `favoritism` prophecies expect `moreau_caretaker_drift.per_pet`, but `caretaker-drift.js` persists `{ score, favorite, neglected_ticks, dumb_remaining, last_diary_tier }` and never writes `per_pet`. This prophecy condition cannot become true from the current drift state format. — Suggested fix: either persist a real per-pet drift map or rewrite the prophecy to use existing drift fields.

- [W3] — `web/static/island/prophecy.html:1890` — `order_misfire` prophecies expect `moreau_standing_orders.last_misfire`, but `standing-orders.js` stores the key as an array of order objects. The required field is never written, so this prophecy branch is effectively dead code. — Suggested fix: add a structured misfire ledger to standing orders or remove this prophecy until the data exists.

- [W9] — `web/static/island/dreams-engine.js:506` — Dream toast markup injects `dream.pet_name` directly into `innerHTML`. Pet names are user-controlled, so a crafted name can become stored XSS when a dream toast renders. — Suggested fix: escape `dream.pet_name` before interpolation or build the toast with `textContent` nodes instead of string HTML.

- [W10] — `web/static/island/dreams-engine.js:355` — `generateDream()` parses `moreau_dreams` without a `try/catch`. Any malformed value in localStorage will throw and break the entire dream-generation path. — Suggested fix: wrap this parse in the same guarded loader pattern already used on `dreams.html`.

- [W10] — `web/static/island/home.html:2305` — The home quick-actions renderer parses `moreau_dreams` without a guard. Corrupted localStorage can break dashboard rendering instead of degrading gracefully. — Suggested fix: wrap the parse in `try/catch` with a safe fallback `{ dreams: [], unread_count: 0 }`.
