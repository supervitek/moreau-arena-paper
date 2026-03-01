# ROADMAP — Moreau Arena

## PHASE 1: PUBLICATION (Weekend Sprint — Feb 28-Mar 2, 2026)

### Platform (deploy + API + animals)
- [x] Add `render.yaml` + `Procfile` for Render.com free tier deployment
- [x] Add `/api/v1/` REST endpoints: `POST /fight`, `GET /leaderboard`, `POST /challenge`
- [x] Add CORS middleware for cross-origin frontend access
- [x] Add 4 new animals to simulator: Rhino, Panther, Hawk, Viper
- [x] Rerun round-robin with all animals, update leaderboard data
- [x] Balance tuning: Viper and Rhino nerfed, all animals under 85% win rate

### Content (marketing)
- [x] Write Twitter/X thread: 5 tweets about paper findings
- [x] Write Reddit post for r/MachineLearning (800 words, academic tone)
- [x] Write Reddit post for r/LocalLLaMA (casual tone, "test your model against our arena")
- [x] Write LinkedIn post (professional, link to paper + repo)
- [ ] Create demo screenshot of web UI for social media

### Testing (QA + benchmarks)
- [x] Test all new API endpoints (fight, leaderboard, challenge) — 10/10 pass
- [x] Benchmark: 2,114 fights/sec on Mac Mini M4
- [x] Verify web UI serves correctly via uvicorn
- [x] Test Render deployment config locally
- [x] Write test results to `tests/phase1_results.md`

---

## PHASE 2: COMMUNITY (Week 2)
- [ ] Launch public challenge: "Beat the Bear" — submit builds via API
- [ ] Add WebSocket live fight viewer
- [ ] Integrate LLM agent leaderboard
- [ ] Add ELO rating system

## PHASE 3: SCALE (Week 3-4)
- [ ] Multi-round adaptive tournaments
- [ ] Model comparison dashboard
- [ ] Paper v2 with community results
