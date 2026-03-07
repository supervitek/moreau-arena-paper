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
  - Rhino Bulwark Frame caps single-hit damage exceeding 18% max HP
  - Porcupine reflect during damage application
  - Ring mechanics (tick 30 start, 2% max HP/tick)
  - `run_match()` public API

- **Verified**: All 7 cross-animal matchups run correctly
