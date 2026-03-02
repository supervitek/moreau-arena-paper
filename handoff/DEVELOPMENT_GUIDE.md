# Development Guide — How to Contribute

## The Golden Rule: Moreau Core Is Frozen

The single most important rule: **never modify frozen files.** The invariant test suite will catch violations, but understanding why matters more than the alarm.

### What is frozen (hash-verified):
- `simulator/config.json` — SHA-256: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
- `data/tournament_001/*` — 2 files with hardcoded hashes
- `data/tournament_002/*` — 8 files with hardcoded hashes

### Why:
All scientific claims rest on these files being identical to when the experiments ran. If config changes, T001/T002 results become invalid. If tournament data changes, rankings become unreproducible.

### What you CAN change:
Everything else. New agents, new experiments, new analysis, web UI, seasons, DSL, documentation — all fair game. Build *around* the frozen core, never modify it.

---

## Invariant Tests

Before any commit, run:

```bash
python -m pytest tests/test_invariants.py -v
```

**89 tests must pass.** No exceptions. The test suite verifies:

1. Config hash integrity
2. Deterministic simulation
3. Stat formula correctness
4. Combat termination and validity
5. Grid invariants
6. Ability proc rate bounds
7. Tournament data immutability (SHA-256)
8. Known regression outcomes
9. Variance budget (RNG < 25%)
10. Monotonicity (ATK, HP)
11. No hidden mechanics
12. Symmetry (no systematic bias)

If tests fail after your changes, your changes broke an invariant. Fix the issue before committing.

---

## Branch Strategy

From `AGENTS.md`:

```
- Never push to main directly
- Create branch: feature/<issue-number>-<short-name>
- Open PR when done
- PR title: "Task X.Y: description"
```

Example workflow:
```bash
git checkout -b feature/42-new-agent
# ... make changes ...
python -m pytest tests/test_invariants.py  # Must pass
git add specific_files.py
git commit -m "Task 4.5: Add new agent implementation"
git push -u origin feature/42-new-agent
# Open PR via GitHub
```

---

## Adding a New Agent

### 1. Implement the BaseAgent interface

```python
# agents/my_agent.py
from agents.baselines import BaseAgent, Build, Animal

class MyAgent(BaseAgent):
    def choose_build(self, opponent_animal=None, banned=None, opponent_reveal=None):
        # Your logic here
        return Build(
            animal=Animal.BEAR,
            hp=3, atk=14, spd=2, wil=1
        )
```

Requirements:
- Stats must sum to 20
- Each stat >= 1
- Animal must not be in banned list
- Return a valid Build object

### 2. Or implement the MoreauAgent interface (for public submissions)

```python
class MyMoreauAgent:
    def get_build(self, prompt: str, game_state: dict | None = None) -> dict:
        return {"animal": "BEAR", "hp": 3, "atk": 14, "spd": 2, "wil": 1}

    def adapt_build(self, prompt, opponent_build, my_build, result, game_state) -> dict:
        # Called after losses in Track B
        return {"animal": "TIGER", "hp": 6, "atk": 8, "spd": 5, "wil": 1}
```

See `docs/AGENT_API.md` for the full specification.

### 3. Test your agent

```bash
# Quick test: 100 games vs GreedyAgent
python -m simulator --build1 "bear 3 14 2 1" --build2 "boar 8 8 3 1" --games 100

# Full challenge: your agent vs all baselines
python run_challenge.py --dry-run --provider your_provider --model your_model --series 5
```

---

## Adding a New Experiment

### Pattern to follow:

1. Create `run_<experiment>.py` in the repo root
2. Support `--dry-run` flag (replaces API calls with random builds)
3. Output results to `results/` as JSONL or JSON
4. Include all relevant metadata (model, provider, timestamp, config hash)
5. Use the simulator from `simulator/` — don't implement your own combat

### Template:

```python
import argparse
import json
from datetime import datetime
from simulator.engine import simulate_game
from simulator.animals import Animal, Build

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--provider', default='anthropic')
    parser.add_argument('--model', default='test')
    parser.add_argument('--series', type=int, default=10)
    parser.add_argument('--output-dir', default='results')
    args = parser.parse_args()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{args.output_dir}/experiment_{timestamp}.jsonl"

    # Your experiment logic here
    # Use simulate_game() for combat simulation
    # Write results as JSONL

if __name__ == '__main__':
    main()
```

---

## Code Style

From `AGENTS.md`:

- Python 3.10+
- Type hints on function signatures
- Docstrings on public functions
- Use only stdlib + packages in `requirements.txt`
- Add new dependencies to `requirements.txt` if needed

---

## CLAUDE.md and AGENTS.md

These files control how AI coding assistants (Claude Code, Codex, etc.) interact with the repo.

### CLAUDE.md
```
Moreau Core is FROZEN. Config hash: b7ec5885...
Test command: python -m pytest tests/test_invariants.py
Immutable files: config.json, data/tournament_001/*, data/tournament_002/*
Architecture rules:
- New features go in versioned tracks, not Core
- Ablation variants go in run_ablation.py
- All metrics must be reproducible from JSONL data
```

### AGENTS.md
```
Test command: python -m pytest tests/test_invariants.py
Branch rules: Never push to main directly
What you MUST NOT change: config.json, tournament data, paper
What you MUST do: Run pytest before opening PR
Code style: Python 3.10+, type hints, docstrings
```

These files are read automatically by AI assistants. If you modify the rules, all future AI sessions will follow the new rules.

---

## How Autopilot Works

The repo was developed using Claude Code in semi-autonomous mode ("autopilot"). Here's how it was structured:

### Agent Teams
The ROADMAP_v2.md assigns tasks to named agents:
- `spec-writer` — Documentation and specifications
- `ablation-runner` — Experiment scripts
- `infra-builder` — Tests and infrastructure
- `platform-builder` — Web UI and seasons
- `report-writer` — Analysis and reports
- `suite-designer` — Depth experiment suites

### Execution Pattern
1. Agent reads ROADMAP_v2.md for task assignment
2. Agent reads CLAUDE.md and AGENTS.md for rules
3. Agent implements the task
4. Agent runs `python -m pytest tests/test_invariants.py`
5. Agent commits with message: "Task X.Y: description"
6. Agent updates PROGRESS.md with status

### Guard Rails
- Invariant tests block broken commits
- Config hash verification prevents accidental Core changes
- Tournament data hashes prevent data corruption
- CLAUDE.md rules prevent agents from modifying frozen files

---

## Directory Conventions

```
agents/           ← Agent implementations (BaseAgent subclasses)
analysis/         ← Analysis scripts (BT, pairwise, reports)
data/             ← Tournament results (FROZEN)
docs/             ← Specifications and documentation
moreau_script/    ← DSL parser, interpreter, examples
paper/            ← LaTeX source and compiled PDF
prompts/          ← Verbatim prompt templates
reports/          ← Auto-generated season reports
results/          ← Experiment output files
scripts/          ← Setup and benchmark utilities
seasons/          ← Season system (patches, generators)
simulator/        ← Combat engine (FROZEN CORE)
tests/            ← Invariant test suite
web/              ← FastAPI app and static frontend
```

New files should go in the appropriate directory. If you need a new category, create a directory and add it to `.gitignore` if it will contain generated artifacts.

---

## Common Pitfalls

1. **Modifying config.json** — Tests will fail. Use `seasons/` for config variants.
2. **Forgetting --dry-run** — Real API calls cost money. Always test with dry-run first.
3. **Adding dependencies without updating requirements.txt** — Others won't be able to run your code.
4. **Pushing directly to main** — Use feature branches and PRs.
5. **Creating agents that don't sum stats to 20** — The simulator will reject invalid builds.
6. **Comparing rankings across tracks** — Track A rankings and Track B rankings measure different things. Never compare them directly.
