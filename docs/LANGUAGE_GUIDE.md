# Language Guide — Moreau Arena

How to describe Moreau Arena accurately. Use this guide for papers, docs, README, and public communication.

---

## Allowed Phrases

These are accurate descriptions of what Moreau Arena is and does:

| Phrase | Why it's accurate |
|--------|-------------------|
| "contamination-resistant benchmark" | The game is original; it cannot be memorized from training data |
| "strategic reasoning benchmark" | It measures reasoning about stat allocation and counter-picking |
| "strategic reasoning under uncertainty" | Models reason with incomplete information about opponent choices |
| "pairwise comparison benchmark" | Models compete against each other, producing relative rankings |
| "novel game environment" | The Moreau Arena rules do not exist in any known training corpus |
| "measures adaptation" | Track B explicitly measures build changes after seeing opponent |
| "reproducible measurement" | Deterministic combat + recorded seeds = fully reproducible |
| "seasonal benchmark" | Each season freezes its own config; results are never cross-compared |
| "Bradley-Terry ranking with confidence intervals" | This is the primary metric, statistically principled |
| "a benchmark for strategic reasoning" | Uses indefinite article; does not claim uniqueness |

## Forbidden Phrases

These are inaccurate, overclaimed, or misleading. Do not use them.

| Phrase | Why it's wrong |
|--------|---------------|
| "the benchmark" (with definite article implying it's the only one) | There are many benchmarks; Moreau is one of them |
| "proves general reasoning" | Moreau measures strategic reasoning in one domain, not general reasoning |
| "game solved" | The combinatorial space is large; no claim of solved status is made |
| "better than [other benchmark]" | Different benchmarks measure different things; direct comparison is invalid |
| "measures intelligence" | Moreau measures strategic reasoning performance, not intelligence |
| "state-of-the-art benchmark" | This implies ranking among benchmarks, which we don't claim |
| "comprehensive evaluation" | Moreau measures one axis (strategic reasoning); it is not comprehensive |
| "human-level" or "superhuman" | Moreau does not include human baselines, so these comparisons are invalid |
| "game-playing ability" | The combat is automatic; the only decision is pre-fight build choice |
| "solves the contamination problem" | Moreau is contamination-resistant, not contamination-proof |

## Gray Area (Use with Qualification)

| Phrase | Required qualification |
|--------|----------------------|
| "reasoning benchmark" | Must specify "strategic reasoning" — not general reasoning |
| "outperforms" | Only valid within the same Track and Season, with BT CI non-overlapping |
| "optimal strategy" | Only valid when referring to brute-force computed best build from simulator |
| "significant improvement" | Must reference BT confidence intervals; visual differences are not "significant" |
| "converges to optimum" | Only valid in Lab Mode with explicit distance-to-optimum metric |

## Examples

**Good:** "Moreau Arena is a contamination-resistant strategic reasoning benchmark that uses pairwise competition in a novel game environment."

**Bad:** "Moreau Arena is the benchmark that proves which LLMs have real reasoning ability."

**Good:** "In Track B, Claude 3.5 Sonnet outperforms GPT-4o with non-overlapping 95% BT confidence intervals."

**Bad:** "Claude is smarter than GPT-4o at games."

**Good:** "This is a benchmark for strategic reasoning under uncertainty."

**Bad:** "This comprehensive evaluation solves the contamination problem in LLM benchmarks."
