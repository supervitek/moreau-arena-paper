# Phase 1 Report — Moreau Arena Publication Sprint

**Date:** February 28 – March 1, 2026
**Platform:** Mac Mini M4, macOS Sequoia 24.6.0
**Method:** 3-agent parallel team (platform, content, testing)

---

## What Was Built

### Deployment Infrastructure
- **render.yaml** — Render.com free tier config (Python, uvicorn, auto-deploy)
- **Procfile** — `web: uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8000}`
- Status: **Ready to deploy** (just connect GitHub repo to Render)

### API v1 Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/fight` | POST | Run N games between two builds |
| `/api/v1/leaderboard` | GET | Ranked agent performance data |
| `/api/v1/challenge` | POST | Test a build against 5 reference builds |
| `/fight` | POST | Legacy endpoint (still works) |
| `/leaderboard` | GET | Legacy endpoint (still works) |

- CORS enabled (all origins)
- All endpoints tested: **10/10 pass**

### 4 New Animals (18 total)
| Animal | Passive | Abilities |
|--------|---------|-----------|
| **Rhino** | Iron Hide (20% dmg reduction above 50% HP) | Horn Slam (+30% dmg), Trample (25% base_dmg instant) |
| **Panther** | Shadow Stalk (first attack 2x crit) | Shadow Pounce (+60% dmg), Fade Out (+40% dodge, 2 ticks) |
| **Hawk** | Thermal Soar (movement +1) | Dive Strike (+90% dmg), Screech (+15% miss chance, 3 ticks) |
| **Viper** | Hemotoxin (35% chance: 1% max_hp DoT, 2 ticks, 2 stacks max) | Quick Strike (+25% dmg), Constrict (1 tick stun) |

### Marketing Content
| File | Description |
|------|-------------|
| `docs/social/twitter_thread.md` | 5-tweet thread with hook, findings, and CTA |
| `docs/social/reddit_ml.md` | 800-word r/MachineLearning post (academic) |
| `docs/social/reddit_localllama.md` | r/LocalLLaMA post (casual, quick-start) |
| `docs/social/linkedin.md` | 270-word professional LinkedIn post |

---

## Performance Stats

### Benchmark (Mac Mini M4)
- **2,114 fights/sec** (0.47ms per fight)
- Python 3.14.3, scipy 1.17.1, numpy 2.4.2
- Linear scaling confirmed up to 5,000 fights

### 18-Animal Tournament (balanced, 500 games/pair, seed 777)
| Rank | Animal | Win Rate |
|------|--------|----------|
| 1 | Rhino | 81.1% |
| 2 | Viper | 74.4% |
| 3 | Wolf | 64.6% |
| 4 | Buffalo | 62.1% |
| 5 | Panther | 60.6% |
| 6 | Snake | 58.6% |
| 7 | Bear | 56.3% |
| 8 | Tiger | 55.5% |
| 9 | Scorpion | 53.0% |
| 10 | Boar | 50.7% |
| 11 | Eagle | 48.6% |
| 12 | Fox | 47.2% |
| 13 | Monkey | 36.2% |
| 14 | Hawk | 32.8% |
| 15 | Raven | 29.9% |
| 16 | Owl | 29.5% |
| 17 | Crocodile | 29.4% |
| 18 | Shark | 29.0% |

**No animal exceeds 85% win rate** at equal stats.

---

## Balance Fix Details

### Problem (pre-fix)
- Viper: **99.9% win rate** — Hemotoxin fired on every hit (guaranteed), 5 stacks max, 2% max_hp/tick
- Rhino: **93.5% win rate** — Iron Hide flat -2 damage (33% reduction at base_dmg=6), Horn Slam +80%, Trample 60% + stun

### Changes Applied

**Viper — Hemotoxin passive:**
| Parameter | Before | After |
|-----------|--------|-------|
| Trigger | Every hit (100%) | 35% chance per hit |
| Max stacks | 5 | 2 |
| Damage/tick | 2% max_hp | 1% max_hp |
| Duration | 3 ticks | 2 ticks |

**Viper — Quick Strike ability:**
| Parameter | Before | After |
|-----------|--------|-------|
| ATK modifier | +40% | +25% |

**Rhino — Iron Hide passive:**
| Parameter | Before | After |
|-----------|--------|-------|
| Reduction | Flat -2 damage (always) | 20% damage reduction (above 50% HP only) |

**Rhino — Horn Slam ability:**
| Parameter | Before | After |
|-----------|--------|-------|
| ATK modifier | +80% | +30% |

**Rhino — Trample ability:**
| Parameter | Before | After |
|-----------|--------|-------|
| Instant damage | 60% base_dmg + stun | 25% base_dmg (no stun) |

### Result
- Viper: 99.9% → **74.4%**
- Rhino: 93.5% → **81.1%**

---

## API Test Results

All tests run via curl against local uvicorn server:

| Test | Result |
|------|--------|
| POST /api/v1/fight (valid builds) | PASS |
| POST /api/v1/fight (invalid build) | PASS (400) |
| POST /api/v1/fight (empty build) | PASS (422) |
| GET /api/v1/leaderboard | PASS |
| POST /api/v1/challenge | PASS |
| CORS headers present | PASS |
| Legacy /fight still works | PASS |
| Legacy /leaderboard still works | PASS |
| Web UI serves at / | PASS |
| Render config valid | PASS |

---

## Deployment Readiness

| Component | Status |
|-----------|--------|
| Simulator (18 animals) | Ready |
| Web UI (FastAPI) | Ready |
| API v1 (fight/leaderboard/challenge) | Ready |
| CORS | Enabled |
| render.yaml | Valid |
| Procfile | Valid |
| requirements.txt | Complete |
| Balance | Verified (no animal >85%) |
| Marketing content | 4/4 posts written |
| Demo screenshot | Pending (needs live server) |

**Next step:** Connect GitHub repo to Render.com dashboard and deploy.

---

## Files Modified/Created

```
New files:
  render.yaml
  Procfile
  ROADMAP.md
  PHASE1_REPORT.md
  scripts/benchmark.py
  docs/social/twitter_thread.md
  docs/social/reddit_ml.md
  docs/social/reddit_localllama.md
  docs/social/linkedin.md
  data/tournament_003/results.md
  data/tournament_003/results_balanced.md
  tests/phase1_api_tests.md
  tests/phase1_results.md

Modified files:
  web/app.py (CORS + API v1 endpoints)
  simulator/animals.py (4 new animals)
  simulator/abilities.py (new ability handlers + balance tuning)
  simulator/engine.py (new passive handlers + balance tuning)
  simulator/__main__.py (THERMAL_SOAR movement support)
```
