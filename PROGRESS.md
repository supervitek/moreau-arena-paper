# Progress Log

## Task 1: Fix paper LaTeX
**Status:** COMPLETE
**Changes:**
- 1a: Fixed pgfplots error bars in Figures 1 and 2 — replaced broken `error bars/.cd, x dir=both, x explicit` with explicit `\draw` whisker lines using `axis cs` coordinates. Asymmetric CIs now render correctly across all pgfplots versions.
- 1b: Added GitHub URL (`https://github.com/supervitek/moreau-arena-paper`) to Conclusion (Section 11).
- 1c: Added challenge platform sentence as last paragraph in Future Work (Section 9).
- Verified: compiled twice with pdflatex, 0 errors, 17 pages output.

## Task 2: Standalone Simulator CLI
**Status:** COMPLETE
**Changes:**
- Created `simulator/__main__.py` with three modes:
  - Single match: `--build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 100`
  - Round-robin: `--round-robin --builds "bear 3 14 2 1" "buffalo 8 6 4 2" ...`
  - Series (best-of-7): `--series --build1 ... --build2 ... --series-count 10`
- Features: `--seed` for reproducibility, `--verbose` for tick-by-tick log
- Displays derived stats (max_hp, base_dmg, dodge%, resist%)
- Graceful error handling for invalid inputs
- All three modes tested and verified working.
