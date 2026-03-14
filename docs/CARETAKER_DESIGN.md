# The Caretaker — Design Document

**Date:** 2026-03-14
**Status:** Building
**Components:** 6 (3 original + 3 brainstormed)

---

## Architecture

### New Files
- `web/static/island/caretaker-engine.js` — ALL game logic (~1200 lines)
- `web/static/island/caretaker.html` — Main page (~1800 lines)

### Modified Files
- `web/static/island/home.html` — Needs bars, alerts, decay on load, caretaker button
- `web/app.py` — Add "caretaker" to island allowed pages

### New localStorage Keys
| Key | Type | Description |
|-----|------|-------------|
| moreau_caretaker_log | array | Chronological action log (max 100 entries) |
| moreau_overnight | object | {start, petIndex, rounds, completed, results} |
| moreau_caretaker_premium | boolean | Premium status (stub) |
| moreau_caretaker_trust | number | 0-10, default 5 |
| moreau_caretaker_diary | array | Diary entries with approve/override |
| moreau_mercy_pending | object/null | Active mercy clause if any |
| moreau_caretaker_streak | object | {lastCare, consecutiveDays, longestStreak} |
| moreau_feeding_ledger | object | {pagesUnlocked, nurseryFound} |

### Pet Object Additions
```js
pet.needs = {
  hunger: 100,    // -5/hr, feed +50
  health: 100,    // -2/hr if instability>50, heal +30
  morale: 100,    // -1/hr if >6hr absent, motivate +20
  energy: 100,    // -20/fight, +10/hr natural
  last_checked: timestamp
}
pet.debts = []    // Mercy clause sacrifices: [{name, animal, level, sacrificed_at}]
```

---

## CaretakerEngine API

```js
// === Needs System ===
CaretakerEngine.initNeeds(pet)           // Add needs to pet if missing
CaretakerEngine.decay(pet)               // Calculate time-based decay
CaretakerEngine.getStatus(pet)           // → {urgent:[], warnings:[], tips:[]}

// === Actions ===
CaretakerEngine.feed(petIndex)           // hunger +50
CaretakerEngine.heal(petIndex)           // health +30, costs 1 stat point for 5 fights
CaretakerEngine.rest(petIndex)           // energy +50, 1hr lockout
CaretakerEngine.train(petIndex)          // auto-fight vs RandomAgent, energy -20
CaretakerEngine.motivate(petIndex)       // morale +20
CaretakerEngine.autoManage(petIndex)     // PREMIUM: optimal actions
CaretakerEngine.getAdvice(pet)           // → string[] (3-5 context-aware tips)

// === Overnight ===
CaretakerEngine.startOvernight(petIndex, rounds)  // 3/5/7/10
CaretakerEngine.processOvernight()       // Simulate on return
CaretakerEngine.getOvernightReport()     // → results object or null

// === Diary + Trust ===
CaretakerEngine.getDiary()               // → diary entries array
CaretakerEngine.approveDiaryEntry(id)    // Trust +0.5
CaretakerEngine.overrideDiaryEntry(id)   // Trust -1
CaretakerEngine.getTrust()               // → 0-10
CaretakerEngine.addDiaryEntry(type, text, petIndex)

// === Mercy Clause ===
CaretakerEngine.checkMercyClause(pets)   // Check if any pet critical
CaretakerEngine.getMercyPending()        // → pending mercy or null
CaretakerEngine.executeMercy(sacrificeIndex, saveIndex)  // Sacrifice one to save other
CaretakerEngine.declineMercy()           // Let the Caretaker decide
CaretakerEngine.getMercyTimeRemaining()  // → seconds until auto-resolve

// === Feeding Ledger (Aleph) ===
CaretakerEngine.updateCareStreak()       // Track daily care consistency
CaretakerEngine.getLedgerPages()         // → number of unlocked pages (0-12)
CaretakerEngine.getLedgerContent(page)   // → text for that page
CaretakerEngine.isNurseryUnlocked()     // → boolean
```

---

## Feature Details

### 1. Needs System (Original)
- 4 bars: hunger, health, morale, energy
- Real-time decay based on hours since last_checked
- hunger=0 → -1 HP permanent per 2 hours
- energy restored +10/hr naturally

### 2. Caretaker Actions (Original)
- Feed/Heal/Rest/Train/Motivate — free tier
- AutoManage — premium stub
- 30+ contextual advice strings based on pet state

### 3. Overnight Training (Original)
- Simulated fights (not API calls — local win probability)
- Win probability: based on pet level and stats vs RandomAgent baseline
- Results calculated on next visit
- Premium: 10 rounds + auto-feed

### 4. Diary + Trust System (Brainstormed)
- Caretaker logs decisions with personality
- Player approves (+trust) or overrides (-trust)
- Trust 0: Caretaker refuses to act
- Trust 7+: Creative decisions (risky but effective)
- Trust 10: Unsanctioned mutations possible
- 6 entry types: report, opinion, warning, apology, decision, observation

### 5. Mercy Clause (Brainstormed)
- Triggers when any pet has: hunger=0 + health<20, OR instability>90 + health<30
- 1 tidal cycle (6hr) to decide
- Sacrifice one pet to save another
- Saved pet gets "Survivor's Guilt" mutation: -2 WIL, +3 ATK, permanent
- Sacrificed pet's name in saved pet's debts[]
- 3+ debts = "Abomination" tag (NPC interactions blocked)
- If timer expires: Caretaker auto-sacrifices lowest-level pet

### 6. Feeding Ledger / Aleph (Brainstormed)
- 7 consecutive days of care (2+ visits per day) unlocks page 1
- Each subsequent week: +1 page (12 total)
- Page 6: describes the "15th animal" — Aleph
- Page 9: different if player used Forbidden Lab (redacted version)
- Page 12: reveals The Nursery — Caretaker IS Aleph
- Streak resets silently if any pet drops below 30% HP unhealed for 1 cycle
- Streak tracked in moreau_caretaker_streak
