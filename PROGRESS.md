# Progress Log

## Sprint 2 — Parallel Teammates (2026-03-01)

### Test Results

```
python3 -m pytest tests/test_invariants.py — 89 passed in 5.03s
```

All invariants green. No immutable files modified.

### Final Status Table

| Teammate | Task | Description | Status | Notes |
|----------|------|-------------|--------|-------|
| docs | 1.9 | Launch Checklist | DONE | 4 gates with pass/fail criteria |
| docs | 1.10 | FAQ | DONE | 10 Q&A for public launch |
| docs | 1.11 | Language Guide | DONE | Allowed/forbidden/gray-area phrases |
| ablation | 1.5 | PSI Mini-Suite | DONE | 3 prompt variants + Kendall tau, stdlib-only |
| ablation | 1.8 | T003-D/E Ablation Variants | DONE | Both variants verified with --dry-run |
| platform | 2.1 | Season System | DONE | season_0_base.json + patch_generator.py + SEASON_RULES.md |
| platform | 2.3 | Agent Submission API | DONE | MoreauAgent interface + examples in docs/AGENT_API.md |
| lab | 3.1 | Lab Mode v2 | DONE | Convergence tracking, distance-to-optimum, iteration curves |

### Files Created/Modified

#### New Files
- `docs/LAUNCH_CHECKLIST.md` — 4 launch gates
- `docs/FAQ.md` — 10 Q&A
- `docs/LANGUAGE_GUIDE.md` — Approved terminology
- `docs/AGENT_API.md` — MoreauAgent interface spec
- `prompts/t002_v2.txt` — Paraphrased T002 prompt (variant 2)
- `prompts/t002_v3.txt` — Paraphrased T002 prompt (variant 3)
- `seasons/season_0_base.json` — Frozen core config copy
- `seasons/patch_generator.py` — EMA-based balance patch generator
- `seasons/SEASON_RULES.md` — Season system documentation

#### Modified Files
- `run_psi.py` — Replaced scipy dependency with stdlib Kendall tau
- `lab_mode.py` — Added convergence tracking, sampled optimum search, iteration curve JSON

#### Immutable Files (verified unchanged)
- `simulator/config.json` — Hash verified
- `data/tournament_001/*` — SHA-256 hashes verified
- `data/tournament_002/*` — SHA-256 hashes verified

### Blocked Tasks
None — all tasks completed successfully.

---

## Sprint 1 (Previous)

### Task 1: Fix paper LaTeX
**Status:** COMPLETE
- 1a: Fixed pgfplots error bars in Figures 1 and 2
- 1b: Added GitHub URL to Conclusion
- 1c: Added challenge platform sentence in Future Work

### Task 2: Standalone Simulator CLI
**Status:** COMPLETE
- Created `simulator/__main__.py` with three modes (single/round-robin/series)

### Task 3: Challenge Script
**Status:** COMPLETE
- Created `run_challenge.py` with full LLM challenge pipeline

### Task 4: Laboratory Mode Prototype
**Status:** COMPLETE
- Created `lab_mode.py` with iteration efficiency curve experiment

### Task 5: Documentation update
**Status:** COMPLETE
- Updated README.md, created docs/MECHANICS.md, docs/CONTRIBUTING.md
