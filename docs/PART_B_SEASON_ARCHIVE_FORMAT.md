# Part B Season Archive Format

Last updated: 2026-03-17
Status: Active

## Canonical Archive Payload

The season archive is exported as one JSON plus one Markdown summary.

JSON includes:
- season contract snapshot
- family-score leaderboards
- per-run envelopes
- per-run reports
- per-run event streams

Markdown includes:
- season identity
- headline note
- leaderboard summaries by family

## Export Tool

- `scripts/export_part_b_season.py`

## Output Contract

- JSON: machine-readable replay/archive artifact
- Markdown: human-readable season summary

## Reason

Part B should remain inspectable and reproducible as a benchmark season, not only as a live app state.
