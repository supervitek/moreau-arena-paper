# Paper Verification Report

Date: 2026-03-16

Scope: explicit quantitative claims in [`paper/moreau_arena.tex`](../paper/moreau_arena.tex) were checked against committed JSONL data and reproducible scripts. Frozen benchmark data files were not modified.

## Verified Claims

- `T001` completed series count: `779`
- `T001` total games: `3652`
- `T002` completed series count: `780`
- `T002` total games: `4015`
- LLM-vs-baseline series win rate:
  - `T001`: `150/400 = 37.50%`
  - `T002`: `359/400 = 89.75%`
- BT rank shift for `gpt-5.2-codex`:
  - `T001`: rank `9`, BT `0.1193`
  - `T002`: rank `1`, BT `1.0000`
  - gain: `+0.8807` (matches paper's rounded `+0.881`)
- Adaptation headline is directionally supported, but the exact paper table is still not canonical:
  - committed script [`scripts/compute_t002_adaptation_metrics.py`](../scripts/compute_t002_adaptation_metrics.py) yields `557/1095 = 50.87%` for the direct JSONL-derived adapted win rate
  - paper reports `51.06%`
  - stale derived artifact [`data/tournament_002/adaptation_analysis.md`](../data/tournament_002/adaptation_analysis.md) still disagrees and should not be treated as source of truth
- Strict 3-cycles:
  - `T001`: `0`
  - `T002`: `12`
- WIL-trap statistics in `T001` across LLMs:
  - Spearman correlation between mean WIL and BT: `rho = -0.9286`, `p = 0.000863`
  - Spearman correlation between build diversity and BT: `rho = 0.8095`, `p = 0.0149`
- Claude Opus escape-from-WIL-trap claim:
  - `T001` average stats: `3.0 / 8.1 / 1.0 / 7.9`
  - `T002` average stats: `8.6 / 8.5 / 1.9 / 1.0`
  - BT improvement: `0.2520 / 0.0173 = 14.57x`

## Verification Sources

- Direct JSONL scripts run locally on:
  - [`data/tournament_001/results.jsonl`](../data/tournament_001/results.jsonl)
  - [`data/tournament_002/results.jsonl`](../data/tournament_002/results.jsonl)
- BT recomputation via [`verify_all.py`](../verify_all.py)
- Config integrity via [`scripts/verify_config_hash.py`](../scripts/verify_config_hash.py)
- Adaptation derivation via [`scripts/compute_t002_adaptation_metrics.py`](../scripts/compute_t002_adaptation_metrics.py)
- Existing integrity docs:
  - [`docs/T003_INTEGRITY.md`](T003_INTEGRITY.md)
  - [`docs/T003_SPEC.md`](T003_SPEC.md)

## Important Note

[`data/tournament_002/adaptation_analysis.md`](../data/tournament_002/adaptation_analysis.md) is a stale derived artifact and does not match the direct JSONL-derived adaptation/cycle counts used above. Because `data/tournament_*` is frozen, the file was not edited. For launch/paper verification, direct JSONL recomputation and [`verify_all.py`](../verify_all.py) should be treated as the source of truth.

## Outcome

Core benchmark numbers in the paper match the committed data: tournament sizes, game counts, LLM-vs-baseline rates, BT rankings, cycle counts, WIL-trap correlations, and Opus stat-shift claims are all supported. The remaining reproducibility issue is now narrower and explicit: the adaptation derivation script is committed, but its canonical JSONL output does not exactly match the paper/stale artifact. The project should treat Gate 1 as `PARTIAL` until the paper values are re-derived from canonical JSONL or the table in [`paper/moreau_arena.tex`](../paper/moreau_arena.tex) is corrected to match the committed derivation.
