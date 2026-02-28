# Sprint Report — 2026-02-28

## Summary

Three parallel teammates executed 9 tasks across testing, web UI, and code quality. All tasks completed successfully with zero blocking issues.

## Commits

| Commit | Author | Description |
|--------|--------|-------------|
| `d070075` | tester | test: verify all scripts pass -- simulator, challenge, lab_mode |
| `7994c9f` | web | feat: add FastAPI web UI for fight simulator |
| `c5d29c3` | quality | chore: clean up unused imports, add analysis __init__.py, requirements.txt, setup script |

## What Was Built

### Testing (tester, tasks #1-5)

All scripts verified working:

| Test | Command | Result |
|------|---------|--------|
| Single match | `python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 100` | PASS -- bear wins 78-22% |
| Round-robin | `python -m simulator --round-robin` with 5 paper builds | PASS -- bear dominates (83.2% avg WR) |
| Challenge T001 | `python run_challenge.py --dry-run --protocol t001 --series 3` | PASS -- BT score 0.308 |
| Challenge T002 | `python run_challenge.py --dry-run --protocol t002 --series 3` | PASS -- adaptive boosts WR 27%->47% |
| Lab mode | `python lab_mode.py --dry-run --rounds 3` | PASS -- converges in 3 rounds |

No bugs found in any script. Full results in `tests/RESULTS.md`.

### Web UI (web, task #6)

FastAPI web application in `web/`:

- **POST /fight** -- accepts two builds + game count, returns win/loss/draw + avg ticks
- **GET /leaderboard** -- aggregates results from `results/*.jsonl` files
- **GET /** -- serves dark-themed HTML page with fight form
- Error handling for invalid animals, bad stat sums, stats < 1
- All endpoints tested with curl and verified

Files: `web/app.py`, `web/static/index.html`, `web/README.md`

### Code Quality (quality, tasks #7-9)

**Code review:**
- Fixed 23 unused imports (F401) across 9 files
- Created missing `analysis/__init__.py` (was blocking `python -m analysis.*`)
- No hardcoded paths, no syntax errors, no critical issues

**Analysis verification:**
- All 4 analysis script runs pass (bt_ranking + pairwise_matrix for both T001 and T002)

**Infrastructure:**
- Created root `requirements.txt` (scipy, numpy, fastapi, uvicorn, flake8)
- Created `scripts/setup.sh` with venv creation + import verification
- Updated `.gitignore` with `results/` and `venv/`

## What Works

- All CLI scripts (simulator, challenge, lab_mode)
- All analysis scripts (bt_ranking, pairwise_matrix) with both tournament datasets
- Web UI with fight endpoint and leaderboard
- Clean imports across all Python files

## What Needs Fixing

Nothing critical. Potential follow-ups:

- Web UI leaderboard depends on `results/` directory having JSONL files (returns empty if none exist)
- `scripts/setup.sh` uses `source venv/bin/activate` (Linux/Mac) -- Windows users need `venv\Scripts\activate`
- No automated test suite (pytest) yet -- only manual test results in `tests/RESULTS.md`
- Web UI has no authentication or rate limiting (fine for local use)
