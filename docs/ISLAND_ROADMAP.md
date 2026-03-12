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

### Phase 0 — Setup (NOW)
- [ ] Create Supabase project, get URL + anon key
- [ ] Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to Render env vars
- [ ] "FIGHT!" button in nav on all pages → links to `/island`

### Phase 1 — Auth + DB (3-4 days)
- [ ] Supabase Auth (Google OAuth + email/password)
- [ ] `/island` landing page with login
- [ ] `/island/home` dashboard
- [ ] DB tables: `users`, `pets`
- [ ] localStorage → DB migration on first login
- [ ] `/island/create` (save to DB)
- [ ] `/island/kennel` (read from DB)

### Phase 2 — Core Gameplay (3-4 days)
- [ ] `/island/train` (fights saved to DB)
- [ ] `/island/lab` (mutations + instability saved to DB)
- [ ] Death mechanic (instability-based, persisted)
- [ ] `/island/graveyard`
- [ ] `/island/pit` (local PvP, results to DB)
- [ ] `fights` table
- [ ] `mutations_codex` table

### Phase 3 — Social (3-4 days)
- [ ] `/island/leaderboard` (computed from DB)
- [ ] `/island/profile` (public shareable dossier)
- [ ] `/island/pit` global PvP (async matchmaking)
- [ ] Auto-arena cron job
- [ ] Moreddit integration (auto-posts from top pets)

### Phase 4 — Polish + Premium
- [ ] Soul premium toggle (Stripe)
- [ ] Rebirth mechanic
- [ ] Cosmetics store
- [ ] Live matchmaking
- [ ] Mobile optimization

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
