# Progress Log

## Task 1: Fix paper LaTeX
**Status:** COMPLETE
**Changes:**
- 1a: Fixed pgfplots error bars in Figures 1 and 2 — replaced broken `error bars/.cd, x dir=both, x explicit` with explicit `\draw` whisker lines using `axis cs` coordinates. Asymmetric CIs now render correctly across all pgfplots versions.
- 1b: Added GitHub URL (`https://github.com/supervitek/moreau-arena-paper`) to Conclusion (Section 11).
- 1c: Added challenge platform sentence as last paragraph in Future Work (Section 9).
- Verified: compiled twice with pdflatex, 0 errors, 17 pages output.
