# Start Here — Moreau Arena Handoff Package

## What Is This?

This is a self-contained handoff package for the **Moreau Arena** project — a contamination-resistant benchmark for evaluating LLM strategic reasoning through creature combat simulation. The package contains everything needed to understand the project, reproduce results, and continue development. All tables and numbers in this package are either (a) taken directly from frozen source-of-truth files or (b) programmatically generated from raw tournament data via `scripts/generate_results_summary.py`.

---

## Reading Order

1. **This file** — orientation and what is frozen
2. **PROJECT_OVERVIEW.md** — what the project is, what it measures, high-level architecture
3. **CANONICAL_FORMULAS.md** — exact formulas from config.json and prompts, discrepancies noted
4. **RESULTS_SUMMARY.md** — programmatically-generated BT rankings, pairwise matrices, W-L records (auto-generated from raw JSONL)
5. **ARCHITECTURE.md** — file structure, module relationships, data flow
6. **KEY_DECISIONS.md** — why things are designed the way they are
7. **HOW_TO_RUN.md** — practical commands for running everything
8. **DEVELOPMENT_GUIDE.md** — how to add agents, experiments, features
9. **ROADMAP_STATUS.md** — what is done, what remains
10. **FILES_MANIFEST.md** — complete file listing with source-of-truth annotations

---

## What Is Canon (Source of Truth)

These are the immutable source-of-truth files. All derived documents must agree with them.

| File | Hash (SHA-256) | Contains |
|------|---------------|----------|
| `simulator/config.json` | `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` | All game mechanics, formulas, animal definitions, proc rates |
| `data/tournament_001/results.jsonl` | Verified by test suite | 780 series records — Track A (T001) |
| `data/tournament_002/results.jsonl` | Verified by test suite | 780 series records — Track B (T002) |
| `prompts/t001_prompt.txt` | Source text | Verbatim prompt shown to LLMs in T001 |
| `prompts/t002_prompt.txt` | Source text | Verbatim prompt shown to LLMs in T002 |

---

## What Is Frozen (Must NOT Be Changed)

The following files are protected by 89 invariant tests in `tests/test_invariants.py`. Any modification will cause test failures:

- **`simulator/config.json`** — Frozen game config (hash-verified)
- **`data/tournament_001/*`** — All T001 tournament data (SHA-256 verified)
- **`data/tournament_002/*`** — All T002 tournament data (SHA-256 verified)

**Why:** All scientific claims (rankings, win rates, the 180-degree leaderboard flip) depend on these files being identical to when the experiments ran. Modifying them invalidates all results.

**What you CAN change:** Everything else — agents, experiments, analysis, web UI, documentation, new tournament tracks.

---

## What To Do Next

1. **Verify data integrity:** Run `python -m pytest tests/test_invariants.py -v` — expect 89 tests passed
2. **Verify handoff consistency:** Run `python scripts/verify_handoff_consistency.py` — expect exit code 0
3. **Run real ablations:** Set `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` and run `python run_ablation.py --variant formulas-only --series 5 --provider <provider>` (all code is ready, just needs an API key)
4. **Deploy the web leaderboard:** Connect the GitHub repo to Render — `render.yaml` is already configured
5. **Run Track C/D tournaments:** Define final protocols in `docs/TRACKS.md`, implement agent wrappers, run with real LLMs

---

## How To Verify Data Integrity

```bash
# 1. Run the invariant test suite (89 tests, ~5 seconds)
python -m pytest tests/test_invariants.py -v

# 2. Run the handoff consistency checker
python scripts/verify_handoff_consistency.py

# 3. Verify config hash manually
python -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('simulator/config.json').read_bytes()).hexdigest())"
# Expected: b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534

# 4. Regenerate RESULTS_SUMMARY.md from raw data
python scripts/generate_results_summary.py
```
