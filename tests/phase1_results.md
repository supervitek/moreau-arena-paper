# Phase 1 Complete Test Results

**Date:** 2026-02-28
**Platform:** Mac Mini M4, Darwin 24.6.0, Python 3.14.3
**Tester:** testing agent

---

## 1. Benchmark Results (5000 fights)

| Metric | Value |
|--------|-------|
| Total fights | 5,000 |
| Total time | 2.365s |
| Per fight | 0.47ms |
| Fights/sec | 2,114 |
| Avg ticks/fight | 12.5 |
| Build A wins | 2,595 (51.9%) |
| Build B wins | 2,405 (48.1%) |
| Draws | 0 (0.0%) |

**Summary:** Simulator runs at ~2,100 fights/sec on M4. Consistent with 1000-fight baseline (2,105 fights/sec). Linear scaling confirmed.

---

## 2. API Endpoint Tests (10/10 PASS)

| # | Test | Endpoint | Expected | Result |
|---|------|----------|----------|--------|
| 1 | Valid fight | POST /api/v1/fight | 200 | PASS |
| 2 | Invalid animal | POST /api/v1/fight | 400 | PASS |
| 3 | Bad stat sum | POST /api/v1/fight | 400 | PASS |
| 4 | Empty build | POST /api/v1/fight | 422 | PASS |
| 5 | Leaderboard | GET /api/v1/leaderboard | 200 | PASS |
| 6 | Challenge | POST /api/v1/challenge | 200 | PASS |
| 7 | CORS headers | HEAD /api/v1/leaderboard | CORS present | PASS |
| 8 | Legacy fight | POST /fight | 200 | PASS |
| 9 | Legacy leaderboard | GET /leaderboard | 200 | PASS |
| 10 | Invalid challenge | POST /api/v1/challenge | 400 | PASS |

See `tests/phase1_api_tests.md` for full details.

---

## 3. New Animal Tests

### 3a. New Animals Implemented

| Animal | Passive | Ability 1 | Ability 2 | Fights OK |
|--------|---------|-----------|-----------|-----------|
| Rhino | Yes | Horn Slam | Rhino Trample | PASS |
| Panther | Yes | Shadow Pounce | Fade Out | PASS |
| Hawk | Yes | Dive Strike | Screech Debuff | PASS |
| Viper | Yes | Quick Strike | Constrict Stun | PASS |

### 3b. New Animal Mini Round-Robin (200 games/pair, non-standard builds)

| Rank | Animal | Build | Avg WR |
|------|--------|-------|--------|
| 1 | Rhino | 6/8/3/3 | 100.0% |
| 2 | Viper | 4/6/7/3 | 49.5% |
| 3 | Panther | 3/6/8/3 | 46.8% |
| 4 | Hawk | 3/5/8/4 | 3.7% |

### 3c. Cross-Species Matchups (new vs original, 200 games)

| Matchup | Result |
|---------|--------|
| Rhino 5/8/4/3 vs Bear 3/14/2/1 | Bear wins 64.5% (bear's extreme ATK allocation) |
| Panther 4/5/8/3 vs Tiger 3/8/6/3 | Tiger wins 78.5% |
| Hawk 4/5/7/4 vs Eagle 2/8/6/4 | Eagle wins 76.0% |
| Viper 3/7/6/4 vs Snake 4/6/7/3 | Viper wins 90.5% |

---

## 4. Full 18-Animal Balance Assessment (equal stats 5/5/5/5, 100 games/pair)

**CRITICAL FINDING: Viper and Rhino are severely overpowered**

| Rank | Animal | Avg WR | Assessment |
|------|--------|--------|------------|
| 1 | **Viper** | **99.9%** | **OVERPOWERED** - beats every animal including rhino |
| 2 | **Rhino** | **93.5%** | **OVERPOWERED** - loses only to viper |
| 3 | Wolf | 59.6% | Slightly strong |
| 4 | Panther | 57.9% | Slightly strong |
| 5 | Buffalo | 56.9% | Balanced |
| 6 | Bear | 56.1% | Balanced |
| 7 | Snake | 55.9% | Balanced |
| 8 | Tiger | 50.6% | Perfectly balanced |
| 9 | Scorpion | 47.9% | Balanced |
| 10 | Fox | 47.5% | Balanced |
| 11 | Eagle | 46.8% | Balanced |
| 12 | Boar | 46.2% | Balanced |
| 13 | Monkey | 34.5% | Slightly weak |
| 14 | Hawk | 32.8% | Weak |
| 15 | Owl | 30.5% | Weak |
| 16 | Crocodile | 28.1% | Weak |
| 17 | Shark | 27.7% | Weak |
| 18 | Raven | 27.5% | Weak |

**Balance Notes:**
- Viper is nearly unbeatable at equal stats (99.9% WR). Quick Strike + Constrict Stun likely needs tuning.
- Rhino at 93.5% WR is also far above the original animals' range (27-60%).
- The original 14 animals range from 27.5% to 59.6% -- reasonable spread.
- Panther slots into the balanced tier nicely at 57.9%.
- Hawk at 32.8% is on the weak side but within the original animal range.
- **Recommendation:** Reduce viper's Quick Strike and/or Constrict Stun proc rates/damage. Reduce rhino's Horn Slam/Trample damage or add a counterplay mechanic.

---

## 5. Deployment Readiness

| Check | Status |
|-------|--------|
| render.yaml | Valid: web service, python, pip install, uvicorn, free plan |
| Procfile | Valid: `web: uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8000}` |
| requirements.txt | Has all deps: scipy, numpy, fastapi, uvicorn, flake8 |
| Web server starts | PASS |
| Index page loads | PASS |
| API v1 endpoints work | PASS (all 6 routes) |
| CORS configured | PASS (allow all origins) |
| Legacy routes preserved | PASS |

**Deployment Status: READY** (pending balance fix for viper/rhino)

---

## 6. Summary

| Category | Status |
|----------|--------|
| Simulator engine | PASS - 2,114 fights/sec |
| API v1 endpoints | PASS - 10/10 tests |
| CORS middleware | PASS |
| 4 new animals | PASS - all implemented and fighting |
| Animal balance | WARNING - viper (99.9%) and rhino (93.5%) overpowered |
| Deployment files | PASS - render.yaml + Procfile valid |
| Legacy compatibility | PASS - old routes work |
| Tournament results | PENDING - waiting for platform to run tournament_003 |
