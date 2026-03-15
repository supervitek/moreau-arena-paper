# Launch Checklist — Moreau Arena

Four gates must pass before public release. Each gate has clear pass/fail criteria.

---

## Gate 1: Paper Verified

- [ ] All claims in `paper/moreau_arena.tex` are supported by data in `data/`
- [ ] BT scores and CI in paper match `analysis/bt_ranking.py` output
- [ ] Tournament sample sizes stated correctly (T001: blind, T002: adaptive)
- [ ] Ablation results (if included) match `run_ablation.py --dry-run` patterns
- [ ] No claims about "general reasoning" — only "strategic reasoning under uncertainty"

**Pass criteria:** Two independent reviewers confirm all numerical claims are reproducible from JSONL data.

**Fail criteria:** Any numerical claim in the paper cannot be reproduced from the committed data files.

---

## Gate 2: Reproducibility Bundle

- [ ] `config.json` SHA-256 matches frozen hash: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
- [ ] `python -m pytest tests/test_invariants.py` passes (all invariants green)
- [ ] `data/tournament_001/` files match hardcoded SHA-256 hashes in test suite
- [ ] `data/tournament_002/` files match hardcoded SHA-256 hashes in test suite
- [ ] `data/tournament_003/` files have explicit integrity verification
- [ ] Top-level `requirements.txt` is the authoritative pinned environment file
- [ ] `scripts/setup.sh` produces a working environment from clean clone
- [ ] README includes "Quick Reproduce" section with exact commands

**Pass criteria:** A fresh `git clone` + `pip install -r requirements.txt` + `pytest` succeeds on Python 3.10+.

**Fail criteria:** Any step in the reproduction process fails on a clean machine.

---

## Gate 3: Benchmark Identity Page

- [ ] `docs/MEASUREMENT_SPEC.md` defines primary metric (Bradley-Terry + bootstrap CI)
- [ ] `docs/TRACKS.md` defines at least Track A (one-shot) and Track B (feedback)
- [ ] `docs/FAQ.md` answers "What is Moreau Arena?" clearly
- [ ] `docs/LANGUAGE_GUIDE.md` defines allowed/forbidden claims
- [ ] `web/static/index.html` renders leaderboard with T001+T002 data
- [ ] Repository description and README use approved terminology only

**Pass criteria:** A newcomer can read the docs and understand what Moreau measures, how, and why — without confusion about scope.

**Fail criteria:** Any doc uses forbidden phrases from LANGUAGE_GUIDE.md, or benchmark scope is unclear.

---

## Gate 4: T003 Specified

- [ ] T003 protocol defined in `docs/TRACKS.md` or separate spec document
- [ ] T003 differs from T002 in exactly one controlled variable
- [ ] T003 ablation variants identified (at minimum: structured-output-only, formulas-no-meta)
- [ ] Run command documented: `python run_ablation.py --variant <name> --dry-run`
- [ ] Expected outputs and analysis plan documented

**Pass criteria:** T003 can be executed by a new contributor following only the documentation.

**Fail criteria:** T003 protocol is ambiguous or changes more than one variable vs T002.

---

## Status

| Gate | Status | Last Checked | Notes |
|------|--------|--------------|-------|
| 1. Paper Verified | PENDING | 2026-03-15 | Needs explicit paper-vs-data claim check, not just repo inspection |
| 2. Reproducibility Bundle | PARTIAL | 2026-03-15 | Invariants pass; T003 integrity item still needs to be formalized |
| 3. Benchmark Identity | PARTIAL | 2026-03-15 | Core docs and site pages exist; final terminology sweep still required |
| 4. T003 Specified | PARTIAL | 2026-03-15 | Spec docs exist; final operator-style verification still pending |
