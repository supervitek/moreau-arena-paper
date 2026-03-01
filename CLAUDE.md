# CLAUDE.md — Rules for Claude Code sessions
## Project: Moreau Arena benchmark
## Key principle
Moreau Core is FROZEN. Config hash: b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534
## Test command
python -m pytest tests/test_invariants.py
## Immutable files
- config.json
- data/tournament_001/*
- data/tournament_002/*
## Architecture rules
- New features go in versioned tracks, not Core
- Ablation variants go in run_ablation.py
- All metrics must be reproducible from JSONL data
