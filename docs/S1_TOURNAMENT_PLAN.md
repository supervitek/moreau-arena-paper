# Season 1 — Round 1: Tournament Plan

**Status:** Pre-launch planning
**Branch:** season1
**Date:** 2026-03-08

---

## 1. Overview

Season 1 — Round 1 is the first competitive tournament using the full 14-animal Season 1 roster. It follows the same agent lineup as T003 (10 LLM models + 5 baselines) and applies the validated best-of-7 format, now played on an expanded animal pool that introduces eight new animals and the WIL regen mechanic.

The primary goal is to measure how the expanded strategy space shifts LLM performance relative to the T003 benchmark results. T003 established a clear ranking (SmartAgent >> claude-opus-4-6 > claude-sonnet-4-6 >> gpt-5.4, with baselines filling the gaps); Season 1 is designed to test whether that ordering survives when the animal selection problem becomes materially harder.

---

## 2. Research Questions

**Q1 — WIL dominance revisited.** In T003, WIL=1 (dumping all points into Willpower) was reportedly a strong strategy on the 6-animal benchmark roster. The S1 roster adds animals where WIL has direct mechanical value: Wolf's Pack Sense amplifies proc rates, Vulture uses WIL sustain to ramp its Carrion Feeder scaling, and Viper's Shed Skin pairs with regen for sustained DOT loops. Does WIL-heavy building remain dominant, or do new anti-heal threats (Scorpion's Venom Gland, which cuts regen by 50%) punish it?

**Q2 — GPT-5.4 recovery.** GPT-5.4 finished last among LLMs in T003 (BT score 0.0246, 5% win rate in PSI validation). Its T003 weakness may partly reflect poor fit with the limited 6-animal set. With 14 animals available, does it find better matchup choices, or does the ordering hold?

**Q3 — Lower-tier model unlocks.** claude-sonnet-4-6 and the weaker baselines had limited differentiation in T003. New animals like Panther (ambush reset via Fade), Fox (proc suppression via Cunning), and Eagle (kite + Aerial Advantage) offer qualitatively different strategic axes. Do these unlock distinct strategies from models that appeared undifferentiated before?

**Q4 — LLM vs. baseline animal preferences.** The 5 baselines (SmartAgent, GreedyAgent, ConservativeAgent, HighVarianceAgent, RandomAgent) use fixed heuristics. Which new S1 animals do LLMs prefer over baselines, and vice versa? This probes whether LLMs recognize context-dependent value (e.g., Scorpion as a counter-pick vs. WIL-heavy opponents).

**Q5 — Non-transitivity in practice.** The balance harness confirmed 5 non-transitive cycles in the S1 roster (e.g., bear > vulture > monkey > bear). Do these cycles appear in actual tournament outcomes, or does overall stat quality wash them out?

---

## 3. Format Specification

| Parameter | Value |
|-----------|-------|
| Agents | 10 LLMs + 5 baselines = 15 total |
| LLM roster | GPT-5.4, Claude-opus-4-6, Claude-sonnet-4-6, Gemini-3.1-pro, Gemini-flash, Grok, DeepSeek-R1, Kimi-K2 + 2 others from T003 |
| Baseline roster | SmartAgent, GreedyAgent, ConservativeAgent, HighVarianceAgent, RandomAgent |
| Animal pool | All 14 S1 animals |
| Series format | Best-of-7, 3 animal-selection rounds per series |
| WIL regen | Active — wil × 0.0025 × max_hp per tick |
| Grid | 8×8, 60 ticks max |
| Ring mechanic | Activates at tick 30, 2% max HP per tick |
| RNG seeding | SHA-256 deterministic (same as benchmark) |

The animal selection prompt will be the T003 v2 paraphrase (PSI-validated, tau = 1.0, prompt-robust). No changes to prompt wording between agents.

---

## 4. Cost and Runtime Estimate

**Series count:** 15 × 14 / 2 = **105 series**
**Games per series:** 7 max (best-of-7)
**Total games:** ~735 maximum, ~500 expected (series end early when one side reaches 4 wins)

API calls are made at animal selection time (typically 1 call per selection round, 3 rounds per series). Adaptation calls are optional and model-dependent.

| Model tier | Rate estimate | Expected games | Estimated cost |
|------------|---------------|----------------|----------------|
| GPT-5.4 | ~$0.20/game | ~100 | ~$20 |
| Claude (opus/sonnet) | ~$0.15/game | ~100 | ~$15 |
| Gemini-3.1-pro | ~$0.08/game | ~60 | ~$5 |
| Gemini-flash | ~$0.03/game | ~60 | ~$2 |
| Grok / DeepSeek / Kimi | ~$0.10/game | ~80 | ~$8 |
| **Total** | | | **~$80–120** |

Baselines make no API calls.

**Runtime:** 4–6 hours with parallel execution, assuming rate limits are manageable. The Gemini free tier (250 req/day/model) will not cover a full run — paid tier is required for Gemini-flash and Gemini-3.1-pro. Google calls must be serialized with a 2-second gap between requests (threading lock, same as T003).

---

## 5. What Changes vs T003

**Roster size.** Six animals offered a narrow strategy space; most agents converged on a small number of viable builds. Fourteen animals increase the decision tree substantially, which should surface more differentiation between models.

**WIL regen.** The benchmark animals did not reward WIL investment with direct combat returns. The S1 engine implements `wil * 0.0025 * max_hp` regen per tick. This is meaningful for Wolf (proc amplification + regen), Vulture (sustain-to-ramp), and Buffalo (Iron Will + regen stack), but is hard-countered by Scorpion. Models that recognize this interaction should outperform those that treat WIL as a dump stat.

**Passive interactions.** New cross-animal mechanics add complexity: Fox Cunning halves opponent proc rates, directly countering Wolf Pack Sense. Scorpion Venom Gland cuts healing, making WIL regen less reliable. Boar's Charge ignores dodge, partially neutralizing Eagle and Fox evasion. These interactions reward counter-pick reasoning.

**Expected variance.** More matchup options should reduce the role of luck in individual series. The balance harness already shows tighter win rate clustering in S1 (42%–57%) than the 6-animal benchmark, which ran wider.

---

## 6. Success Criteria

- All 5 quality gates (G1–G5) confirmed passing with the S1 engine under tournament conditions
- At least one confirmed non-transitive cycle appears in tournament outcomes (not just the balance harness)
- At least 3 distinct meta strategies are identified across the top-6 agents (e.g., WIL-regen, burst-opener, anti-proc)
- Kendall tau between T003 final rankings and S1 final rankings is below 0.80 — i.e., S1 reshuffles the ordering meaningfully rather than reproducing T003

---

## 7. Next Steps

- [ ] Confirm API budget allocation for all 10 LLM models
- [ ] Verify Grok availability — T003 had intermittent 403 errors; confirm before scheduling
- [ ] Run 1 sample series per model against SmartAgent to validate S1 engine + prompt integration end-to-end
- [ ] Confirm Gemini paid tier is active (free tier: 250 req/day, insufficient for full tournament)
- [ ] Schedule tournament run — estimated 1 weekend block
- [ ] Publish results alongside Season 1 leaderboard page
