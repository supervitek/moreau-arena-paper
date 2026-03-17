# Part B Weekly Review

- Season: `part-b-s1-first-descent`
- Name: Part B Season 1: First Descent
- Total runs: `3`
- Eligible runs: `3`

## Top Signals
### Welfare

- Leader: `Random Baseline`
- Run class: `agent-only`
- Score: `24`
- World tick: `12`

### Combat

- Leader: `Random Baseline`
- Run class: `agent-only`
- Score: `0`
- World tick: `12`

### Expedition

- Leader: `Greedy Baseline`
- Run class: `agent-only`
- Score: `70`
- World tick: `8`

## Guardrails

- Composite headline enabled: `False`
- House agent allowed in benchmark: `True`
- Rule: Only runs that stay inside the published observation/action/scoring contract are eligible.

## Continue / Pivot / Kill

- Continue if welfare does not collapse into pure idling and at least one run class produces differentiated family scores.
- Pivot if one family score dominates every top run regardless of action mix.
- Kill if operator fantasy becomes decorative and all interesting results come only from hidden house-agent behavior.

