# Island Status Report — Moreau Arena
**Generated:** 2026-03-10
**Scope:** All user-facing ("Island") features — Pets, Lore, Social, Forbidden Lab

---

## 1. PETS SYSTEM

### 1.1 Backend: `pets/mutation_tree.py`

**Core Mutation Tree (standard path, NOT lab):**
- **Level 3** — 3 mutations: `blood_rage` (+2 ATK/-1 SPD), `thick_hide` (+2 HP/-1 ATK), `quick_feet` (+2 SPD/-1 HP)
- **Level 6** — 6 mutations (2 per L3 parent): `frenzy`, `intimidate`, `regeneration`, `fortress`, `ambush`, `evasion`
- **Level 9** — 6 mutations (1 per L6 parent, "Destiny"): `berserker`, `warlord`, `immortal`, `juggernaut`, `phantom_strike`, `ghost`
- **Total standard mutations:** 15 (3 + 6 + 6)
- **Branching:** L3 choice → unlocks 2 L6 options → each unlocks 1 L9. Six unique paths total.

**XP System:**
- Win: +30 XP, Loss: +10 XP
- Level thresholds: {1:0, 2:50, 3:100, 4:150, 5:200, 6:300, 7:400, 8:500, 9:600, 10:750}
- Stat total: 20 points across 4 stats (HP/ATK/SPD/WIL), min 1, max 16 each

**14 Valid Animals:** bear, buffalo, boar, tiger, wolf, monkey, porcupine, scorpion, vulture, rhino, viper, fox, eagle, panther

**Key Functions:** `create_pet()`, `add_xp()`, `get_available_mutations()`, `apply_mutation()`, `get_effective_stats()`, `get_mutation_tree()`, `calculate_mood()`, `xp_for_next_level()`

**Tests:** `pets/mutation_tree_test.py` — **22 tests, all passing**

---

### 1.2 Backend: `pets/soul.py`

AI personality engine using Claude Haiku (100 tokens, temp 0.9).

**14 Animal Personalities** (sourced from `FIGHTER_LORE.md`):

| Animal | Personality | Voice |
|--------|-----------|-------|
| fox | Con artist (Atlantic City) | Slick, amused, conspiratorial |
| tiger | Wetwork operative | Terse, clinical, flat |
| porcupine | Paranoid sysadmin | Whispered, urgent, over-detailed |
| rhino | Retired Sergeant Major | LOUD, clipped, imperative |
| eagle | Banking heir | Drawling, dismissive, withering |
| wolf | Published poet | Earnest, lyrical, yearning |
| scorpion | Noir private investigator | World-weary, sardonic |
| buffalo | Retired Marine | Quiet, steady, paternal |
| monkey | Birthday entertainer | LOUD, manic, self-narrating |
| bear | Head librarian | Gentle-then-VIOLENT |
| viper | Intelligence operative | Low, intimate, double-edged |
| panther | Art school dropout | Flat, detached, self-deprecating |
| boar | Construction foreman | Loud, confused, indignant |
| vulture | Buddhist monk | Serene, unhurried, paradoxical |

**6 Context Types:** `idle`, `post_fight_win`, `post_fight_loss`, `pre_mutation`, `mutation_reaction`, `rival_encountered`

**7 Mood States:** happy, angry, philosophical, excited, tired, confident, furious

**API Endpoint:** `POST /api/v1/pets/soul` — takes pet + context, returns in-character dialogue + mood

**Fallback:** Static message when no API key: `"* {name} stares at you silently. The soul awaits awakening... *"`

**Tests:** `pets/soul_test.py` — **10 tests, all passing**

---

### 1.3 Frontend Pages (`web/static/pets/`)

**7 HTML pages total:**

| Page | Path | Purpose | Size |
|------|------|---------|------|
| **Creation** | `/pets/index.html` | 5-step pet creation wizard (animal → name → stats → confirm) | 35KB |
| **Hub** | `/pets/hub.html` | "The Kennels" — multi-pet selector, max 6 pets, deceased styling | 17KB |
| **Home** | `/pets/home.html` | Dashboard — stats, soul window, actions, fight history, lab mutations | 25KB |
| **Train** | `/pets/train.html` | Fight AI (Easy/Medium/Hard), HP animation, XP gain, soul reaction | 29KB |
| **Mutate** | `/pets/mutate.html` | Standard mutation tree (L3/L6/L9 branching cards) | 33KB |
| **Profile** | `/pets/profile.html` | "Subject Dossier" — shareable stats, mutations, fight history | 49KB |
| **Forbidden Lab** | `/pets/forbidden-lab.html` | Secret lab — gacha rolls, instability, death system, mutation map | 109KB |

**Access path:** Hub → Home → Train/Mutate/Profile. Forbidden Lab is secret (triple-click in mutate intro).

---

### 1.4 localStorage Schema

| Key | Type | Structure |
|-----|------|-----------|
| `moreau_pets` | Array (max 6) | `[{name, animal, level, xp, base_stats:{hp,atk,spd,wil}, mutations:[], fights:[], mood, created_at, lab_mutations:{L3,L6,L9}, side_effects:[], instability, scars, lab_log:[], deceased, mercy_used}]` |
| `moreau_active_pet` | String (index) | `"0"` through `"5"` |
| `moreau_codex` | Object | `{mutation_id: true, ...}` — tracks all discovered lab mutations |
| `moreau_pet` | Object (LEGACY) | Old single-pet format, auto-migrated on load |
| `moreau_ultra_rare_post` | Object | `{animal, mutation, timestamp}` — last ultra-rare roll for social |

**Critical pet data pattern:** Stats are in `pet.base_stats` (NOT `pet.stats`). Always read as `pet.base_stats || pet.stats || {}`.

---

## 2. FORBIDDEN LABORATORY

### 2.1 Three Tiers — Mutation Pools

**Tier 1 — Stable** (10 mutations, 0% side effect, 0% ultra-rare):
1. Tough Skin (+2 HP)
2. Sharp Claws (+1 ATK)
3. Quick Feet (+1 SPD)
4. Iron Will (+1 WIL)
5. Keen Eyes (+3% accuracy)
6. Thick Hide (+5% dmg reduction)
7. Swift Reflexes (+3% dodge)
8. Battle Scars (+3 HP)
9. Predator Instinct (+2% crit)
10. Survival Instinct (+1 HP, +1 WIL)

**Tier 2 — Volatile** (15 mutations, 35% side effect, 0% ultra-rare):
1. Fleet Tendons (+3 SPD, +5% dodge)
2. Barbed Blood (15% reflect)
3. Adrenaline Surge (+20% ATK first 3 ticks)
4. Shadow Step (+8% dodge, +2 SPD)
5. Venom Glands (3-tick poison)
6. Berserker Gene (+4 ATK, -1 WIL)
7. Regeneration (2% max HP/tick)
8. Hardened Bones (+4 HP, +10% dmg red)
9. Feral Senses (+5% crit, +3% accuracy)
10. Ambush Wiring (+30% first-strike)
11. Symbiotic Armor (+3 HP, +1 ATK)
12. Neural Boost (+3 WIL, +10% ability power)
13. Kinetic Absorber (10% negate hit)
14. Bloodlust (+2% ATK per hit, stacks to 5)
15. Territorial Rage (+15% ATK on home terrain)

**Tier 3 — Forbidden** (10 mutations, 70% side effect, 2% ultra-rare):
1. Apex Predator (+5 ATK, +3 SPD)
2. Unkillable (survive lethal at 1 HP)
3. Phase Shift (20% dodge any attack)
4. Doom Bloom (every 4th tick: buff OR hex, 50/50)
5. Chimera Heart (gain random trait from another species)
6. Gene Overload (all stats +2, 10% lose turn)
7. Perfect Form (+2 to all stats)
8. Unstoppable Force (ignore defenses 2 ticks)
9. Shadow Clone (first attack hits twice)
10. Evolution's Edge (+3 highest stat, +1 lowest)

**Total lab mutation pool: 35 base + 14 ultra-rares = 49**

---

### 2.2 Side Effects — All Implemented

**5 categories, 26 total effects:**

| Category | Weight | Count | Status |
|----------|--------|-------|--------|
| Symbiotic | 35% | 8 items | Implemented |
| Cosmetic | 25% | 8 items | Implemented |
| Corruption | 20% | 5 items | Implemented |
| Cascade | 15% | 1 item (free T1 bonus roll) | Implemented |
| Personality | 5% | 4 items (Aggressive/Serene/Manic/Ancient Drift) | Implemented |

**Note:** Side effects are stored on pet but do NOT mechanically affect fights yet (no fight engine integration). They are recorded and displayed.

---

### 2.3 Ultra-Rares — All 14 Implemented

All 14 animal-specific ultra-rares are in the ULTRA_RARES pool. They roll at 2% chance from Tier 3 Forbidden. Each has unique name, animal tag, and description. Getting one triggers:
- Confetti animation (80 particles)
- Screen shake
- Dedicated gold overlay with "Ultra-Rare" flash
- Saved to `moreau_ultra_rare_post` in localStorage

| # | Animal | Name | Effect |
|---|--------|------|--------|
| 1 | Fox | Moreau's Briefcase | Copy opponent's passive |
| 2 | Tiger | Echolocation | Nullify accuracy penalties, double dodge |
| 3 | Bear | Ursine Apotheosis | <30% HP: all stats +25% for 3 ticks |
| 4 | Wolf | Pack Echo | Clone last successful ability |
| 5 | Scorpion | Neurotoxin Cascade | DOTs spread to adjacent hexes |
| 6 | Eagle | Stratospheric Dive | First strike from max range = 3x |
| 7 | Porcupine | Living Fortress | Reflect 100% damage 1 tick (10-tick CD) |
| 8 | Rhino | Tectonic Charge | Movement creates blocking rubble |
| 9 | Viper | Hemotoxin Bloom | Poison stacks → healing on kill |
| 10 | Vulture | Carrion Authority | +5% all stats per dead unit |
| 11 | Monkey | Chaos Theory | Randomize 1 opponent stat per tick |
| 12 | Buffalo | Immovable Object | Immune to displacement/knockback |
| 13 | Panther | Void Step | Teleport behind target before attack |
| 14 | Boar | Blood Frenzy | +3% ATK per hit (stacks infinitely) |

---

### 2.4 Cascade — Working

When a side effect roll lands on Cascade (15% of side effect rolls):
- A free Tier 1 bonus mutation is rolled
- Both the main mutation AND the cascade bonus are offered
- Cascade result is discovered in codex
- Stats from cascade are applied if player accepts
- Special "CASCADE!" visual with flash styling

**Limitation:** Design doc says cascade can chain (max 2), but current implementation does NOT chain — cascade gives exactly one free T1 roll.

---

### 2.5 Codex — Two Implementations

**Grid Codex (tab "Codex"):**
- Grid layout by tier (Stable/Volatile/Forbidden/Ultra-Rare)
- Tiles: undiscovered ("???", dim), discovered (tier-colored), equipped (gold pulse)
- Counter: "X / 49 discovered"
- Stored in `moreau_codex` localStorage key

**Radial Mutation Map (tab "Mutation Map"):**
- SVG radial web visualization, 4 concentric rings
- Ring 1 (r=75): 10 Stable nodes (green)
- Ring 2 (r=138): 15 Volatile nodes (orange)
- Ring 3 (r=195): 10 Forbidden nodes (red)
- Ring 4 (r=232): 14 Ultra-Rare nodes (gold)
- Undiscovered = dim dot, Discovered = colored, Equipped = pulsing gold with label
- Connection lines from center (pet) to each node
- Click node → info panel shows details
- Interactive legend below

---

### 2.6 Additional Forbidden Lab Systems

**Instability System (0-100%):**
- Gain per roll: Stable +4, Volatile +9, Forbidden +16, plus +2 per existing mutation
- Zones: Safe (0-39), Caution (40-59), Danger (60-79), Critical (80+)
- Death chance: 0% below 40, scales up to 85% at 100
- Ambient visual escalation: background darkens, biohazard pulses at high instability

**Death System:**
- Death roll happens AFTER instability applied, BEFORE mutation reveal
- First death is prevented (one-time mercy, `pet.mercy_used`)
- On death: EKG flatline animation, Dr. Moreau research notes (6 variants), permanent `pet.deceased = true`
- Deceased pets: greyed out in hub, redirect from home, can't enter lab

**Scar System:**
- Stabilize button: -20 instability, +1 scar (if inst >= 40)
- Max 5 scars, each raises instability floor by +3
- Visual: 5 scar dots displayed

**Experiment Log:**
- Tab "Research Notes" — styled as Dr. Moreau's research log
- Max 30 entries per pet, stored in `pet.lab_log[]`
- Entries for: rolls (applied/discarded), stabilizations, deaths
- Shows tier dot, mutation name, side effect, instability, relative timestamp

**Confirmation Modal:**
- Pre-roll modal shows exact mortality risk % and instability change
- Button text changes to "I Accept the Risk" when death chance > 20%

---

## 3. LORE & SOCIAL

### 3.1 Fighter Lore — `season1/FIGHTER_LORE.md`

**14 characters, each with 7-8 sections:**
1. Subject Profile (background/pre-Island)
2. Island Arrival (how they got there)
3. Transformation (relationship with abilities)
4. Fighting Philosophy (signature quote)
5. Rival (worst matchup + context)
6. Dream (personal motivation)
7. Voice Style (personality markers)
8. Sample Quote (in-character demo)

**Rankings by win rate:** Fox (57.06%, #1) → Vulture (43.91%, #14)

---

### 3.2 Fighter Dossier Pages — `web/static/fighters/`

**14 individual HTML pages** (one per animal):
bear.html, boar.html, buffalo.html, eagle.html, fox.html, monkey.html, panther.html, porcupine.html, rhino.html, scorpion.html, tiger.html, viper.html, vulture.html, wolf.html

**Each page contains:** Fighter header, profile, stats table (role/WR/threat), abilities with proc rates, best & worst matchup, psychology section, signal transmission lore snippet, navigation to adjacent fighters.

**Grid page:** `web/static/s1-fighters.html` — 3-column card grid linking to all 14 dossier pages.

---

### 3.3 The Moreddit — `web/static/moreddit.html`

**21 posts from all 14 characters**, plus 30+ comments.

**Character usernames:**
| Character | Username |
|-----------|----------|
| Fox | u/OutfoxedAgain, u/TrickedByTricks |
| Tiger | u/OnePerfectStrike |
| Bear | u/NotMyChoice |
| Buffalo | u/ToughAsNails |
| Boar | u/JUSTCHARGE |
| Wolf | u/MoonlitHowl |
| Monkey | u/ChaosMonke |
| Porcupine | u/QuillAndAlert |
| Scorpion | u/NoirDetective |
| Vulture | u/PatientWings |
| Rhino | u/SgtBulwark |
| Viper | u/SilkAndVenom |
| Eagle | u/LordOfTheSkies |
| Panther | u/xX_ShadowFade_Xx |

**Subreddits:** m/ArenaChat, m/ArenaDrill, m/ArenaPolls, m/FightLogs, m/MorningReport, m/Poetry

**Post types:** Rants, poetry, conspiracy theories, noir narratives, polls, 3AM confessions, fight commentary, drill reports, haiku

---

### 3.4 Lore → Soul Connection

```
FIGHTER_LORE.md (14 dossiers, ~8 sections each)
    ↓ personality, voice, sample fields extracted
pets/soul.py (ANIMAL_PERSONALITIES dict — 14 entries)
    ↓ Claude Haiku generates in-character dialogue
POST /api/v1/pets/soul (API endpoint)
    ↓ called by frontend JS
web/static/pets/home.html (soul window with typewriter animation)
web/static/pets/train.html (post-fight soul reaction)
web/static/pets/mutate.html (pre/post mutation thoughts)
```

Also feeds into:
- `web/static/s1-fighters.html` — role + quote per card
- `web/static/fighters/*.html` — full dossier pages
- `web/static/moreddit.html` — character voices in posts/comments

---

## 4. DESIGN DOC STATUS — `docs/MUTATION_GACHA_DESIGN.md`

### Phase 1 (MVP) — Mostly Done

| Feature | Status | Notes |
|---------|--------|-------|
| 3-tier system with mutation pools | **DONE** | 10 + 15 + 10 mutations across Stable/Volatile/Forbidden |
| Side effect taxonomy (all 5 categories) | **DONE** | Symbiotic (8), Cosmetic (8), Corruption (5), Cascade (1), Personality (4) |
| Mutation Codex UI | **DONE** | Grid codex + radial mutation map, both functional |
| Visual marks for Tier 3 mutations | **PARTIAL** | Tier 3 stored on pet, shown in hub/home/profile. No unique silhouette/particle effects in fight view |

### Phase 2 (Retention) — Not Started

| Feature | Status | Notes |
|---------|--------|-------|
| Daily free roll system | **NOT DONE** | No daily limit or free roll mechanic exists |
| Pity timer / Research Bar | **NOT DONE** | No pity counter or near-miss display |
| Stabilizer item | **NOT DONE** | Stabilize button exists but it's the scar system, not the "lock slot" Stabilizer from design |
| "Most Mutated" leaderboard | **NOT DONE** | No backend/leaderboard for mutation counts |

### Phase 3 (Endgame) — Partially Done

| Feature | Status | Notes |
|---------|--------|-------|
| Ultra-rare mutations (14 animal-specific) | **DONE** | All 14 in pool, 2% chance from Tier 3 |
| Secret Synergies / Apex Forms | **NOT DONE** | No combo detection, no Apex Form system |
| Seasonal resets + Hall of Fame | **NOT DONE** | No seasons/retirement system |
| PvP point budget system | **NOT DONE** | No mutation cost budgets for PvP |

### Additional Features Built (beyond design doc)

| Feature | Status |
|---------|--------|
| Instability / death system | **DONE** — not in original design doc |
| Scar system (stabilization cost) | **DONE** — not in original design doc |
| One-time mercy mechanic | **DONE** — not in original design doc |
| Experiment log (Research Notes) | **DONE** — not in original design doc |
| Confirmation modal with exact mortality % | **DONE** — not in original design doc |
| Deceased pet handling across all pages | **DONE** — not in original design doc |
| Radial mutation map visualization | **DONE** — not in original design doc |
| Ambient visual escalation | **DONE** — not in original design doc |

---

## 5. CONCRETE TODO LIST

### High Priority (gameplay impact)
- [ ] **Slot replacement on reroll** — design doc says rerolling a slot replaces both mutation and side effect; current implementation just overwrites the same slot key but doesn't handle side effect replacement properly
- [ ] **Cascade chaining** — design doc allows chain of 2; current implementation gives exactly 1 free T1
- [ ] **Fight engine integration** — lab mutations and side effects are stored but don't affect actual fight calculations in `run_challenge.py`
- [ ] **Visual marks in fights** — Tier 3 / ultra-rare mutations should show particles/effects during fights

### Medium Priority (retention)
- [ ] **Daily free roll** — 1 free Tier 2 roll per day (earned by playing)
- [ ] **Pity timer** — after 15 Tier 2 rolls without rare result, guarantee strong-pool
- [ ] **Near-miss display** — "You were 1 away from Echolocation"
- [ ] **Stabilizer item** — lock a mutation slot (earn via 5 PvP wins or 10-win AI streak)
- [ ] **Stabilize cooldown** — currently instant, no cooldown between stabilizations
- [ ] **Personality Drift soul integration** — Personality side effects are stored but don't actually change the soul.py voice used for dialogue

### Low Priority (endgame / social)
- [ ] **Apex Forms** — define mutation+side effect combos that trigger named transformations
- [ ] **Apex Form community discovery** — server-wide announcements
- [ ] **Most Mutated leaderboard** — needs backend persistence (currently all localStorage)
- [ ] **Seasonal resets** — pet retirement to Hall of Fame
- [ ] **PvP mutation budget** — point costs per mutation, cap for ranked
- [ ] **Cosmetic visibility in PvP** — show opponent's cosmetic mutations
- [ ] **Mutation loadout sharing** — screenshot/social export
- [ ] **Backend persistence** — migrate from localStorage to server-side storage (required for leaderboards, seasons, social features)

### Polish
- [ ] **Ultra-rare cosmetic visibility** — unique silhouette/particle effects (design doc: "always cosmetically visible")
- [ ] **Codex bitfield compression** — current JSON object is inefficient for 49 boolean flags
- [ ] **Visual mutation map: fog of war** — undiscovered tiers could be visually obscured
- [ ] **Collapsible experiment log** — `<details>` element alternative to tab

---

## 6. SUMMARY COUNTS

| Component | Count |
|-----------|-------|
| Animals | 14 |
| Standard mutations (mutation_tree.py) | 15 (3 L3 + 6 L6 + 6 L9) |
| Lab mutations (forbidden-lab.html) | 49 (10 T1 + 15 T2 + 10 T3 + 14 ultra) |
| Side effects | 26 (8+8+5+1+4) |
| Soul personalities | 14 |
| Soul contexts | 6 |
| Pet pages (HTML) | 7 |
| Fighter dossier pages | 14 |
| Moreddit posts | 21 |
| Moreddit characters with posts | 14/14 |
| Backend tests passing | 32 (22 + 10) |
| localStorage keys used | 5 |
| API endpoints (pets) | 2 (soul + fight) |
| Design doc phases done | ~1.5 of 3 |
