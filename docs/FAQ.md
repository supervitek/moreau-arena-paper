# FAQ — Moreau Arena

## 1. What is Moreau Arena?

Moreau Arena is a contamination-resistant strategic reasoning benchmark for large language models. It presents LLMs with a novel 1v1 creature combat game that does not exist in any training corpus, then measures how well they reason about stat allocation, counter-picking, and adaptation under uncertainty.

## 2. Why is prompt sensitivity a concern?

LLM benchmarks can produce different rankings depending on how the prompt is worded. Moreau addresses this through the Prompt Sensitivity Index (PSI): we run the same tournament with multiple paraphrased prompts and measure ranking stability using Kendall's tau. A PSI below 0.15 means the benchmark is prompt-robust.

## 3. Why only six animals in the original tournaments?

Six animals create a rich enough strategic space (6 animals × ~3,000 valid stat allocations = ~18,000 possible builds) while keeping the prompt short enough for single-turn reasoning. The animal roster could expand in a future season without invalidating existing results, since each season's config is frozen independently — but no such expansion has been designed yet.

## 4. Is Moreau Arena a game?

Moreau Arena is a benchmark that uses game mechanics as its measurement instrument. The combat is fully deterministic given a seed — there is no player skill involved during the fight. The only decision is the pre-fight build choice. This makes it a strategic reasoning task, not a game-playing task.

## 5. Why Bradley-Terry over Elo?

Bradley-Terry (BT) is a principled statistical model for pairwise comparisons that produces maximum-likelihood estimates with well-defined confidence intervals. Elo is an online approximation of BT that is order-dependent (results change depending on which games are processed first). We use BT as the primary metric for research and display Elo on the leaderboard only for familiarity.

## 6. How is Moreau different from existing LLM benchmarks?

Most benchmarks test knowledge recall or code generation on problems that may appear in training data. Moreau tests strategic reasoning on a novel game that cannot be memorized. Key differences:
- **Contamination-resistant:** The game rules are original and not in any training corpus.
- **Pairwise comparison:** Models compete against each other, not against a fixed answer key.
- **Adaptation measurement:** Track B measures whether models can learn from opponent feedback within a series.
- **Reproducible:** All outcomes are deterministic given the seed, config hash, and prompt.

## 7. Can I submit my own model?

Yes. See `docs/AGENT_API.md` for the submission interface. You implement a `MoreauAgent` class with `get_build()` and optionally `adapt_build()` methods, then run your agent through the standard tournament protocol.

## 8. How do you ensure reproducibility?

Every match outcome is determined by three inputs: the config hash (frozen), the match seed (recorded), and the model's build choice (logged in JSONL). Given these three values, anyone can replay any match and get identical results. The invariant test suite (`tests/test_invariants.py`) verifies this property on every commit.

## 9. What does the closing ring do?

The closing ring is a tiebreaker mechanism. Starting at tick 30 (out of 60 max), outer tiles begin dealing increasing damage to creatures standing on them. This prevents stalemates between defensive builds and ensures every match resolves within 60 ticks.

## 10. Can Moreau Arena measure reasoning improvements over time?

Yes. Because the benchmark is seasonal (each season freezes its config), you can track the same model across seasons or compare model versions on the same season. Lab Mode (`lab_mode.py`) specifically measures how efficiently a model converges to the optimal strategy over multiple rounds of feedback, providing iteration curves and distance-to-optimum metrics.
