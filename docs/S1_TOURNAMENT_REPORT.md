# Season 1 Tournament Report — Round 1

**Date:** 2026-03-08
**Series:** 91 (14 agents, all-pairs)
**Format:** Best-of-7, adaptive (loser sees opponent's previous animal)
**Runtime:** 13 minutes, 5 parallel workers, 0 errors

---

## BT Rankings

| Rank | Agent | Type | BT Score | 95% CI | W | L | WR |
|------|-------|------|----------|--------|---|---|-----|
| 1 | gpt-5.2 | LLM | 1.0000 | [0.74, 1.00] | 18 | 7 | 72.0% |
| 2 | gpt-5.4 | LLM | 0.6984 | [0.40, 1.00] | 15 | 10 | 60.0% |
| 3 | gpt-5.2-codex | LLM | 0.5046 | [0.28, 0.96] | 16 | 9 | 64.0% |
| 4 | gpt-5.3-codex | LLM | 0.5046 | [0.28, 0.93] | 14 | 11 | 56.0% |
| 5 | ConservativeAgent_S1 | Baseline | 0.4319 | [0.25, 0.77] | 17 | 8 | 68.0% |
| 6 | claude-opus-4-6 | LLM | 0.3705 | [0.22, 0.66] | 15 | 10 | 60.0% |
| 7 | grok-4-1-fast-reasoning | LLM | 0.3705 | [0.21, 0.65] | 7 | 6 | 53.8% |
| 8 | HighVarianceAgent_S1 | Baseline | 0.3180 | [0.19, 0.59] | 11 | 14 | 44.0% |
| 9 | claude-haiku-4-5 | LLM | 0.3180 | [0.18, 0.58] | 11 | 14 | 44.0% |
| 10 | claude-sonnet-4-6 | LLM | 0.2728 | [0.15, 0.53] | 12 | 13 | 48.0% |
| 11 | gemini-3-flash-preview | LLM | 0.2728 | [0.16, 0.49] | 5 | 8 | 38.5% |
| 12 | SmartAgent_S1 | Baseline | 0.1991 | [0.12, 0.33] | 8 | 17 | 32.0% |
| 13 | GreedyAgent_S1 | Baseline | 0.1419 | [0.10, 0.24] | 8 | 17 | 32.0% |
| 14 | RandomAgent_S1 | Baseline | 0.1419 | [0.09, 0.25] | 7 | 18 | 28.0% |

**LLM vs Baseline overall: 36/45 = 80.0%**

---

## Key Findings

### 1. GPT-5.4 Rehabilitation

The headline result. In T003, GPT-5.4 ranked **14th of 15** — below fixed-strategy bots, with a BT score of 0.0246. In Season 1, it rises to **2nd of 14** (BT=0.6984). This is the single largest rank swing in Moreau Arena history.

The T003 failure was not a flaw in GPT-5.4's reasoning ability. It was a failure of the 6-animal benchmark to offer sufficient strategic space. With 14 animals and WIL regen, GPT-5.4 finds effective builds (avg WIL=3.9, 21 unique builds across 5 animals) and adapts to opponents.

### 2. GPT-5.2 Dominance

GPT-5.2 takes #1 (BT=1.0, 72% WR), ahead of its Codex variants. It uses 24 unique builds across 6 animals with avg WIL=3.3 — investing in regen but not over-committing. This mirrors its T002/T003 performance where it consistently adapted.

### 3. ConservativeAgent_S1 Above Claude Opus

The ConservativeAgent baseline (rank 5, BT=0.43) outranks claude-opus-4-6 (rank 6, BT=0.37). ConservativeAgent uses exactly 1 fixed build across all 77 games — but that build is apparently well-calibrated. Claude Opus uses 9 unique builds across 5 animals but doesn't reliably find optimal stat allocations.

### 4. Frozen Models Persist

Two models use exactly 1 build across all games: **gemini-3-flash-preview** (rank 11) and **grok-4-1-fast-reasoning** (rank 7). Despite the expanded roster, they lock onto a single animal and stat allocation. Grok's frozen build is apparently decent (53.8% WR); Gemini Flash's is not (38.5% WR).

---

## T003 vs S1 Rank Comparison

| Agent | T003 Rank (of 15) | S1 Rank (of 14) | Delta |
|-------|-------------------|-----------------|-------|
| gpt-5.2 | 2 | 1 | +1 |
| gpt-5.4 | **14** | **2** | **+12** |
| gpt-5.2-codex | 1 | 3 | -2 |
| gpt-5.3-codex | 4 | 4 | 0 |
| claude-opus-4-6 | 3 | 6 | -3 |
| grok-4-1-fast-reasoning | 5 | 7 | -2 |
| claude-haiku-4-5 | 9 | 9 | 0 |
| claude-sonnet-4-6 | 7 | 10 | -3 |
| gemini-3-flash-preview | 6 | 11 | -5 |

Note: T003 had 15 agents (incl. gemini-pro, gpt-5.3-codex at different ranks). S1 has 14 (gemini-pro excluded due to API quota). Baseline agents differ between T003 and S1.

---

## WIL Analysis

In the 6-animal benchmark, WIL=1 was the dominant strategy (dump stat). Season 1 introduced WIL regen (+0.25% max HP per tick per WIL point), and the results show LLMs have adjusted:

| Agent | Avg WIL | WIL=1 Rate | Rank |
|-------|---------|------------|------|
| gemini-3-flash-preview | 5.0 | 0% | 11 |
| grok-4-1-fast-reasoning | 5.0 | 0% | 7 |
| claude-opus-4-6 | 4.7 | 1% | 6 |
| claude-sonnet-4-6 | 4.1 | 0% | 10 |
| gpt-5.4 | 3.9 | 0% | 2 |
| claude-haiku-4-5 | 3.5 | 0% | 9 |
| gpt-5.2 | 3.3 | 2% | 1 |
| gpt-5.2-codex | 2.7 | 9% | 3 |
| gpt-5.3-codex | 2.3 | 3% | 4 |

**WIL=1 has essentially vanished.** Every LLM invests in WIL when regen is available. However, over-investing in WIL (5.0) correlates with lower performance — the top 4 agents all have WIL between 2.3 and 3.9. The sweet spot appears to be WIL 3-4: enough to benefit from regen without sacrificing offensive stats.

---

## Build Diversity

| Agent | Unique Builds | Games | Animals Used | Builds/Game |
|-------|--------------|-------|-------------|-------------|
| gpt-5.2-codex | 44 | 67 | 7 | 0.66 |
| gpt-5.2 | 24 | 64 | 6 | 0.38 |
| claude-haiku-4-5 | 23 | 70 | 8 | 0.33 |
| gpt-5.4 | 21 | 70 | 5 | 0.30 |
| gpt-5.3-codex | 18 | 59 | 4 | 0.31 |
| claude-sonnet-4-6 | 17 | 71 | 7 | 0.24 |
| claude-opus-4-6 | 9 | 72 | 5 | 0.13 |
| grok-4-1-fast-reasoning | **1** | 64 | **1** | 0.02 |
| gemini-3-flash-preview | **1** | 66 | **1** | 0.02 |

GPT-5.2-codex is the most creative (44 unique builds, 7 animals) but ranks below the more focused GPT-5.2 (24 builds, 6 animals). Exploration doesn't always beat exploitation.

---

## Non-Transitivity

**36 non-transitive cycles** detected across the 14-agent field. This confirms that no single strategy dominates — the competitive landscape is rich and cyclical, exactly as designed.

---

## What This Means

Expanding the roster from 6 animals to 14 dramatically reshuffles LLM rankings. GPT-5.4 goes from last to second; Gemini Flash drops from 6th to 11th; Claude Opus falls from 3rd to 6th. The T003 benchmark measured one slice of strategic reasoning — the ability to optimize within a narrow build space. Season 1 measures something broader: the ability to navigate a complex roster with meaningful counter-picks and a functioning regen economy.

The implication for benchmark design is clear: a fixed, small strategy space can produce misleading rankings. Models that appear weak may simply lack room to express their reasoning. Moreau Arena's seasonal expansion is not just new content — it's a methodological necessity for measuring reasoning depth.

---

## Excluded Models

| Model | Provider | Reason |
|-------|----------|--------|
| gemini-3.1-pro-preview | Google | API free tier: 250 req/day. gemini-3-flash-preview retained as Google representative. |
