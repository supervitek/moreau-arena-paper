# Launch Checklist — Moreau Arena

Four gates must pass before public release. Each gate has clear pass/fail criteria.

---

## Gate 1: Paper Verified

- [x] All claims in `paper/moreau_arena.tex` are supported by data in `data/`
- [x] BT scores and CI in paper match `analysis/bt_ranking.py` output
- [x] Tournament sample sizes stated correctly (T001: blind, T002: adaptive)
- [x] Adaptation table / adapt-vs-stick percentages have a committed derivation script: `python scripts/compute_t002_adaptation_metrics.py`
- [x] Ablation results (if included) match `run_ablation.py --dry-run` patterns
- [x] No claims about "general reasoning" — only "strategic reasoning under uncertainty"

**Pass criteria:** Two independent reviewers confirm all numerical claims are reproducible from JSONL data.

**Fail criteria:** Any numerical claim in the paper cannot be reproduced from the committed data files.

---

## Gate 2: Reproducibility Bundle

- [x] `simulator/config.json` embedded SHA-256 matches the canonical hash excluding the `sha256` field: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
- [x] `python -m pytest tests/test_invariants.py` passes (all invariants green)
- [x] `data/tournament_001/` files match hardcoded SHA-256 hashes in test suite
- [x] `data/tournament_002/` files match hardcoded SHA-256 hashes in test suite
- [x] `data/tournament_003/` files have explicit integrity verification
- [x] Top-level `requirements.txt` is the authoritative pinned environment file
- [x] `scripts/setup.sh` produces a working environment from clean clone
- [x] README includes "Quick Reproduce" section with exact commands

**Pass criteria:** A fresh `git clone` + `pip install -r requirements.txt` + `pytest` succeeds on Python 3.10+.

**Fail criteria:** Any step in the reproduction process fails on a clean machine.

---

## Gate 3: Benchmark Identity Page

- [x] `docs/MEASUREMENT_SPEC.md` defines primary metric (Bradley-Terry + bootstrap CI)
- [x] `docs/TRACKS.md` defines at least Track A (one-shot) and Track B (feedback)
- [x] `docs/FAQ.md` answers "What is Moreau Arena?" clearly
- [x] `docs/LANGUAGE_GUIDE.md` defines allowed/forbidden claims
- [x] `web/static/index.html` renders leaderboard with T001+T002 data
- [x] Repository description and README use approved terminology only

**Pass criteria:** A newcomer can read the docs and understand what Moreau measures, how, and why — without confusion about scope.

**Fail criteria:** Any doc uses forbidden phrases from LANGUAGE_GUIDE.md, or benchmark scope is unclear.

---

## Gate 4: T003 Specified

- [x] T003 protocol defined in `docs/TRACKS.md` or separate spec document
- [x] T003 differs from T002 in exactly one controlled variable
- [x] T003 ablation variants identified (at minimum: structured-output-only, formulas-no-meta)
- [x] Run command documented: `python run_ablation.py --variant <name> --dry-run`
- [x] Expected outputs and analysis plan documented

**Pass criteria:** T003 can be executed by a new contributor following only the documentation.

**Fail criteria:** T003 protocol is ambiguous or changes more than one variable vs T002.

---

## Status

| Gate | Status | Last Checked | Notes |
|------|--------|--------------|-------|
| 1. Paper Verified | PASS | 2026-03-16 | Core claims match data, the T002 derivation script is committed, and the paper adaptation table was re-derived to match canonical JSONL; see `docs/PAPER_VERIFICATION_REPORT.md` |
| 2. Reproducibility Bundle | PASS | 2026-03-15 | Config hash verification, setup script, invariant suite, and T003 integrity doc all checked |
| 3. Benchmark Identity | PASS | 2026-03-15 | README/docs terminology and public-facing benchmark descriptions were refreshed for current state |
| 4. T003 Specified | PASS | 2026-03-15 | Track docs, T003 spec, tournament doc, and integrity report now agree on exact-only cleanroom protocol |
