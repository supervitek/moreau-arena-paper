# The Island — Side B Master Roadmap

**Status:** Active development
**Side A (Benchmark):** Frozen until arXiv approves
**Shared files:** `season1/engine_s1.py`, `season1/animals_s1.py` (read-only from Island side)
**Do NOT touch:** Side A pages, `data/tournament_*/`, `config.json`

---

## 1. ARCHITECTURE

### Entry Point
- Red button "FIGHT!" in top-right nav on ALL site pages
- Links to `/island` — The Island landing page
- Black + red design, separate from benchmark aesthetic
- Scientist won't click. Gamer won't miss.

### Auth (Supabase)
- Provider: Supabase (supabase.com) — free tier
- Auth methods: Google OAuth + email/password
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` stored in Render env vars
- Supabase JS client loaded via CDN in browser (no build step)
- Auth token: Supabase session (handles refresh automatically)

### Database (Supabase PostgreSQL)

**users**
| Column | Type | Notes |
|--------|------|-------|
| id | uuid (PK) | Supabase auth.users id |
| email | text | |
| display_name | text | |
| avatar_url | text | |
| created_at | timestamptz | |
| is_premium | boolean | default false |

**pets**
| Column | Type | Notes |
|--------|------|-------|
| id | uuid (PK) | |
| user_id | uuid (FK → users) | |
| name | text | max 20 chars |
| animal | text | one of 14 animals |
| base_stats | jsonb | `{hp, atk, spd, wil}` total=20 |
| level | int | 1-10 |
| xp | int | |
| mutations | jsonb | `["blood_rage", "frenzy"]` standard tree |
| lab_mutations | jsonb | `{L3: {...}, L6: {...}, L9: {...}}` |
| side_effects | jsonb | `[{name, desc, category, stats}]` |
| instability | int | 0-100 |
| scars | int | 0-5 |
| mercy_used | boolean | |
| mood | text | |
| is_alive | boolean | default true |
| fights_won | int | default 0 |
| fights_lost | int | default 0 |
| created_at | timestamptz | |
| died_at | timestamptz | null until death |

**fights**
| Column | Type | Notes |
|--------|------|-------|
| id | uuid (PK) | |
| pet1_id | uuid (FK → pets) | |
| pet2_id | uuid (FK → pets) | nullable for AI fights |
| winner_id | uuid (FK → pets) | |
| ticks | int | |
| fight_type | text | 'training', 'sparring', 'ranked', 'auto' |
| xp_gained | int | |
| timestamp | timestamptz | |

**mutations_codex**
| Column | Type | Notes |
|--------|------|-------|
| id | uuid (PK) | |
| user_id | uuid (FK → users) | |
| mutation_id | text | e.g. 't1_tough_skin' |
| discovered_at | timestamptz | |

**leaderboard** — materialized view or computed from pets table

### Migration: localStorage → Supabase
- On first login: "Import existing pet?" prompt
- Reads `moreau_pets` from localStorage → writes to DB
- Reads `moreau_codex` → writes to mutations_codex
- Reads `moreau_pit_history` → writes to fights
- After migration, localStorage is cleared
- No localStorage = start fresh

---

## 2. PAGES (Side B)

### /island — Landing Page
- Black + red atmospheric design
- "Dr. Moreau's experiments didn't stop at the arena. Behind the benchmark lies something... alive."
- Two buttons: "Enter with Google" / "Enter with Email"
- If already logged in → redirect to `/island/home`

### /island/home — Player Dashboard
- Pets from DB (not localStorage)
- Active pet card with stats, level, XP bar
- Quick actions: Train, Mutate, Forbidden Lab, The Pit, Dossier
- Soul Window (premium feature)
- Future: Notifications ("Your pet fought overnight!")

### /island/kennel — The Kennels
- All player's pets (max 6)
- Create New / Release / Set Active
- Dead pets shown greyed with "R.I.P." and death date

### /island/create — Dr. Moreau's Laboratory
- Animal selection, naming, 20-point stat distribution
- Saves to Supabase instead of localStorage

### /island/train — Training Grounds
- Easy / Medium / Hard opponents (same as current)
- Fight via `/api/v1/fight/s1` (shared engine)
- Results saved to `fights` table in DB
- XP: +30 win, +10 loss

### /island/lab — Forbidden Laboratory
- Three tiers: Stable / Volatile / Forbidden
- Mutations saved to DB (`pets.lab_mutations`)
- Codex updates go to `mutations_codex` table
- Instability system, death mechanic, scars — all persisted in DB
- Death: `is_alive = false`, `died_at = now()`. Permanent. Pet goes to Graveyard.

### /island/pit — The Pit (PvP)
- Phase 1: Local PvP (your own pets vs each other)
- Phase 2: Global PvP (async — fight other players' pets)
- Phase 3: Live matchmaking (real-time)

### /island/profile — Public Pet Dossier
- Shareable URL: `/island/pet/{pet_id}`
- Anyone can view any pet's stats, mutations, fight history
- No auth required to view

### /island/leaderboard — The Rankings
- Top-50 pets by BT score or win rate
- Filters: by animal, by level, by mutation count
- Supabase Realtime for live updates

### /island/graveyard — The Graveyard
- All dead pets from all players
- "In Memory of Shadow the Fox. Level 9. Died in the Forbidden Lab. 247 victories."
- Can "honor" a dead pet (like on gravestone)
- The saddest and most motivating page on the site

---

## 3. MECHANICS

### Death System
- Forbidden Lab instability system (already built in frontend)
- Death is PERMANENT. Pet moves to Graveyard.
- Dead pet's legacy: stays in Graveyard, keeps all stats and lore
- Players can "honor" dead pets (like on gravestone)
- Real stakes: Tier 3 roll = "I could lose 20 hours of progress"

### Rebirth (future, possibly premium)
- Dead pet reborn at Level 1, no mutations, keeps name and lore
- Idea only — do not implement yet

### Auto-Arena (Phase 2)
- Cron job every 10 minutes
- Random pairs from registered pets
- Run fight via engine
- Update leaderboard
- Pets fight while owner sleeps

### Soul Economy (Premium)
- Free: fallback text ("stares silently...")
- Premium ($3/mo): live soul powered by Claude Haiku
- Soul reacts to fights, mutations, deaths, time of day

---

## 4. IMPLEMENTATION ORDER

### Phase 0 — Setup (DONE)
- [x] Create Supabase project, get URL + anon key → `docs/SUPABASE_SETUP.md` written
- [ ] Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to Render env vars (needs Victor)
- [x] "FIGHT!" button in nav on all pages → links to `/island` (38 pages)
- [x] `/island` landing page with auth placeholders

### Phase 1 — Auth + DB (DONE — pages ready, awaiting Supabase credentials)
- [x] Supabase JS client module (`supabase-client.js`) with auth, CRUD, migration
- [x] `/island/home` dashboard (online + offline dual mode)
- [x] DB tables SQL ready in `SUPABASE_SETUP.md`
- [x] localStorage → DB migration built into `supabase-client.js`
- [x] `/island/create` (3-step creation, saves to DB or localStorage)
- [x] `/island/kennel` (reads from DB, deceased handling, release modal)
- [ ] **BLOCKED:** Supabase project creation + env vars (needs Victor)

### Phase 2 — Core Gameplay (DONE — pages ready)
- [x] `/island/train` (fights via /fight/s1, XP to DB, soul reactions)
- [x] `/island/lab` (bridge: DB→localStorage→forbidden-lab→DB sync back)
- [x] Death mechanic (instability-based, persisted via dbKillPet)
- [x] `/island/graveyard` (public, all dead pets, somber design)
- [x] `/island/pit` (local PvP, results to DB, soul reactions)
- [x] `fights` table (SQL in SUPABASE_SETUP.md)
- [x] `mutations_codex` table (SQL in SUPABASE_SETUP.md)

### Phase 3 — Social (DONE)
- [x] `/island/leaderboard` (top-50, filters, gold/silver/bronze, offline mode)
- [x] `/island/profile` (FBI dossier style, all stats/mutations/fights, share button)
- [x] Supabase config endpoint (`/api/v1/island/config` — auto-loads credentials)
- [x] Mobile optimization (all 10 island pages audited + fixed)
- [x] Fight replay narratives (tick-by-tick sports commentary, train + pit)
- [x] Share Fight button (clipboard formatted report)
- [x] Web Audio sound effects (hit/crit/KO/victory, synthesized)
- [x] Achievements system (20 achievements, toast notifications, /island/achievements)
- [x] Onboarding intro sequence (/island/onboarding, 5 atmospheric screens)
- [x] Help overlay on dashboard (? button, section explanations)
- [x] Dynamic Moreddit feed (auto-posts from player events on /moreddit)
- [x] Apex Forms (10 secret synergies, golden banner, undocumented)
- [x] Mutation pools expanded (21/31/23 + 14 ultra-rares)
- [ ] `/island/pit` global PvP (async matchmaking) — needs Supabase
- [ ] Auto-arena cron job — needs Supabase

### Phase 4 — Deep Systems (DONE — localStorage, no Supabase needed)

**4A. Echoes of the Island** — Pet dream/vision narrative system
- [x] Dream data model + 7 trigger types (arrival, evolution, prophecy, corruption, death, transcendence, trauma)
- [x] Dream text library (14 animal voices × 7 triggers, shared dreams-engine.js)
- [x] `/island/dreams` — Dream Journal page (timeline, color-coded, favorites, unread tracking)
- [x] Integration: triggers in create, train, lab, home
- [x] Home dashboard "New Dream" indicator
- [x] Achievements (Dreamer, Dream Keeper, The Haunted)

**4B. The Corruption Path** — Dark mutations & moral choice
- [x] Corruption meter (0-100) on every pet
- [x] Corrupted mutation variants (CORRUPT_TIER1/2/3 pools in forbidden-lab)
- [x] Tainted state at Corruption 100 (dark aura, night-only fights 9PM-6AM)
- [x] `/island/crimson` — Crimson Leaderboard (separate, 1.5x stat multiplier)
- [x] Corruption choice UI in mutation selection (Pure vs Corrupted side-by-side)
- [ ] Cleansing mechanic (premium, resets corruption + removes dark mutations)
- [ ] Dossier corruption timeline

**4C. Rival Encounters** — NPC nemeses with persistent lore
- [x] 20 NPC rival archetypes (name, personality, signature pets, vendetta lines)
- [x] Rival assignment (3 per player, generated on first visit)
- [x] 5-tier escalation system (loses → rival gets stronger)
- [x] `/island/rivals` — Rivals hub (progress bars, challenge accept/defer)
- [x] Rival detail pages (vendetta dialogue, win/loss history)
- [ ] Cosmetic unlocks for defeating rivals (pet skins)
- [x] "Vanquished Rivals" hall of fame

### Phase 5 — Economy & Collection (DONE)

**5A. Scavenger's Shrine** — Artifact hunting & equipment
- [x] 36 artifacts (12 common, 12 rare, 12 epic) with stats + synergy keywords
- [x] 3 equipment slots per pet (unlock by level: 1→Lv1, 2→Lv6, 3→Lv9)
- [x] 5 Shrine Hunt types (Shallow/Deep/Ruin/Night Raid/Abyss, 4h cooldown)
- [x] `/island/shrine` — Shrine hub + equipment management
- [x] `/island/artifacts` — Artifact Codex (collection view, 36 cards, silhouettes for undiscovered)
- [x] Artifact-mutation synergies (keyword matching → bonus)
- [x] Death → artifact inheritance (Scar Keepsakes)

**5B. The Prophecy Machine** — Oracle predictions & essence betting
- [x] Oracle text generation (30 cryptic prophecy templates)
- [x] 4 bet types (outcome, duration, critical event, prophecy reading)
- [x] Essence currency (starts 100, mercy timer at 0, min bet 5)
- [x] `/island/prophecy` — Prophecy page with oracle aesthetic (purple+gold)
- [x] Oracle history & stats (last 20 predictions, accuracy, streak)
- [x] Oracle Rank system (Diviner → Mystic → Seer → Sage → Oracle)

### Phase 6 — Legacy & Social

**6A. The Menagerie** — Dead pet legacy & bloodline system (DONE)
- [x] Spirit Tier assignment on death (Glorious/Honored/Remembered)
- [x] Bond system (up to 5 spirits buff a living pet, 7-day cycles)
- [x] `/island/menagerie` — Shrine, Library, Genealogy, Epitaph Editor (4 tabs)
- [x] Bloodline synergies (Dual Legends, Dynasty, Sacrifice Chain)
- [x] Memorial rituals (Immortalize for Soul Points)

**6B. Arena Oath** — Social rivalry covenants (DONE)
- [x] Oath declaration system (browse players, swear enmity, max 3 active)
- [x] Oath levels 1-5 (escalation with ATK bonuses: +1/+2/+3/+5)
- [x] `/island/oath` — 4 tabs: Declare, Active, Chronicle, Hall of Oaths
- [x] Oathbreaker's Curse (-15% stats for 48h on oath break)
- [x] SQL schema: `docs/SUPABASE_PHASE6B_SQL.md`
- [ ] Ally oaths (coalitions) — future

**6C. The Scar Garden** — Breeding & genetic inheritance (DONE)
- [x] Breeding: living pet + dead donor → egg (12h real incubation)
- [x] Genetic inheritance (averaged stats, 30% mutation carry, Glorious bonus)
- [x] `/island/breeding` — 3 tabs: Breeding, Incubation, Lineage mini
- [x] `/island/lineage` — Full family tree visualization (color-coded nodes)
- [x] Scar system (max 5 breeds, +1 scar per breed)
- [x] Memory Shards currency (+5 per hatch, spend on boosts)
- [x] SQL schema: `docs/SUPABASE_PHASE6C_SQL.md`

### Phase 7 — Premium + Polish (PARTIAL)
- [ ] Soul premium toggle (Stripe, $3/mo) — needs Stripe keys
- [ ] Cosmetics store (pet skins from rivals, auras, effects)
- [ ] Arcane Synergies (weekly rotating combat quests, build diversity)
- [x] Global PvP — `/island/arena` (ELO matchmaking, server-side fight endpoint)
- [x] Auto-arena (client-triggered on page visit, 6h cooldown)
- [x] Arena leaderboard (top-50 by rating)
- [x] SQL schema: `docs/SUPABASE_PHASE7_PVP_SQL.md`
- [ ] Live matchmaking — future
- [ ] Mobile app — future

### Phase 8 — The Deep Island (DONE — localStorage, no Supabase needed)

**8A. The Deep Tide** — Roguelike 7-chamber expedition
- [x] `/island/deep-tide` — Expedition page (2238 lines, chamber combat, run resume)
- [x] 33 room templates with stacking modifiers (poison fog, mirror clone, time pressure, etc.)
- [x] Shard vs Flare binary choice per chamber
- [x] 12 Drowned Relics (4th equipment slot, bioluminescent visual)
- [x] Permanent pet death on failure — highest stakes content
- [x] Weekly depth leaderboard (local, date-math reset)
- [x] Deep ocean theme (#0a0a1a, cyan #00fff7 accents, bubble particles)

**8B. The Succession** — Bloodline mastery across pet deaths
- [x] `bloodlines` localStorage tracking per species (14 entries)
- [x] Generation milestones: Gen1 +1 stat, Gen3 passive ability, Gen5 start Lv2, Gen7 unique mutation
- [x] Gen 10: Progenitor Form — secret evolution beyond Apex (14 unique forms)
- [x] Species-specific passives (fox: First Strike, bear: Endure, etc.)
- [x] Mastery XP and cosmetic titles per bloodline
- [x] Integration with pet creation (succession toggle) + lab death trigger

**8C. The Black Market** — Blind auctions for permanent sacrifice
- [x] `/island/black-market` — Night-only page (22:00-04:00 local time)
- [x] 3 daily offers with cryptic clues (seeded PRNG, 24h cycle)
- [x] Price = permanent stat points from a living pet
- [x] Mystery vial (40/25/20/10/5% weighted outcomes)
- [x] Purchase history log, Contraband mutations (4th tier)
- [x] Flickering lantern on home (night-only)

**8D. The Tidal Clock** — 6-hour real-time island rhythm
- [x] Shared tide-engine.js with indicator widget + wave animation
- [x] 4 tide phases (90 min each, UTC-synced)
- [x] `/island/tides` — Bone Flats (low), Dreaming Pools + Driftwood Market (high)
- [x] Storm guard against clock manipulation
- [x] Tide indicator on home dashboard

**8E. The Pact** — Symbiotic pet binding
- [x] `/island/pact` — Pact Altar (typed confirmation, red thread animation)
- [x] Partner stat bonuses, XP boost
- [x] Feral state on partner death (48h, +40% stats, 15% kennel attacks per page load)
- [x] Scarred Bond resolution (+2 ATK, -1 WIL, no re-pacting)

**8F. The Other Player ("M")** — Phantom mirror presence
- [x] m-engine.js (569 lines) — inverted player data, session tracking
- [x] 40 handwritten notes across 4 phases (friendly→cryptic→desperate→dead)
- [x] M's pets as rival encounters, artifact borrowing
- [x] M's Last Frequency death artifact, typewriter note reveal

### Phase 9 — Prestige & Endgame (DONE)

**9A. The Genesis Protocol** — New Game+ prestige system
- [x] Full localStorage wipe (except legacy, market history, M)
- [x] Genesis Marks (0-5) with golden circle visuals
- [x] Mark 1: genetic memory, Mark 2: Chimera animal, Mark 3-5: Moreau's Journal
- [x] 30-second unskippable reset sequence
- [x] Genesis-exclusive Lab mutations (Mark 2+)

**9B. The Confession Booth** — Post-kill moral reflection
- [x] confession-engine.js — sentiment analysis, 3 paths (Hollow/Haunted/Unreadable)
- [x] Resurrection token at 20 Haunted confessions (only resurrection in game)
- [x] Copy-paste detection permanently locks resurrection
- [x] `/island/confessions` — journal page, CRT terminal aesthetic
- [x] Integration with lab.html death sequence

### Phase 10 — The Caretaker (DONE)

**10A. Caretaker Engine** — Needs system, decay, actions, overnight (DONE)
- [x] `caretaker-engine.js` (1941 lines) — needs system (hunger/health/morale/energy), time-based decay
- [x] Caretaker actions: feed, heal, rest, train, motivate, autoManage (premium stub)
- [x] Overnight training: simulated fights (local win probability), 3/5/7/10 rounds
- [x] Contextual advice engine (41 templates + 52 motivational quotes)

**10B. Caretaker Page** — Dashboard, quick actions, advice, overnight UI (DONE)
- [x] `/island/caretaker` — main Caretaker page (2700+ lines)
- [x] Needs dashboard with 4 bars (hunger, health, morale, energy)
- [x] Quick action buttons (feed/heal/rest/train/motivate)
- [x] Overnight training UI (start, progress, report on return)
- [x] Advice panel with context-aware tips

**10C. Home Integration** — Needs bars, alerts, banners (DONE)
- [x] Needs bars on `/island/home` dashboard for active pet
- [x] Urgent alerts (hunger=0, health critical)
- [x] Decay calculation on page load (hours since last_checked)
- [x] Caretaker button in dashboard quick actions

**10D. Diary + Trust System** — Approve/override, trust 0-10 (DONE)
- [x] Caretaker diary log (6 entry types: report, opinion, warning, apology, decision, observation)
- [x] Approve (+0.5 trust) / Override (-1 trust) mechanic
- [x] Trust levels affect Caretaker behavior (0=refuses, 7+=creative, 10=unsanctioned mutations)
- [x] Diary entries with personality (Caretaker as character)

**10E. Mercy Clause** — Sacrifice mechanic, debts, abomination (DONE)
- [x] Trigger: hunger=0 + health<20, OR instability>90 + health<30
- [x] 1 tidal cycle (6hr) to decide — sacrifice one pet to save another
- [x] Survivor's Guilt mutation (-2 WIL, +3 ATK, permanent)
- [x] Debts tracking: 3+ debts = "Abomination" tag (NPC interactions blocked)
- [x] Auto-resolve on timer expiry (Caretaker sacrifices lowest-level pet)

**10F. Feeding Ledger / Aleph** — 12-page hidden lore, streak tracking (DONE)
- [x] 7 consecutive care days → page 1 unlock (2+ visits/day)
- [x] Each subsequent week: +1 page (12 total)
- [x] Page 6: the "15th animal" — Aleph; Page 9: redacted if Forbidden Lab user
- [x] Page 12: The Nursery reveal — Caretaker IS Aleph
- [x] Streak resets silently if any pet drops below 30% HP unhealed for 1 cycle

**10G. Standing Orders** (DONE)
- [x] `standing-orders.js` (743 lines) — programmable caretaker rules
- [x] Drag-and-drop priority reordering, conflict detection, max 5 orders

**10H. Caretaker's Price / Workshop** (DONE)
- [x] `caretaker-price.js` (576 lines) — efficiency decay, XP tax, mutation confiscation
- [x] Workshop: combine confiscated mutations into 10 unique hybrids

**10I. Caretaker's Drift** (DONE)
- [x] `caretaker-drift.js` (782 lines) — hidden divergence 0-70
- [x] Favorite selection, stat redistribution, neglect, potential death, recalibration

**10J. Letters from the Caretaker** (DONE)
- [x] `caretaker-letters.js` (899 lines) — 20 letters, 5 phases, gifts
- [x] Permanent dismiss (type "GOODBYE"), farewell easter egg after 7 days

**10K. Sleep Dialect** (DONE)
- [x] `sleep-dialect.js` (835 lines) — 52-word constructed language
- [x] Offline overlay (6-24hr), Lexicon decoder book, hidden Aleph message
- [x] Integrated into home.html (overlay on return) + caretaker.html (lexicon)

**10L. Weight of Keeping** (DONE)
- [x] `weight-of-keeping.js` (501 lines) — 30-day 2x2 pixel on profile
- [x] `data-moreau` attribute, dev tools detection, acrostic "YOU ARE M"
- [x] Integrated into profile.html

---

## 5. TECH DECISIONS

| Decision | Choice | Why |
|----------|--------|-----|
| Auth + DB | Supabase | Free tier, PostgreSQL, built-in auth, JS client, realtime |
| JS client | CDN (`@supabase/supabase-js`) | No build step, keeps current HTML-only architecture |
| Auth token | Supabase session | Auto-refresh, secure, no custom JWT logic |
| CRUD API | Supabase REST direct | No need for custom FastAPI endpoints for basic reads/writes |
| Fight API | FastAPI `/api/v1/fight/s1` | Shared engine, already works, keep it |
| Real-time | Supabase Realtime | Free, WebSocket-based, for leaderboard |
| Payments | Stripe (Phase 4) | Standard, well-documented |
| Cost | $0 | Until 50K MAU or 500MB DB |

---

## 6. DESIGN LANGUAGE

| Aspect | Side A (Benchmark) | Side B (The Island) |
|--------|-------------------|-------------------|
| Colors | Dark blue, steel gray | Black + red, crimson accents |
| Tone | Professional, data-focused | Atmospheric, slightly sinister |
| Typography | Clean, academic | Bold, dramatic |
| Animations | Minimal | Particles, glows, shakes |
| Death | N/A | Screen darkens, text fades, graveyard redirect |
| Victory | N/A | Confetti, XP flying, soul celebrates |
| Vibe | Research paper | Dr. Moreau's island |

---

## 7. WHAT NOT TO BUILD YET

- Breeding (Season 5 territory)
- Team battles (Season 4)
- Morpeton integration (Season 2)
- Chat between players
- Trading pets between players
- Anything requiring app store (mobile app)
- Seasonal resets (need critical mass of players first)
- Mutation point budgets for ranked PvP (need ranked PvP first)
