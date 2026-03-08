# T003 PSI Validation -- Prompt Sensitivity Index

Generated: 2026-03-08 21:33 UTC


## Summary

| Metric | Value |
|--------|-------|
| Kendall tau | **1.0000** |
| Verdict | **PROMPT-ROBUST** |
| LLM avg win rate (PSI run) | 37.7% |
| Total series | 50 |
| Runtime | 120s |

> tau > 0.85: T003 finding is robust to prompt paraphrasing.

## Method

Prompt Sensitivity Index (PSI) measures whether tournament rankings are stable
across semantically-equivalent prompt paraphrases. We created `t003_v2.txt` --
a paraphrase of the original T003 prompt with identical game mechanics but
different wording -- and ran a mini tournament with 6 agents (4 LLMs + 2 baselines).

- **Original prompt**: `prompts/t003_prompt.txt`
- **Paraphrased prompt**: `prompts/t003_v2.txt` (sha256: `0e4e4319d9d2...`)
- **Protocol**: Adaptive best-of-7 (same as T003)
- **Agents**: gemini-flash, gemini-pro, gpt-5.4, claude-opus-4-6, claude-sonnet-4-6, SmartAgent, GreedyAgent
- **Series per pair**: 5

## Ranking Comparison

| Agent | T003 Original Rank | T003 Original BT | PSI (v2) Rank | PSI (v2) BT | Delta |
|-------|--------------------|-------------------|---------------|-------------|-------|
| SmartAgent | 1 | 0.9839 | 1 | 1.0000 | 0 |
| claude-opus-4-6 | 2 | 0.8952 | 2 | 0.1951 | 0 |
| claude-sonnet-4-6 | 3 | 0.4650 | 3 | 0.1205 | 0 |
| GreedyAgent | 4 | 0.3741 | 4 | 0.1024 | 0 |
| gpt-5.4 | 5 | 0.1750 | 5 | 0.0246 | 0 |

## Per-Agent Win Rates (PSI Run)

| Agent | W | L | Total | WR |
|-------|---|---|-------|----|
| gpt-5.4 | 1 | 19 | 20 | 5.0% |
| claude-opus-4-6 | 9 | 5 | 14 | 64.3% |
| claude-sonnet-4-6 | 7 | 9 | 16 | 43.8% |
| SmartAgent | 18 | 0 | 18 | 100.0% |
| GreedyAgent | 5 | 7 | 12 | 41.7% |

## BT Rankings (PSI Run, full)

| Rank | Agent | BT Score | 95% CI |
|------|-------|----------|--------|
| 1 | SmartAgent | 1.0000 | [1.0000, 1.0000] |
| 2 | claude-opus-4-6 | 0.1951 | [0.0875, 0.4575] |
| 3 | claude-sonnet-4-6 | 0.1205 | [0.0549, 0.2450] |
| 4 | GreedyAgent | 0.1024 | [0.0553, 0.1948] |
| 5 | gpt-5.4 | 0.0246 | [0.0123, 0.0497] |

## Interpretation

Kendall tau thresholds:
- tau > 0.85: **prompt-robust** -- rankings are stable across paraphrases
- 0.60 < tau < 0.85: **moderate** -- some sensitivity, investigate further
- tau < 0.60: **prompt-sensitive** -- rankings depend on exact wording

Our tau = 1.0000 -> **PROMPT-ROBUST**
