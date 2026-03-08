# AGENT_STATE.md — Read before, update after every task

Last updated: 2026-03-08 16:30 UTC

## Current Branch
`main`

## Recent Commits (main)
```
17adb45 feat: Round Table brainstorm #2 — Ollama cloud models + 8-model comparison
a1b7b8a feat: Round Table brainstorm — 200 ideas for Seasons 2-5 (4 models)
825f498 feat: add Benchmark/Season 1 toggle to homepage Quick Fight
a5e09a2 feat: Season 1 — 14 animals, S1 Quick Fight, leaderboard, heatmap, fighters page, matchup explorer
```

## PSI Validation — COMPLETED

- **Result: tau = 1.0000, PROMPT-ROBUST**
- T003 findings are NOT prompt-dependent. Rankings perfectly stable across paraphrases.
- GPT-5.4 ranked last (5/5) in PSI run, confirming original T003 rank 14/15.
- LLM avg win rate: 37.7% (consistent with T003 without meta-hints)

### PSI v2 Run Details
- **Agents (5):** gpt-5.4, claude-opus-4-6, claude-sonnet-4-6, SmartAgent, GreedyAgent
- **Series:** 10 pairs x 5 series = 50 total, 0 failed
- **Prompt:** `prompts/t003_v2.txt` (paraphrase of t003_prompt.txt)
- **Gemini excluded:** Structured output quota exhausted (both Flash 10K RPD and Pro 250 RPD hit 429)
- **Grok excluded:** Intermittent 403 errors (unreliable)
- **No GreedyAgent fallback:** API failures → series marked FAILED (none occurred)

### PSI v1 (superseded)
- tau = 0.7333 (MODERATE) — corrupted by Grok 403s + GreedyAgent fallback
- Committed at bed3e2f, now overwritten by v2

## Completed Tasks
- T003 Integrity Verification (prompt integrity, determinism, bootstrap stability)
- T003 PSI Validation (tau=1.0, PROMPT-ROBUST)
- Season 1 (14 animals, balance harness, all 5 gates pass, deployed)
- Replication Package (Dockerfile, verify_all.py, pyproject.toml)
- Round Table brainstorm S2-S5 (8 models, 2 councils, ~350 ideas)

## Next Tasks
1. Add Gemini to PSI when quota resets (optional — tau=1.0 already conclusive)
2. Create paper v2 (moreau_arena_v2.tex) with T003 + PSI results
3. Upload v2 to arXiv when v1 approves
4. Run Season 1 LLM tournament
5. Begin Season 2 development (hex grid + terrain)

## API Status
| Provider | Status | Notes |
|----------|--------|-------|
| Google (Gemini) | QUOTA ISSUE | Flash: 10K RPD but structured output blocked. Pro: 250 RPD exhausted. |
| OpenAI (gpt-5.4) | OK | |
| Anthropic (Claude) | OK | opus-4-6, sonnet-4-6. Sonnet has 30K input tokens/min limit. |
| xAI (Grok) | EXCLUDED | Intermittent 403 errors |

## Key Constraints
- `config.json` is FROZEN (hash: b7ec588...)
- `data/tournament_001/`, `002/`, `003/` are immutable
- New features go in versioned tracks, not Core
- Use `.venv/bin/python` (macOS has no `python`)
- Source `~/.zshrc` for API keys
