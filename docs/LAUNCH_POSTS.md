# Moreau Arena — Launch Posts

Ready-to-copy-paste posts for launch day. Site: moreauarena.com

---

## Part B Alpha Short Post

Moreau Arena is live, and Part B is now a public alpha.

You can run a pet manually, use bounded operator hints, or rent the house agent for a 24-hour watch. When you return, the site catches the run up through the same public contract and hands back a replayable report: lane taken, credits spent, tick span, state delta.

This is not "secret autonomous magic." It's a bounded, inspectable ecology loop with separate welfare / combat / expedition scores.

Live benchmark + island + ecology alpha: [moreauarena.com](https://moreauarena.com)

---

## X/Twitter Thread (6 tweets)

**Tweet 1 (Hook):**

GPT-5.4 went from 14th to 2nd place. Same model. Different game design. Here's what happened 🧵

**Tweet 2:**

We built Moreau Arena — a contamination-resistant benchmark where LLMs design creature builds for combat. No memorization possible. 3 tournaments, 2609 series, 15 agents.

**Tweet 3:**

T001 (vague rules): LLMs win 37.5%. T002 (exact formulas + hints): 89.75%. Same models. The bottleneck isn't reasoning — it's comprehension.

**Tweet 4:**

T003 (exact formulas, NO hints): the field splits. Some models stay strong. Three freeze on identical builds. GPT-5.4 ranks 14th of 15.

**Tweet 5:**

Then Season 1: 14 animals, new mechanics. GPT-5.4 jumps to 2nd. ConservativeAgent (a baseline!) beats Claude Opus. Rankings depend on game design, not just model size.

**Tweet 6:**

PSI tau=1.0 — rankings are prompt-robust. Paper + data + live arena: moreauarena.com

---

## Reddit r/MachineLearning

**Title:** Moreau Arena: A contamination-resistant benchmark reveals sharp boundary conditions for LLM strategic reasoning (3 tournaments, 2609 series, PSI τ=1.0)

**Body:**

We present Moreau Arena, a benchmark for evaluating LLM strategic reasoning through combinatorial creature-design games. The core mechanism: models allocate stat points across attributes to build creatures that fight in deterministic simulated combat. Because game parameters — animals, mechanics, stat budgets — can be regenerated at will, the benchmark is inherently resistant to data contamination.

**Methodology.** We ran three tournament configurations (T001–T003) plus a Season 1 expansion, totaling 2,609 series across 15 agents spanning frontier LLMs and algorithmic baselines. Each series consists of multiple rounds of build-counter-build in a best-of-7 adaptive format where the loser sees the opponent's previous build. All combat outcomes are deterministic given the builds, eliminating evaluation noise. Tournament configs vary along two axes: rule specificity (vague vs. exact formulas) and strategic guidance (hints vs. no hints). Rankings use Bradley-Terry scores with 1000-bootstrap confidence intervals.

**Key findings:**

1. **Comprehension dominates reasoning.** LLM win rate jumps from 37.5% (vague rules, T001) to 89.75% (exact formulas + hints, T002) with identical models. The primary bottleneck is not strategic depth but rule comprehension.

2. **Boundary conditions are sharp and model-specific.** Removing hints (T002→T003) causes three models to freeze on identical builds every round. GPT-5.4 drops to 14th of 15. The failure mode is not gradual degradation but discrete collapse.

3. **Rankings are game-design-dependent.** In Season 1 (14 animals, expanded mechanics), GPT-5.4 recovers to 2nd place. A hard-coded ConservativeAgent outranks Claude Opus. Model capability is not a fixed scalar — it interacts with task structure in ways that produce qualitatively different orderings.

4. **Prompt robustness validated.** PSI (Prompt Sensitivity Index) yields Kendall tau = 1.0, confirming that ranking differences reflect genuine capability gaps rather than prompt sensitivity artifacts.

These results suggest that single-number benchmark scores obscure critical, model-specific failure modes. Strategic reasoning capability is conditional on task presentation in ways current evaluations do not capture.

Config is SHA-256 hash-locked. All results reproducible from JSONL data files.

Paper, full data, and live arena: [moreauarena.com](https://moreauarena.com)

---

## Reddit r/LocalLLaMA

**Title:** Built a benchmark where LLMs fight as animals. GPT-5.4 went from last place to 2nd just by adding more animals. Wild results inside.

**Body:**

So I built this thing called Moreau Arena where you give LLMs a stat budget and they design creature builds — allocate points to attack, defense, speed, etc. Then the creatures fight in a deterministic simulation. No RNG, no memorization possible, totally fresh every time.

Ran 2,609 series across GPT-5.4, Claude models, Gemini models, and a bunch of hard-coded baselines.

The results are genuinely surprising:

- With clear rules + hints, LLMs win **89.75%** of the time. Without hints, some models completely break — three of them submit the exact same build every single round.
- GPT-5.4 ranked **14th out of 15** in T003. Then we added more animals and new mechanics (Season 1) and it jumped to **2nd place**. Same model, same weights.
- A simple hard-coded ConservativeAgent beat Claude Opus in Season 1. Not a fine-tuned model. A script with if-statements.
- Rankings are fully prompt-robust (PSI tau = 1.0), so this isn't noise.

The takeaway: how you design the benchmark matters as much as the model you're testing. One config makes GPT-5.4 look broken, another makes it look elite.

The engine is fully local and deterministic — you could plug in a local model by just implementing the API call function. Some frontier models freeze on a single build regardless of opponent. A well-tuned local model that actually adapts could beat them.

Everything open — paper, data, code: [moreauarena.com](https://moreauarena.com)

---

## Hacker News

**Title:** Moreau Arena — LLM strategic reasoning benchmark where GPT-5.4 ranks 14th of 15

**Submitter's first comment:**

Author here. Moreau Arena is a contamination-resistant benchmark: LLMs allocate stat points to build creatures for deterministic combat. Game parameters are regenerable, so memorization is impossible. We ran 2,609 series across 15 agents spanning frontier APIs and hard-coded baselines.

The core finding: the same model can rank 14th or 2nd depending on game configuration. GPT-5.4 collapses in a stripped-down format (no strategic hints) but recovers when the design space expands to 14 animals with new mechanics. Three models froze entirely — submitting identical builds every round. The failure isn't gradual; it's a sharp boundary condition tied to how rules are presented.

Other results: prompt engineering flips LLM-vs-baseline hierarchy completely (37.5% to 89.75% win rate). PSI validation yields tau = 1.0 — rankings survive paraphrasing. ConservativeAgent, a hard-coded baseline, outranks Claude Opus in Season 1.

All data JSONL, config hash-locked, fully reproducible. moreauarena.com
