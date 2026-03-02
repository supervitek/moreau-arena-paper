# NEXT_TASKS.md — Moreau Arena

**Generated:** 2026-03-01

## DONE

All tasks across Phases 1–4 of ROADMAP_v2.md are complete.

| Phase | Tasks | Status |
|-------|-------|--------|
| 1: Harden the Instrument | 1.1–1.7 + 1.8–1.11 | 11/11 DONE |
| 2: Live Meta + Public Ladder | 2.1–2.4 | 4/4 DONE |
| 3: Depth Suites | 3.1–3.3 | 3/3 DONE |
| 4: Ecosystem | 4.1–4.3 | 3/3 DONE |

89 invariant tests pass. All immutable files verified.

---

### One blocked item (external dependency, not a code task)

**Real LLM Ablation Run** — Phase 3 success criterion requires `elapsed_s > 1.0` proving real API calls. All code is ready (`agents/gemini_agent.py`, `run_ablation.py --provider gemini`). Blocked on missing `GEMINI_API_KEY`.

To unblock:
```bash
export GEMINI_API_KEY=<your-key>
python3 run_ablation.py --variant formulas-only --provider gemini --model gemini-2.0-flash-lite --series 5
```
