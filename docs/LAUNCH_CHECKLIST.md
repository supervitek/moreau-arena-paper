# Moreau Arena — Launch Checklist

Four gates must clear before public release. Each gate has concrete deliverables with pass/fail criteria.

---

## Gate 1: Paper Verified

The paper is technically correct, internally consistent, and ready for arXiv submission.

- [ ] All numeric claims match JSONL source data (T001: 779 series / 3652 games; T002: 780 series / 4015 games)
- [ ] Bradley-Terry scores reproducible via `python -m analysis.bt_ranking data/tournament_00X/results.jsonl`
- [ ] Pairwise win-rate matrices match paper tables
- [ ] LLM-vs-baseline aggregate win rates confirmed (T001: 37.50%; T002: 89.75%)
- [ ] WIL trap characterization supported by build distribution data
- [ ] Non-transitivity claims verified (T001: 0 strict 3-cycles; T002: 12 strict 3-cycles)
- [ ] Adaptation analysis numbers match `data/tournament_002/adaptation_analysis.md`
- [ ] Config hash in paper matches frozen hash: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
- [ ] All 8 LLM model identifiers and versions are accurate as of tournament run date
- [ ] `python -m pytest tests/test_invariants.py` passes with zero failures

---

## Gate 2: Reproducibility Bundle

Anyone with the repo can independently verify every claim in the paper.

- [ ] `requirements.txt` and `analysis/requirements.txt` install cleanly on Python 3.10+
- [ ] `data/tournament_001/results.jsonl` present and matches known hash
- [ ] `data/tournament_002/results.jsonl` present and matches known hash
- [ ] `simulator/config.json` SHA-256 matches frozen value
- [ ] BT ranking script runs end-to-end on both tournament datasets without errors
- [ ] Pairwise matrix script runs end-to-end on both tournament datasets without errors
- [ ] Verbatim prompts included (`prompts/t001_prompt.txt`, `prompts/t002_prompt.txt`)
- [ ] Seed scheme documented so any game can be replayed deterministically
- [ ] `run_challenge.py` works with `--dry-run` flag for local testing without API keys
- [ ] README includes step-by-step verification instructions

---

## Gate 3: Benchmark Identity Page

The project has a clear public identity: what it is, what it is not, and how to engage.

- [ ] README.md covers: motivation, key result, quick start, repo structure, citation block
- [ ] `docs/FAQ.md` answers the 10 most likely public questions
- [ ] `docs/LANGUAGE_GUIDE.md` defines allowed and forbidden framing for Moreau
- [ ] `docs/MECHANICS.md` fully documents game rules and formulas
- [ ] `docs/CONTRIBUTING.md` explains how to submit a new agent
- [ ] License file present (MIT)
- [ ] BibTeX citation block in README and paper

---

## Gate 4: T003 Specified

Track C (Meta-Conditioned) protocol is fully defined so it can be run immediately after launch.

- [ ] `docs/TRACKS.md` defines Track C protocol unambiguously
- [ ] Track C prompt construction rules documented (Track A base + meta context, no formulas)
- [ ] Meta context block format specified with concrete example
- [ ] Expected output format defined (plain text, same as Track A)
- [ ] Adaptation rules stated explicitly (none — one build per series)
- [ ] Metrics to compute listed (same as Track A)
- [ ] Research question stated: "Are examples enough to break priors without understanding mechanics?"
- [ ] Comparison plan documented: C vs A (effect of examples), C vs B (value of formulas + adaptation)
- [ ] `prompts/t003_prompt.txt` placeholder or draft exists
- [ ] Implementation checklist in TRACKS.md has all Track C items listed

---

## Sign-off

All four gates must be checked off before:
- arXiv upload
- Public repo visibility change
- Any social media or blog post announcement
