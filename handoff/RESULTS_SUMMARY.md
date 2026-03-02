# Results Summary — Scientific Findings

## The Headline

Same 13 agents, same game, different scaffolding — the leaderboard flips 180 degrees.

| | Tournament 001 | Tournament 002 |
|---|---|---|
| **Series** | 779 | 780 |
| **Agents** | 13 (8 LLM + 5 baseline) | 13 (same) |
| **Format** | Best-of-7, blind pick | Adaptive best-of-7 |
| **LLM vs Baseline Win Rate** | **37.5%** | **89.75%** |
| **Top Agent** | SmartAgent (baseline) | gpt-5.2-codex (LLM) |
| **Bottom Agent** | gpt-3.5-sonnet (LLM) | SmartAgent (baseline) |

**The 180-degree leaderboard flip:** In T001, baselines dominate. In T002, LLMs dominate. The agents are identical — only the information wrapper changed.

---

## Tournament 001 — Detailed Results

### Protocol
- Track A (One-Shot): qualitative descriptions, basic formulas, no meta context, no adaptation
- Single build per series (no changes between games)
- Plain-text output parsed with regex

### BT Rankings (T001)
SmartAgent (baseline) ranked #1. All LLMs ranked below the top baseline. LLMs consistently over-invested in WIL and under-invested in ATK.

### Key Numbers
- **779 series** across all 13-agent pairings
- **37.5% LLM win rate** against baselines
- SmartAgent's counter-pick logic outperformed LLM reasoning
- LLMs failed to recognize that ATK stacking dominates in the stat system

### Data Files
- `data/tournament_001/results.jsonl` (670 KB) — Complete match records
- `data/tournament_001/report.md` — Summary with rankings

---

## Tournament 002 — Detailed Results

### Protocol
- Track B (Feedback + Counter-Pick): exact formulas with worked examples, top-5 meta builds, structured JSON output, adaptation after losses
- Adaptive best-of-7: loser sees winner's build, may re-pick
- JSON output format with retry/fallback chain

### BT Rankings (T002)
gpt-5.2-codex ranked #1. SmartAgent dropped to #7. All LLMs above all baselines.

### Key Numbers
- **780 series** across all 13-agent pairings
- **89.75% LLM win rate** against baselines (172.5 wins / 192 games)
- **52.25 percentage point improvement** over T001
- LLMs correctly identified ATK stacking and adapted to counter opponents

### Adaptation Analysis
- LLMs changed builds after losses in the majority of cases
- Counter-pick success rate was high — adapted builds won more often
- Build diversity increased relative to T001 (LLMs explored more animals)

### Data Files
- `data/tournament_002/results.jsonl` (1.2 MB) — Complete match records
- `data/tournament_002/results_chunk_[0-3].jsonl` — Data split into 4 chunks
- `data/tournament_002/report.md` — Summary with rankings
- `data/tournament_002/adaptation_analysis.md` — Adaptation behavior analysis

---

## What Caused the Improvement?

Four factors changed between T001 and T002:

| Factor | What Changed | Expected Impact |
|--------|-------------|-----------------|
| Exact formulas | Qualitative → numeric with worked examples | LLMs can calculate stat scaling |
| Meta context | None → top-5 builds with win rates | Calibrates expectations, breaks priors |
| Adaptation | Fixed build → loser re-picks after seeing winner | Feedback loop enables learning |
| Structured output | Free text → JSON format | More reliable build parsing |

### Ablation Design (T003)

Five ablation variants isolate each factor's individual contribution:

| Variant | Formulas | Meta | Adaptation | Structured Output |
|---------|----------|------|------------|-------------------|
| T001 (baseline) | Qualitative | No | No | Text |
| formulas-only | **Exact** | No | No | Text |
| meta-only | Qualitative | **Yes** | No | Text |
| adaptation-only | Qualitative | No | **Yes** | Text |
| structured-output-only | Qualitative | No | No | **JSON** |
| formulas-no-meta | **Exact** | No | No | JSON |
| T002 (full) | **Exact** | **Yes** | **Yes** | **JSON** |

**Current status:** All ablation code is written and tested with `--dry-run`. Real LLM ablation runs are blocked on `GEMINI_API_KEY`. Code is ready — just needs the API key set.

### Expected Ablation Findings

Based on the T001/T002 difference, the ablations should reveal:
- **Formulas-only** should show moderate improvement (LLMs can reason about scaling)
- **Meta-only** should show moderate improvement (examples calibrate build choices)
- **Adaptation-only** should show improvement in later series games (feedback helps)
- **Structured-output** alone should show minimal improvement (parsing is not the bottleneck)
- The full T002 combination should be greater than any single factor (synergy)

---

## Other Experimental Data

### PSI (Prompt Sensitivity Index)
- 3 paraphrased T002 prompts tested (same info, different wording)
- Kendall tau computed between resulting rankings
- Results in `results/psi_*.json`

### Lab Mode
- Dry-run iteration curves in `results/lab_test_*.json`
- Measures: builds per round, best win rate per round, convergence round

### Seasonal Reports
- `reports/season_1_report.md` — Auto-generated from T001 data
- `reports/season_2_report.md` — Auto-generated from T002 data
- Include: BT rankings, pairwise heatmap, 3-cycle detection, signature builds

### Data File Reference

| File | Content | Size | Format |
|------|---------|------|--------|
| `data/tournament_001/results.jsonl` | T001 match records | 670 KB | JSONL |
| `data/tournament_002/results.jsonl` | T002 match records | 1.2 MB | JSONL |
| `results/ablation_*.jsonl` | Ablation dry-run results | Various | JSONL |
| `results/lab_test_*.json` | Lab iteration curves | 3.4 KB | JSON |
| `results/psi_*.json` | PSI computation results | 3.1 KB | JSON |
| `results/po_fog05_*.jsonl` | Partial observability results | 15 KB | JSONL |
| `results/planning_*.jsonl` | Planning suite results | 4 KB | JSONL |
| `reports/season_*_report.md` | Seasonal analysis reports | 4-6 KB | Markdown |

### JSONL Record Format

Each line in a results JSONL file contains:

```json
{
  "series_num": 779,
  "game_num": 1,
  "agent_a": "llm-gpt-4",
  "agent_b": "SmartAgent",
  "animal_a": "BEAR",
  "animal_b": "BUFFALO",
  "stats_a": [3, 14, 2, 1],
  "stats_b": [8, 6, 4, 2],
  "winner": "a",
  "ticks": 23,
  "end_condition": "death",
  "env_hash": "b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534",
  "seed": 42,
  "elapsed_s": 0.5
}
```
