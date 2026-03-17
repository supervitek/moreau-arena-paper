# Part B Score Calibration

Last updated: 2026-03-17
Status: Active

## Goal

Make sure `welfare`, `combat`, and `expedition` reward actual ecological tradeoffs instead of degenerate behavior.

## Current Calibration Method

1. Run deterministic baselines:
   - `conservative`
   - `greedy`
   - `random`
2. Export current season leaderboards.
3. Compare family-score separation by run class and policy.
4. Flag degeneration if:
   - `welfare` wins while `idle_ticks` or `neglect_ticks` are obviously high
   - one policy dominates all three families
   - `agent-only` runs outperform through hidden privileges instead of public-contract actions

## Tooling

- Baseline generator:
  - `scripts/run_part_b_baselines.py`
- Weekly review packet:
  - `scripts/generate_part_b_review.py`
- Season archive export:
  - `scripts/export_part_b_season.py`

## Initial Interpretation Rules

- `conservative` should usually lead or stay competitive in welfare.
- `greedy` should usually create stronger combat or expedition peaks but with worse welfare stability.
- `random` should not top the season unless the contract is underconstrained.
- If every policy converges to the same top family, calibration needs another pass.

## Next Tightening Moves

- increase welfare decay if passive idling still wins
- reduce combat reward weight if arena spam dominates every leaderboard
- increase expedition injury penalty if cave greed becomes free EV
