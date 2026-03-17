# Part B Weekly Review

- Season: `part-b-s1-first-descent`
- Name: Part B Season 1: First Descent
- Total runs: `12`
- Eligible runs: `12`

## Top Signals
### Welfare

- Leader: `Caremax Baseline R2`
- Run class: `agent-only`
- Score: `100`
- World tick: `12`

### Combat

- Leader: `Greedy Baseline R1`
- Run class: `agent-only`
- Score: `33`
- World tick: `10`

### Expedition

- Leader: `Expedition-Max Baseline R2`
- Run class: `agent-only`
- Score: `100`
- World tick: `12`

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

- `arena-spam`: welfare `0`, combat `11`, expedition `0`, runs `2`
- `caremax`: welfare `100`, combat `0`, expedition `0`, runs `2`
- `conservative`: welfare `0`, combat `0`, expedition `0`, runs `2`
- `expedition-max`: welfare `68.5`, combat `0`, expedition `100`, runs `2`
- `greedy`: welfare `0`, combat `19.5`, expedition `89`, runs `2`
- `random`: welfare `37`, combat `0`, expedition `48.5`, runs `2`

