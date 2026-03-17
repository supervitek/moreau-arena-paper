# Part B Supabase Production Readiness

Last updated: 2026-03-17
Status: Prepared

## Goal

Move Part B from file-backed development persistence to real server-backed persistence without changing the public benchmark contract.

## Required Inputs

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- applied schema:
  - [`/Users/cc/Desktop/Claude/a/moreau-arena-paper/sql/PART_B_STATE_MIGRATION_B1_5.sql`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/sql/PART_B_STATE_MIGRATION_B1_5.sql)

## What Is Ready In Code

- `part_b_state.py` automatically switches to Supabase when both env vars are present.
- file fallback remains available for local/dev.
- replay, report, queue, season archive, and leaderboards all read through the same store abstraction.
- `scripts/verify_part_b_supabase.py` checks environment and storage-status expectations before live cutover.

## Production Checklist

- apply SQL schema to Supabase
- verify `part_b_runs` and `part_b_events` exist
- verify RLS policies behave as expected
- set `SUPABASE_URL`
- set `SUPABASE_SERVICE_ROLE_KEY`
- verify `/api/v1/island/part-b/storage-status` reports `backend: supabase`
- create one run, append one event, fetch one replay, fetch season leaderboards

## Risk Notes

- service-role path must not become a hidden benchmark privilege
- season archive export should remain reproducible across backends
- house-agent eligibility depends on contract parity, not backend choice
