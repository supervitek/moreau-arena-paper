#!/bin/bash
# Auto-revert — if the last self/ commit broke something, revert it
# Called by mirror loop if tests fail after a rule change

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
cd "$PROJECT_DIR"

# Find last self/ commit
LAST_SELF_COMMIT=$(git log --oneline -- self/ | head -1 | awk '{print $1}')

if [ -z "$LAST_SELF_COMMIT" ]; then
    echo "No self/ commits found. Nothing to revert."
    exit 0
fi

# Run project tests
if python3 -m pytest tests/test_invariants.py -q 2>/dev/null; then
    echo "Tests pass. No revert needed."
    exit 0
fi

echo "Tests FAILED after self/ changes. Reverting commit $LAST_SELF_COMMIT..."
git revert --no-edit "$LAST_SELF_COMMIT"
echo "Reverted. Please check self/REVIEW.md for what went wrong."

# Log the revert
echo "$(date +%Y-%m-%d_%H%M) AUTO-REVERT: $LAST_SELF_COMMIT (tests failed)" >> self/logs/reverts.log
