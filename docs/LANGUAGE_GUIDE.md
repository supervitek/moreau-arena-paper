# Moreau Arena — Language Guide

How to describe Moreau Arena accurately. Use this guide for the paper, README, blog posts, social media, and any public-facing text.

---

## Allowed Phrases

These accurately describe what Moreau Arena is and what the results show.

### Describing the benchmark

- "a contamination-resistant benchmark for LLM strategic reasoning"
- "a novel synthetic strategy game designed to minimize training-data leakage"
- "a controlled environment for studying how information scaffolding affects LLM decision-making"
- "a compact combat game whose rules are specified only in the prompt"
- "an original game — no corpus contains its rules or optimal strategies"

### Describing the results

- "LLMs shift from losing to baselines to beating them when given exact formulas, examples, and feedback"
- "the performance reversal implicates comprehension and feedback, not raw capability"
- "with vague rules, LLMs pattern-match archetypes; with exact mechanics, they reliably surpass baselines"
- "adaptation is not a universal solution — several models win by finding strong builds early"
- "the T001-to-T002 flip is a controlled comparison: same agents, same game, different scaffolding"
- "baselines dominate under Track A conditions; LLMs dominate under Track B conditions"

### Describing the method

- "Bradley-Terry ranking on series outcomes with bootstrap confidence intervals"
- "two 13-agent round-robin tournaments under different information regimes"
- "frozen game configuration with cryptographic hash verification"
- "all prompts, match records, and analysis code are released for reproducibility"

### Describing limitations

- "results are specific to this game and this set of agents"
- "the benchmark measures strategic reasoning in one domain, not general intelligence"
- "Track C and Track D are specified but not yet run"
- "we do not claim that T002 performance reflects 'true' strategic ability — it reflects performance under those specific conditions"

---

## Forbidden Phrases

These overstate claims, invite misinterpretation, or mischaracterize the work. Do not use them.

### Overclaiming

- ~~"LLMs can/cannot reason strategically"~~ — The results are conditional on information scaffolding. Say what conditions produce what outcomes.
- ~~"proves that LLMs are/aren't capable of strategic thinking"~~ — One benchmark on one game does not prove general claims.
- ~~"superhuman performance"~~ — Baselines are not human players. Beating a SmartAgent is not beating a human.
- ~~"solves the strategic reasoning problem"~~ — Moreau Arena is a measurement tool, not a solution.
- ~~"definitive benchmark"~~ or ~~"the gold standard"~~ — It is one benchmark among many.

### Mischaracterizing the comparison

- ~~"LLMs failed in T001"~~ — They underperformed baselines. That is a relative statement, not an absolute failure.
- ~~"LLMs succeeded in T002"~~ — They outperformed baselines under different conditions. State the conditions.
- ~~"the same model got smarter"~~ — The model did not change. The prompt changed.
- ~~"adaptation makes LLMs intelligent"~~ — Adaptation is one factor among several (formulas, meta context, structured output).
- ~~"T002 is the fair test"~~ — Neither tournament is more "fair" than the other. They test different conditions.

### Misleading framing

- ~~"AI beats humans at strategy"~~ — No humans were tested.
- ~~"real-world strategic reasoning"~~ — Moreau Arena is a synthetic game, not a real-world scenario.
- ~~"general-purpose reasoning benchmark"~~ — It measures strategic reasoning in a specific combat game.
- ~~"IQ test for AI"~~ or ~~"intelligence test"~~ — It is not.
- ~~"game-playing AI"~~ — The agents do not play the game in real time. They submit a build; the simulator resolves combat.

### Technical inaccuracies

- ~~"the LLM plays the game"~~ — The LLM designs a build. The simulator plays the game.
- ~~"reinforcement learning"~~ — No RL is involved. Adaptation is prompt-based, not gradient-based.
- ~~"the model learns from experience"~~ — In Track B, the loser sees the winner's build. This is in-context information, not learning.
- ~~"fine-tuned for Moreau"~~ — All models are used via their public APIs with no fine-tuning.
- ~~"training on game data"~~ — No model was trained on Moreau data.

---

## Edge Cases

Phrases that are acceptable only with qualification.

| Phrase | Acceptable if... |
|--------|-----------------|
| "LLMs reason about game mechanics" | ...you specify which conditions (T002 formulas + examples) |
| "adaptation helps" | ...you note it helps in aggregate (51.06% post-change win rate) but is not the sole factor |
| "contamination-resistant" | ...you note this is by design (novel game), not a formal guarantee |
| "the leaderboard flips" | ...you specify it flips between T001 and T002, not that individual models change |
| "strategic failure" | ...you use it for specific failure modes (WIL trap), not as a blanket label |
| "benchmark" | ...you do not imply it measures general intelligence or replaces other benchmarks |

---

## Tone

- Precise over dramatic. State conditions and results, not narratives.
- Comparative, not absolute. "X outperforms Y under Z conditions" rather than "X is good/bad."
- Humble scope. One game, one set of agents, two conditions. That is the claim space.
