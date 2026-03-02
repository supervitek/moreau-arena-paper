# How to Run — Practical Guide

## Prerequisites

```bash
# Python 3.10+ required
python3 --version

# Install dependencies
pip install -r requirements.txt

# Optional: analysis dependencies (scipy for bootstrap CI)
pip install -r analysis/requirements.txt

# Verify everything works
python -m pytest tests/test_invariants.py -v
# Expected: 89 passed
```

No external services needed for the simulator, tests, or dry-run experiments. API keys only needed for real LLM experiments.

---

## 1. Simulator — Run Matches Directly

### Single matchup
```bash
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 1000
```

Output:
```
Moreau Arena — Standalone Simulator
Config: config.json (hash: b7ec5885)

Build 1: bear 3/14/2/1 (max_hp=80, base_dmg=13, dodge=5.0%, resist=3.3%)
Build 2: buffalo 8/6/4/2 (max_hp=130, base_dmg=7, dodge=10.0%, resist=6.6%)

Simulating 1000 games...

Results:
  Build 1 wins: 730 (73.0%)
  Build 2 wins: 270 (27.0%)
  Draws: 0
  Avg game length: 38.2 ticks
```

### Round-robin (all builds vs all builds)
```bash
python -m simulator --round-robin --games 500
```

Uses default builds for all 6 core animals. Prints pairwise win-rate matrix.

### Best-of-7 series
```bash
python -m simulator --series --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --series-count 10
```

### With specific seed (for reproducibility)
```bash
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 1 --seed 42
```

### Verbose mode (tick-by-tick combat log)
```bash
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 1 --verbose
```

---

## 2. Challenge Mode — Test Any LLM Against Baselines

### Dry run (no API key needed)
```bash
python run_challenge.py --dry-run --provider anthropic --model test --series 3
```

### With real API
```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python run_challenge.py --provider anthropic --model claude-sonnet-4-20250514

# OpenAI
export OPENAI_API_KEY=sk-...
python run_challenge.py --provider openai --model gpt-4o

# Google
export GOOGLE_API_KEY=...
python run_challenge.py --provider google --model gemini-2.0-flash

# xAI
export XAI_API_KEY=...
python run_challenge.py --provider xai --model grok-2
```

### Options
```
--protocol t001|t002   Protocol variant (default: t002)
--series N             Series per baseline (default: 10)
--output-dir PATH      Output directory (default: results/)
```

Output: JSONL results file + terminal summary with BT ranking and comparison to paper results.

---

## 3. Ablation Suite — Isolate T002 Components

### All variants dry-run
```bash
python run_ablation.py --variant all --dry-run
```

### Individual variant
```bash
python run_ablation.py --variant formulas-only --dry-run
python run_ablation.py --variant meta-only --dry-run
python run_ablation.py --variant adaptation-only --dry-run
python run_ablation.py --variant structured-output-only --dry-run
python run_ablation.py --variant formulas-no-meta --dry-run
```

### Real LLM ablation
```bash
export GEMINI_API_KEY=...
python run_ablation.py --variant formulas-only --provider gemini --model gemini-2.0-flash-lite --series 5

# Or with any provider
export ANTHROPIC_API_KEY=...
python run_ablation.py --variant formulas-only --provider anthropic --model claude-sonnet-4-20250514 --series 5
```

Output: `results/ablation_<variant>_<timestamp>.jsonl`

---

## 4. PSI — Prompt Sensitivity Index

### Dry run
```bash
python run_psi.py --dry-run
```

### With real API
```bash
export ANTHROPIC_API_KEY=...
python run_psi.py --provider anthropic --model claude-sonnet-4-20250514
```

Uses 3 paraphrased T002 prompts (`prompts/t002_prompt.txt`, `t002_v2.txt`, `t002_v3.txt`). Computes Kendall tau between resulting BT rankings.

Output: `results/psi_<timestamp>.json`

Interpretation:
- PSI < 0.15 = prompt-robust
- PSI 0.15-0.30 = moderate sensitivity
- PSI > 0.30 = prompt-sensitive

---

## 5. Lab Mode — Interactive Iteration Experiment

### Dry run
```bash
python lab_mode.py --dry-run --rounds 5 --builds-per-round 5
```

### With real API
```bash
export ANTHROPIC_API_KEY=...
python lab_mode.py --provider anthropic --model claude-sonnet-4-20250514 --rounds 10
```

### Options
```
--builds-per-round N   Builds proposed per round (default: 20)
--games-per-pair N     Games per matchup for testing (default: 50)
--rounds N             Number of iteration rounds (default: 10)
```

Output: `results/lab_<model>_<timestamp>.json` with iteration curve data:
```json
{
  "curve": [
    {"round": 1, "best_build": "bear 5/11/3/1", "best_wr": 0.812},
    {"round": 2, "best_build": "bear 3/14/2/1", "best_wr": 0.897},
    ...
  ],
  "convergence_round": 3,
  "distance_to_optimum": 0.02
}
```

---

## 6. Partial Observability Suite

### Dry run at different fog levels
```bash
python run_po.py --fog 0.0 --series 3 --dry-run   # Full info
python run_po.py --fog 0.5 --series 3 --dry-run   # Animal name only
python run_po.py --fog 1.0 --series 3 --dry-run   # No info
```

### With real API
```bash
export ANTHROPIC_API_KEY=...
python run_po.py --fog 0.5 --series 10 --provider anthropic
```

Output: `results/po_fog<N>_<model>_<timestamp>.jsonl`

---

## 7. Planning Suite — Ban/Pick Draft Phase

### Dry run
```bash
python run_planning.py --dry-run --series 3
```

### With real API
```bash
export ANTHROPIC_API_KEY=...
python run_planning.py --series 7 --provider anthropic
```

Features:
- Ban phase: each player bans 3 animals
- Pick phase: choose from remaining animals
- Stat reveal: 2 of 4 stats visible to opponent
- Reroll: limited re-rolls of stat allocation

Output: `results/planning_<timestamp>.jsonl`

---

## 8. Analysis — BT Rankings, Pairwise Matrices, Reports

### Bradley-Terry + Elo rankings
```bash
python -m analysis.bt_ranking data/tournament_002/results.jsonl
```

Output: BT scores with 95% CI + Elo ratings for all agents.

### Pairwise win-rate matrix
```bash
python -m analysis.pairwise_matrix data/tournament_002/results.jsonl
```

Output: `pairwise_matrix.csv` + `pairwise_heatmap.png` (if matplotlib available).

### Seasonal meta report
```bash
python -m analysis.seasonal_report --data data/tournament_002/results.jsonl --season 2
```

Output: Markdown report with BT/Elo, heatmap, 3-cycle detection, signature builds, balance assessment.

---

## 9. Moreau Script — DSL for Strategies

### Run a script
```bash
python -m moreau_script moreau_script/examples/counter_pick.ms
```

Output: The build selected by the script rules.

### Example script (`counter_pick.ms`)
```
IF opponent_animal = "BOAR" THEN
  PREFER BEAR with hp=3 atk=14 spd=2 wil=1
ELIF opponent_spd > 10 THEN
  PREFER WOLF with hp=5 atk=10 spd=3 wil=2
ELSE
  PREFER BUFFALO with hp=8 atk=6 spd=4 wil=2
```

### Validate a script (security check)
The validator runs automatically and rejects scripts with eval, exec, import, or open.

---

## 10. Season System — Balance Patches

### Generate a balance patch
```bash
python seasons/patch_generator.py
```

Reads match data, computes EMA win rates per ability, proposes proc rate adjustments.

### Generate new abilities
```bash
python seasons/ability_generator.py --dry-run
python seasons/ability_generator.py --dry-run --ability-count 14 --seed 42
```

Validates generated abilities against invariants (proc rates within bounds, EV estimation).

---

## 11. Web Leaderboard

### Start the server
```bash
pip install fastapi uvicorn
uvicorn web.app:app --reload --port 8000
```

### Endpoints
- `http://localhost:8000/` — Index page
- `http://localhost:8000/leaderboard` — BT/Elo leaderboard + heatmap
- `http://localhost:8000/play` — Create your fighter
- `http://localhost:8000/research` — Academic summary

### API
```bash
# BT scores (JSON)
curl http://localhost:8000/api/v1/leaderboard/bt

# Pairwise matrix (JSON)
curl http://localhost:8000/api/v1/leaderboard/pairwise

# 3-cycle detection (JSON)
curl http://localhost:8000/api/v1/leaderboard/cycles

# Run a single game
curl -X POST http://localhost:8000/api/v1/fight \
  -H "Content-Type: application/json" \
  -d '{"build_a": {"animal": "bear", "hp": 3, "atk": 14, "spd": 2, "wil": 1}, "build_b": {"animal": "buffalo", "hp": 8, "atk": 6, "spd": 4, "wil": 2}}'
```

---

## 12. Tests — Verify Invariants

### Run all 89 tests
```bash
python -m pytest tests/test_invariants.py -v
```

### Run specific test category
```bash
python -m pytest tests/test_invariants.py -v -k "config"       # Config integrity
python -m pytest tests/test_invariants.py -v -k "determinism"   # Determinism
python -m pytest tests/test_invariants.py -v -k "combat"        # Combat invariants
python -m pytest tests/test_invariants.py -v -k "immutable"     # Data immutability
python -m pytest tests/test_invariants.py -v -k "monotonic"     # Monotonicity
```

Expected: All 89 tests pass in ~5 seconds.

---

## Environment Variables Reference

| Variable | Used By | Required For |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | run_challenge, run_ablation, lab_mode, run_psi, run_po, run_planning | Anthropic models |
| `OPENAI_API_KEY` | run_challenge, run_ablation, lab_mode | OpenAI models |
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | run_challenge, run_ablation | Google models |
| `XAI_API_KEY` | run_challenge | xAI Grok models |

No API key needed for: simulator, tests, analysis, dry-run mode, Moreau Script, season tools.
