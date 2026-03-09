# Launch Posts -- Moreau Arena

Ready-to-publish posts for X/Twitter, Reddit, and Hacker News.

Data source: 2,609 series across T001 (779), T002 (780), T003 (1,050) + Season 1 (91 series).

---

## 1. X/Twitter Thread

### Tweet 1 (Hook)

GPT-5.4 went from 14th to 2nd place. Same model. Different game design.

We built Moreau Arena -- a benchmark that tests LLM strategic reasoning through creature combat. 2,609 series. 15 agents. 4 tournaments. What we found challenges how we measure intelligence.

### Tweet 2 (The Story)

The progression:

T001 (minimal prompt): Baselines beat every LLM. Claude Opus ranked 12th of 13.
T002 (engineered prompt): LLMs crushed baselines 61% to 30%. GPT-5.2-Codex jumped from 9th to 1st.
T003 (no meta-context): Rankings reshuffled again. Claude Opus climbed to 3rd. GPT-5.4 sank to 14th.

Same engine. Same rules. The prompt changed everything.

### Tweet 3 (Season 1 Twist)

Then we expanded from 6 animals to 14 with new mechanics.

GPT-5.4 -- dead last among LLMs in T003 -- jumped to 2nd overall. SmartAgent (a heuristic bot ranked 2nd in T003) dropped to 12th.

The model wasn't bad at reasoning. The game was too small for it to show what it could do.

### Tweet 4 (Negative Transfer)

The finding we didn't expect: negative transfer.

GPT-5.4 excels at creative strategic reasoning (21 unique builds across 5 animals in S1). But in T003's constrained 6-animal format, that same creativity was a liability -- it explored when it should have exploited.

Narrow benchmarks don't just undercount ability. They can actively penalize it.

### Tweet 5 (PSI)

How do we know the results aren't just prompt sensitivity?

We ran PSI validation -- the same tournament with a semantically equivalent paraphrased prompt. Kendall tau = 1.0 (perfect rank correlation). Rankings are robust to wording changes.

### Tweet 6 (CTA)

Paper, data, code -- everything open.

15 agents from 5 providers (OpenAI, Anthropic, Google, xAI + baselines). All 2,609 series with full match records. Reproducible from JSONL.

Site: moreauarena.com
Paper: moreauarena.com/paper

The arena is open.

---

## 2. Reddit r/MachineLearning

**Title:** [R] Moreau Arena: A Multi-Tournament Benchmark Revealing Negative Transfer in LLM Strategic Reasoning (tau=1.0 prompt robustness, 2,609 series, 15 agents)

**Body:**

We present Moreau Arena, a benchmark for evaluating LLM strategic reasoning through creature combat tournaments. Agents select animals and allocate stat points, then fight in a deterministic tick-based simulation. No training data leakage is possible -- the game engine is custom.

**Key results across 4 tournaments (2,609 series, 15 agents from OpenAI/Anthropic/Google/xAI):**

| Tournament | Prompt | Animals | Key Finding |
|------------|--------|---------|-------------|
| T001 | Minimal (qualitative) | 6 | Baselines dominate LLMs (53.6% vs 46.5% avg WR) |
| T002 | Engineered (exact formulas + meta) | 6 | LLMs dominate baselines (60.9% vs 30.0%) |
| T003 | Engineered minus meta-context | 6 | LLM avg WR = 53.1% -- formulas alone provide partial lift |
| Season 1 | Engineered + adaptation | 14 | Rankings dramatically reshuffle |

**Main findings:**

1. **Negative transfer in LLM reasoning.** GPT-5.4 ranked 14th of 15 in T003 (6 animals, BT=0.175) but 2nd of 14 in Season 1 (14 animals, BT=0.698). The model's creative exploration -- 21 unique builds across 5 animals -- was penalized in the constrained format but rewarded in the expanded one. This suggests narrow strategy spaces can produce misleading rankings.

2. **Heuristic collapse under complexity.** SmartAgent (a hand-crafted heuristic) ranked 2nd in T003 but 12th in Season 1. Fixed strategies that exploit small game spaces fail when the strategy space expands.

3. **Prompt sensitivity validation.** PSI (Prompt Sensitivity Index) using a semantically equivalent paraphrase yielded Kendall tau = 1.0 -- perfect rank preservation. Rankings measure reasoning ability, not prompt sensitivity.

4. **Prompt engineering as intervention.** T001 to T002 (adding exact formulas, worked examples, and meta-context) flipped the LLM-vs-baseline hierarchy completely. Claude Opus went from BT=0.036 (rank 12) to BT=0.531 (rank 5) -- a 15x improvement.

**T003 vs Season 1 rank shifts (LLMs only):**

| Agent | T003 Rank | S1 Rank | Delta |
|-------|-----------|---------|-------|
| GPT-5.2 | 4 | 1 | +3 |
| GPT-5.4 | 14 | 2 | **+12** |
| GPT-5.2-Codex | 1 | 3 | -2 |
| Claude Opus 4.6 | 3 | 6 | -3 |
| Gemini Flash | 7 | 11 | -5 |

**Methodology:**

- Bradley-Terry ranking with 1000-bootstrap CIs (seed=42)
- Best-of-7 adaptive format (loser sees opponent's previous build)
- Frozen config (SHA-256 hash-locked)
- All results reproducible from JSONL data files

Paper: moreauarena.com/paper
Code + data: open source

---

## 3. Reddit r/LocalLLaMA

**Title:** We ran 2,609 LLM battles in a creature combat arena. GPT-5.4 went from dead last to 2nd place just by changing the game design.

**Body:**

Moreau Arena is a benchmark where LLMs design creatures (pick an animal, allocate 20 stat points) and then fight in a tick-based simulation. Think Pokemon teambuilding meets LLM evaluation.

Some things that surprised us:

**The rankings are unstable across game designs.** GPT-5.4 ranked 14th of 15 agents with 6 animals but jumped to 2nd when we expanded to 14 animals. The model wasn't dumb -- it was exploring too much for a small game space. Give it room to be creative, and it dominates.

**Heuristic bots can beat frontier LLMs.** In our first tournament with vague rules, a simple ConservativeAgent (hardcoded build) beat every frontier model. In the engineered prompt tournament, every LLM beat every baseline. The prompt matters as much as the model.

**Models have different strategic personalities.** GPT-5.2-Codex generates 44 unique builds across 7 animals (maximum exploration). Grok and Gemini Flash each produce exactly 1 build for all 64+ games (total lock-in). Neither extreme is optimal -- GPT-5.2 with moderate exploration (24 builds, 6 animals) took the top spot in Season 1.

**Prompt paraphrasing doesn't change rankings.** We validated with Kendall tau = 1.0 -- reword the prompt, get the same ranking.

The arena runs against API models right now, but the engine is fully local and deterministic. If you wanted to plug in a local model, you'd just need to implement the API call function -- the simulation, scoring, and analysis are all open source.

Worth noting: some models (Grok, Gemini Flash) produce a single frozen build regardless of opponent or adaptation history. A well-tuned local model that actually adapts could potentially outperform them.

Site: moreauarena.com
Paper: moreauarena.com/paper

---

## 4. Hacker News

**Title:** Moreau Arena: LLM benchmark where GPT-5.4 goes from last to 2nd by changing game design

**First comment:**

Author here. Moreau Arena is a strategic reasoning benchmark built around creature combat. LLMs pick an animal (from a roster of 6 or 14), allocate stat points, and fight in a deterministic tick-based simulation. We ran 2,609 best-of-7 series across 4 tournaments with 15 agents from OpenAI, Anthropic, Google, and xAI.

The core finding is about negative transfer. GPT-5.4 ranked 14th of 15 in our 6-animal tournament -- below hand-coded heuristic bots. When we expanded to 14 animals with new mechanics, it jumped to 2nd. The model's tendency to explore creative builds (21 unique builds, 5 different animals) was punished in a narrow game space but rewarded in a rich one.

This has implications for benchmark design. If your evaluation space is too constrained, you're not just failing to measure some abilities -- you may be actively penalizing them. A model that "wastes" moves exploring in a small game might be exactly the one that excels in a complex environment.

Other findings:
- Prompt engineering flips LLM-vs-baseline rankings entirely (46.5% to 60.9% LLM win rate)
- PSI validation shows tau=1.0 prompt robustness -- rankings survive paraphrasing
- 36 non-transitive cycles in the 14-agent field -- no single dominant strategy
- SmartAgent (heuristic baseline) went from rank 2 to rank 12 when complexity increased

All data is JSONL, all results are reproducible, config is hash-locked.

moreauarena.com/paper
