# Next Tasks — 2026-03-01

## Status Summary

**Phase 1:** COMPLETE (all tasks done)
**Phase 2:** COMPLETE (Tasks 2.1–2.4 all done)
**Phase 3:** 3 of 4 criteria met — missing real LLM ablation run
**Phase 4:** Not started

---

## Task 1: Real LLM Ablation Run (Phase 3 completion)

**Teammate:** ablation-runner
**Priority:** HIGH — last gate to close Phase 3
**Files:** `run_ablation.py`, `results/`

All ablation results so far are dry-run (synthetic agents, `elapsed_s ≈ 0.0`). The Phase 3 success criterion requires: *"At least one ablation run with real LLM (Gemini Flash)."*

**Instructions:**
1. Read `run_ablation.py` to understand the existing `--dry-run` path and how agents are wired.
2. Read `docs/AGENT_API.md` for the `MoreauAgent` interface.
3. Configure a Gemini Flash agent (cheapest real LLM). You'll need:
   - A `GeminiFlashAgent` class implementing `MoreauAgent.get_build()`
   - API key from environment variable `GEMINI_API_KEY` (do NOT hardcode)
   - Use `google-generativeai` SDK or raw HTTP — whatever is simplest
4. Run **one** ablation variant (`formulas-only` is the most informative) with:
   - 3 agents minimum: Gemini Flash + 2 existing baselines (random, heuristic)
   - 5 series per pair (keep it cheap — ~50 API calls total)
   - `python run_ablation.py --variant formulas-only --series 5`
5. Save output to `results/ablation_formulas_only_live_TIMESTAMP.jsonl`
6. Compute BT ranking on the live results and compare against dry-run rankings.
7. Run `python -m pytest tests/test_invariants.py` before committing.

**DoD:** At least one JSONL file in `results/` with `elapsed_s > 1.0` per series (proving real API calls). BT ranking computed.

---

## Task 2: Moreau Script — Tier-2 DSL (Task 4.1)

**Teammate:** infra-builder
**Priority:** MEDIUM — first Phase 4 task, enables program-synthesis research
**Files:** Create `moreau_script/` package

**Instructions:**
1. Read `simulator/ability_grammar.py` — the grammar it defines is the foundation.
2. Read `simulator/config.json` to understand valid animals, stat budget (20), and stat ranges.
3. Create `moreau_script/` with:
   - `parser.py` — parse a safe DSL (max 50 rules, no eval/import/network)
   - `interpreter.py` — sandboxed execution with 100ms timeout per decision
   - `validator.py` — validate scripts don't exceed rule count, use only allowed constructs
4. DSL syntax (from ROADMAP_v2.md):
   ```
   IF opponent.animal == "BEAR" AND my.hp_pct < 50:
     PREFER animal="TIGER", atk=MAX
   ELIF opponent.last_build.atk > 12:
     PREFER hp=MAX, animal="BUFFALO"
   ```
5. Create `moreau_script/examples/` with 3 example scripts:
   - `random_strategy.ms` — random pick
   - `counter_pick.ms` — counter-pick based on opponent animal
   - `stat_optimizer.ms` — maximize ATK against low-HP opponents
6. Create a `ScriptAgent` class implementing `MoreauAgent` that runs a `.ms` file.
7. Test: `python -m moreau_script.interpreter examples/counter_pick.ms` should produce a valid build dict.
8. Run `python -m pytest tests/test_invariants.py` before committing.
9. Do NOT modify `simulator/config.json` or any data files.

**DoD:** DSL parses all 3 examples, `ScriptAgent` produces valid builds, execution is sandboxed (no eval/import).

---

## Task 3: Rules-as-Data Generator (Task 4.2)

**Teammate:** suite-designer
**Priority:** MEDIUM — requires Task 1.7 (ability grammar, already done)
**Files:** Create `seasons/ability_generator.py`

**Instructions:**
1. Read `simulator/ability_grammar.py` — this defines `Trigger × Target × Effect × Constraint`.
2. Read `seasons/patch_generator.py` — understand how seasonal patches work.
3. Read `seasons/SEASON_RULES.md` — understand the season lifecycle.
4. Create `seasons/ability_generator.py` that:
   - Input: desired meta properties as a config dict:
     ```python
     {"diversity_target": 0.8,    # minimum 80% of animals picked at least once
      "max_win_rate": 0.65,       # no animal exceeds 65% overall win rate
      "ability_count": 6}         # generate 6 abilities (one per animal)
     ```
   - Output: a new ability set expressed in the ability grammar
   - Validation: run generated abilities through the simulator invariants (monotonic ATK/HP, variance budget)
   - Uses sampling + rejection: generate random abilities from grammar, simulate round-robin, reject if constraints violated
5. Test with `python seasons/ability_generator.py --dry-run` — should produce one valid ability set.
6. Do NOT modify `simulator/config.json` or any data files.
7. Run `python -m pytest tests/test_invariants.py` before committing.

**DoD:** `ability_generator.py --dry-run` produces a valid ability set. Generated abilities pass grammar validation.

---

## Task 4: Tournament Challenge Platform Skeleton (Task 4.3)

**Teammate:** platform-builder
**Priority:** LOW — long-term, but the skeleton can be laid now
**Files:** Extend `web/`

**Instructions:**
1. Read `web/app.py` and `web/static/leaderboard.html` — understand the existing Flask app.
2. Read `docs/AGENT_API.md` — the submission API spec.
3. Add three route groups to the existing Flask app:
   - `/research` — academic face: link to paper PDF, methodology summary, leaderboard with BT+CI
   - `/play` — game face: "Create your fighter" form (pick animal + allocate 20 stat points), shows result against a baseline
   - `/api/v1/submit` — endpoint accepting a JSONL result file upload, validates format against MMR_SPEC, stores in `results/submissions/`
4. For `/play`:
   - HTML form with animal dropdown + 4 stat sliders (HP/ATK/SPD/WIL) that enforce budget=20
   - On submit, run a single series (best-of-7) against the `random` baseline via the simulator
   - Display result with win/loss and game-by-game breakdown
5. For `/api/v1/submit`:
   - Validate JSONL against `docs/MMR_SPEC.md` required fields
   - Return 400 with specific errors if validation fails
   - Store accepted files in `results/submissions/`
6. Keep it simple — no auth, no database, just file-based storage.
7. Run `python -m pytest tests/test_invariants.py` before committing.
8. Do NOT modify `simulator/config.json` or any data files.

**DoD:** `/play` renders a form and runs a fight. `/api/v1/submit` accepts and validates JSONL. `/research` links to leaderboard.

---

## Rules (same as always)

- `python -m pytest tests/test_invariants.py` must pass before every commit
- Do NOT modify `simulator/config.json`, `data/tournament_001/*`, or `data/tournament_002/*`
- Commit message format: `feat: Task X.Y — description` or `docs: Task X.Y — description`
- If blocked, document in PROGRESS.md and move to the next task
