# Season Rules — Moreau Arena

## Overview

Seasons provide a structured cadence for balance updates without invalidating
historical data.  Each season freezes a config snapshot; changes happen only
between seasons.

## Principles

1. **Within a season the config is FROZEN.**  No mid-season balance changes.
2. **Between seasons** `patch_generator.py` proposes adjustments based on
   observed win-rate EMA.  Changes are reviewed, approved, and saved as
   `season_N_patch.json`.
3. **Core suite always runs on `season_0_base.json`** — it never changes.
   This ensures longitudinal comparability.
4. **Season suite runs on `season_N_patch.json`** — results are tagged with the
   season number and cannot be compared across seasons in the same leaderboard.

## Directory Layout

```
seasons/
├── season_0_base.json      # Exact copy of the frozen Core config
├── season_1_patch.json     # First balance patch (generated, reviewed)
├── season_N_patch.json     # Subsequent patches
├── patch_generator.py      # EMA-based balance proposer
└── SEASON_RULES.md         # This file
```

## Patch Generation Process

1. **Collect data.**  Run a full tournament on the current season config.
2. **Compute EMA win rates.**  `patch_generator.py` reads the JSONL results
   and applies exponential moving average smoothing (alpha = 0.15).
3. **Propose adjustments.**  Animals whose EMA win rate deviates more than 1 pp
   from 50 % receive proc-rate changes of ±beta (beta = 0.03).
   - Over-performing animals → proc rates decreased
   - Under-performing animals → proc rates increased
   - Rates are clamped to [0.025, 0.055]
4. **Review.**  A human reviews the proposed patch.  Adjustments may be
   accepted, modified, or rejected.
5. **Save.**  The approved patch is saved as `season_N_patch.json`.
6. **Announce.**  The new season begins; the previous season's leaderboard is
   archived.

### Running the generator

```bash
python -m seasons.patch_generator \
    --results data/tournament_002/results.jsonl \
    --base seasons/season_0_base.json \
    --out seasons/season_1_patch.json \
    --alpha 0.15 \
    --beta 0.03 \
    --season 1
```

## What Can Change Between Seasons

- Ability proc rates (within [0.025, 0.055])
- Ability coefficient tuning (duration, damage multipliers)

## What NEVER Changes

These parameters are locked to Core and are **not** subject to seasonal
adjustment.  Changing any of them requires a new Core snapshot (v2.0):

- Damage / HP / dodge formulas
- Ring behaviour (tick, damage, size)
- Turn order / initiative system
- Grid size (8×8)
- Stat budget (20 points)
- Series format (best-of-7)

## Leaderboard Isolation

- Each season has its own leaderboard.
- Rankings from Season N are never merged with Season M.
- The Core leaderboard (season 0) persists across all seasons for
  longitudinal comparison.

## Versioning

| Field | Example | Meaning |
|-------|---------|---------|
| `meta.version` | `MOREAU_SEASON_1` | Season identifier |
| `meta.base_version` | `MOREAU_CORE_v1` | Core snapshot this season derives from |
| `meta.season` | `1` | Integer season number |
