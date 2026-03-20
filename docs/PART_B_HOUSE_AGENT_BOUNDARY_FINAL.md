# Part B House Agent Boundary — Final

Last updated: 2026-03-20  
Status: Canonical synthesis after Round Table + 3 Claude Opus 4.6 reviews

## Verdict

`Cautious go.`

The settled model is:

- `Part B` keeps one public benchmark contract
- the house agent may be richer on the product side
- benchmark truth remains inside the public contract
- trust comes from visible labels and machine-enforced gates, not from full quarantine

This rejects two bad extremes:

- making the house agent so restricted that the product dies
- giving the house agent hidden privileges that would poison benchmark legitimacy

## The Boundary

The real wall is not a marketing page.

It is the published `B1` contract plus the code gates that enforce it:

1. observation gate
2. action gate
3. budget/scoring gate

Practical rule:

- product richness may exist above the contract
- benchmark measurement only sees what passes through the contract

## Product Truth vs Benchmark Truth

### Product truth

Allowed above the contract:

- richer session memory
- soul/personality output
- narrative traces
- private planning/orchestration
- nicer operator-facing reports

These features make the house agent worth renting.

### Benchmark truth

Must stay public and stable:

- observation fields
- action verbs
- scoring formulas
- tick cadence
- budget rules
- season versioning

These features determine what counts as a benchmark claim.

## What House Agents May Do

- reason with richer internal planning
- remember prior decisions and operator priorities
- explain actions in a distinct voice
- generate narrative/accounting output for the operator
- use private prompt engineering and orchestration

## What House Agents Must Not Do

- read hidden observation fields
- emit hidden verbs
- bypass tick cadence
- bypass budget/autopause
- receive different scoring
- leak cross-run hidden data
- silently change season rules

## Leaderboard Rule

The final synthesis lands here:

- one benchmark board per score family
- filterable by run class
- visibly labeled by run class
- visibly labeled by agent type for agent-only runs

This means:

- `manual`
- `operator-assisted`
- `agent-only / house-agent`

There is no separate "product board" in the benchmark layer.

If a run goes through the public contract, it is benchmark data.

## Trust Rule

Users must be able to see:

- who acted
- under which run class
- whether the run stayed contract-compliant
- how scores are computed

Users do not need:

- full internal prompts
- streamed chain-of-thought
- a second documentation regime pretending to be governance

## Main Risks

1. `Memory bleed`
- product memory silently becomes hidden observation advantage

2. `Label drift`
- UI stops clearly showing run class / agent type / compliance

3. `Contract bypass`
- future product enrichment routes around the public action/observation gates

## Final Build Rule

For a tiny team, the correct next layer is:

1. machine-enforced contract assertions
2. visible labels in ecology UI
3. concise scoring/contract explainer
4. auditable house-agent decision context
5. only then richer product polish

## Canonical One-Sentence Policy

`The house agent may be richer in personality, memory, and presentation, but every benchmarked Part B action must still be chosen from the same public observation, action, scoring, tick, and budget contract as any other valid run.`
