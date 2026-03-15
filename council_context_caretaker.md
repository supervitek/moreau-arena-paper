# Context for Round Table Council — Moreau Arena: The Caretaker & Next Steps

## What is Moreau Arena?

Moreau Arena is a browser-based game inspired by H.G. Wells' "The Island of Doctor Moreau." It has two sides:
- **Side A (Benchmark):** A frozen academic benchmark for AI agent evaluation
- **Side B (The Island):** A full creature-battling RPG built in vanilla HTML/JS with localStorage

## The Island — What Exists (10 Phases, ~44,000 lines)

### Core Systems (Phases 1-3)
- 14 animal species, 4 stats (HP/ATK/SPD/WIL), levels 1-10, XP progression
- Mutation tree: standard mutations at L3/L6/L9, 6 ultimate paths
- Forbidden Laboratory: 3 tiers of experimental mutations (Stable/Volatile/Forbidden), 49 mutations + 14 ultra-rares, side effects, instability → permanent pet death
- Training fights vs AI, local PvP (The Pit), global PvP with ELO (Arena)
- Achievements (32 total), Moreddit social feed, pet profiles (FBI dossier style)

### Deep Systems (Phases 4-5)
- **Dream System:** Pet dreams triggered by key events, 14 animal voices × 7 triggers
- **Corruption Path:** Dark mutations, corruption meter 0-100, Crimson Leaderboard for tainted pets
- **NPC Rivals:** 20 archetypes, 3 per player, 5-tier escalation
- **Scavenger's Shrine:** 36 artifacts, 3 equipment slots, hunt missions
- **Prophecy Machine:** Oracle predictions, essence betting, accuracy tracking

### Legacy & Social (Phase 6)
- **Menagerie:** Dead pet spirits buff living pets, bloodlines, epitaphs
- **Arena Oath:** Social rivalry covenants, 5-level escalation, Oathbreaker's Curse
- **Scar Garden:** Breeding system (living pet + dead donor), 12h incubation, genetic inheritance, family tree

### Deep Island (Phase 8)
- **Deep Tide:** Roguelike 7-chamber expedition, permadeath on failure
- **Succession:** Bloodline mastery across generations (Gen 10 = Progenitor Form)
- **Black Market:** Night-only (22:00-04:00), blind auctions, permanent stat sacrifice
- **Tidal Clock:** 6-hour real-time rhythm affecting all systems
- **The Pact:** Symbiotic pet binding, feral state on partner death
- **Player "M":** Phantom mirror player, 40 handwritten notes across 4 phases

### Endgame (Phase 9)
- **Genesis Protocol:** New Game+ prestige (0-5 marks), 30-second unskippable reset
- **Confession Booth:** Post-kill moral reflection, 3 paths, resurrection token at 20 confessions

## The Caretaker — Phase 10 (Just Built Today)

An AI zoo manager NPC with 12 subsystems across 8 JS files (~9,300 lines total):

### Core (caretaker-engine.js, 1941 lines)
- **Needs system:** 4 bars (hunger/health/morale/energy), real-time decay based on hours since last check
- **6 Actions:** Feed (+50 hunger), Heal (+30 health), Rest (+50 energy, 1hr lockout), Train (auto-fight), Motivate (+20 morale), AutoManage (premium stub)
- **41 contextual advice templates** + 52 motivational quotes
- **Overnight Training:** Simulated fights while player is away (3/5/7/10 rounds)
- **Diary + Trust System (0-10):** Caretaker logs decisions with personality. Player approves (+0.5 trust) or overrides (-1 trust). Trust 0 = Caretaker refuses. Trust 7+ = creative decisions. Trust 10 = unsanctioned mutations.
- **Mercy Clause:** When a pet is critically low (hunger=0 + health<20), player has 6 hours to sacrifice one pet to save another. Saved pet gets "Survivor's Guilt" mutation. 3+ debts = "Abomination" tag.
- **Feeding Ledger (Aleph):** 12 pages of lore unlocked by consecutive daily care. Page 6 reveals the "15th animal." Page 12 reveals the Caretaker IS Aleph.

### Extended Modules (6 standalone IIFE files, 4336 lines total)
- **Standing Orders (743 lines):** Programmable rules with drag-and-drop priority. "Feed when hunger < 30." Max 5 orders, conflict detection.
- **Caretaker's Price (576 lines):** Efficiency decay over time, XP tax at trust>7, mutation confiscation at trust>9, Workshop to combine confiscated mutations into 10 unique hybrids.
- **Caretaker Drift (782 lines):** Hidden 0-70 divergence score. Caretaker develops favorites, redistributes stats toward preferred pets, neglects others. Potential pet death at max drift. Recalibration costs trust.
- **Letters from the Caretaker (899 lines):** 20 evolving letters across 5 phases (curious→attached→possessive→fraying→gone). Each has gifts. Permanent dismiss: type "GOODBYE." Farewell easter egg appears 7 days later.
- **Sleep Dialect (835 lines):** 52-word constructed language. Dark overlay appears when returning after 6-24hr absence. Lexicon decoder book. Hidden message about Aleph.
- **Weight of Keeping (501 lines):** A 2x2 pixel appears on the profile page after 30 real days. Acrostic message spelling "YOU ARE M." Dev tools detection via MutationObserver.

## Architecture Constraints
- **localStorage only** — no server state for game logic (Supabase only for auth + global PvP)
- **Vanilla JS** — no frameworks, no build step, all IIFE modules
- **14 animal species** — bear, buffalo, boar, tiger, wolf, monkey, porcupine, scorpion, vulture, rhino, viper, fox, eagle, panther
- **Standalone pages** — each page is a full HTML file with inline CSS and scripts
