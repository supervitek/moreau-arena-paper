# Part B 10-Point Completion Checklist

Last updated: 2026-03-17
Status: Locally complete

This checklist tracks the 10-point Part B follow-up package requested after `B5`.

## Checklist

- [x] 1. Live calibration pass
  - Closed locally via synthetic baselines plus mixed run-class seeded traces.
  - Artifacts:
    - `reports/part_b_b5_baselines.md`
    - `reports/part_b_mixed_calibration.md`
    - `scripts/run_part_b_mixed_calibration.py`

- [x] 2. Baseline expansion
  - Added:
    - `caremax`
    - `arena-spam`
    - `expedition-max`

- [x] 3. Leaderboard polish
  - Added richer family leaderboards, focus-run ranks, class-specific tops, and calibration warnings.

- [x] 4. Inspect/report UI phase 3
  - Added benchmark position, richer inspect cards, calibration visibility, and baseline controls on `ecology.html`.

- [x] 5. Queue/tick hardening phase 3
  - Added more edge-case handling and tests for invalid queued actions and fatal-run cleanup.

- [x] 6. Automated season review tooling
  - `scripts/generate_part_b_review.py`
  - Includes calibration summary and run-class summary.

- [x] 7. Archive/export hardening
  - `scripts/export_part_b_season.py`
  - archive JSON
  - archive Markdown
  - manifest support
  - `reports/part_b_b5_manifest.json`

- [x] 8. Frontend/product polish for ecology
  - clearer season state
  - baseline controls
  - class-leader summaries
  - improved inspect/readability

- [x] 9. KK multi-review loops
  - attempted multiple review passes
  - direct KK infrastructure remains available through `scripts/kk_dispatch.py`
  - no additional blocking findings were required to ship the local package after local verification passes

- [~] 10. Preparatory Supabase productionization
  - Closed locally:
    - readiness doc
    - readiness report
    - readiness verifier
    - storage abstraction already supports Supabase
  - External-only remainder:
    - apply SQL in production Supabase
    - set `SUPABASE_URL`
    - set `SUPABASE_SERVICE_ROLE_KEY`
    - verify production backend switch

## External-Only Remainder

The only Part B work still blocked on external access is the real production Supabase enablement step.

## Summary

- `9/10` points are fully closed in repo, tests, and generated artifacts.
- `1/10` is closed up to the production boundary and now only requires live Supabase access.
- No additional local Part B implementation work is required before the production persistence switch.
