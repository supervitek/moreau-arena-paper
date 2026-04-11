# Island Habitat V1 Runbook

This is the practical entry for the small hidden island habitat.

Primary plan:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/ISLAND_HABITAT_V1_PLAN.md`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/docs/ISLAND_HABITAT_V1_PLAN.md)

Implementation surfaces:
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/island_habitat.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/island_habitat.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_island_habitat_v1.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/scripts/run_island_habitat_v1.py)
- [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/tests/test_island_habitat_v1.py`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/tests/test_island_habitat_v1.py)

## What Exists Right Now

`v1` is intentionally small:

- 9-node persistent world
- exogenous weather and resource shifts
- occasional irreversible edge collapses
- one survival resource: vitality
- 3 actions:
  - `MOVE:<node>`
  - `GATHER`
  - `REST`
- partial observability
- carry-forward state with hard cap
- 3 baseline agents:
  - random
  - fresh heuristic
  - persistent scout

## Quick Run

```bash
python3 scripts/run_island_habitat_v1.py --cycles 25 --seeds 5
```

This writes logs under:

- `results/island_habitat_v1/<timestamp>/`

You get:

- one `summary.json`
- one `.jsonl` file per agent/seed run

## What To Read In The Output

First:
- compare `persistent-scout` vs `fresh-heuristic`

The point is not to prove anything cosmic.
The point is to see whether carry-forward state changes behavior enough to matter.

Look at:

- `mean_cycles`
- `death_rate`
- `mean_action_diversity`
- `mean_carry_bytes`

Then open one run log and inspect:

- what the world looked like
- what the agent could see
- what it did
- what it wrote forward
- whether later actions actually reflect remembered state

## What This Does Not Yet Do

Not yet:

- real LLM agent calls
- UI integration
- multi-agent dynamics
- retrieval archive
- public Island presentation

This is the hidden proving ground only.

## Next Honest Step

If the current sweep produces a real signal, the next step is:

1. add a fresh-agent control that replays the same cycle conditions without carry-forward
2. plug in one real LLM agent
3. inspect divergence manually before adding more world complexity
