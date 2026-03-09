# AGENT_STATE.md — Read before, update after every task

Last updated: 2026-03-08 20:00 UTC

## Current Branch
`main`

## Season 1 Tournament — COMPLETED

- **Result:** 91 series, 14 agents (9 LLMs + 5 baselines), 0 errors, 13 min
- **Format:** Best-of-7, adaptive (loser sees opponent's previous animal)
- **Engine:** 14 animals, WIL regen (+0.25% max HP/tick/WIL), 8x8 grid, 60 ticks

### BT Rankings (Top 5)
| Rank | Agent | BT Score | W-L | WR |
|------|-------|----------|-----|-----|
| 1 | gpt-5.2 | 1.0000 | 18-7 | 72.0% |
| 2 | gpt-5.4 | 0.6984 | 15-10 | 60.0% |
| 3 | gpt-5.2-codex | 0.5046 | 16-9 | 64.0% |
| 4 | gpt-5.3-codex | 0.5046 | 14-11 | 56.0% |
| 5 | ConservativeAgent_S1 | 0.4319 | 17-8 | 68.0% |

### Key Findings
- **GPT-5.4 rehabilitation:** 14th in T003 → 2nd in S1 (+12 ranks). Largest swing in project history.
- **WIL=1 vanished:** All LLMs invest in WIL with regen. Sweet spot: WIL 3-4.
- **36 non-transitive cycles** confirm balanced competitive landscape.
- **ConservativeAgent_S1 > Claude Opus:** Fixed baseline (rank 5) beats claude-opus-4-6 (rank 6).
- **Frozen models:** grok-4-1-fast-reasoning and gemini-3-flash-preview each use exactly 1 build.

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

## Completed Tasks
- T003 Integrity Verification (prompt integrity, determinism, bootstrap stability)
- T003 PSI Validation (tau=1.0, PROMPT-ROBUST)
- Season 1 (14 animals, balance harness, all 5 gates pass, deployed)
- Season 1 Tournament (91 series, BT rankings, report, leaderboard updated)
- Replication Package (Dockerfile, verify_all.py, pyproject.toml)
- Round Table brainstorm S2-S5 (8 models, 2 councils, ~350 ideas)

## Deliverables
- `docs/S1_TOURNAMENT_REPORT.md` — Full tournament analysis
- `data/season1_tournament/bt_rankings.json` — BT scores for all 14 agents
- `data/season1_tournament/results.jsonl` — 91 series records
- `web/static/s1-leaderboard.html` — Updated with tournament BT rankings
- `web/app.py` — New `/api/v1/s1/tournament` endpoint

## Next Tasks
1. Create paper v2 (moreau_arena_v2.tex) with T003 + PSI + S1 results
2. Upload v2 to arXiv when v1 approves
3. Begin Season 2 development (hex grid + terrain)

## API Status
| Provider | Status | Notes |
|----------|--------|-------|
| Google (Gemini) | QUOTA ISSUE | Flash: 10K RPD but structured output blocked. Pro: 250 RPD exhausted. |
| OpenAI (gpt-5.4) | OK | |
| Anthropic (Claude) | OK | opus-4-6, sonnet-4-6. Sonnet has 30K input tokens/min limit. |
| xAI (Grok) | OK | grok-4-1-fast-reasoning works. Intermittent 403s resolved. |

## Key Constraints
- `config.json` is FROZEN (hash: b7ec588...)
- `data/tournament_001/`, `002/`, `003/` are immutable
- New features go in versioned tracks, not Core
- Use `.venv/bin/python` (macOS has no `python`)
- Source `~/.zshrc` for API keys
