# AGENTS.md — Rules for Codex and automated agents
## Repo: moreau-arena-paper
## Test command
python -m pytest tests/test_invariants.py
## Branch rules
- Never push to main directly
- Create branch: feature/<issue-number>-<short-name>
- Open PR when done
- PR title: "Task X.Y: description"
## What you MUST NOT change
- config.json (frozen, hash-verified)
- data/tournament_001/ (immutable)
- data/tournament_002/ (immutable)
- paper/moreau_arena.tex (unless task explicitly says so)
## What you MUST do
- Run pytest before opening PR
- Commit after each subtask
- If blocked, add comment to the GitHub issue explaining why
## Code style
- Python 3.10+, type hints, docstrings
- Use only stdlib + packages in requirements.txt
