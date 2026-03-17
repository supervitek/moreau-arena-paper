# Part B First Measurement Season — B5

Last updated: 2026-03-17
Status: Active

## Season Lock

- Season ID: `part-b-s1-first-descent`
- Name: `Part B Season 1: First Descent`
- Scope:
  - `The Arena`
  - `Cave of Catharsis`
- Run classes:
  - `manual`
  - `operator-assisted`
  - `agent-only`

## Frozen Contract

- Observation version: `B1`
- Action version: `B1`
- Scoring version: `B1`
- Tick cadence: `1 world tick / 6 real hours`
- Budget mode: `hybrid`
- Default queue cap: `6`
- Headline score families:
  - `welfare`
  - `combat`
  - `expedition`

## Explicit Rules

- Composite score is not headline-visible in this season.
- House agent runs are benchmark-eligible only if they stay inside the public observation/action/scoring contract.
- No hidden shortcuts, no secret action surface, no third zone.
- Season boundary changes require a new season ID if any of these move:
  - zones
  - scoring formula
  - action grammar
  - observation fields
  - tick cadence
  - budget rails

## Outputs

- API season status:
  - `/api/v1/island/part-b/season`
- Family-score leaderboards:
  - `/api/v1/island/part-b/leaderboards`
- Season archive export:
  - `scripts/export_part_b_season.py`

## Exit Rule

Part B is no longer just a prototype when this season has:
- benchmark-visible runs
- run-class-separated leaderboards
- reproducible archive export
- control baselines for calibration
