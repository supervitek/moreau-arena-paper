# LinkedIn Post — Moreau Arena

**A new approach to evaluating what LLMs can actually reason about**

We often assume that if a frontier model fails at a task, it lacks the capability. Our research suggests the problem is more nuanced than that.

Moreau Arena is an open-source strategic reasoning benchmark where AI agents design combat creatures under resource constraints and fight in a stochastic simulation. We tested 8 frontier LLMs and 5 hand-coded baselines across 1559 best-of-7 series totaling 7667 games — in two tournaments with identical agents but different information scaffolding.

The results were striking. Under vague, qualitative rules, every LLM lost to simple heuristic bots (37.5% win rate). When we provided exact numerical formulas, structured output requirements, top-performing build examples, and per-game adaptation feedback, the same models achieved 89.75% win rates against the same bots.

Same models. Same game. The only difference was how we communicated the rules and what feedback we provided.

This has direct implications for AI capability assessment. If your evaluation shows an LLM "can't do X," the bottleneck may not be reasoning ability — it may be comprehension, output formatting, or the absence of feedback loops. Moreau Arena provides a controlled framework for disentangling these factors.

The benchmark is contamination-resistant by design: the game is novel, the configuration is hash-verified, and the full protocol (prompts, match records, analysis code) is released for reproducibility.

We invite the research community to test their own models against the arena and contribute to a growing cross-model leaderboard.

Paper, code, and data: https://github.com/supervitek/moreau-arena-paper

#AI #MachineLearning #LLM #Benchmark #OpenSource #AIResearch
