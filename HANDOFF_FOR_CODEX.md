# HANDOFF FOR CODEX — Moreau Arena

Generated: 2026-03-10
Branch: `main` (clean, up to date with origin)
Live site: https://moreauarena.com

---

## 1. Project Goal

**Moreau Arena** is a contamination-resistant benchmark for evaluating LLM strategic reasoning. LLMs design creature builds (stat allocations + animal choice) that fight in a simulated combat engine. Because game mechanics are novel and unpublished, models cannot rely on memorized strategies.

**What's ready:**
- 3 benchmark tournaments (T001–T003) with 2609 series across 15 agents
- Season 1: 14-animal combat system with unique passives/abilities, balance-tested across 182K+ games
- Live website with leaderboard, matchup explorer, fighter pages, fight simulator, Moreddit social feed
- Pets system: create pets, train via fights, mutation tree, soul personality (Claude API)
- PSI (Prompt Sensitivity Index) validation: τ=1.0 — rankings are prompt-robust
- Paper submitted to arXiv (awaiting approval)

**What's in progress:**
- Season 2 design (Morpeton DSL, action language)
- Pets polish (recently fixed fight/stats bugs)
- Launch materials (posts ready, not yet published)

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Web framework | FastAPI + Uvicorn |
| Frontend | Static HTML/CSS/JS (no build step, no framework) |
| Hosting | Render (free tier, auto-deploy from `main`) |
| Package manager | pip (requirements.txt + pyproject.toml) |
| Tests | pytest |
| Stats | scipy, numpy, matplotlib |
| LLM APIs | Anthropic, OpenAI, Google Gemini, xAI (Grok) |

**No database.** All data is JSONL files in `data/`. All frontend state is localStorage.

### Entry Points

| What | How |
|------|-----|
| Web server | `uvicorn web.app:app --host 0.0.0.0 --port 8000` |
| Run tournament | `python run_challenge.py` (T001/T002), `python run_t003.py` (T003) |
| Run S1 tournament | `python run_s1_tournament.py` |
| Run ablation | `python run_ablation.py` |
| Run PSI validation | `python run_psi.py` or `python run_t003_psi.py` |
| Round Table council | `python roundtable.py` |
| Tests | `python -m pytest tests/test_invariants.py` |

### Config Files

| File | Purpose |
|------|---------|
| `render.yaml` | Render deploy config |
| `Procfile` | Uvicorn start command |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Package metadata + deps |
| `config.json` | **FROZEN** — core game config (hash-verified) |
| `CLAUDE.md` | Project rules for AI agents |

---

## 3. Repository Map

```
moreau-arena-paper/
├── web/
│   ├── app.py              ← FastAPI app, 1900 lines, ALL routes
│   └── static/             ← All HTML pages, CSS, PDF
│       ├── index.html       ← Homepage
│       ├── style.css        ← Global styles
│       ├── pets/            ← Pets UI (hub, home, train, mutate, profile, create)
│       └── fighters/        ← 14 individual fighter dossier pages
├── simulator/               ← Core benchmark engine (T001–T003)
│   ├── engine.py            ← Combat simulation
│   ├── animals.py           ← 14 original benchmark animals
│   ├── abilities.py         ← Ability system
│   └── config.json          ← FROZEN config
├── season1/                 ← Season 1 engine (separate from core)
│   ├── engine_s1.py         ← S1 combat engine (1400+ lines)
│   ├── animals_s1.py        ← 14 S1 animals with passives/abilities
│   └── baselines_s1.py      ← Baseline agents (Conservative, Smart, etc.)
├── pets/                    ← Pets backend
│   ├── mutation_tree.py     ← Mutation/evolution system
│   └── soul.py              ← AI personality via Claude API
├── morpeton/                ← Morpeton DSL (Season 2 prototype)
│   ├── grammar.py           ← Parser
│   ├── interpreter.py       ← Executor
│   └── validator.py         ← Constraint checker
├── agents/                  ← LLM agent wrappers
│   ├── llm_agent.py         ← Generic LLM agent
│   └── baselines.py         ← Non-LLM baseline agents
├── analysis/                ← Stats/ranking
│   ├── bt_ranking.py        ← Bradley-Terry rankings
│   └── pairwise_matrix.py   ← Win rate matrices
├── data/                    ← Tournament results (JSONL)
│   ├── tournament_001/      ← FROZEN — T001 results
│   ├── tournament_002/      ← FROZEN — T002 results
│   ├── tournament_003/      ← T003 results
│   └── season1_tournament/  ← S1 tournament results
├── prompts/                 ← Tournament prompt templates
├── docs/                    ← Documentation and specs
├── roundtable/              ← Multi-model AI council framework
├── tests/                   ← pytest invariant tests
└── council_records/         ← Round Table session outputs
```

---

## 4. Current State

### Working
- Site live at moreauarena.com (all pages load)
- Fight simulator (both benchmark and S1 engines)
- Leaderboard with BT scores (Track A and B — Track C uses hardcoded fallback)
- Season 1: 14 fighters, matchup explorer, quick fight
- Pets: creation, training (fights), mutations, hub ("The Kennels")
- Fighter dossier pages (14 FBI/SHIELD-style pages)
- Moreddit social feed
- Paper PDF served at /static/paper.pdf

### Known Issues / Technical Debt
- **T003 leaderboard API returns empty** — Track C data not in the standard cache pipeline. Homepage uses JS fallback array.
- **Pet stat sliders can produce 21 points** (should be 20) — validation relaxed to 4–24 to accommodate, but the creation UI should enforce 20 exactly.
- **Pets Soul Window** requires `ANTHROPIC_API_KEY` on Render — currently shows fallback text ("the soul awaits awakening") since no key is set on free tier.
- **All old pet fight records show as losses** with `ticks: "?"` — caused by pre-fix bug (win detection checked nonexistent `data.winner` field). Old records in localStorage are not retroactively fixable.
- **No database** — all pet data is client-side localStorage. Lost on browser clear.
- **Render free tier** — cold starts, may sleep after inactivity.
- **Gemini free tier** — 250 req/day/model limit makes large tournament runs difficult.
- **xAI/Grok** — intermittent 403 errors, excluded from PSI v2.

---

## 5. Runbook

### Install
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Dev Server
```bash
uvicorn web.app:app --reload --port 8000
```
Site at http://localhost:8000

### Run Tests
```bash
python -m pytest tests/test_invariants.py -v
```

### Run Morpeton Tests
```bash
PYTHONPATH=. python -m pytest morpeton/test_morpeton.py -v
```

### Run Pets Tests
```bash
PYTHONPATH=. python -m pytest pets/mutation_tree_test.py pets/soul_test.py -v
```

### Environment Variables (for tournament runs, not needed for web)
```
ANTHROPIC_API_KEY=...    # Claude models + Pets soul
OPENAI_API_KEY=...       # GPT models
GOOGLE_API_KEY=...       # Gemini models
XAI_API_KEY=...          # Grok (unreliable)
```

### Common Issues
- **macOS**: no `python` in PATH — use `.venv/bin/python`
- **API keys**: source `~/.zshrc` before running tournament scripts
- **Gemini thinking models**: need `maxOutputTokens >= 2048` (thoughtSignature eats tokens)
- **Google rate limiting**: serialize calls with Lock + 2s gap

---

## 6. Recent Work (last week)

| Commit | What |
|--------|------|
| `8c9d8c0` | Fix StatBlock validation (20→4-24) — pets with 21 stats crashed fight API |
| `268e4ba` | Fix API stat validation + add resp.ok check in fight frontend |
| `76c019f` | Fix win detection (`build1_wins > 0`), ticks (`avg_ticks`), XP label |
| `7cb04d5` | T003 fallback on homepage + multi-pet migration in home/creation pages |
| `db662d2` | Multiple pets support + hub page "The Kennels" |
| `cf7cc4d` | Fix stats display (`base_stats`), mutate unlock, fight stats, soul fallback |
| `e4d5f3c` | S1 vs Benchmark comparison page with rank highlights |
| `b856f34` | Launch posts for X, Reddit, HN |
| `adb2866` | Merge pets-mvp into main |
| `970150a` | Pets frontend: 5 pages + API routes |
| `1512192` | Pets backend: mutation tree, soul engine |

**Key decisions:**
- Stat validation relaxed to 4–24 (temporary — slider should enforce 20)
- Multi-pet localStorage schema: `moreau_pets` (array) + `moreau_active_pet` (index), auto-migration from old `moreau_pet` key
- T003 top-6 hardcoded as JS fallback when API returns empty

---

## 7. Incomplete Work / Next Steps

### TODO
- **arXiv launch**: Paper submitted, awaiting approval. Launch posts ready in `docs/LAUNCH_POSTS.md`.
- **Pet stat slider fix**: Creation page should enforce exactly 20 points (currently can drift to 21).
- **Pets Soul**: Needs `ANTHROPIC_API_KEY` on Render for real personality responses.
- **Season 2**: Morpeton DSL designed, parser built (`morpeton/`), but no tournament integration yet.
- **T003 API data**: Track C should be in the BT cache pipeline, not hardcoded in JS.
- **Pet persistence**: Consider server-side storage (currently localStorage only).

### Areas Needing Care
- `config.json` and `data/tournament_001/`, `data/tournament_002/` are **FROZEN** — do not modify.
- `season1/engine_s1.py` is 1400+ lines with precise combat math — changes affect all S1 balance.
- `web/app.py` is 1900 lines — monolithic, handles all routes, fight logic, caching.

---

## 8. Git Context

- **Branch**: `main` (clean)
- **Remote**: `origin/main` (up to date)
- **Other branches**: `pets-mvp` (merged), `season1` (older work)
- **Untracked files**: `docs/T003_INTEGRITY.md`, `docs/T003_PROMPT_DIFF.md`, `verify_t003_*.py` (3 files)
- **No uncommitted changes**

---

## 9. Recommendations For Next Agent

### Start With
1. Read `CLAUDE.md` — project rules and frozen file constraints
2. Read `web/app.py` lines 1–50 (imports) and search for route definitions
3. Run `python -m pytest tests/test_invariants.py` to verify core integrity
4. Run `uvicorn web.app:app --port 8000` to see the site locally

### What NOT To Break
- **`config.json`** — hash-verified, core benchmark integrity depends on it
- **`data/tournament_001/*` and `data/tournament_002/*`** — immutable tournament data
- **`season1/engine_s1.py` combat formulas** — 182K games of balance testing depend on them
- **`simulator/engine.py`** — core benchmark engine, all T001–T003 results depend on it

### Architecture Notes
- Frontend is plain HTML/JS with no build step — edit files directly in `web/static/`
- All pet state is client-side localStorage — there is no backend persistence for pets
- Fight API returns `{build1_wins, build2_wins, draws, avg_ticks}` — NOT a winner string
- BT scores are cached at app startup from JSONL files — restart server to refresh

---

## 10. Important Files

| File | Purpose |
|------|---------|
| `web/app.py` | All backend routes, fight logic, caching — the entire API in one file |
| `web/static/index.html` | Homepage with track comparison, quick fight, S1 preview |
| `web/static/style.css` | Global styles (dark theme, variables, components) |
| `web/static/pets/home.html` | Pet dashboard — stats, fights, XP, soul window |
| `web/static/pets/train.html` | Pet training — opponent selection, fight animation, results |
| `web/static/pets/hub.html` | "The Kennels" — multi-pet manager |
| `web/static/pets/index.html` | Pet creation wizard (animal + name + stat sliders) |
| `web/static/pets/mutate.html` | Mutation selection UI |
| `web/static/s1-fighters.html` | All 14 fighters with abilities, matchups, tips |
| `season1/engine_s1.py` | S1 combat engine — tick loop, abilities, passives, terrain |
| `season1/animals_s1.py` | S1 animal definitions, stats, abilities, StatBlock class |
| `simulator/engine.py` | Core benchmark combat engine (T001–T003) |
| `config.json` | **FROZEN** — core game parameters (hash-verified in tests) |
| `analysis/bt_ranking.py` | Bradley-Terry ranking computation |
| `pets/mutation_tree.py` | Mutation/evolution tree with stat bonuses |
| `pets/soul.py` | Soul personality generator (uses Claude API) |
| `morpeton/grammar.py` | Morpeton DSL parser (Season 2 prototype) |
| `requirements.txt` | Python dependencies |
| `render.yaml` | Render deploy config (auto-deploy on push to main) |
| `docs/LAUNCH_POSTS.md` | Ready-to-publish launch posts (X, Reddit, HN) |

---

# START HERE

## 5 Most Important Files
1. **`web/app.py`** — entire backend, all routes and fight logic
2. **`web/static/pets/train.html`** — pet fight flow (most recently bugfixed)
3. **`season1/engine_s1.py`** — S1 combat engine (do not change formulas)
4. **`config.json`** — FROZEN core config (hash-verified, never modify)
5. **`web/static/index.html`** — homepage (T003 fallback, quick fight)

## 3 Primary Commands
```bash
uvicorn web.app:app --reload --port 8000     # Run dev server
python -m pytest tests/test_invariants.py -v  # Run core tests
git push                                       # Deploy to Render (auto)
```

## 3 Main Risks
1. **Modifying `config.json` or `data/tournament_00{1,2}/*`** — breaks test_invariants.py hash check and invalidates published results
2. **Changing combat formulas in `engine.py` or `engine_s1.py`** — invalidates all tournament data and balance testing
3. **Pushing broken code to `main`** — auto-deploys to live site immediately

## 3 Next Steps
1. **Fix pet creation slider** — enforce exactly 20 stat points (currently can produce 21)
2. **Add `ANTHROPIC_API_KEY` to Render** — enables pet Soul personality responses
3. **Integrate T003 data into BT cache pipeline** — replace hardcoded JS fallback on homepage
