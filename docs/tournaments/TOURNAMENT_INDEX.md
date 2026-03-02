# Tournament Index

Master index of all Moreau Arena tournaments. See [TOURNAMENT_STANDARD.md](../TOURNAMENT_STANDARD.md) for the documentation format.

## Tournaments

| ID | Track | Prompt Strategy | #1 Agent | LLM Avg WR | Baseline Avg WR | Games | Status |
|----|-------|----------------|----------|------------|-----------------|-------|--------|
| [T001](T001.md) | A — Fixed Strategy | Minimal (30 lines, qualitative, text output) | ConservativeAgent (baseline) | 46.5% | 53.6% | 3,652 | complete |
| [T002](T002.md) | B — Engineered Prompt | Engineered (75 lines, exact formulas, JSON, adaptation) | gpt-5.2-codex (llm) | 60.9% | 30.0% | 4,015 | complete |

## Key Comparison: T001 → T002

The same 13 agents, the same simulator, the same config — but a redesigned prompt flips the leaderboard:

- **LLM average win rate**: 46.5% → 60.9% (+14.4pp)
- **Baseline average win rate**: 53.6% → 30.0% (−23.6pp)
- **#1 agent**: ConservativeAgent (baseline) → gpt-5.2-codex (llm)
- **Biggest LLM gainer**: gpt-5.2-codex (#9 → #1, BT 0.1950 → 1.0000)
- **Biggest baseline loser**: ConservativeAgent (#1 → #10, BT 1.0000 → 0.2219)

## Data Integrity

All tournaments use the same frozen config:
- **Config SHA-256**: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
- **Frozen data files**: `data/tournament_001/*`, `data/tournament_002/*`
- **BT parameters**: N_bootstrap=1000, seed=42

## Planned Tournaments

| ID | Track | Status | Description |
|----|-------|--------|-------------|
| T003 | C — Meta-Conditioning | planned | Tests whether LLMs can adapt their strategy when given meta-game information |
| T004 | D — Tool Use | planned | Tests LLM ability to use external tools for strategy optimization |
