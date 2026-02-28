# Moreau Arena — Companion Repository

Companion code and data for the paper:

> **Moreau Arena: Benchmarking Frontier LLMs as Game-Playing Agents in a Deterministic Combat Simulator**
> Victor Stasiuc (2026)

## Structure

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
└── paper/
    └── moreau_arena.tex  # Paper source (placeholder)
```

## Quick Start

```bash
# Install analysis dependencies
pip install -r analysis/requirements.txt

# Compute Bradley-Terry rankings from Tournament 002 data
python analysis/bt_ranking.py data/tournament_002/results.jsonl

# Generate pairwise win-rate matrix
python analysis/pairwise_matrix.py data/tournament_002/results.jsonl
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
| **Top BT** | SmartAgent | gpt-5.2-codex |
| **Key finding** | Baselines dominate LLMs | LLMs surpass baselines with structured output + adaptation |

## License

MIT License. See [LICENSE](LICENSE).

## Citation

```bibtex
@article{stasiuc2026moreau,
  title={Moreau Arena: Benchmarking Frontier LLMs as Game-Playing Agents in a Deterministic Combat Simulator},
  author={Stasiuc, Victor},
  year={2026}
}
```
