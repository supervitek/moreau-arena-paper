# Roadmap Status — What Is Done, What Remains

## Summary

**21 of 21 planned tasks are complete.** All code is written, tested, and committed. The single remaining blocker is an API key for running real LLM ablation experiments.

---

## Phase 1: Harden the Instrument — COMPLETE

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| 1.1 | Core Measurement Spec | DONE | `docs/MEASUREMENT_SPEC.md` |
| 1.2 | MMR v1.1 (Match Record Format) | DONE | `docs/MMR_SPEC.md` |
| 1.3 | Track Formalization (A/B/C/D) | DONE | `docs/TRACKS.md` |
| 1.4 | Ablation Suite (5 variants) | DONE | `run_ablation.py` |
| 1.5 | PSI Mini-Suite | DONE | `run_psi.py`, `prompts/t002_v2.txt`, `prompts/t002_v3.txt` |
| 1.6 | Invariant Test Suite | DONE | `tests/test_invariants.py` (89 tests) |
| 1.7 | Ability Grammar Foundation | DONE | `simulator/ability_grammar.py` |
| 1.8 | T003-D/E Ablation Variants | DONE | Additional variants in `run_ablation.py` |
| 1.9 | Launch Checklist | DONE | `docs/LAUNCH_CHECKLIST.md` |
| 1.10 | FAQ | DONE | `docs/FAQ.md` |
| 1.11 | Language Guide | DONE | `docs/LANGUAGE_GUIDE.md` |

## Phase 2: Live Meta + Public Ladder — COMPLETE

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| 2.1 | Season System | DONE | `seasons/season_0_base.json`, `seasons/patch_generator.py`, `seasons/SEASON_RULES.md` |
| 2.2 | Public Leaderboard | DONE | `web/static/leaderboard.html`, `web/app.py` |
| 2.3 | Agent Submission API | DONE | `docs/AGENT_API.md`, `web/app.py` routes |
| 2.4 | Seasonal Meta Report | DONE | `analysis/seasonal_report.py`, `reports/season_*_report.md` |

## Phase 3: Depth Suites — COMPLETE

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| 3.1 | Lab Mode v2 | DONE | `lab_mode.py` (convergence, distance-to-optimum) |
| 3.2 | Partial Observability Suite | DONE | `run_po.py` (fog levels 0.0/0.5/1.0) |
| 3.3 | Ban/Pick Planning Suite | DONE | `run_planning.py` (draft phase) |

## Phase 4: Ecosystem — COMPLETE

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| 4.1 | Real LLM Ablation | DONE (code) | `agents/gemini_agent.py` — **blocked on GEMINI_API_KEY** |
| 4.2 | Moreau Script DSL | DONE | `moreau_script/` (parser, interpreter, validator, examples) |
| 4.3 | Rules-as-Data Generator | DONE | `seasons/ability_generator.py` |
| 4.4 | Tournament Challenge Platform | DONE | `web/static/play.html`, `web/static/research.html` |

---

## The One Blocker: GEMINI_API_KEY

All ablation code is complete and verified with `--dry-run`. Running real LLM ablations requires:

```bash
export GEMINI_API_KEY=your_key_here
python run_ablation.py --variant formulas-only --provider gemini --model gemini-2.0-flash-lite --series 5
```

This is the only thing blocking real experimental data from ablation studies. Everything else works.

Alternative providers also work:
```bash
export ANTHROPIC_API_KEY=your_key
python run_ablation.py --variant formulas-only --provider anthropic --model claude-sonnet-4-20250514 --series 5
```

---

## What Phase 5-6 Could Look Like

These are not planned — just possibilities for future development.

### Phase 5: Real Ablation Data + Paper Update

| Task | Description | Requires |
|------|-------------|----------|
| 5.1 | Run all 5 ablation variants with real LLMs | API key (any provider) |
| 5.2 | Analyze ablation results | Ablation data from 5.1 |
| 5.3 | Run Track C tournament (meta-conditioned) | API calls for 13 agents |
| 5.4 | Run Track D tournament (tool-augmented) | Simulator tool interface |
| 5.5 | Update paper with ablation + Track C/D results | LaTeX editing |
| 5.6 | Submit to arXiv | Paper ready |

### Phase 6: Community + Scale

| Task | Description | Requires |
|------|-------------|----------|
| 6.1 | Deploy web leaderboard publicly | Hosting (Render config exists) |
| 6.2 | Open agent submissions | Public API endpoint |
| 6.3 | Run Season 2 with new balance patch | Season 1 data analysis |
| 6.4 | Add more LLMs to tournament roster | API keys for new providers |
| 6.5 | Integrate Moreau Script into leaderboard | ScriptAgent → web pipeline |
| 6.6 | Community-contributed animals | Ability grammar + generator |

---

## What Needs Human Decisions vs. What Can Be Automated

### Needs Human Decisions

- **API key provisioning** — Which provider to use for ablations, budget allocation
- **Paper submission** — arXiv timing, author decisions, abstract revisions
- **Public deployment** — Domain name, hosting provider, access policies
- **Season transitions** — Approve balance patches before applying
- **New animal approval** — Review ability generator output before adding to roster
- **Track C/D tournament design** — Final protocol decisions for unrun tracks

### Can Be Automated

- **Running ablations** — `run_ablation.py` handles everything given an API key
- **Generating seasonal reports** — `analysis/seasonal_report.py` auto-generates from JSONL
- **Invariant testing** — 89 tests run automatically, block broken commits
- **Balance patch proposals** — `seasons/patch_generator.py` computes from data
- **Ability generation** — `seasons/ability_generator.py` with sampling + EV validation
- **BT/Elo computation** — `analysis/bt_ranking.py` recomputes from raw data
- **Web leaderboard updates** — API endpoints serve from computed data

---

## Sprint History

| Sprint | Date | Tasks Done | Key Achievement |
|--------|------|-----------|-----------------|
| Sprint 1 | 2026-02-28 | 5 | Paper fixes, simulator CLI, challenge script, lab mode, docs |
| Sprint 2 | 2026-03-01 | 8 | Launch checklist, FAQ, PSI suite, season system, agent API, lab mode v2 |
| Sprint 3 | 2026-03-01 | 4 | Leaderboard, seasonal reports, PO suite, planning suite |
| Sprint 4 | 2026-03-01 | 4 | Gemini agent, Moreau Script, ability generator, challenge platform |
| Sprint 5 | 2026-03-01 | 0 (commit) | Committed Phase 1 specs + roadmap, verified 89 tests pass |

Total development time: ~2 days across 5 sprints.
