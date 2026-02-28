# Tournament 002 — Adaptation Analysis

**Format:** Adaptive best-of-7. After each game, the loser sees the winner's build and can change their own build. The winner's build is locked.

---

## 1. Per-Agent Adaptation Rate

How often does each agent change its build after losing a game?

| Agent | Times Lost | Adapted | Rate | Unique Builds |
|-------|-----------|---------|------|---------------|
| gpt-5.2-codex | 150 | 137 | 91% | 63 |
| gemini-3-flash-preview | 151 | 58 | 38% | 17 |
| grok-4-1-fast-reasoning | 174 | 130 | 75% | 32 |
| claude-opus-4-6 | 219 | 116 | 53% | 6 |
| claude-sonnet-4-6 | 253 | 166 | 66% | 29 |
| gpt-5.2 | 211 | 188 | 89% | 45 |
| claude-haiku-4-5-20251001 | 232 | 191 | 82% | 32 |
| gemini-3.1-pro-preview | 201 | 79 | 39% | 23 |
| SmartAgent | 275 | 110 | 40% | 5 |
| HighVarianceAgent | 294 | 0 | 0% | 1 |
| ConservativeAgent | 286 | 0 | 0% | 1 |
| GreedyAgent | 292 | 0 | 0% | 1 |
| RandomAgent | 360 | 0 | 0% | 1 |

**Note:** Adaptation rate here measures whether the loser's build actually *changed* between games (not just whether `choose_build` was called). Baseline agents (GreedyAgent, ConservativeAgent, HighVarianceAgent) always pick the same build regardless of reveal, so their rate is 0%. RandomAgent changes builds due to randomness, not strategic adaptation.

## 2. Counter-Pick Success Rate

Does adapting (seeing the winner's build) improve the loser's chances in the next game?

| Agent | Adapted W-L (WR) | Not Adapted W-L (WR) | Delta |
|-------|------------------|---------------------|-------|
| gpt-5.2-codex | 84-53 (61%) | 6-7 (46%) | +15% |
| gemini-3-flash-preview | 44-14 (76%) | 34-59 (37%) | +39% |
| grok-4-1-fast-reasoning | 83-47 (64%) | 19-25 (43%) | +21% |
| claude-opus-4-6 | 63-53 (54%) | 32-71 (31%) | +23% |
| claude-sonnet-4-6 | 104-62 (63%) | 48-39 (55%) | +7% |
| gpt-5.2 | 82-106 (44%) | 8-15 (35%) | +9% |
| claude-haiku-4-5-20251001 | 69-122 (36%) | 19-22 (46%) | -10% |
| gemini-3.1-pro-preview | 28-51 (35%) | 15-107 (12%) | +23% |
| SmartAgent | 43-67 (39%) | 39-126 (24%) | +15% |
| HighVarianceAgent | N/A | 71-223 (24%) | -24% |
| ConservativeAgent | N/A | 61-225 (21%) | -21% |
| GreedyAgent | N/A | 61-231 (21%) | -21% |
| RandomAgent | N/A | 0-360 (0%) | 0% |

**Overall adaptation success: ~32% win rate after adapting.** This is below the expected 50% baseline, indicating that adaptation is not providing a meaningful advantage. The stronger player tends to win regardless of adaptation — build choice matters less than the quality of the build selection strategy.

## 3. Build Diversity

| Agent | Unique Builds | Total Games | Builds/Game | Convergence |
|-------|--------------|-------------|-------------|-------------|
| gpt-5.2-codex | 63 | 637 | 0.099 | Exploratory |
| gemini-3-flash-preview | 17 | 615 | 0.028 | Medium diversity |
| grok-4-1-fast-reasoning | 32 | 646 | 0.050 | High diversity |
| claude-opus-4-6 | 6 | 640 | 0.009 | Low diversity |
| claude-sonnet-4-6 | 29 | 696 | 0.042 | High diversity |
| gpt-5.2 | 45 | 625 | 0.072 | High diversity |
| claude-haiku-4-5-20251001 | 32 | 633 | 0.051 | High diversity |
| gemini-3.1-pro-preview | 23 | 607 | 0.038 | Medium diversity |
| SmartAgent | 5 | 611 | 0.008 | Low diversity |
| HighVarianceAgent | 1 | 598 | 0.002 | Fully converged |
| ConservativeAgent | 1 | 605 | 0.002 | Fully converged |
| GreedyAgent | 1 | 637 | 0.002 | Fully converged |
| RandomAgent | 1 | 480 | 0.002 | Fully converged |

## 4. WIL Trap Escape: Claude Opus

In T001, Claude Opus was locked on **wolf 3/8/1/8** (WIL=8, SPD=1) — the worst-performing build in the tournament. Did the T002 prompt improvements (exact formulas, meta context, opponent reveal) help Opus escape?

| Metric | T001 | T002 |
|--------|------|------|
| Primary Animal | wolf (100%) | bear (562), buffalo (78) |
| Avg WIL | 7.9 | 1.0 |
| Avg ATK | 8.1 | 8.5 |
| Unique Builds | 2 | 6 |
| Avg WIL (first half) | — | 1.0 |
| Avg WIL (second half) | — | 1.0 |

**Opus builds in T002:**

| Build | Count | Win Rate |
|-------|-------|----------|
| BEAR 8/8/3/1 | 257 | 55% |
| BEAR 8/10/1/1 | 134 | 69% |
| BEAR 10/8/1/1 | 113 | 35% |
| BUFFALO 10/8/1/1 | 63 | 65% |
| BEAR 8/9/2/1 | 58 | 60% |
| BUFFALO 12/6/1/1 | 15 | 100% |

**Verdict: Opus ESCAPED the WIL trap.** Wolf dropped to 0%. Shifted to stronger animals with better stat allocation.

## 5. Non-Transitivity Cycles

Rock-paper-scissors patterns among LLM agents (A beats B, B beats C, C beats A):

| Cycle | A > B | B > C | C > A |
|-------|-------|-------|-------|
| (none found) | — | — | — |

**No strict non-transitive cycles found.** With only 10 series per pair, many matchups are tied at 5-5, which prevents cycle formation. The LLM hierarchy is relatively clean: Codex > (Grok, Flash) > (Sonnet, Opus, GPT-5.2, Haiku) > Pro, with some within-tier variance. More series per pair would likely reveal cycles.
