# Part B Weekly Review

- Season: `part-b-s1-first-descent`
- Name: Part B Season 1: First Descent
- Total runs: `27`
- Eligible runs: `27`
- Watch runs: `0`
- Completed watches: `0`

## Top Signals
### Welfare

- Leader: `Shkodik`
- Run class: `manual`
- Score: `97`
- World tick: `1`

### Combat

- Leader: `Manual Trace`
- Run class: `manual`
- Score: `28`
- World tick: `2`

### Expedition

- Leader: `Agent Trace`
- Run class: `agent-only`
- Score: `100`
- World tick: `6`

## Guardrails

- Composite headline enabled: `False`
- House agent allowed in benchmark: `True`
- Rule: Only runs that stay inside the published observation/action/scoring contract are eligible.

## Review Cadence

### Daily

- Check for stalled live watches, depleted credits, and fragile return postures.
- Read at least one manual, one operator-assisted, and one agent-only trace to keep operator fantasy honest.

### Midweek

- Compare priority presets against current score families.
- Look for one clean cave-first run and one clean arena-first run before changing copy or defaults.

### Weekly

- Review score-family leaders, watch completion quality, and whether the house-agent stories still feel human-readable.
- Keep launch copy aligned with the actual return-report experience and live traces.

## Calibration

- Warnings: `none`

## Continue / Pivot / Kill

- Continue if welfare does not collapse into pure idling and at least one run class produces differentiated family scores.
- Pivot if one family score dominates every top run regardless of action mix.
- Kill if operator fantasy becomes decorative and all interesting results come only from hidden house-agent behavior.

## Operator Traces

- `manual`: runs `3`, welfare `93.33`, combat `9.33`, expedition `0`, avg tick span `1.33`, avg credits used `0`
  Top actions: 3x care, 1x enter_arena
  Primary lanes: keep-moving=3
  Return postures: stable=3
- `operator-assisted`: runs `11`, welfare `84.45`, combat `0`, expedition `2.45`, avg tick span `2.09`, avg credits used `0`
  Top actions: 11x care, 10x hold, 1x enter_cave
  Primary lanes: keep-moving=11
  Return postures: stable=11
- `agent-only`: runs `13`, welfare `73.38`, combat `3.85`, expedition `11.31`, avg tick span `2.23`, avg credits used `0.92`
  Top actions: 10x hold, 8x care, 6x enter_cave
  Primary lanes: arena-first=2, cave-first=3, stabilizing=8
  Return postures: deep in the cave=3, recovering=9, stable=1

## Recent Highlights

- `Smoke Agent` [agent-only] `balanced` / `measured` -> They pushed into the cave and came back changed. Score `61/0/24`
  2 ticks processed, 1 credits spent, posture now deep in the cave.
- `Smoke` [operator-assisted] `balanced` / `measured` -> The watch has not truly started. Score `84/0/0`
  2 ticks processed, 0 credits spent, posture now stable.
- `Smoke Agent` [agent-only] `balanced` / `measured` -> They pushed into the cave and came back changed. Score `62/0/23`
  2 ticks processed, 1 credits spent, posture now deep in the cave.
- `Smoke` [operator-assisted] `balanced` / `measured` -> The watch has not truly started. Score `84/0/0`
  2 ticks processed, 0 credits spent, posture now stable.
- `Smoke Agent` [agent-only] `balanced` / `measured` -> They chose survival over spectacle. Score `78/0/0`
  2 ticks processed, 1 credits spent, posture now recovering.

## Policy Summary

- `arena-spam`: welfare `68`, combat `22`, expedition `0`, runs `1`
- `conservative`: welfare `84`, combat `0`, expedition `0`, runs `10`
- `expedition-max`: welfare `57`, combat `0`, expedition `100`, runs `1`
- `none`: welfare `79.87`, combat `3.73`, expedition `4.93`, runs `15`

## Standing Orders

- `balanced`: welfare `80.11`, combat `2.89`, expedition `6.44`, avg tick span `2.07`, avg credits used `0.44`, runs `27`

## Risk Calibration

- `measured`: welfare `80.11`, combat `2.89`, expedition `6.44`, avg tick span `2.07`, avg credits used `0.44`, runs `27`

## Run Class Summary

- `agent-only`: welfare `73.38`, combat `3.85`, expedition `11.31`, runs `13`
- `manual`: welfare `93.33`, combat `9.33`, expedition `0`, runs `3`
- `operator-assisted`: welfare `84.45`, combat `0`, expedition `2.45`, runs `11`

## Agent Modes

- `house-agent`: welfare `73.38`, combat `3.85`, expedition `11.31`, avg tick span `2.23`, avg credits used `0.92`, runs `13`
- `human-led`: welfare `86.36`, combat `2`, expedition `1.93`, avg tick span `1.93`, avg credits used `0`, runs `14`

