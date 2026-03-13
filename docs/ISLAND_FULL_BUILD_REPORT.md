# The Island — Side B: Full Build Report

**Date:** 2026-03-12
**Author:** Claude (Opus 4.6) + Victor
**Status:** Phase 0–9 complete. Phase 6B/6C/7 blocked on Supabase.
**Total code:** 34,841 lines across 31 files in `web/static/island/`
**Total pages:** 27 HTML pages + 4 shared JS engines

---

## TABLE OF CONTENTS

1. [Architecture Overview](#1-architecture-overview)
2. [File Inventory](#2-file-inventory)
3. [Phase-by-Phase Build Log](#3-phase-by-phase-build-log)
4. [Data Model (localStorage)](#4-data-model-localstorage)
5. [Shared Engines](#5-shared-engines)
6. [Integration Points](#6-integration-points)
7. [What's Blocked](#7-whats-blocked)
8. [How to Continue](#8-how-to-continue)

---

## 1. ARCHITECTURE OVERVIEW

### Two Sides
- **Side A (Benchmark):** Frozen research paper + tournament engine. DO NOT TOUCH.
- **Side B (The Island):** Interactive browser game. Dark science, pet fighting, permanent death.

### Tech Stack
- **Backend:** FastAPI (`web/app.py`), serves static HTML pages at `/island/{page}`
- **Frontend:** Pure HTML/CSS/JS, no build step, no framework
- **Data:** localStorage (offline-first). Supabase planned but not yet connected.
- **Fight Engine:** `POST /api/v1/fight/s1` — shared Season 1 engine (`season1/engine_s1.py`)
- **Auth:** Supabase JS client via CDN (prepared but inactive — waiting for credentials)

### Entry Point
- Red "FIGHT!" button in top-right nav on ALL site pages → links to `/island`
- `/island` = atmospheric landing page with auth placeholders

### Design Language
- **Colors:** Black (#0a0a0a) + crimson (#dc3545) primary; systems have unique accents
- **Tone:** Dr. Moreau's island — dark science, dread, attachment, permanent consequences
- **14 Animals:** wolf 🐺, bear 🐻, fox 🦊, hawk 🦅, snake 🐍, panther 🐆, shark 🦈, eagle 🦅, tiger 🐅, croc 🐊, rhino 🦏, mantis 🦗, scorpion 🦂, chameleon 🦎

---

## 2. FILE INVENTORY

### Pages (27 HTML files)

| File | Lines | Phase | Description |
|------|-------|-------|-------------|
| `index.html` | 390 | 0 | Landing page, auth placeholders |
| `home.html` | 2,420 | 1+ | Main dashboard, actions grid, all engine integrations |
| `create.html` | 1,056 | 1 | 3-step pet creation, succession toggle, inspired-by |
| `kennel.html` | 912 | 1 | Pet roster (max 6), release, deceased display |
| `train.html` | 1,662 | 2 | AI fights (easy/med/hard), replay narrative, sounds |
| `pit.html` | 1,720 | 2 | Local PvP, fight replay, share button |
| `lab.html` | 764 | 2 | Bridge to forbidden-lab, apex detection, death triggers |
| `graveyard.html` | 629 | 2 | Public graveyard for all dead pets |
| `leaderboard.html` | 883 | 3 | Top-50, filters, gold/silver/bronze, crimson link |
| `profile.html` | 1,229 | 3 | FBI dossier style, all stats/mutations/fights |
| `achievements.html` | 508 | 3 | 20+ achievements, progress bar, toast notifications |
| `onboarding.html` | 326 | 3 | 5-screen atmospheric intro sequence |
| `dreams.html` | 847 | 4A | Dream journal, timeline, color-coded, favorites |
| `crimson.html` | 948 | 4B | Crimson Leaderboard for tainted (corruption 100) pets |
| `rivals.html` | 1,987 | 4C | 20 NPC nemeses, 5-tier escalation, vendetta dialogues |
| `shrine.html` | 1,640 | 5A | 36 artifacts, 5 hunt types, 3 equipment slots |
| `artifacts.html` | 628 | 5A | Artifact Codex, collection view, silhouettes |
| `prophecy.html` | 2,068 | 5B | Oracle, 4 bet types, essence currency, rank progression |
| `menagerie.html` | 2,160 | 6A | Spirit shrine, bonds, bloodline library, epitaphs |
| `deep-tide.html` | 2,238 | 8A | 7-chamber roguelike, 33 modifiers, 12 Drowned Relics |
| `succession.html` | 1,504 | 8B | Bloodline mastery, 14 species, Progenitor Forms |
| `black-market.html` | 1,764 | 8C | Night-only blind auctions, stat sacrifice, contraband |
| `tides.html` | 1,220 | 8D | Tide hub, Bone Flats, Dreaming Pools, Driftwood Market |
| `pact.html` | 1,600 | 8E | Symbiotic binding, feral state, scarred bond |
| `genesis.html` | 1,562 | 9A | New Game+ prestige, 5 marks, 30s reset sequence |
| `confessions.html` | 507 | 9B | Confession journal, resurrection tracker |

### Shared JS Engines (4 files)

| File | Lines | Description |
|------|-------|-------------|
| `dreams-engine.js` | 275 | Dream library (7 types × 14 animals), `generateDream()`, toast |
| `tide-engine.js` | 196 | 6-hour cycle calculator, indicator widget, wave animation |
| `m-engine.js` | 569 | Phantom player "M", 40 notes, artifact movement, death arc |
| `confession-engine.js` | 373 | Sentiment analysis, 3 paths, resurrection token, CRT modal |

### Other JS

| File | Lines | Description |
|------|-------|-------------|
| `supabase-client.js` | 256 | Supabase client with async init, CRUD, migration (dormant) |

---

## 3. PHASE-BY-PHASE BUILD LOG

### Phase 0 — Setup ✅
- "FIGHT!" button added to nav on all 38+ site pages
- `/island` landing page with auth placeholders
- Supabase setup documentation (`docs/SUPABASE_SETUP.md`)
- Instructions for Victor on desktop (`~/Desktop/SUPABASE_TODO_VICTOR.md`)

### Phase 1 — Auth + DB ✅ (pages ready, auth dormant)
- **`/island/home`** — Player dashboard with active pet card, stats, XP bar, quick actions grid
- **`/island/create`** — 3-step creation: animal selection → naming → 20-point stat allocation
- **`/island/kennel`** — All pets (max 6), create/release/set active, deceased greyed with R.I.P.
- **`supabase-client.js`** — Async init from `/api/v1/island/config`, CRUD helpers, migration
- Dual mode: works with localStorage offline, ready for Supabase when credentials arrive

### Phase 2 — Core Gameplay ✅
- **`/island/train`** — Fight AI opponents (easy/medium/hard), XP +30 win/+10 loss
  - Tick-by-tick fight replay narrative (sports commentary style)
  - Web Audio sound effects (hit/crit/KO/victory, synthesized)
  - Share Fight button (clipboard formatted report)
  - Achievement triggers (first_win, win_streak_10, max_level)
  - Dream triggers (EVOLUTION on level-up, TRAUMA on comeback)
  - Moreddit auto-posts on win/loss
  - Tainted time check (9PM-6AM only for corruption 100 pets)
- **`/island/pit`** — Local PvP (your pets vs each other)
  - Same replay/sound/share features as train
  - Achievement trigger (civil_war)
- **`/island/lab`** — Bridge page: loads pet data, syncs to forbidden-lab.html and back
  - Apex Form detection (JS mirroring Python's `check_apex_form()`)
  - Moreddit posts on mutations/deaths
  - Dream triggers (PROPHECY, CORRUPTION, DEATH, TRANSCENDENCE)
  - Bloodline update on death (Phase 8B integration)
  - Confession trigger on death (Phase 9B integration)
  - Artifact inheritance on death (Phase 5A integration)
- **`/island/graveyard`** — All dead pets, somber design, achievement trigger

### Phase 3 — Social ✅
- **`/island/leaderboard`** — Top-50 by BT score, filters (animal/level/mutations), medals
  - Excludes tainted pets (links to Crimson Leaderboard instead)
  - Offline mode with localStorage data
- **`/island/profile`** — FBI dossier style pet page
  - Full stats, mutations, lab mutations, side effects, fight history
  - Shareable URL concept (`/island/pet/{id}` — ready for Supabase)
  - Share button (clipboard)
- **`/island/achievements`** — 20+ achievements system
  - Toast notifications on unlock
  - `checkAchievement(id)` utility called from multiple pages
  - Categories: combat, lab, social, exploration
- **`/island/onboarding`** — 5-screen atmospheric intro
  - Plays on first visit, sets `moreau_onboarded` flag
  - Dark, cinematic, introduces the island's premise
- **Supabase config endpoint** — `GET /api/v1/island/config` in app.py
- **Mobile optimization** — All island pages audited and fixed
- **Dynamic Moreddit** — Auto-posts from player events on `/moreddit` page
- **Apex Forms** — 10 secret synergies, golden banner, Python + JS detection

### Phase 4A — Echoes of the Island ✅
- **`dreams-engine.js`** — Shared dream generation engine
  - `DREAM_LIBRARY`: 7 dream types × 14 animal-specific texts
  - Types: ARRIVAL, EVOLUTION, PROPHECY, CORRUPTION, DEATH, TRANSCENDENCE, TRAUMA
  - `generateDream(type, pet, extra)` — creates dream in `moreau_dreams` localStorage
  - `showDreamToast(dream)` — type-colored notification
- **`/island/dreams`** — Dream Journal page
  - Vertical timeline, color-coded by dream type
  - Expandable cards with full dream text
  - Favorites system, unread tracking
  - Filter by dream type
- **Triggers integrated in:** create.html (ARRIVAL), train.html (EVOLUTION, TRAUMA), lab.html (PROPHECY, CORRUPTION, DEATH, TRANSCENDENCE)
- **Home dashboard:** "New Dream" indicator when unread dreams exist

### Phase 4B — The Corruption Path ✅
- **Corruption system:** `corruption` field (0-100) on every pet
  - Corrupted mutation pools in `forbidden-lab.html`: CORRUPT_TIER1 (5), CORRUPT_TIER2 (6), CORRUPT_TIER3 (5)
  - Corruption choice modal: Pure vs Corrupted side-by-side during mutation selection
  - Corrupted variants have better stats but increase corruption
- **Tainted state** at corruption ≥ 100:
  - Dark aura visual on pet card
  - Can only fight between 9PM-6AM local time (enforced in train.html + pit.html)
  - Excluded from normal leaderboard
- **`/island/crimson`** — Crimson Leaderboard
  - Dark red/black theme, skull rank badges
  - 1.5x stat display multiplier
  - Only shows tainted pets

### Phase 4C — Rival Encounters ✅
- **`/island/rivals`** — Full NPC nemesis system (1,987 lines)
  - 20 NPC rival archetypes with unique names, personalities, signature pets
  - Full vendetta dialogue trees (taunt/victory/defeat/escalation lines)
  - 3 rivals assigned per player on first visit
  - 5-tier escalation: rival stats increase when player loses
  - 3 wins to defeat a rival → "Vanquished" hall of fame
  - Fight integration via `/api/v1/fight/s1`
  - Moreddit posts on rival encounters
- **Home dashboard:** "RIVALS" button in actions grid

### Phase 5A — Scavenger's Shrine ✅
- **`/island/shrine`** — Artifact hunting hub (1,640 lines)
  - 36 artifacts: 12 Common, 12 Rare, 12 Epic
  - All themed around Dr. Moreau's island (surgical tools, creature specimens, lab chemicals, island relics)
  - Stat bonuses: Common +1, Rare +1-2, Epic +2-3
  - Synergy keywords: predator, speed, tank, mystic, blood, shadow, storm, venom, iron, flame, frost, void
  - 5 hunt types:
    - Shallow Search (easy, mostly common)
    - Deep Dig (medium, common + rare)
    - Ruin Expedition (hard, rare + epic chance)
    - Night Raid (9PM-6AM only, better epic chance)
    - The Abyss (hardest, guaranteed rare+, costs 1 HP temporarily)
  - 4-hour hunt cooldown (`moreau_last_hunt` localStorage)
  - Hunt animation with progress bar and atmospheric text
  - Card-flip artifact reveal animation
  - 3 equipment slots per pet (Lv1 / Lv6 / Lv9 unlock)
  - Equipment stored in `pet.equipment = {slot1, slot2, slot3}`
  - Artifact-mutation synergy: keyword match → +1 bonus to primary stat
  - Death → artifact inheritance (Scar Keepsakes in `moreau_scar_keepsakes`)
- **`/island/artifacts`** — Artifact Codex (628 lines)
  - Collection view: all 36 as cards
  - Found = full color, unfound = dark silhouette with "???"
  - Filter by rarity (All/Common/Rare/Epic)
  - Progress: "X/36 Artifacts Discovered"
  - Click → detail modal with stats, lore, synergy info

### Phase 5B — The Prophecy Machine ✅
- **`/island/prophecy`** — Oracle predictions page (2,068 lines)
  - **Aesthetic:** Dark purple (#1a0a2e) + gold (#d4af37), crystal ball motif
  - **Oracle:** 30 cryptic prophecy templates with variable slots for animal names, stats, outcomes
  - **Matchup:** Player's pet vs random AI, or two random AIs
  - **4 bet types:**
    - Outcome (2x): predict winner
    - Duration (3x): fight ends in <30 or ≥30 ticks
    - Critical Event (2.5x): predict crit happens
    - Prophecy Reading (4x): interpret the oracle's cryptic message
  - **Essence currency:** `moreau_essence` (starts at 100)
    - Min bet 5, payouts multiplied
    - Mercy timer: 10 free essence every 6 hours at 0
  - **Oracle Rank:** Diviner (0) → Mystic (100) → Seer (250) → Sage (500) → Oracle (1000+)
    - Based on `moreau_oracle_total_earned`
  - **History tab:** Last 20 predictions with timestamps, accuracy, best streak

### Phase 6A — The Menagerie ✅
- **`/island/menagerie`** — Dead pet legacy system (2,160 lines, 4 tabs)
  - **Tab 1: Spirit Shrine**
    - Dead pets as ethereal spirit cards
    - Spirit Tier: Glorious (gold, Lv8+ & 50+ wins), Honored (silver, Lv5+ & 20+ wins), Remembered (bronze)
    - Click → detail modal with full stats, cause of death, epitaph
  - **Tab 2: Spirit Bonds**
    - Link up to 5 spirits to ONE living pet
    - Tier-based buffs: Glorious +2, Honored +1, Remembered +1 random
    - 7-day cycle timer, rebind on reset
    - Visual: orbital CSS animation (spirits circle the living pet)
  - **Tab 3: Bloodline Library**
    - Vertical family tree (uses `pet.inspired_by` from create.html)
    - 3 synergy types:
      - Dual Legends: 2 Glorious spirits bonded → +1 all stats
      - Dynasty: 3+ same animal → +2 signature stat
      - Sacrifice Chain: lab death + combat death → +3 ATK
  - **Tab 4: Epitaph Editor**
    - Custom epitaphs (max 140 chars) for dead pets
    - Contextual suggestions based on pet's life
    - Stored in `moreau_epitaphs`
  - **Memorial Rituals:** Immortalize Glorious spirits for 10 Soul Points → permanent buff
  - **localStorage:** `moreau_spirit_bonds`, `moreau_epitaphs`, `moreau_soul_points`, `moreau_immortalized`

### Phase 8A — The Deep Tide ✅
- **`/island/deep-tide`** — Roguelike expedition (2,238 lines)
  - **7 chambers**, one pet, no healing, permanent death on loss
  - **Expedition HP** = pet's HP stat × 10; fights cost HP = ticks / 5
  - **33 room modifiers** that STACK as you descend:
    - Stat modifiers: Darkness (SPD ÷2), Whirlpool (WIL ÷2), Thermal Vent (ATK ÷2)
    - Enemy buffs: Predator's Den (+3 ATK), Bone Garden (+2 all), Leviathan's Shadow (HP ×2)
    - Damage: Poison Fog, Pressure Spike, Coral Maze
    - Special: Mirror Chamber (clone), Echo Chamber (double-stack), Time Pressure, Dead Zone
  - **Enemy scaling:** 1.5x (ch1-2) → 2.0x (3-4) → 2.5x (5-6) → 3.0x (ch7, always shark/croc "The Leviathan")
  - **Binary choice per chamber:** Tide Shard (progress, need 7 for relic) vs Tide Flare (full heal, max 2)
  - **12 Drowned Relics** (4th equipment slot):
    1. Leviathan's Tooth — +3 ATK, first hit crits
    2. Abyssal Lantern — +2 WIL, +2 SPD
    3. Pressure Crown — +4 HP, survive killing blow at 1 HP
    4. Tidecaller's Horn — +2 all stats, +10 instability
    5. Drowned King's Signet — +3 WIL
    6. Mariana Plate — +5 HP, -1 SPD
    7. Biolume Serum — +3 SPD, glow cosmetic
    8. Coral Exoskeleton — +2 HP, +2 ATK
    9. Deep Current Valve — +4 SPD, -1 HP
    10. Kraken Ink — +3 ATK, +10% crit
    11. Void Pearl — +2 all, +15 corruption
    12. The Last Breath — +5 WIL, prophetic dreams
  - **Run state:** persisted in `moreau_tide_run`, supports resume
  - **Death sequence:** water rising animation, "The deep claims [name]...", redirect to graveyard
  - **Visual:** deep ocean (#0a0a1a), bioluminescent cyan (#00fff7), bubble particles

### Phase 8B — The Succession ✅
- **`/island/succession`** — Bloodline mastery (1,504 lines)
  - **Bloodlines** per species in `moreau_bloodlines` localStorage
  - Only pets level 5+ count toward generation on death
  - **Generation milestones:**
    - Gen 1: +1 to predecessor's highest stat
    - Gen 3: Species-specific passive ability:
      - Wolf: Pack Instinct (+2 ATK when HP <50%)
      - Bear: Endure (survive first killing blow)
      - Fox: First Strike (+15% opening damage)
      - Hawk: Aerial Advantage (+2 SPD first 10 ticks)
      - Snake: Venom Linger (10% ATK reduction)
      - Panther: Shadow Step (15% dodge)
      - Shark: Blood Frenzy (+1 ATK per 10 ticks)
      - Eagle: Piercing Gaze (see enemy stats)
      - Tiger: Territorial Rage (+3 ATK first attack)
      - Croc: Death Roll (10% instant KO at <20% HP)
      - Rhino: Iron Hide (-1 damage taken)
      - Mantis: Precision (+20% crit)
      - Scorpion: Neurotoxin (15% SPD halve)
      - Chameleon: Adaptation (copy enemy's highest stat after 15 ticks)
    - Gen 5: Start at level 2
    - Gen 7: Species-specific unique Lab mutation
    - Gen 10: **Progenitor Form** — +3 all stats, unique ability, but +20 instability
  - **Mastery titles:** Novice → Warden → Master → Architect → Lord
  - **Integration:** create.html succession toggle, lab.html bloodline update on death

### Phase 8C — The Black Market ✅
- **`/island/black-market`** — Night-only blind auctions (1,764 lines)
  - **Access:** 22:00-04:00 local time only. Locked gate with rain effect + countdown outside hours.
  - **3 daily offers** (deterministic from day-seed via mulberry32 PRNG):
    - Slot 1: Contraband Mutation (15 in pool, 4th tier above Forbidden)
    - Slot 2: Contraband Artifact (10 in pool, stronger than Shrine epics)
    - Slot 3: Mystery Vial (40% mutation, 25% artifact, 20% instability, 10% Dr. Moreau's Syringe +3 all, 5% poison)
  - **Price:** permanent stat points from a living pet (not currency)
    - Mutations: 2-3 stat points
    - Artifacts: 1-2 stat points + optional mutation removal
    - Vials: 3 stat points (player chooses which)
  - **Cryptic clues** on each card, no reveal until purchased
  - **Purchase flow:** select pet → select stats → "PAY THE PRICE" → dramatic card flip reveal
  - **Visual:** ultra-dark #0a0a0a, lantern glow, vendor silhouette with glowing eyes, noir rain
  - **Home integration:** flickering lantern button (night-only, CSS animation)

### Phase 8D — The Tidal Clock ✅
- **`tide-engine.js`** — Shared 6-hour cycle engine (196 lines)
  - `getTideState()` → phase, minutesLeft, progress
  - `renderTideIndicator(id)` → compact widget, auto-refreshes 15s
  - `renderTideWave(id)` → animated bottom wave bar
  - Anti-manipulation: 7h+ gap → "Storm" event (+5 instability)
- **`/island/tides`** — Tide hub page (1,220 lines)
  - Animated circular SVG tide clock
  - **4 phases** (90 min each, UTC-synced):
    - Low Tide: Bone Flats (scavenge dead pet remains, +1 stat, 15% curse risk)
    - Rising: transitional
    - High Tide: Lab locked, Dreaming Pools (heal instability/scars/corruption), Driftwood Market (free artifact transfers)
    - Falling: transitional
  - Phase-locked content (tabs lock/unlock)
  - 24-hour schedule grid
  - **Home integration:** tide indicator in dashboard header

### Phase 8E — The Pact ✅
- **`/island/pact`** — Symbiotic pet binding (1,600 lines)
  - **Binding:** two pets Lv3+, permanent, irreversible
  - **Confirmation:** type pact name to confirm (GitHub-style)
  - **Benefits:** +2 to partner's highest stat, +20% XP
  - **Feral state** when partner dies:
    - 48 real-world hours
    - +40% all combat stats
    - 15% chance per page load to attack random kennel pet (1-3 stat point loss)
    - Feral attack log in `moreau_feral_log`
  - **Resolution:** Scarred Bond trait (+2 ATK, -1 WIL), can never pact again
  - **Visual:** blood ritual crimson, red thread connections, feral red pulse
  - **Home integration:** feral check on page load, feral warning banner, pact partner display

### Phase 8F — The Other Player ("M") ✅
- **`m-engine.js`** — Phantom mirror presence (569 lines)
  - **M generated from inverted player data:** if player maxes ATK, M maxes WIL
  - **Session tracking:** every 5th home.html load, M acts:
    - 60% leave a note, 25% move an artifact, 15% introduce a pet
  - **40 handwritten notes** across 4 relationship phases:
    - Friendly (sessions 1-14): curious, helpful
    - Cryptic (15-24): unsettling, questioning reality
    - Desperate (25-34): pleading, existential
    - Final (35+): acceptance, farewell
  - **Artifact borrowing:** M takes unequipped artifact, returns after 3 sessions
  - **M's pets:** inverted stat builds, appear as special rival encounters (20% chance)
  - **M's death:** triggered by 10+ sessions of ignoring M
    - Final note, M's pets become Menagerie ghosts
    - "M's Last Frequency" artifact: +2 all stats, fight commentary glitch effect
  - **Home integration:** subtle bottom-left post-it note, typewriter reveal modal, no dedicated button (organic, not a menu item)

### Phase 9A — The Genesis Protocol ✅
- **`/island/genesis`** — New Game+ prestige (1,562 lines)
  - **Requirements:** Lv8+ pet, 5+ dead pets, 50+ fights
  - **Genesis Marks** (0-5):
    - Mark 1: Genetic Memory (+1 random stat per dead pet from prior cycles, cap +5)
    - Mark 2: 15th animal — The Chimera (fused from 3 dead species)
    - Mark 3: Moreau's Journal Vol. 1 (lore + mechanical secrets)
    - Mark 4: Journal Vol. 2 + Genesis-exclusive Lab mutations
    - Mark 5: Journal Vol. 3 + permanent color palette shift
  - **The Reset** (30 seconds, unskippable):
    1. Darkness (2s) → "GENESIS PROTOCOL INITIATED" (2s)
    2. Water rising flood (4s)
    3. Pet names scroll and fade, one by one (8s)
    4. Loss counter: "X pets, Y artifacts, Z achievements..." (4s)
    5. Silence. Black. (3s)
    6. Genesis Mark brands with golden rings (5s)
    7. "The island remembers." (2s) → redirect
  - **What's wiped:** ALL `moreau_*` keys EXCEPT `moreau_genesis`, `moreau_market_history`, `moreau_other_player`
  - **Confirmation:** type "I ACCEPT" to proceed
  - **Visual:** deep gold (#c9a227), sacred/apocalyptic, journal on aged parchment

### Phase 9B — The Confession Booth ✅
- **`confession-engine.js`** — Sentiment analysis engine (373 lines)
  - Triggers after pet death in lab (modal overlay)
  - Text input: 10-500 chars, freeform
  - **Keyword sentiment scoring:**
    - 25 remorse words (+0.1 each): sorry, regret, forgive, miss, loved...
    - 21 cold words (-0.1 each): weak, pathetic, whatever, necessary...
    - 11 deflection words (0): game, just, pixel, code...
  - **Three paths:**
    - **Hollow** (score < -0.2): +2 ATK, dreams suppressed 10 fights, "The Hollow" title at 5 consecutive
    - **Haunted** (score > 0.3): -1 WIL for 5 fights, BUT resurrection token at 20 total Haunted confessions
    - **Unreadable** (else): random quirk from 10 options (alters fight commentary)
  - **Copy-paste detection:** 3+ identical texts → resurrection path PERMANENTLY locked
  - **Resurrection token:** the ONLY way to bring back a dead pet in the entire game
- **`/island/confessions`** — Confession journal (507 lines)
  - Unlocks after 3rd confession
  - CRT terminal aesthetic (#00ff41 on #0a0a0a, scanlines)
  - Timeline with case numbering, pet emojis, colored path borders
  - Resurrection tracker: X/20 progress bar
  - Full resurrection UI with pet selector
- **Home integration:** subtle "CONFESSIONS" link (opacity 0.35), golden RESURRECTION button when token available

---

## 4. DATA MODEL (localStorage)

### Core Pet Data (`moreau_pets` — array, max 6)
```json
{
  "name": "Shadow",
  "animal": "fox",
  "level": 7,
  "xp": 2150,
  "base_stats": {"hp": 8, "atk": 12, "spd": 9, "wil": 6},
  "mutations": [],
  "fights": [{"opponent": "Bear", "result": "win", "ticks": 42, "timestamp": "..."}],
  "lab_mutations": {"L3": {...}, "L6": {...}, "L9": {...}},
  "side_effects": [{name, desc, category, stats}],
  "equipment": {"slot1": "artifact_id", "slot2": null, "slot3": null},
  "instability": 35,
  "corruption": 45,
  "scars": 2,
  "mood": "fierce",
  "deceased": false,
  "died_at": null,
  "cause_of_death": null,
  "mercy_used": false,
  "is_tainted": false,
  "pact": {"partner": "Fang", "partnerIndex": 2, "boundAt": "..."},
  "feral": {"until": "timestamp", "partnerName": "..."},
  "scarred_bond": {"partner": "Fang", "date": "..."},
  "bloodline_successor": true,
  "bloodline_generation": 3,
  "is_progenitor": false,
  "inspired_by": "Echo",
  "quirk": "whispers to opponents",
  "dreamsSuppressed": 0,
  "weightDebuff": 0,
  "created_at": "..."
}
```

### All localStorage Keys
| Key | Type | Description |
|-----|------|-------------|
| `moreau_pets` | array | All pets (max 6) |
| `moreau_active_pet` | number | Active pet index |
| `moreau_onboarded` | boolean | Onboarding complete flag |
| `moreau_achievements` | object | {achievement_id: {unlocked, date}} |
| `moreau_codex` | array | Discovered mutation IDs |
| `moreau_pit_history` | array | PvP fight history |
| `moreau_moreddit_feed` | array | Dynamic Moreddit posts |
| `moreau_dreams` | array | Dream journal entries |
| `moreau_artifacts` | array | Found artifact IDs |
| `moreau_scar_keepsakes` | array | Inherited artifacts from dead pets |
| `moreau_last_hunt` | timestamp | Shrine hunt cooldown |
| `moreau_essence` | number | Prophecy betting currency |
| `moreau_oracle_total_earned` | number | All-time essence earned |
| `moreau_oracle_history` | array | Prediction history |
| `moreau_spirit_bonds` | object | {petName, spirits[], cycleStart} |
| `moreau_epitaphs` | object | {petName: "text"} |
| `moreau_soul_points` | number | Immortalize currency |
| `moreau_immortalized` | object | {petName: {date}} |
| `moreau_bloodlines` | object | {species: {generation, ancestors[], masteryXP, unlocks[]}} |
| `moreau_bloodline_deepened` | string | Notification flag |
| `moreau_tide_run` | object | Active Deep Tide expedition state |
| `moreau_tide_records` | object | Best depths, weekly reset |
| `moreau_market_history` | array | Black Market purchase log |
| `moreau_last_tide_check` | timestamp | Anti-manipulation guard |
| `moreau_feral_log` | array | Feral attack history |
| `moreau_confessions` | array | Confession booth entries |
| `moreau_resurrection_token` | boolean | Available resurrection |
| `moreau_recitations_detected` | boolean | Copy-paste lock |
| `moreau_other_player` | object | M's full state |
| `moreau_m_session_counter` | number | Page load counter |
| `moreau_m_borrowed` | object | Artifacts M has taken |
| `moreau_m_last_frequency` | object | Death artifact state |
| `moreau_genesis` | object | Genesis legacy (NEVER wiped) |

---

## 5. SHARED ENGINES

### dreams-engine.js
- Included in: home.html, create.html, train.html, lab.html
- `generateDream(type, pet, extra)` — writes to `moreau_dreams`
- `showDreamToast(dream)` — colored toast notification
- 7 types × 14 animals = 98 unique dream texts

### tide-engine.js
- Included in: home.html, tides.html
- `TideEngine.getTideState()` — phase, minutesLeft, progress
- `TideEngine.renderTideIndicator(id)` — compact widget
- 6-hour UTC cycle, 4 phases × 90 min

### m-engine.js
- Included in: home.html
- `MEngine.process()` — session tracking, M actions
- `MEngine.getState()` — UI rendering data
- `MEngine.getRivalEncounter()` — fight API opponent (20% chance)

### confession-engine.js
- Included in: home.html, lab.html
- `ConfessionEngine.trigger(killer, dead, cause)` — shows modal
- `ConfessionEngine.getResurrectionStatus()` — token availability
- `ConfessionEngine.resurrectPet(index)` — bring back one dead pet

---

## 6. INTEGRATION POINTS

### home.html — The Hub (2,420 lines)
Everything connects through home.html. It includes all 4 engines and has:
- Active pet card with stats, XP, level, mood
- Pact partner display + feral warning
- Spirit bond count + equipped artifacts
- Genesis Mark badge
- Tide indicator (header)
- M's note trigger (bottom-left, subtle)
- Confession/resurrection link (hidden until earned)
- Black Market lantern (night-only)
- Dream indicator (new dreams)
- Bloodline deepened notification
- **Actions grid** (all buttons): Train, Mutate, Pit, Shrine, Prophecy, Rivals, Tides, Deep Tide, Bloodlines, Pact, Menagerie, Achievements, Genesis + hidden Confessions/M

### app.py — Allowed Island Pages
```python
island_pages = {
    "index", "home", "create", "kennel", "train", "lab", "pit",
    "graveyard", "profile", "leaderboard", "achievements", "onboarding",
    "dreams", "crimson", "rivals", "shrine", "artifacts", "prophecy",
    "menagerie", "deep-tide", "succession", "black-market", "tides",
    "pact", "genesis", "confessions"
}
```
Total: 27 pages.

### Fight API Usage
Pages that call `POST /api/v1/fight/s1`:
- train.html (AI opponents)
- pit.html (local PvP)
- rivals.html (NPC nemeses)
- prophecy.html (oracle prediction fights)
- deep-tide.html (expedition chambers)
- pact.html (indirectly, via feral state)

---

## 7. WHAT'S BLOCKED

All require Supabase (Victor's task — instructions on desktop):

| Phase | Feature | Why Blocked |
|-------|---------|-------------|
| 6B | Arena Oath | Social rivalries need shared DB |
| 6C | Scar Garden | Breeding needs shared DB |
| 7 | Global PvP | Async matchmaking needs shared DB |
| 7 | Auto-Arena | Cron job needs shared DB |
| 7 | Soul Premium | Stripe + user accounts |
| 7 | Live Matchmaking | WebSocket + shared state |

### Supabase Connection (Ready)
- `supabase-client.js` built and included
- `GET /api/v1/island/config` endpoint serves credentials from env vars
- All pages call `await initSupabase()` (falls back to localStorage if no credentials)
- SQL schema ready in `docs/SUPABASE_SETUP.md`
- Victor's instructions: `~/Desktop/SUPABASE_TODO_VICTOR.md` (4 steps, ~15 min)

---

## 8. HOW TO CONTINUE

### For Claude Code / Next Session:
1. Read this document for full context
2. Read `docs/ISLAND_ROADMAP.md` for task status
3. Remaining localStorage work: none (Phases 0-9 complete)
4. Next meaningful work: Supabase integration when Victor provides credentials

### For Claude in Browser:
1. The project is at `github.com/supervitek/moreau-arena-paper`
2. Side B lives in `web/static/island/`
3. ALL game logic is client-side JavaScript in HTML files
4. Pet data schema is documented above — ALWAYS use `pet.base_stats` not `pet.stats`
5. Fight API: `POST /api/v1/fight/s1` with `{agent1: {animal, stats}, agent2: {animal, stats}, games: 1}`

### Key Patterns:
- Every page includes standard nav (copied from home.html pattern)
- EMOJI_MAP constant defined in each page for 14 animals
- Achievement triggers: `checkAchievement('id')` (defined in achievements system)
- Dream triggers: include dreams-engine.js, call `generateDream(type, pet, extra)`
- Moreddit posts: push to `moreau_moreddit_feed` localStorage array
- Tide awareness: include tide-engine.js, call `TideEngine.getTideState()`
- M awareness: include m-engine.js, call `MEngine.process()` on page load

### Testing:
```bash
source ~/.zshrc && .venv/bin/python -m pytest tests/test_invariants.py
```
89 tests, all must pass. Tests only cover Side A (benchmark) — Side B is frontend-only.
