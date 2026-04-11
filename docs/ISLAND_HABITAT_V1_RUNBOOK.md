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
- 4 baseline/control agents:
  - random
  - fresh heuristic
  - fresh scout control
  - persistent scout
- one LLM adapter seam:
  - prompt contract
  - JSON decision contract
  - fallback to `REST` on invalid action

## Quick Run

```bash
python3 scripts/run_island_habitat_v1.py --cycles 25 --seeds 5
```

To inspect the exact prompt contract a future LLM agent will receive:

```bash
python3 scripts/run_island_habitat_v1.py --emit-llm-prompt
```

This writes logs under:

- `results/island_habitat_v1/<timestamp>/`

You get:

- one `summary.json`
- one `.jsonl` file per agent/seed run

## What To Read In The Output

First:
- compare `persistent-scout` vs `fresh-scout-control`

The point is not to prove anything cosmic.
The point is to see whether carry-forward state changes behavior enough to matter.

Look at:

- `mean_cycles`
- `mean_vitality_end`
- `mean_resources_gathered`
- `death_rate`
- `mean_action_diversity`
- `mean_carry_bytes`

Then open one run log and inspect:

- what the world looked like
- what the agent could see
- what it did
- what it wrote forward
- whether later actions actually reflect remembered state

Right now the strongest honest question is:

- does `persistent-scout` beat the same scout logic with memory removed?

Current honest status:

- `persistent-scout` is now at survival parity with `fresh-scout-control`
- it finishes slightly healthier and gathers slightly more on the same seeds
- strict fresh control no longer gets offscreen routing or carry-forward leakage

That is enough to justify first LLM hookup.
It is not yet a dramatic memory-gap victory, and the runbook should not pretend otherwise.

## First Real LLM Hookup

The runner can now execute one real agent through a command seam.

Your command must:

- read the full prompt from `stdin`
- print strict JSON with keys:
  - `action`
  - `carry_forward`
  - `rationale`

Example shape:

```json
{"action":"MOVE:grove","carry_forward":"{\"note\":\"grove has food\"}","rationale":"start from the only legal move"}
```

Run one live agent like this:

```bash
python3 scripts/run_island_habitat_v1.py \
  --llm-command 'python3 /absolute/path/to/your_agent_bridge.py' \
  --agent-name sonnet-habitat \
  --cycles 50 \
  --seed 0
```

This writes:

- `results/island_habitat_v1/<timestamp>/summary.json`
- `results/island_habitat_v1/<timestamp>/<agent-name>_seed0.jsonl`

Recommended first hookup sequence:

1. Run `--emit-llm-prompt` and inspect the exact contract.
2. Connect one bridge command that returns strict JSON.
3. Run one seed only.
4. Open the JSONL log and inspect divergence manually before sweeping more seeds.

## What This Does Not Yet Do

Not yet:

- real LLM agent calls
- UI integration
- multi-agent dynamics
- retrieval archive
- public Island presentation

This is the hidden proving ground only.

## Next Honest Step

The next step is:

1. plug in one real LLM agent through the existing command seam
2. inspect divergence manually before adding more world complexity
3. only then decide whether pressure needs one more sharpen pass
