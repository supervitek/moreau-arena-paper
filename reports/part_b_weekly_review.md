# Part B Weekly Review

- Season: `part-b-s1-first-descent`
- Name: Part B Season 1: First Descent
- Total runs: `13`
- Eligible runs: `13`

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

## Calibration

- Warnings: `none`

## Continue / Pivot / Kill

- Continue if welfare does not collapse into pure idling and at least one run class produces differentiated family scores.
- Pivot if one family score dominates every top run regardless of action mix.
- Kill if operator fantasy becomes decorative and all interesting results come only from hidden house-agent behavior.

## Policy Summary

- `arena-spam`: welfare `68`, combat `22`, expedition `0`, runs `1`
- `conservative`: welfare `84`, combat `0`, expedition `0`, runs `3`
- `expedition-max`: welfare `57`, combat `0`, expedition `100`, runs `1`
- `none`: welfare `85.62`, combat `7`, expedition `3.38`, runs `8`

## Run Class Summary

- `agent-only`: welfare `73.5`, combat `8.33`, expedition `16.67`, runs `6`
- `manual`: welfare `93.33`, combat `9.33`, expedition `0`, runs `3`
- `operator-assisted`: welfare `85.25`, combat `0`, expedition `6.75`, runs `4`

