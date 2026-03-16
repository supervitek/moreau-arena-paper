# Tournament Index

Master index of all Moreau Arena tournaments. See [TOURNAMENT_STANDARD.md](../TOURNAMENT_STANDARD.md) for the documentation format.

## Tournaments

| ID | Track | Prompt Strategy | #1 Agent | LLM Avg WR | Baseline Avg WR | Games | Status |
|----|-------|----------------|----------|------------|-----------------|-------|--------|
| [T001](T001.md) | A — Fixed Strategy | Minimal (30 lines, qualitative, text output) | ConservativeAgent (baseline) | 46.5% | 53.6% | 3,652 | complete |
| [T002](T002.md) | B — Engineered Prompt | Engineered (75 lines, exact formulas, JSON, adaptation) | gpt-5.2-codex (llm) | 60.9% | 30.0% | 4,015 | complete |
| [T003](T003.md) | C — Exact-Only Cleanroom | Exact formulas, JSON, adaptation, no meta hints | gpt-5.2-codex (llm) | 53.1% | 44.1% | 5,634 | complete |

## Key Comparison: T001 → T003

The frozen benchmark now spans three completed prompt conditions. T003 isolates what happens when Track B keeps formulas and adaptation but loses meta hints:

- **LLM average win rate**: 46.5% → 53.1% (+6.6pp)
- **#1 agent**: ConservativeAgent (baseline) → gpt-5.2-codex (llm)
- **Key ablation result**: formulas + adaptation still help without meta-context, but not nearly as much as in T002
- **Most visible failure mode**: frozen-model collapse on identical `BOAR 8/8/3/1` builds

## Data Integrity

All tournaments use the same frozen config:
- **Config SHA-256**: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
- **Frozen data files**: `data/tournament_001/*`, `data/tournament_002/*`, `data/tournament_003/*`
- **BT parameters**: N_bootstrap=1000, seed=42

## Planned Tournaments

| ID | Track | Status | Description |
|----|-------|--------|-------------|
| T004 | D — Tool Use | planned | Tests LLM ability to use external tools for strategy optimization |
