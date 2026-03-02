# Current State — What Exists Right Now

**As of:** 2026-03-01
**Test status:** 89/89 passing (`python -m pytest tests/test_invariants.py`)
**Config hash:** `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` (verified)

---

## What Is Frozen vs. What Can Change

### Frozen (hash-verified, never modify)

| File | Hash Verified | Purpose |
|------|--------------|---------|
| `simulator/config.json` | SHA-256 in test suite | All game parameters |
| `data/tournament_001/results.jsonl` | SHA-256 in test suite | T001 match records |
| `data/tournament_001/report.md` | SHA-256 in test suite | T001 summary report |
| `data/tournament_002/results.jsonl` | SHA-256 in test suite | T002 match records |
| `data/tournament_002/results_chunk_0.jsonl` | SHA-256 in test suite | T002 chunk 0 |
| `data/tournament_002/results_chunk_1.jsonl` | SHA-256 in test suite | T002 chunk 1 |
| `data/tournament_002/results_chunk_2.jsonl` | SHA-256 in test suite | T002 chunk 2 |
| `data/tournament_002/results_chunk_3.jsonl` | SHA-256 in test suite | T002 chunk 3 |
| `data/tournament_002/report.md` | SHA-256 in test suite | T002 summary report |
| `data/tournament_002/adaptation_analysis.md` | SHA-256 in test suite | T002 adaptation report |

Total: 10 frozen files with hardcoded SHA-256 hashes in `tests/test_invariants.py`.

### Editable (extend freely)

Everything else — agents, experiments, analysis, web, docs, seasons, DSL, scripts.

---

## File Inventory by Category

### Simulator (Frozen Core)

| File | Size | Description |
|------|------|-------------|
| `simulator/__init__.py` | 78 B | Package init, exports key classes |
| `simulator/config.json` | 13.7 KB | **FROZEN** — All game parameters (stats, animals, abilities, grid, ring) |
| `simulator/engine.py` | 21.8 KB | Core combat tick loop, damage calculation, ability resolution |
| `simulator/animals.py` | 15.8 KB | Animal types, stat blocks, passive/ability definitions |
| `simulator/abilities.py` | 19.8 KB | Ability proc logic, effect application, duration tracking |
| `simulator/ability_grammar.py` | 30.5 KB | Formal grammar expressing all 14 core animals' abilities |
| `simulator/grid.py` | 7.3 KB | 8x8 arena grid, pathfinding (Chebyshev distance), ring zone |
| `simulator/seed.py` | 2.1 KB | SHA-256 deterministic RNG (tick/hit/proc seed derivation) |
| `simulator/__main__.py` | 17.2 KB | CLI interface (single match, round-robin, series modes) |

### Agents

| File | Size | Description |
|------|------|-------------|
| `agents/__init__.py` | 57 B | Package init |
| `agents/baselines.py` | 10.5 KB | 5 baseline agents (Random, Greedy, Smart, Conservative, HighVariance) |
| `agents/llm_agent.py` | 6.2 KB | T001 LLM agent — plain text prompt, regex parsing |
| `agents/llm_agent_v2.py` | 12.9 KB | T002 LLM agent — structured JSON output, meta context, adaptation |
| `agents/gemini_agent.py` | 7.8 KB | Google Gemini integration for ablation studies |

### Experiment Runners

| File | Size | Description |
|------|------|-------------|
| `run_challenge.py` | 27.7 KB | Challenge mode — test any LLM vs 5 baselines |
| `run_ablation.py` | 35.6 KB | 5 ablation variants isolating T002 components |
| `lab_mode.py` | 43.8 KB | Interactive iteration efficiency experiment |
| `run_psi.py` | 21.0 KB | Prompt Sensitivity Index — ranking stability across paraphrases |
| `run_planning.py` | 25.2 KB | Ban/pick planning suite with draft phase |
| `run_po.py` | 16.2 KB | Partial observability suite (fog levels 0.0/0.5/1.0) |

### Prompts

| File | Size | Description |
|------|------|-------------|
| `prompts/__init__.py` | 49 B | Package init |
| `prompts/t001_prompt.txt` | 1.8 KB | Tournament 001 prompt (qualitative descriptions) |
| `prompts/t002_prompt.txt` | 3.8 KB | Tournament 002 prompt (exact formulas + meta context) |
| `prompts/t002_v2.txt` | 4.1 KB | Paraphrased T002 prompt variant 2 (for PSI) |
| `prompts/t002_v3.txt` | 4.1 KB | Paraphrased T002 prompt variant 3 (for PSI) |
| `prompts/meta_extractor.py` | 4.0 KB | Extracts top-N builds from JSONL for meta context |

### Tournament Data

| File | Size | Description |
|------|------|-------------|
| `data/tournament_001/results.jsonl` | 670.5 KB | **FROZEN** — 779 series, 13 agents, blind pick |
| `data/tournament_001/report.md` | 3.5 KB | **FROZEN** — T001 summary with BT rankings |
| `data/tournament_002/results.jsonl` | 1.2 MB | **FROZEN** — 780 series, 13 agents, adaptive |
| `data/tournament_002/results_chunk_0.jsonl` | 201.1 KB | **FROZEN** — T002 data chunk 0 |
| `data/tournament_002/results_chunk_1.jsonl` | 352.0 KB | **FROZEN** — T002 data chunk 1 |
| `data/tournament_002/results_chunk_2.jsonl` | 341.0 KB | **FROZEN** — T002 data chunk 2 |
| `data/tournament_002/results_chunk_3.jsonl` | 340.1 KB | **FROZEN** — T002 data chunk 3 |
| `data/tournament_002/report.md` | 3.9 KB | **FROZEN** — T002 summary with BT rankings |
| `data/tournament_002/adaptation_analysis.md` | 5.0 KB | **FROZEN** — T002 adaptation behavior analysis |
| `data/tournament_003/results.md` | 5.9 KB | T003 preliminary results |
| `data/tournament_003/results_balanced.md` | 5.2 KB | T003 balanced track results |

### Analysis

| File | Size | Description |
|------|------|-------------|
| `analysis/__init__.py` | 71 B | Package init |
| `analysis/bt_ranking.py` | 7.8 KB | Bradley-Terry + Elo rating computation with bootstrap CI |
| `analysis/pairwise_matrix.py` | 3.8 KB | JSONL to pairwise win-rate matrix (CSV + heatmap) |
| `analysis/seasonal_report.py` | 24.4 KB | Auto-generates season reports (BT, Elo, heatmap, cycles) |
| `analysis/requirements.txt` | 26 B | scipy (for bootstrap CI) |

### Documentation

| File | Size | Description |
|------|------|-------------|
| `docs/MECHANICS.md` | 6.7 KB | Complete game rules and stat formulas |
| `docs/MEASUREMENT_SPEC.md` | 12.1 KB | BT scores, CI, non-transitivity, PSI methodology |
| `docs/MMR_SPEC.md` | 13.9 KB | Match Record Format v1.1 schema |
| `docs/TRACKS.md` | 16.0 KB | Track A/B/C/D definitions and protocols |
| `docs/AGENT_API.md` | 5.8 KB | MoreauAgent interface specification |
| `docs/CONTRIBUTING.md` | 5.2 KB | How to add your own model |
| `docs/FAQ.md` | 3.9 KB | 10 frequently asked questions |
| `docs/LANGUAGE_GUIDE.md` | 3.7 KB | Approved terminology for describing results |
| `docs/LAUNCH_CHECKLIST.md` | 3.2 KB | 4 launch gates with pass/fail criteria |
| `docs/social/twitter_thread.md` | 1.4 KB | Twitter thread template |
| `docs/social/linkedin.md` | 1.8 KB | LinkedIn post template |
| `docs/social/reddit_ml.md` | 6.4 KB | r/MachineLearning post template |
| `docs/social/reddit_localllama.md` | 4.1 KB | r/LocalLLaMA post template |

### Web UI

| File | Size | Description |
|------|------|-------------|
| `web/app.py` | 21.6 KB | FastAPI application (API routes + static serving) |
| `web/README.md` | 1.3 KB | Web deployment instructions |
| `web/static/index.html` | 7.9 KB | Navigation hub / landing page |
| `web/static/leaderboard.html` | 26.3 KB | Interactive BT/Elo leaderboard with heatmap |
| `web/static/play.html` | 15.7 KB | "Create your fighter" form with stat sliders |
| `web/static/research.html` | 10.6 KB | Academic face with methodology summary |

### Moreau Script (DSL)

| File | Size | Description |
|------|------|-------------|
| `moreau_script/__init__.py` | 905 B | Package init |
| `moreau_script/__main__.py` | 1.9 KB | CLI entry point |
| `moreau_script/parser.py` | 6.1 KB | Safe parser (IF/ELIF/ELSE + PREFER, max 50 rules) |
| `moreau_script/interpreter.py` | 7.8 KB | Sandboxed interpreter with iteration limit |
| `moreau_script/validator.py` | 4.8 KB | Security validation (no eval/exec/import) |
| `moreau_script/script_agent.py` | 6.9 KB | ScriptAgent implementing BaseAgent |
| `moreau_script/examples/random_strategy.ms` | 113 B | Random animal pick example |
| `moreau_script/examples/counter_pick.ms` | 339 B | Counter-pick strategy example |
| `moreau_script/examples/stat_optimizer.ms` | 239 B | ATK maximizer example |

### Seasons

| File | Size | Description |
|------|------|-------------|
| `seasons/__init__.py` | 0 B | Package init |
| `seasons/season_0_base.json` | 13.7 KB | Frozen core config copy (baseline for patches) |
| `seasons/season_1_patch.json` | 13.1 KB | First balance patch (EMA-adjusted proc rates) |
| `seasons/patch_generator.py` | 8.3 KB | EMA-based auto-balance patch generator |
| `seasons/ability_generator.py` | 20.8 KB | Rules-as-Data: procedural ability generation |
| `seasons/SEASON_RULES.md` | 1.8 KB | Season system documentation |

### Results (experiment outputs)

| File | Size | Description |
|------|------|-------------|
| `results/challenge_DryRun-test_t001_*.jsonl` | 17.1 KB | Dry-run challenge results (T001 protocol) |
| `results/challenge_DryRun-test_t002_*.jsonl` | ~19 KB | Dry-run challenge results (T002 protocol) |
| `results/lab_test_*.json` | 3.4 KB | Lab mode iteration curve data |
| `results/ablation_*_*.jsonl` | Various | Ablation variant dry-run results |
| `results/po_fog05_*.jsonl` | 15.1 KB | Partial observability dry-run results |
| `results/psi_*.json` | 3.1 KB | PSI computation results |
| `results/psi_series_*.jsonl` | 102.9 KB | PSI series match data |
| `results/planning_*.jsonl` | 4.0 KB | Planning suite dry-run results |
| `reports/season_1_report.md` | 4.0 KB | Auto-generated Season 1 report |
| `reports/season_2_report.md` | 5.8 KB | Auto-generated Season 2 report |

### Paper

| File | Size | Description |
|------|------|-------------|
| `paper/moreau_arena.tex` | 51.1 KB | LaTeX source for the paper |
| `paper/moreau_arena.pdf` | 465.3 KB | Compiled PDF |
| `paper/moreau_arena.aux` | 11.5 KB | LaTeX auxiliary file |
| `paper/moreau_arena.log` | 46.3 KB | LaTeX compilation log |
| `paper/moreau_arena.out` | 4.9 KB | LaTeX hyperref output |

### Tests

| File | Size | Description |
|------|------|-------------|
| `tests/test_invariants.py` | 33.9 KB | **89 tests** — config hash, determinism, stats, combat, grid, procs, data immutability, regressions, variance, monotonicity, hidden mechanics, symmetry |
| `tests/RESULTS.md` | 5.6 KB | Test results documentation |
| `tests/phase1_results.md` | 5.1 KB | Phase 1 test results |
| `tests/phase1_api_tests.md` | 2.8 KB | Phase 1 API test notes |
| `tests/mac_test.md` | 830 B | macOS test notes |

### Project Management

| File | Size | Description |
|------|------|-------------|
| `README.md` | 5.3 KB | Repository overview and quick start |
| `CLAUDE.md` | 516 B | Rules for Claude Code sessions |
| `AGENTS.md` | 751 B | Rules for automated agent sessions |
| `ROADMAP.md` | 1.6 KB | Original development roadmap |
| `ROADMAP_v2.md` | 16.2 KB | Full 4-phase development roadmap |
| `PROGRESS.md` | 9.6 KB | Sprint 1-5 completion log |
| `TASKS.md` | 14.4 KB | Sprint 1 detailed task breakdown |
| `NEXT_TASKS.md` | 5 B | Current task status ("Done") |
| `PHASE1_REPORT.md` | 5.7 KB | Phase 1 specifications and verification |
| `SPRINT_REPORT.md` | 3.1 KB | Sprint completion summary |
| `LICENSE` | 1.1 KB | MIT License |
| `.gitignore` | 337 B | Git ignore rules |

### Infrastructure

| File | Size | Description |
|------|------|-------------|
| `requirements.txt` | 87 B | Python dependencies |
| `Procfile` | 62 B | Render.com deployment config |
| `render.yaml` | 247 B | Render.com service definition |
| `scripts/setup.sh` | 317 B | Environment setup script |
| `scripts/benchmark.py` | 3.7 KB | Performance benchmarking script |
| `a.claudestartup_message.txt` | 43 B | Claude Code startup message |
| `nohup.out` | 128 B | Background process output |
