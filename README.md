# Moreau Arena

Companion repository for the paper:

> **Moreau Arena: How Adaptation and Exact Formulas Transform LLM Strategic Reasoning from Systematic Failure to Baseline-Beating Performance**
>
> Victor Stasiuc (2026), Independent Researcher

**Key result:** Same 13 agents, same game, different scaffolding -- the leaderboard flips 180 degrees. LLMs go from losing to hand-coded bots (37.5% win rate) to crushing them (89.75%).

## Project Structure

| Component | Status | Description |
|-----------|--------|-------------|
| **Benchmark v1** | Frozen research | 6 animals, 3 tournament tracks (T001–T003), 89 invariant tests. Core data is immutable. |
| **Arena Season 1** | Public preview | 14 animals (6 original + 8 new), calibrated over 182K games, all 5 quality gates pass. First LLM tournament pending. |

Benchmark v1 is the research artifact — frozen, reproducible, citable. Arena Season 1 is built on top of that proof, expanding the roster for competitive play. They share the simulator core but run independently.

## What You Can Do

### 1. Verify Results

Reproduce the Bradley-Terry rankings and pairwise win-rate matrices from raw JSONL data.

```bash
pip install -r analysis/requirements.txt

# Bradley-Terry + Elo rankings for Tournament 002
python -m analysis.bt_ranking data/tournament_002/results.jsonl

# Pairwise win-rate matrix
python -m analysis.pairwise_matrix data/tournament_002/results.jsonl
```

### 2. Explore the Simulator

Run individual matchups or full round-robin tournaments.

```bash
# Single matchup: 1000 games
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 1000

# Round-robin: all animals with default stat spreads
python -m simulator --round-robin --games 500
```

### 3. Challenge Mode

Pit any frontier model against the full agent roster using the T002 protocol (structured output, exact formulas, meta context).

```bash
python run_challenge.py --provider anthropic --model claude-sonnet-4-5 --protocol t002
```

### 4. Lab Mode

Interactive experimentation loop where your model plays repeated rounds and you can observe its reasoning, adaptation, and build choices in real time.

```bash
python lab_mode.py --provider openai --model gpt-4o --rounds 10
```

## Game Rules (Quick Summary)

Two creatures fight on an 8x8 grid for up to 60 ticks. Each creature picks one of 6 animals and distributes 20 stat points across HP, ATK, SPD, and WIL (minimum 1 each). A shrinking ring activates at tick 30, dealing 2% max HP per tick to creatures outside the safe zone.

### Animals

| Animal | Passive | Abilities |
|--------|---------|-----------|
| Bear | Fury Protocol (+ATK at <50% HP) | Berserker Rage, Last Stand |
| Buffalo | Thick Hide (-50% first hit) | Thick Hide block, Iron Will |
| Boar | Charge (1.5x first attack) | Stampede, Gore |
| Tiger | Ambush (2x if faster) | Pounce, Hamstring |
| Wolf | Pack Sense (+1.5% proc bonus) | Pack Howl, Rend |
| Monkey | Primate Cortex (copies) | Chaos Strike, Mimic |

For full stat formulas, ability proc rates, and strategic analysis, see [docs/MECHANICS.md](docs/MECHANICS.md).

## Repository Structure

```
moreau-arena-paper/
├── simulator/        # Deterministic combat engine (standalone)
│   ├── engine.py     # Core tick loop
│   ├── animals.py    # Types, enums, stat blocks
│   ├── abilities.py  # Ability proc logic
│   └── config.json   # Frozen config (hash-verified)
├── agents/           # Agent implementations
│   ├── baselines.py  # 5 baseline agents (Random, Greedy, Smart, Conservative, HighVariance)
│   ├── llm_agent.py  # T001 LLM agent (plain-text prompt)
│   └── llm_agent_v2.py  # T002 LLM agent (structured output + meta context)
├── prompts/          # Verbatim prompt templates
│   ├── t001_prompt.txt   # Tournament 001 prompt
│   ├── t002_prompt.txt   # Tournament 002 prompt
│   └── meta_extractor.py # Top-N build extractor for meta context
├── data/
│   ├── tournament_001/   # 779 series, 13 agents, blind pick
│   │   ├── results.jsonl
│   │   └── report.md
│   └── tournament_002/   # 780 series, 13 agents, adaptive best-of-7
│       ├── results.jsonl
│       ├── results_chunk_[0-3].jsonl
│       ├── report.md
│       └── adaptation_analysis.md
├── analysis/         # Reproducible analysis scripts
│   ├── bt_ranking.py     # Bradley-Terry + Elo rating systems
│   ├── pairwise_matrix.py # JSONL → pairwise win-rate matrix
│   └── requirements.txt
├── docs/
│   ├── MECHANICS.md      # Full game rules and formulas
│   └── CONTRIBUTING.md   # How to add your own model
└── paper/
    └── moreau_arena.tex  # Paper source
```

## Config Verification

The frozen config hash should match:
```
SHA-256: b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534
```

## Tournament Overview

| | Tournament 001 | Tournament 002 |
|---|---|---|
| **Series** | 779 | 780 |
| **Agents** | 13 (8 LLM + 5 baseline) | 13 (8 LLM + 5 baseline) |
| **Format** | Best-of-7, blind pick | Adaptive best-of-7 (loser sees winner build) |
| **Top BT** | SmartAgent (baseline) | gpt-5.2-codex (LLM) |
| **LLM vs Baseline** | 37.5% LLM win rate | 89.75% LLM win rate |
| **Key finding** | Baselines dominate LLMs | LLMs surpass baselines with structured output + adaptation |

## Quick Verify

Reproduce all results from the raw data in three steps.

### Install

```bash
pip install .
```

Or with requirements directly:

```bash
pip install -r requirements.txt
```

### Run verification

```bash
python verify_all.py
```

This re-derives Bradley-Terry rankings, pairwise matrices, and config hash checks from the JSONL match data.

### Docker (optional)

```bash
docker-compose up --build verify
```

Runs the full verification suite in an isolated environment with pinned dependencies.

## Citation

```bibtex
@article{stasiuc2026moreau,
  title={Moreau Arena: How Adaptation and Exact Formulas Transform LLM Strategic Reasoning from Systematic Failure to Baseline-Beating Performance},
  author={Stasiuc, Victor},
  year={2026}
}
```

## License

MIT License. See [LICENSE](LICENSE).
