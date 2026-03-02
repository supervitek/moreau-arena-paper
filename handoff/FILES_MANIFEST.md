# Files Manifest — Complete Repository Inventory

Every file in the repository with path, size, purpose, last modified date, and frozen/editable status.

**Legend:**
- FROZEN = hash-verified, never modify
- Editable = can be changed freely
- Generated = output from running experiments (can be regenerated)

---

## Root Directory

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `.gitignore` | 337 B | Git ignore rules (.claude/, .venv/, __pycache__/) | 2026-03-01 | Editable |
| `AGENTS.md` | 751 B | Rules for automated agent sessions | 2026-03-01 | Editable |
| `CLAUDE.md` | 516 B | Rules for Claude Code sessions | 2026-03-01 | Editable |
| `LICENSE` | 1.1 KB | MIT License | 2026-02-27 | Editable |
| `NEXT_TASKS.md` | 5 B | Current task status ("Done") | 2026-03-01 | Editable |
| `PHASE1_REPORT.md` | 5.7 KB | Phase 1 specifications and verification | 2026-02-28 | Editable |
| `Procfile` | 62 B | Render.com deployment config | 2026-02-28 | Editable |
| `PROGRESS.md` | 9.6 KB | Sprint 1-5 completion log | 2026-03-01 | Editable |
| `README.md` | 5.3 KB | Repository overview and quick start | 2026-02-28 | Editable |
| `ROADMAP.md` | 1.6 KB | Original development roadmap | 2026-02-28 | Editable |
| `ROADMAP_v2.md` | 16.2 KB | Full 4-phase development roadmap | 2026-02-28 | Editable |
| `SPRINT_REPORT.md` | 3.1 KB | Sprint completion summary | 2026-02-28 | Editable |
| `TASKS.md` | 14.4 KB | Sprint 1 detailed task breakdown | 2026-02-28 | Editable |
| `a.claudestartup_message.txt` | 43 B | Claude Code startup message | 2026-02-28 | Editable |
| `nohup.out` | 128 B | Background process output | 2026-03-01 | Generated |
| `render.yaml` | 247 B | Render.com service definition | 2026-02-28 | Editable |
| `requirements.txt` | 87 B | Python dependencies | 2026-03-01 | Editable |

## simulator/ — Combat Engine (Core)

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `simulator/__init__.py` | 78 B | Package init, exports key classes | 2026-02-27 | Editable |
| `simulator/__main__.py` | 17.2 KB | CLI interface (single/round-robin/series) | 2026-02-28 | Editable |
| `simulator/abilities.py` | 19.8 KB | Ability proc logic, effect application | 2026-02-28 | Editable |
| `simulator/ability_grammar.py` | 30.5 KB | Formal grammar for 14 core animals | 2026-02-28 | Editable |
| `simulator/animals.py` | 15.8 KB | Animal types, stat blocks, definitions | 2026-02-28 | Editable |
| `simulator/config.json` | 13.7 KB | All game parameters | 2026-02-27 | **FROZEN** |
| `simulator/engine.py` | 21.8 KB | Core tick loop, combat simulation | 2026-02-28 | Editable |
| `simulator/grid.py` | 7.3 KB | 8x8 arena, pathfinding, ring zone | 2026-02-27 | Editable |
| `simulator/seed.py` | 2.1 KB | SHA-256 deterministic RNG | 2026-02-27 | Editable |

## agents/ — Agent Implementations

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `agents/__init__.py` | 57 B | Package init | 2026-02-27 | Editable |
| `agents/baselines.py` | 10.5 KB | 5 baseline agents | 2026-02-28 | Editable |
| `agents/gemini_agent.py` | 7.8 KB | Google Gemini integration | 2026-03-01 | Editable |
| `agents/llm_agent.py` | 6.2 KB | T001 LLM agent (plain text) | 2026-02-28 | Editable |
| `agents/llm_agent_v2.py` | 12.9 KB | T002 LLM agent (structured JSON) | 2026-02-28 | Editable |

## prompts/ — Prompt Templates

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `prompts/__init__.py` | 49 B | Package init | 2026-02-27 | Editable |
| `prompts/meta_extractor.py` | 4.0 KB | Top-N build extractor for meta context | 2026-02-27 | Editable |
| `prompts/t001_prompt.txt` | 1.8 KB | Tournament 001 prompt | 2026-02-27 | Editable |
| `prompts/t002_prompt.txt` | 3.8 KB | Tournament 002 prompt | 2026-02-27 | Editable |
| `prompts/t002_v2.txt` | 4.1 KB | Paraphrased T002 variant 2 (PSI) | 2026-03-01 | Editable |
| `prompts/t002_v3.txt` | 4.1 KB | Paraphrased T002 variant 3 (PSI) | 2026-03-01 | Editable |

## data/ — Tournament Results

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `data/tournament_001/report.md` | 3.5 KB | T001 summary with BT rankings | 2026-02-27 | **FROZEN** |
| `data/tournament_001/results.jsonl` | 670.5 KB | T001 match records (779 series) | 2026-02-27 | **FROZEN** |
| `data/tournament_002/adaptation_analysis.md` | 5.0 KB | T002 adaptation behavior analysis | 2026-02-27 | **FROZEN** |
| `data/tournament_002/report.md` | 3.9 KB | T002 summary with BT rankings | 2026-02-27 | **FROZEN** |
| `data/tournament_002/results.jsonl` | 1.2 MB | T002 match records (780 series) | 2026-02-27 | **FROZEN** |
| `data/tournament_002/results_chunk_0.jsonl` | 201.1 KB | T002 data chunk 0 | 2026-02-27 | **FROZEN** |
| `data/tournament_002/results_chunk_1.jsonl` | 352.0 KB | T002 data chunk 1 | 2026-02-27 | **FROZEN** |
| `data/tournament_002/results_chunk_2.jsonl` | 341.0 KB | T002 data chunk 2 | 2026-02-27 | **FROZEN** |
| `data/tournament_002/results_chunk_3.jsonl` | 340.1 KB | T002 data chunk 3 | 2026-02-27 | **FROZEN** |
| `data/tournament_003/results.md` | 5.9 KB | T003 preliminary results | 2026-02-28 | Editable |
| `data/tournament_003/results_balanced.md` | 5.2 KB | T003 balanced track results | 2026-02-28 | Editable |

## analysis/ — Analysis Scripts

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `analysis/__init__.py` | 71 B | Package init | 2026-02-28 | Editable |
| `analysis/bt_ranking.py` | 7.8 KB | Bradley-Terry + Elo rating system | 2026-02-28 | Editable |
| `analysis/pairwise_matrix.py` | 3.8 KB | JSONL to pairwise win-rate matrix | 2026-02-27 | Editable |
| `analysis/requirements.txt` | 26 B | scipy dependency | 2026-02-27 | Editable |
| `analysis/seasonal_report.py` | 24.4 KB | Auto-generate season reports | 2026-03-01 | Editable |

## docs/ — Documentation

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `docs/AGENT_API.md` | 5.8 KB | MoreauAgent interface specification | 2026-03-01 | Editable |
| `docs/CONTRIBUTING.md` | 5.2 KB | How to add your own model | 2026-02-28 | Editable |
| `docs/FAQ.md` | 3.9 KB | 10 frequently asked questions | 2026-03-01 | Editable |
| `docs/LANGUAGE_GUIDE.md` | 3.7 KB | Approved terminology | 2026-03-01 | Editable |
| `docs/LAUNCH_CHECKLIST.md` | 3.2 KB | 4 launch gates with pass/fail | 2026-03-01 | Editable |
| `docs/MEASUREMENT_SPEC.md` | 12.1 KB | BT, CI, non-transitivity, PSI methodology | 2026-02-28 | Editable |
| `docs/MECHANICS.md` | 6.7 KB | Complete game rules and formulas | 2026-02-28 | Editable |
| `docs/MMR_SPEC.md` | 13.9 KB | Match Record Format v1.1 schema | 2026-02-28 | Editable |
| `docs/TRACKS.md` | 16.0 KB | Track A/B/C/D definitions | 2026-02-28 | Editable |
| `docs/social/linkedin.md` | 1.8 KB | LinkedIn post template | 2026-02-28 | Editable |
| `docs/social/reddit_localllama.md` | 4.1 KB | r/LocalLLaMA post template | 2026-02-28 | Editable |
| `docs/social/reddit_ml.md` | 6.4 KB | r/MachineLearning post template | 2026-02-28 | Editable |
| `docs/social/twitter_thread.md` | 1.4 KB | Twitter thread template | 2026-02-28 | Editable |

## Experiment Runners

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `lab_mode.py` | 43.8 KB | Interactive iteration experiment | 2026-03-01 | Editable |
| `run_ablation.py` | 35.6 KB | 5 ablation variants | 2026-03-01 | Editable |
| `run_challenge.py` | 27.7 KB | Challenge mode (LLM vs baselines) | 2026-02-28 | Editable |
| `run_planning.py` | 25.2 KB | Ban/pick planning suite | 2026-03-01 | Editable |
| `run_po.py` | 16.2 KB | Partial observability suite | 2026-03-01 | Editable |
| `run_psi.py` | 21.0 KB | Prompt Sensitivity Index | 2026-03-01 | Editable |

## moreau_script/ — DSL

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `moreau_script/__init__.py` | 905 B | Package init | 2026-03-01 | Editable |
| `moreau_script/__main__.py` | 1.9 KB | CLI entry point | 2026-03-01 | Editable |
| `moreau_script/interpreter.py` | 7.8 KB | Sandboxed interpreter | 2026-03-01 | Editable |
| `moreau_script/parser.py` | 6.1 KB | Safe parser (IF/ELIF/ELSE) | 2026-03-01 | Editable |
| `moreau_script/script_agent.py` | 6.9 KB | ScriptAgent (BaseAgent impl) | 2026-03-01 | Editable |
| `moreau_script/validator.py` | 4.8 KB | Security validation | 2026-03-01 | Editable |
| `moreau_script/examples/counter_pick.ms` | 339 B | Counter-pick strategy | 2026-03-01 | Editable |
| `moreau_script/examples/random_strategy.ms` | 113 B | Random pick example | 2026-03-01 | Editable |
| `moreau_script/examples/stat_optimizer.ms` | 239 B | ATK maximizer | 2026-03-01 | Editable |

## seasons/ — Season System

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `seasons/__init__.py` | 0 B | Package init | 2026-03-01 | Editable |
| `seasons/SEASON_RULES.md` | 1.8 KB | Season system documentation | 2026-03-01 | Editable |
| `seasons/ability_generator.py` | 20.8 KB | Procedural ability generation | 2026-03-01 | Editable |
| `seasons/patch_generator.py` | 8.3 KB | EMA-based balance patch generator | 2026-03-01 | Editable |
| `seasons/season_0_base.json` | 13.7 KB | Frozen core config copy | 2026-03-01 | Editable |
| `seasons/season_1_patch.json` | 13.1 KB | First balance patch | 2026-03-01 | Editable |

## web/ — Web UI

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `web/README.md` | 1.3 KB | Web deployment instructions | 2026-02-28 | Editable |
| `web/app.py` | 21.6 KB | FastAPI application | 2026-03-01 | Editable |
| `web/static/index.html` | 7.9 KB | Navigation hub | 2026-03-01 | Editable |
| `web/static/leaderboard.html` | 26.3 KB | BT/Elo leaderboard + heatmap | 2026-03-01 | Editable |
| `web/static/play.html` | 15.7 KB | Create your fighter form | 2026-03-01 | Editable |
| `web/static/research.html` | 10.6 KB | Academic summary page | 2026-03-01 | Editable |

## tests/ — Test Infrastructure

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `tests/test_invariants.py` | 33.9 KB | 89 invariant tests | 2026-03-01 | Editable |
| `tests/RESULTS.md` | 5.6 KB | Test results documentation | 2026-02-28 | Editable |
| `tests/mac_test.md` | 830 B | macOS test notes | 2026-02-28 | Editable |
| `tests/phase1_api_tests.md` | 2.8 KB | Phase 1 API test notes | 2026-02-28 | Editable |
| `tests/phase1_results.md` | 5.1 KB | Phase 1 test results | 2026-02-28 | Editable |

## paper/ — Academic Paper

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `paper/moreau_arena.tex` | 51.1 KB | LaTeX source | 2026-02-28 | Editable |
| `paper/moreau_arena.pdf` | 465.3 KB | Compiled PDF | 2026-02-28 | Generated |
| `paper/moreau_arena.aux` | 11.5 KB | LaTeX auxiliary | 2026-02-28 | Generated |
| `paper/moreau_arena.log` | 46.3 KB | LaTeX compilation log | 2026-02-28 | Generated |
| `paper/moreau_arena.out` | 4.9 KB | Hyperref output | 2026-02-28 | Generated |

## results/ — Experiment Outputs

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `results/ablation_*_*.jsonl` | Various | Ablation dry-run results | 2026-03-01 | Generated |
| `results/challenge_DryRun-test_t001_*.jsonl` | 17.1 KB | Challenge dry-run (T001) | 2026-02-28 | Generated |
| `results/challenge_DryRun-test_t002_*.jsonl` | ~19 KB | Challenge dry-run (T002) | 2026-02-28 | Generated |
| `results/lab_test_*.json` | 3.4 KB | Lab mode iteration curves | 2026-02-28 | Generated |
| `results/planning_*.jsonl` | 4.0 KB | Planning suite results | 2026-03-01 | Generated |
| `results/po_fog05_*.jsonl` | 15.1 KB | Partial observability results | 2026-03-01 | Generated |
| `results/psi_*.json` | 3.1 KB | PSI computation results | 2026-03-01 | Generated |
| `results/psi_series_*.jsonl` | 102.9 KB | PSI series match data | 2026-03-01 | Generated |
| `reports/season_1_report.md` | 4.0 KB | Season 1 auto-report | 2026-03-01 | Generated |
| `reports/season_2_report.md` | 5.8 KB | Season 2 auto-report | 2026-03-01 | Generated |

## scripts/ — Utilities

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `scripts/benchmark.py` | 3.7 KB | Performance benchmarking | 2026-02-28 | Editable |
| `scripts/generate_results_summary.py` | 14.4 KB | Generates RESULTS_SUMMARY.md from raw JSONL data | 2026-03-01 | Editable |
| `scripts/verify_handoff_consistency.py` | 11.0 KB | Cross-checks handoff docs against raw data (21 checks) | 2026-03-01 | Editable |
| `scripts/setup.sh` | 317 B | Environment setup | 2026-02-28 | Editable |

## handoff/ — Handoff Package

| Path | Size | Purpose | Modified | Status |
|------|------|---------|----------|--------|
| `handoff/README_START_HERE.md` | 4.1 KB | Entry point — reading order, what is frozen, next steps | 2026-03-01 | **Source of Truth** |
| `handoff/PROJECT_OVERVIEW.md` | — | What the project is, what it measures | 2026-03-01 | Editable |
| `handoff/CANONICAL_FORMULAS.md` | 6.0 KB | Exact formulas from config.json + prompts, discrepancies flagged | 2026-03-01 | **Source of Truth** |
| `handoff/RESULTS_SUMMARY.md` | 9.0 KB | BT rankings, pairwise matrices, W-L records (auto-generated) | 2026-03-01 | **Generated** |
| `handoff/ARCHITECTURE.md` | — | File structure, module relationships, data flow | 2026-03-01 | Editable |
| `handoff/KEY_DECISIONS.md` | — | Design rationale | 2026-03-01 | Editable |
| `handoff/HOW_TO_RUN.md` | — | Practical commands | 2026-03-01 | Editable |
| `handoff/DEVELOPMENT_GUIDE.md` | — | How to add agents, experiments, features | 2026-03-01 | Editable |
| `handoff/ROADMAP_STATUS.md` | — | What is done, what remains | 2026-03-01 | Editable |
| `handoff/FILES_MANIFEST.md` | — | This file — complete file listing | 2026-03-01 | Editable |
| `handoff/GLOSSARY.md` | — | Term definitions | 2026-03-01 | Editable |
| `handoff/CURRENT_STATE.md` | — | Current project state snapshot | 2026-03-01 | Editable |

---

## Summary Statistics

| Category | Files | Total Size |
|----------|-------|-----------|
| Simulator (core) | 9 | ~128 KB |
| Agents | 5 | ~38 KB |
| Experiment runners | 6 | ~170 KB |
| Prompts | 6 | ~18 KB |
| Tournament data (FROZEN) | 11 | ~3.2 MB |
| Analysis | 4 | ~36 KB |
| Documentation | 14 | ~93 KB |
| Web UI | 5 | ~82 KB |
| Moreau Script | 9 | ~29 KB |
| Seasons | 6 | ~58 KB |
| Tests | 5 | ~48 KB |
| Paper | 5 | ~580 KB |
| Results (generated) | ~20 | ~500 KB |
| Handoff package | 12 | ~50 KB |
| Scripts/utilities | 4 | ~30 KB |
| Project management | 12 | ~57 KB |
| Infrastructure | 5 | ~4 KB |

**Total:** ~130+ files, ~5.1 MB (excluding .git, .venv, __pycache__)
