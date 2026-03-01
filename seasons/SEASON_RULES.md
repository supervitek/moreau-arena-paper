# Season Rules -- Moreau Arena

## Core Principle

The base configuration (`season_0_base.json`) is permanently frozen. All balance changes happen through seasonal patches applied on top of the base.

## How Seasons Work

1. **Within a season:** The config is FROZEN. No mid-season balance changes.
2. **Between seasons:** The patch generator proposes adjustments based on accumulated win-rate data.
3. **Patch review:** Proposed changes are reviewed and approved before being saved as `season_N_patch.json`.
4. **Core suite:** Always runs on `season_0_base.json` (the frozen core). Core results are never affected by seasonal patches.
5. **Seasonal suite:** Runs on the patched config for that season.

## Patch Generator Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| EMA alpha | 0.15 | Smoothing factor for win-rate calculation |
| Adjustment beta | 0.03 | Maximum proc-rate change per season |
| Proc rate floor | 0.025 | Minimum allowed proc rate |
| Proc rate ceiling | 0.055 | Maximum allowed proc rate |
| Target win rate | 0.55 | Animals above this are nerfed |
| Lower bound | 0.45 | Animals below this are buffed |

## What Can Change Between Seasons

- Ability proc rates (within floor/ceiling bounds)
- New animals may be added (existing animals are never removed)

## What NEVER Changes

- Stat formulas (HP, ATK, SPD, WIL calculations)
- Combat mechanics (tick order, ring timing, damage formula)
- Grid dimensions (8x8)
- Stat budget (20 points)
- Series format (best-of-7)
- Base config hash

## Season History

| Season | Config | Status | Notes |
|--------|--------|--------|-------|
| 0 | `season_0_base.json` | ACTIVE | Frozen core, identical to `config.json` |
