#\!/usr/bin/env bash
# Quick verification wrapper for the Moreau Arena replication package.
# Usage: ./scripts/quick_verify.sh [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
python3 verify_all.py "$@"
