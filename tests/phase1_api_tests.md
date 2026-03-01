# Phase 1 API Test Results

**Date:** 2026-02-28
**Platform:** Mac Mini M4, Darwin 24.6.0, Python 3.14.3
**Tester:** testing agent

## API v1 Endpoints

| # | Test | Method | Endpoint | Input | Expected | Actual | Status |
|---|------|--------|----------|-------|----------|--------|--------|
| 1 | Valid fight | POST | /api/v1/fight | bear vs buffalo, 10 games | 200 + JSON | 200, `{"build1_wins":7,"build2_wins":3,"draws":0,"avg_ticks":12.8}` | PASS |
| 2 | Invalid animal | POST | /api/v1/fight | dragon (nonexistent) | 400 | 400, clear error listing valid animals | PASS |
| 3 | Bad stat sum | POST | /api/v1/fight | stats sum to 24 | 400 | 400, "Stats must sum to 20, got 24" | PASS |
| 4 | Empty build | POST | /api/v1/fight | empty string | 4xx | 422, validation error | PASS |
| 5 | Leaderboard | GET | /api/v1/leaderboard | - | 200 + JSON array | 200, 6 agents sorted by win_rate | PASS |
| 6 | Challenge | POST | /api/v1/challenge | tiger 5 8 4 3, 50 games | 200 + results vs refs | 200, results against 5 reference builds + overall_win_rate | PASS |
| 7 | CORS headers | HEAD | /api/v1/leaderboard | Origin: example.com | access-control-allow-origin | `access-control-allow-origin: *`, `access-control-allow-credentials: true` | PASS |
| 8 | Legacy fight | POST | /fight | bear vs buffalo | 200 | 200 | PASS |
| 9 | Legacy leaderboard | GET | /leaderboard | - | 200 | 200 | PASS |
| 10 | Invalid challenge | POST | /api/v1/challenge | unicorn (nonexistent) | 400 | 400 | PASS |

**Result: 10/10 PASS**

## Deployment Files

| File | Check | Status |
|------|-------|--------|
| render.yaml | Valid YAML structure, has `services` with web type, python runtime, pip install build cmd, uvicorn start cmd, free plan, PYTHON_VERSION=3.11 | PASS |
| Procfile | Has `web:` prefix, uses uvicorn with `--host 0.0.0.0 --port ${PORT:-8000}` | PASS |
| requirements.txt | Lists scipy, numpy, fastapi, uvicorn, flake8 | PASS |

## Baseline Tests

| Test | Result |
|------|--------|
| Simulator CLI: single match (100 games) | PASS - bear 78%, buffalo 22%, 0 draws, 12.3 avg ticks |
| Simulator CLI: deterministic (seed=42) | PASS - results reproducible |
| Web server: starts on uvicorn | PASS |
| Web server: serves index.html at / | PASS |
| Benchmark: 1000 fights | PASS - 2,105 fights/sec, 0.47ms/fight |

## Notes

- CORS middleware configured with `allow_origins=["*"]` (permissive, suitable for public API)
- New /api/v1/challenge endpoint tests build against 5 reference builds
- Reference builds: bear 5/5/5/5, tiger 3/8/6/3, buffalo 8/6/4/2, wolf 4/6/7/3, scorpion 5/5/5/5
- Error messages include full list of valid animals (already includes new animals: rhino, panther, hawk, viper)
- Legacy routes (/fight, /leaderboard) preserved and working alongside /api/v1/ routes
