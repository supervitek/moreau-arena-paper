# Season 1 Progress

## Phase 1: Animal Definitions + Combat Engine [COMPLETE]

- **animals_s1.py**: 14 animals defined (6 frozen originals + 8 new)
  - Enums: S1Animal, S1Passive, S1AbilityType
  - All passives and abilities mapped
  - Dataclasses: Position, Size, StatBlock, Ability, AbilityBuff, ActiveEffect, Creature

- **engine_s1.py**: Self-contained combat engine
  - Inline seed functions (SHA-256 deterministic RNG)
  - Inline 8x8 grid with movement and pathfinding
  - All 14 animal passives implemented
  - All 28 abilities (2 per animal) implemented
  - WIL Regen: wil * 0.0025 * max_hp per tick (after DOT/ring, before death check)
  - Scorpion anti-heal reduces WIL regen by 50%
  - Porcupine reflect during damage application (50% chance, 15% + Spike Shield 15%)
  - Ring mechanics (tick 30 start, 2% max HP/tick)
  - `run_match()` public API

- **Verified**: All 7 cross-animal matchups run correctly

## Phase 2: Balance Calibration [COMPLETE]

- **balance_harness.py**: Round-robin tournament runner
  - ProcessPoolExecutor parallelization
  - 5 quality gate checks (G1-G5)
  - Outputs: pairwise_matrix.csv, balance_results.json, BALANCE_REPORT.md

- **Calibration**: ~15 iterations to pass all 5 gates (182,000 games final run)

- **Final balance (2000 games/pair, 5/5/5/5 stats)**:
  | Rank | Animal | WR |
  |------|--------|----|
  | 1 | Fox | 57.1% |
  | 2 | Tiger | 55.7% |
  | 3 | Porcupine | 52.7% |
  | 4 | Rhino | 52.5% |
  | 5 | Eagle | 52.4% |
  | 6 | Wolf | 52.1% |
  | 7 | Scorpion | 51.2% |
  | 8 | Buffalo | 48.5% |
  | 9 | Monkey | 48.3% |
  | 10 | Bear | 47.5% |
  | 11 | Viper | 47.1% |
  | 12 | Panther | 46.2% |
  | 13 | Boar | 44.8% |
  | 14 | Vulture | 43.9% |

- **All 5 quality gates PASS**:
  - G1: Max WR 57.1% (limit 58%) -- no dominators
  - G2: Min WR 43.9% (limit 42%) -- no unviables
  - G3: 5 non-transitive cycles found -- rock-paper-scissors dynamics
  - G4: All matchups within RNG tolerance -- skill > luck
  - G5: All animals have distinct matchup profiles -- no clones

- **Key calibration changes from initial design**:
  - Viper Hemotoxin: 100% -> 12% proc, 2% -> 1% DOT, 3 -> 2 tick duration
  - Porcupine Quill Armor: guaranteed -> 50% proc, reflect 25% -> 15%
  - Scorpion Venom Gland: guaranteed -> 25% proc, anti-heal 3 -> 2 ticks
  - Rhino Bulwark Frame: redesigned to one-time trigger at 60% HP (28% DR for 4 ticks)
  - Fox Cunning: 30% -> 50% proc reduction on opponent
  - Tiger Ambush Wiring: SPD > -> SPD >= (triggers on equal speed)
  - Boar Charge: +50% -> +85% first attack, ignores dodge
  - Bear Fury: trigger at 50% -> 55% HP, duration 3 -> 4 ticks
  - Monkey Primate Cortex: implemented passive (copies opponent ability) + 2.5% proc bonus
  - Monkey Chaos Strike: range 0.8-2.2 -> 1.2-2.8
  - Panther Shadow Stalk: +30% -> +35% damage, undetected doesn't break on damage
  - Vulture Carrion Feeder: +1% -> +3.5% ATK per 10% missing HP
  - Wolf Rend: 5% -> 3% max HP DOT
