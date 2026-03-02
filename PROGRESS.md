# Progress Log

## Sprint 5 — Final Verification & Commit (2026-03-01)

### Test Results

```
python3 -m pytest tests/test_invariants.py — 89 passed in 4.98s
```

All invariants green. No immutable files modified.

### Summary

All 21 tasks across Phases 1–4 of ROADMAP_v2.md are complete. This sprint commits previously-untracked spec files from Phase 1 and the roadmap document.

### Files Committed

- `ROADMAP_v2.md` — Full development roadmap (Phases 1–4)
- `docs/MEASUREMENT_SPEC.md` — Task 1.1: BT scores, CI, non-transitivity, PSI
- `docs/MMR_SPEC.md` — Task 1.2: Match Record Format v1.1 schema
- `docs/TRACKS.md` — Task 1.3: Track A/B/C/D definitions
- `simulator/ability_grammar.py` — Task 1.7: Formal ability grammar for all 14 core animals
- `NEXT_TASKS.md` — Updated task status (all done)
- `.gitignore` — Added `.claude/` and `.venv/` exclusions

### Immutable Files (verified unchanged)

- `simulator/config.json` — Hash verified: b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534
- `data/tournament_001/*` — SHA-256 hashes verified (9 tests pass)
- `data/tournament_002/*` — SHA-256 hashes verified (9 tests pass)

### Remaining Blocked Item

**Real LLM Ablation Run** — blocked on missing `GEMINI_API_KEY`. All code is ready.

---

## Sprint 4 — Phase 3 Completion & Phase 4 Start (2026-03-01)

### Test Results

```
python3 -m pytest tests/test_invariants.py — 89 passed in 5.07s
```

All invariants green. No immutable files modified.

### Final Status Table

| Teammate | Task | Description | Status | Notes |
|----------|------|-------------|--------|-------|
| ablation-runner | 1 | Real LLM Ablation Run | BLOCKED | GeminiFlashAgent created; live run blocked on missing GEMINI_API_KEY |
| infra-builder | 2 | Moreau Script — Tier-2 DSL | DONE | Parser, interpreter, validator, 3 examples, ScriptAgent |
| suite-designer | 3 | Rules-as-Data Generator | DONE | Sampling+rejection, analytical EV, --dry-run verified |
| platform-builder | 4 | Tournament Challenge Platform | DONE | /play, /research, /api/v1/submit routes added |

### Files Created/Modified

#### New Files
- `agents/gemini_agent.py` — GeminiFlashAgent (MoreauAgent interface) + GeminiAblationAgent (BaseAgent adapter)
- `moreau_script/__init__.py` — DSL package init
- `moreau_script/parser.py` — Safe DSL parser (IF/ELIF/ELSE + PREFER, max 50 rules)
- `moreau_script/interpreter.py` — Sandboxed interpreter with iteration limit
- `moreau_script/validator.py` — Validates scripts (no eval/import/exec)
- `moreau_script/script_agent.py` — ScriptAgent implementing BaseAgent
- `moreau_script/__main__.py` — CLI entry point
- `moreau_script/examples/random_strategy.ms` — Random pick example
- `moreau_script/examples/counter_pick.ms` — Counter-pick strategy
- `moreau_script/examples/stat_optimizer.ms` — ATK maximizer strategy
- `seasons/ability_generator.py` — Rules-as-Data generator (sampling+rejection, EV-based win rate estimation)
- `web/static/play.html` — "Create your fighter" form with stat sliders + budget enforcement
- `web/static/research.html` — Academic face with methodology summary + BT leaderboard

#### Modified Files
- `run_ablation.py` — Added `gemini` provider with `GEMINI_API_KEY` env var support
- `web/app.py` — Added `/play`, `/research`, `/api/v1/play`, `/api/v1/submit` routes
- `web/static/index.html` — Updated navigation bar
- `web/static/leaderboard.html` — Updated navigation bar

#### Immutable Files (verified unchanged)
- `simulator/config.json` — Hash verified
- `data/tournament_001/*` — SHA-256 hashes verified (9 tests pass)
- `data/tournament_002/*` — SHA-256 hashes verified (9 tests pass)

### Verification Commands

```
python3 -m moreau_script moreau_script/examples/counter_pick.ms   # DSL produces valid build
python3 seasons/ability_generator.py --dry-run                     # Ability generator works
python3 seasons/ability_generator.py --dry-run --ability-count 14 --seed 42  # Full PASS
python3 -m pytest tests/test_invariants.py                         # 89 tests pass
```

### Blocked Tasks

**Task 1 (Real LLM Ablation Run):** BLOCKED on missing `GEMINI_API_KEY` environment variable.
- GeminiFlashAgent code is complete and ready to use
- `run_ablation.py` supports `--provider gemini` which reads `GEMINI_API_KEY`
- To unblock: `export GEMINI_API_KEY=your_key && python3 run_ablation.py --variant formulas-only --provider gemini --model gemini-2.0-flash-lite --series 5`
- This will produce a JSONL file with `elapsed_s > 1.0` per series (proving real API calls)

---

## Sprint 3 — Platform & Depth Suites (2026-03-01)

### Test Results

```
python3 -m pytest tests/test_invariants.py — 89 passed in 5.05s
```

All invariants green. No immutable files modified.

### Final Status Table

| Teammate | Task | Description | Status | Notes |
|----------|------|-------------|--------|-------|
| platform-builder | 2.2 | Public Leaderboard Upgrade | DONE | HTML leaderboard with BT/Elo scores, heatmap, track filters, 3-cycle detection |
| report-writer | 2.4 | Seasonal Meta Report Generator | DONE | Auto-generates Markdown + PNG from JSONL data with BT/Elo, heatmap, cycles, signature builds |
| suite-designer | 3.2 | Partial Observability Suite | DONE | fog=0.0/0.5/1.0 levels, prompt-only modification, dry-run verified |
| suite-designer | 3.3 | Ban/Pick Planning Suite | DONE | Draft phase with ban/pick, reroll, arena selection, 2 baseline draft agents |

### Files Created/Modified

#### New Files
- `web/static/leaderboard.html` — Full leaderboard page with BT/Elo tables, pairwise heatmap, 3-cycle display, track filters
- `analysis/seasonal_report.py` — Auto-report generator (BT+Elo, heatmap, cycles, signature builds, balance check)
- `run_po.py` — Partial observability suite with fog levels 0.0/0.5/1.0
- `run_planning.py` — Ban/pick planning suite with draft phase
- `reports/season_1_report.md` — Auto-generated Season 1 report
- `reports/season_2_report.md` — Auto-generated Season 2 report

#### Modified Files
- `web/app.py` — Added /leaderboard HTML page, /api/v1/leaderboard/bt, /api/v1/leaderboard/pairwise, /api/v1/leaderboard/cycles endpoints
- `web/static/index.html` — Updated leaderboard nav link

#### Immutable Files (verified unchanged)
- `simulator/config.json` — Hash verified
- `data/tournament_001/*` — SHA-256 hashes verified (9 tests pass)
- `data/tournament_002/*` — SHA-256 hashes verified (9 tests pass)

### Verification Commands

```
python3 run_po.py --fog 0.5 --series 3 --dry-run      # PO suite works at all fog levels
python3 run_planning.py --dry-run --series 3            # Planning suite works
python3 -m analysis.seasonal_report --data data/tournament_002/results.jsonl --season 2  # Report generator works
```

### Blocked Tasks
None — all 4 tasks completed successfully.

---

## Sprint 2 — Parallel Teammates (2026-03-01)

### Test Results

```
python3 -m pytest tests/test_invariants.py — 89 passed in 5.03s
```

All invariants green. No immutable files modified.

### Final Status Table

| Teammate | Task | Description | Status | Notes |
|----------|------|-------------|--------|-------|
| docs | 1.9 | Launch Checklist | DONE | 4 gates with pass/fail criteria |
| docs | 1.10 | FAQ | DONE | 10 Q&A for public launch |
| docs | 1.11 | Language Guide | DONE | Allowed/forbidden/gray-area phrases |
| ablation | 1.5 | PSI Mini-Suite | DONE | 3 prompt variants + Kendall tau, stdlib-only |
| ablation | 1.8 | T003-D/E Ablation Variants | DONE | Both variants verified with --dry-run |
| platform | 2.1 | Season System | DONE | season_0_base.json + patch_generator.py + SEASON_RULES.md |
| platform | 2.3 | Agent Submission API | DONE | MoreauAgent interface + examples in docs/AGENT_API.md |
| lab | 3.1 | Lab Mode v2 | DONE | Convergence tracking, distance-to-optimum, iteration curves |

### Files Created/Modified

#### New Files
- `docs/LAUNCH_CHECKLIST.md` — 4 launch gates
- `docs/FAQ.md` — 10 Q&A
- `docs/LANGUAGE_GUIDE.md` — Approved terminology
- `docs/AGENT_API.md` — MoreauAgent interface spec
- `prompts/t002_v2.txt` — Paraphrased T002 prompt (variant 2)
- `prompts/t002_v3.txt` — Paraphrased T002 prompt (variant 3)
- `seasons/season_0_base.json` — Frozen core config copy
- `seasons/patch_generator.py` — EMA-based balance patch generator
- `seasons/SEASON_RULES.md` — Season system documentation

#### Modified Files
- `run_psi.py` — Replaced scipy dependency with stdlib Kendall tau
- `lab_mode.py` — Added convergence tracking, sampled optimum search, iteration curve JSON

#### Immutable Files (verified unchanged)
- `simulator/config.json` — Hash verified
- `data/tournament_001/*` — SHA-256 hashes verified
- `data/tournament_002/*` — SHA-256 hashes verified

### Blocked Tasks
None — all tasks completed successfully.

---

## Sprint 1 (Previous)

### Task 1: Fix paper LaTeX
**Status:** COMPLETE
- 1a: Fixed pgfplots error bars in Figures 1 and 2
- 1b: Added GitHub URL to Conclusion
- 1c: Added challenge platform sentence in Future Work

### Task 2: Standalone Simulator CLI
**Status:** COMPLETE
- Created `simulator/__main__.py` with three modes (single/round-robin/series)

### Task 3: Challenge Script
**Status:** COMPLETE
- Created `run_challenge.py` with full LLM challenge pipeline

### Task 4: Laboratory Mode Prototype
**Status:** COMPLETE
- Created `lab_mode.py` with iteration efficiency curve experiment

### Task 5: Documentation update
**Status:** COMPLETE
- Updated README.md, created docs/MECHANICS.md, docs/CONTRIBUTING.md
