# Live Site Audit — Moreau Arena
**Date:** 2026-03-20
**Auditor:** Claude Opus 4.6 (autonomous browser audit)
**Target:** https://moreauarena.com
**Focus:** Part B ecology, house-agent/watch flow, overall product readiness

---

## Findings

### F1. No custom 404 page for invalid island routes
- **Severity:** Low
- **Page:** `/island/<anything-invalid>`
- **What happened:** Visiting `/island/nonexistent` returns a raw HTTP 404 JSON error (`{"detail":"Unknown island page: nonexistent"}`). No styled error page, no redirect back to island home.
- **Why it matters:** A real user who typos a URL gets a raw API response. Breaks immersion instantly.
- **Fixed now:** No (requires a catch-all handler or custom error page — larger scope)

### F2. "Ecology Slice" and "Research Run" internal dev labels on ecology page
- **Severity:** Medium
- **Page:** `/island/ecology`
- **What happened:** Page title said "Ecology Slice", subtitle said "This is the first real ecological slice for Part B", button said "Start Research Run" / "Start Research Agent Run", collapsible section said "Advanced Research Tools", operator hint said "safer benchmark trace".
- **Why it matters:** These are internal development labels. A product user sees "research run" and thinks "this is a dev tool, not for me." The word "slice" is pure engineering jargon.
- **Fixed now:** Yes — 7 text changes applied:
  - Title: "Ecology Slice" → "Ecology"
  - OG/Twitter meta: cleaned
  - Subtitle: removed "This is the first real ecological slice for Part B"
  - Button: "Start Research Run" → "Start New Run"
  - Button (agent mode): "Start Research Agent Run" → "Deploy Agent Run"
  - Section: "Advanced Research Tools" → "Advanced Tools"
  - Hint: "safer benchmark trace" → "steady run"

### F3. Expedition score flatlined at 0 across all 24 runs
- **Severity:** Medium
- **Page:** `/api/v1/island/part-b/calibration`, `/island/ecology` leaderboards
- **What happened:** Calibration endpoint explicitly flags `expedition_flatlined` as a warning. Mean expedition score is 0.0 across all runs. The Cave of Catharsis zone exists in the UI but no run has used it.
- **Why it matters:** One-third of the scoring families is dead weight. Users see three big score cards — Welfare, Combat, Expedition — but one will always be zero. This undermines the three-family design and makes the Cave feel decorative.
- **Fixed now:** No (design decision — needs either Cave utilization by house agent policies, or UX acknowledgment that expedition is not yet live)

### F4. Zero manual runs in production
- **Severity:** Low
- **Page:** `/api/v1/island/part-b/leaderboards`
- **What happened:** 21 agent-only runs, 3 operator-assisted runs, 0 manual runs.
- **Why it matters:** The "manual" mode exists in the UI but has never been used on prod. If a user selects manual mode and starts a run, they'll be alone in the leaderboard — no reference points.
- **Fixed now:** No (operational gap, not a bug)

### F5. Raw JSON API responses for Part B errors
- **Severity:** Low
- **Page:** All Part B API endpoints
- **What happened:** When a Part B run is not found, the API returns `{"detail":"Part B run not found"}`. This is fine for an API, but the frontend's `fetchJson` wrapper catches it and shows a raw `alert()` with the error text.
- **Why it matters:** `alert("Part B run not found")` is not a user-friendly error. Minor since it only happens on stale localStorage referencing a deleted run.
- **Fixed now:** No (edge case, low priority)

---

## UX Friction

### U1. Budget/credits system is opaque
- **Page:** `/island/ecology` — run creation controls
- **Observation:** Users choose a daily credit budget (4/8/12) but there's no explanation of what a "credit" buys, how fast they deplete, or what happens when they run out. The deploy summary says "bounded by your credit budget and the public contract" — but what does that mean in practice?
- **Recommendation:** Add a one-line explainer: "Each credit funds one house-agent decision. Budget of 4 = 4 autonomous decisions per day."

### U2. Operator hint text still references "benchmark" in multiple places
- **Page:** `/island/ecology`
- **Observation:** Even after fixes, remaining text mentions "benchmark eligible", "benchmark position", "every benchmarked Part B run", "public grammar", "house-agent rule". This is accurate for the research layer but confusing for a product user who just wants to watch their pet.
- **Recommendation:** Consider a "research mode" toggle that shows/hides benchmark-specific labels. Or soften language: "ranked runs" instead of "benchmark-eligible runs".

### U3. Run class selection lacks guidance
- **Page:** `/island/ecology` — run creation
- **Observation:** Three run classes (manual, operator-assisted, agent-only) with no explanation of what each means. An experienced user can guess, but a new visitor has no context for "operator-assisted" — assisted by whom?
- **Recommendation:** Add tooltip or subtitle text under each option: "Manual: you make every decision", "Operator-assisted: you decide, with hints", "Agent-only: the house agent acts for you".

### U4. Ecology page is dense for first-time visitors
- **Page:** `/island/ecology`
- **Observation:** The page immediately presents: run metadata, family scores, run controls (pet select, class, priority, risk, budget, provider, model), zone tabs, 8 action buttons, operator hints, queue system, house agent panel, baselines, replay, return report, run inspect, leaderboards. All visible at once (with some in collapsibles).
- **Recommendation:** Consider progressive disclosure — start with just "Watch Over Them For 24h" and "Start New Run", reveal the rest after a run is active.

### U5. "Cave of Catharsis" tab feels dead
- **Page:** `/island/ecology` — Cave tab
- **Observation:** The Cave tab exists and actions work, but since no runs have ever used it (expedition = 0 everywhere), clicking the Cave tab shows identical-feeling actions with no evidence that the cave path is viable.
- **Recommendation:** Either populate calibration runs that actually use the cave, or add a "coming soon" indicator, or make the house agent occasionally choose cave actions.

### U6. No clear "end run" or "archive run" button
- **Page:** `/island/ecology`
- **Observation:** Runs are created but there's no visible way to end, archive, or abandon a run. The only way to start fresh is to start a new run (which seems to work alongside the old one). Users accumulate runs without closure.
- **Recommendation:** Add a "Complete Run" or "Archive Run" button that finalizes the current run and clears the active run reference.

### U7. Provider/model fields are too technical for product flow
- **Page:** `/island/ecology` — house agent panel
- **Observation:** The house agent panel shows a provider dropdown (Gemini, Anthropic, Fallback) and a text input for model name (e.g., "gemini-2.5-flash-lite"). This is research infrastructure, not a product choice. A user doesn't know or care about model names.
- **Recommendation:** For the product path ("Watch Over Them For 24h"), hide or pre-select the provider/model. Only expose these controls under "Advanced Tools".

### U8. Watch status is text-only, no visual timeline
- **Page:** `/island/ecology` — watch status hint
- **Observation:** The watch status shows a single text line: "Watch Over Them — status running · 22h left · cadence 6h · est. 3 ticks left · 3/4 credits". This is information-dense but hard to scan quickly.
- **Recommendation:** A simple visual progress bar (24h timeline with tick markers) would make the watch status instantly scannable.

---

## What Feels Strong

### Island Home (`/island/home`)
The dashboard is rich and well-organized. 14+ action buttons in a clear grid, active pet card with stats and needs, pet roster management. Feels like a real game hub. Dark theme with red accents is consistent and atmospheric.

### Training Grounds (`/island/train`)
Three-tier opponent selection (Easy/Medium/Hard) is clear. Fight animation with HP bars, tick counter, and narrative replay works well. XP rewards and level-up notifications feel satisfying. Sound design via Web Audio is a nice touch.

### The Pit (`/island/pit`)
Pet-vs-pet sparring with selection UI, fight animation, and sparring history. Clean and functional. Achievement unlock ("Civil War") adds engagement.

### Rivals (`/island/rivals`)
NPC rival system with tier ratings, progress tracking, and reactive dialogue. Good narrative layer on top of combat mechanics.

### Caretaker (`/island/caretaker`)
Deep care system with feeding, healing, resting, trust meter, diary entries, and the Mercy Clause. The Feeding Ledger (hidden pages unlocked by care streaks) is excellent narrative design. This page alone could be a standalone game.

### Moreddit (`/moreddit`)
Reddit-style social feed with fighter personalities posting between matches. Creative community feature that adds worldbuilding without requiring real users.

### Part B API Layer
All 20+ Part B API endpoints respond correctly. Season contract, storage status, calibration, leaderboards, run CRUD, queue management, house agent, baselines — all working. Supabase backend is configured and operational. The API design is clean and RESTful.

### Watch Flow
"Watch Over Them For 24h" → confirmation dialog → run creation → catch-up sync → return report is a complete flow. The 6-hour tick cadence, credit budget, and auto-pause on credit exhaustion are well-designed guardrails.

### Leaderboards
Class-filtered leaderboards (all/manual/operator-assisted/agent-only) with benchmark eligibility badges, contract compliance indicators, and season metadata. Professional-grade.

### Onboarding
Five-screen narrative sequence with auto-advance, skip button, and localStorage completion tracking. Sets the tone without being mandatory.

---

## Final Verdict

### Is the current live product ready for real human curiosity?

**Part A (Island, Pets, Combat): Yes.** The core pet lifecycle — create, train, fight, mutate, care for, lose, breed — is deep and cohesive. The narrative layers (dreams, confessions, caretaker diary, moreddit) add genuine emotional texture. A curious visitor can spend hours here without hitting a wall.

**Part B (Ecology, House Agent, Watch): Almost.** The infrastructure is solid — APIs work, Supabase is live, leaderboards populate, the watch flow completes end-to-end. But the experience still reads as "research instrument being shown to an audience" rather than "product designed for that audience." Specific gaps:

1. **Language drift:** Several labels still say "research", "benchmark", "slice", "calibration". Fixed the worst offenders in this audit, but more remain in leaderboard text and inspect panels.

2. **Expedition is hollow:** 0/24 runs have touched the Cave. One of three score families produces nothing. This is the biggest structural gap — it's not a bug, but it makes the three-pillar design feel incomplete.

3. **Information overload:** The ecology page shows everything at once. A new user needs progressive disclosure: "hire the agent → come back later → see what happened" should be the default path. The queue system, baselines, and provider controls can live behind a toggle.

4. **No run lifecycle closure:** Runs start but never end from the user's perspective. This creates ambient confusion about whether you're "in a run" or not.

### Where does it still feel like an internal prototype?

- The ecology page controls (provider dropdown, model text input, baseline policy selector, calibration warnings)
- "benchmark-eligible" and "public contract" language in leaderboard cells
- The `seasonNotice` line that shows `house_agent_benchmark_rule` verbatim
- Raw JSON error responses on 404s
- The "Advanced Tools" section (even renamed from "Advanced Research Tools") contains research-grade controls (passive queue, baseline policies) that a product user would never touch

### Bottom Line

The **Island** is a product. The **Ecology** is a product trying to emerge from a research tool. The gap is bridgeable — it's mostly copy, progressive disclosure, and a few operational choices (populate cave runs, add manual calibration runs, close the run lifecycle). The hard infrastructure work is done.

---

*Audit generated by Claude Opus 4.6. All findings based on live HTTP fetches of https://moreauarena.com on 2026-03-20.*
