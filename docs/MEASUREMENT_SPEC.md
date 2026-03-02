# Measurement Specification v1.0

This document defines all metrics, artifacts, and statistical procedures used to evaluate agent performance in Moreau Arena tournaments.

---

## 1. Primary Metric: Bradley-Terry Scores

### 1.1 Definition

The primary ranking metric is the **Bradley-Terry (BT) model** fitted to series-level outcomes. A series outcome is a single binary result: one agent wins the best-of-7 series (first to 4 game wins).

The BT model estimates a latent strength parameter `p_i` for each agent `i` such that:

```
P(i beats j) = p_i / (p_i + p_j)
```

### 1.2 Fitting Procedure

BT parameters are estimated via maximum likelihood estimation (MLE) using the iterative algorithm implemented in `analysis/bt_ranking.py`.

**Algorithm details:**

1. Initialize all scores to 1.0.
2. For each agent `i`, update: `p_i = sum(w_ij + s) / sum((w_ij + w_ji + 2s) / (p_i + p_j))` across all opponents `j`, where `w_ij` is the number of series `i` won against `j` and `s = 0.5` is Laplace smoothing.
3. Normalize so that `max(p_i) = 1.0`.
4. Repeat until convergence (`max_delta < 1e-8`) or 200 iterations.

**Laplace smoothing** (`s = 0.5`) prevents degenerate solutions when an agent has a 100% or 0% win rate against some opponent. This adds a virtual half-win to each direction of every matchup.

### 1.3 Bootstrap Confidence Intervals

95% confidence intervals are computed via non-parametric bootstrap resampling:

1. Draw `N = 1000` bootstrap samples by resampling the full set of series outcomes with replacement.
2. Fit BT-MLE on each bootstrap sample.
3. The 95% CI for agent `i` is `[percentile_2.5, percentile_97.5]` of the bootstrap distribution of `p_i`.

The bootstrap seed must be recorded for reproducibility. In the reference implementation, `bootstrap_seed = 42`.

### 1.4 Interpretation

- BT scores are relative, not absolute. The top agent is always normalized to 1.0.
- Agents with non-overlapping CIs are statistically distinguishable at the 95% level.
- BT scores are transitive by construction. Non-transitivity in the underlying data manifests as wide CIs and/or poor model fit (see Section 4).

### 1.5 Example from T001

From `data/tournament_001/report.md` (13 agents, 779 series):

| Rank | Agent | BT Score | CI Lower | CI Upper |
|------|-------|----------|----------|----------|
| 1 | SmartAgent | 1.0000 | 0.6100 | 1.0000 |
| 2 | HighVarianceAgent | 0.9541 | 0.5546 | 1.0000 |
| 3 | ConservativeAgent | 0.6426 | 0.3718 | 0.9170 |
| ... | ... | ... | ... | ... |
| 13 | RandomAgent | 0.0054 | 0.0030 | 0.0078 |

Note the wide CIs for top agents (SmartAgent and HighVarianceAgent overlap), indicating that their relative ranking is not statistically robust at N=10 series per pair.

---

## 2. Secondary Metric: Elo Ratings

### 2.1 Purpose

Elo ratings are computed for **UX and leaderboard display only**. They are NOT used for paper-grade statistical claims. Elo is included because it is intuitive and familiar to game players.

### 2.2 Implementation

Standard Elo with K-factor 32, starting rating 1500, implemented in `analysis/bt_ranking.py`:

```
E_a = 1 / (1 + 10^((R_b - R_a) / 400))
R_a_new = R_a + K * (S_a - E_a)
```

Where `S_a = 1` for a win, `S_a = 0` for a loss, `S_a = 0.5` for a draw.

### 2.3 Known Limitations

- Elo is order-dependent: processing the same results in a different order yields different ratings.
- Elo does not provide confidence intervals.
- Elo assumes transitivity, which may not hold.
- Elo and BT rankings may disagree. When they do, BT takes precedence for all claims.

### 2.4 Example: BT vs Elo Disagreement (T001)

In T001, BT ranked SmartAgent #1 while Elo ranked grok-4-1-fast-reasoning #1. This is because Elo is sensitive to the order in which matches are processed (later matches weigh more due to the incremental update), while BT fits all data simultaneously.

---

## 3. Required Artifacts Per Tournament

Every tournament run must produce and archive the following artifacts:

### 3.1 Data Artifacts

| Artifact | Format | Description |
|----------|--------|-------------|
| `results.jsonl` | JSONL | Full match records (see MMR_SPEC.md) |
| `config.json` | JSON | Frozen simulator configuration |
| `env_hash` | SHA-256 string | Hash of config.json: `sha256(config.json)` |
| `prompt_hash` | SHA-256 string | Hash of the prompt text sent to each model |
| `seed_scheme` | String | Description of seed derivation method (see Section 3.3) |
| `decode_params` | JSON object | `{temperature, top_p, max_tokens, provider, model_id}` per model |

### 3.2 Analysis Artifacts

| Artifact | Format | Description |
|----------|--------|-------------|
| Pairwise matrix | CSV | Agent-by-agent win rate matrix |
| Pairwise heatmap | PNG | Visual heatmap of the pairwise matrix |
| BT scores | CSV | Agent, BT score, CI lower, CI upper, sample size |
| BT ranking table | Markdown | Formatted table for report inclusion |
| Elo rankings | CSV | Agent, Elo rating |

### 3.3 Seed Scheme Documentation

The seed scheme must be fully documented so that any series can be replicated given the same config. The current scheme (from `simulator/config.json` and `simulator/seed.py`):

- **Method:** SHA-256 deterministic derivation.
- **Match seed:** `base_seed` per series, incremented by 1 per game within the series (e.g., series with `base_seed = 5000` uses game seeds 5000, 5001, 5002, ...).
- **Tick seed:** `SHA256(match_seed:u64 || tick_index:u32)`, first 4 bytes as u32.
- **Hit seed:** `SHA256(match_seed:u64 || tick_index:u32 || attack_index:u32)`, first 4 bytes as u32.
- **Proc seed:** `SHA256(match_seed:u64 || tick_index:u32 || creature_index:u8 || ability_index:u8)`, first 4 bytes as u32.
- **Random value:** `SHA256(seed:u32)`, first 8 bytes as u64, divided by `2^64` to yield a float in `[0, 1)`.

All byte packing is big-endian.

---

## 4. Non-Transitivity Metrics

Non-transitivity is a key research question: do LLM agents exhibit rock-paper-scissors patterns in their build choices?

### 4.1 3-Cycle Count

A **3-cycle** (or directed triangle) exists among agents (A, B, C) when:

```
win_rate(A, B) > 0.5  AND  win_rate(B, C) > 0.5  AND  win_rate(C, A) > 0.5
```

**Metric:** Total number of 3-cycles across all agent triples.

For `n` agents, there are `C(n, 3)` possible triples. Each triple can form 0, 1, or 2 directed triangles (one in each direction). Report the count of directed triangles.

### 4.2 3-Cycle Mass

The **mass** of a 3-cycle (A, B, C) is the product of the win-rate margins:

```
mass(A, B, C) = (WR(A,B) - 0.5) * (WR(B,C) - 0.5) * (WR(C,A) - 0.5)
```

Where `WR(X, Y)` is the fraction of series X won against Y.

**Aggregate metric:** Sum of masses across all 3-cycles. Higher mass indicates stronger non-transitivity.

### 4.3 Condorcet Winner

A **Condorcet winner** is an agent that beats every other agent in head-to-head series (win rate > 50% against all opponents).

**Metric:** Binary -- does a Condorcet winner exist? Report yes/no and the agent name if yes.

### 4.4 Near-Cycle Mass

A **near-cycle edge** is a pairwise matchup where the win rate is between 0.45 and 0.55 (inclusive):

```
0.45 <= WR(A, B) <= 0.55
```

**Metric:** The fraction of all pairwise matchups that are near-cycle edges. High near-cycle mass suggests the tournament needs more samples (more series per pair) to resolve rankings.

### 4.5 Example from T002

From `data/tournament_002/adaptation_analysis.md`:
- **3-cycle count:** 0 strict 3-cycles found.
- **Condorcet winner:** No (no agent beats all others; gpt-5.2-codex lost 20% to grok-4-1-fast-reasoning).
- **Near-cycle edges:** Multiple matchups at 50% (e.g., gpt-5.2 vs grok at 50%, gpt-5.2 vs claude-sonnet at 50%).
- **Interpretation:** With only 10 series per pair, many matchups are unresolved. More data would likely reveal cycles among the middle tier.

---

## 5. Prompt Sensitivity Index (PSI)

### 5.1 Motivation

LLM build choices may be sensitive to prompt wording. A model that changes its ranking dramatically when the prompt is paraphrased is less trustworthy as a strategic agent. PSI quantifies this sensitivity.

### 5.2 Protocol

1. Select a single snapshot (frozen config, frozen set of agents, frozen decode params).
2. Create a minimum of **3 paraphrased prompts** that convey identical game rules and constraints but use different wording, structure, or emphasis. Paraphrases must preserve all mechanical information (stat formulas, animal descriptions, output format).
3. Run the full tournament with each prompt variant, keeping all other variables identical (same seeds, same config, same decode params).
4. For each pair of prompt variants `(P_i, P_j)`, compute the BT ranking of all agents under each prompt.
5. Compute **Kendall's tau** (`tau`) between the two BT rankings.

### 5.3 PSI Computation

```
PSI = 1 - mean(tau(P_i, P_j))  for all pairs (i, j)
```

Where `tau(P_i, P_j)` is Kendall's rank correlation coefficient between the BT rankings produced by prompts `P_i` and `P_j`. Kendall's tau ranges from -1 (perfect disagreement) to +1 (perfect agreement).

PSI ranges from 0 (perfectly prompt-robust) to 2 (maximally prompt-sensitive).

### 5.4 Classification

| PSI Range | Classification | Interpretation |
|-----------|---------------|----------------|
| PSI < 0.15 | Prompt-robust | Rankings are stable across paraphrases. Results can be reported without prompt-sensitivity caveats. |
| 0.15 <= PSI <= 0.30 | Moderate | Rankings shift noticeably. Results should note prompt sensitivity and report the range of rankings. |
| PSI > 0.30 | Prompt-sensitive | Rankings are unreliable without controlling for prompt effects. Must report per-prompt rankings separately. |

### 5.5 Reporting Requirements

When PSI is computed:
- Report the PSI value in the tournament summary.
- List all prompt variants used (by hash and version string).
- If PSI > 0.15, include per-prompt BT rankings as supplementary material.
- If PSI > 0.30, do NOT report a single aggregate ranking. Instead, report the range across prompts.

### 5.6 Current Status

PSI has not yet been computed for T001 or T002. T001 and T002 used different prompts (qualitative vs. quantitative) but are different tracks, not paraphrases. PSI requires paraphrases within the same track.

---

## 6. Statistical Power and Sample Size

### 6.1 Series Per Pair

Both T001 and T002 used 10 series per pair. This is the minimum for meaningful BT estimation but may be insufficient to:
- Resolve near-cycle edges (Section 4.4).
- Detect weak non-transitivity (Section 4.1).
- Produce tight CIs for middle-tier agents.

### 6.2 Recommended Minimums

| Goal | Series per pair | Rationale |
|------|----------------|-----------|
| Leaderboard (UX) | 10 | Sufficient for rough ordering |
| Paper claims (ranking) | 30 | Tighter CIs, resolves most near-cycles |
| Paper claims (non-transitivity) | 50+ | Needed to detect weak cycles (mass < 0.01) |
| PSI computation | 10 per prompt variant | 3 prompts x 10 series = 30 total per pair |

### 6.3 Bootstrap Sample Count

The standard bootstrap count is `N = 1000` resamples. This is sufficient for 95% CIs. For 99% CIs or for very small tournaments, increase to `N = 5000`.

---

## 7. Summary of Metrics

| Metric | Type | Used For | Reference |
|--------|------|----------|-----------|
| BT Score | Primary | Paper rankings, statistical claims | Section 1 |
| BT 95% CI | Primary | Statistical significance | Section 1.3 |
| Elo | Secondary | Leaderboard display | Section 2 |
| 3-Cycle Count | Diagnostic | Non-transitivity detection | Section 4.1 |
| 3-Cycle Mass | Diagnostic | Non-transitivity strength | Section 4.2 |
| Condorcet Winner | Diagnostic | Tournament structure | Section 4.3 |
| Near-Cycle Mass | Diagnostic | Sample sufficiency | Section 4.4 |
| PSI | Diagnostic | Prompt robustness | Section 5 |
