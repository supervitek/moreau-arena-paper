#!/bin/bash
# Circuit A — Git audit cycle for Claude
# Triggered: post-session hook (after markers are written)
# Observes git history, verifies predictions, manages learnings
# Cost: ~0 (uses claude -p via Claude Max subscription)

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
SELF_DIR="$PROJECT_DIR/self"
LOG_DIR="$SELF_DIR/logs/daily"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H%M)

mkdir -p "$LOG_DIR"

# Unset API key so claude -p uses Max subscription, not API credits
unset ANTHROPIC_API_KEY

cd "$PROJECT_DIR"

python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
path = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/state.json")
data = json.loads(path.read_text(encoding="utf-8"))
data["mode"] = "audit"
data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
data["last_updated_by"] = "run_audit_preset_mode"
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

# Check if there's been recent git activity (per PROPOSAL-003)
RECENT_COMMITS=$(git log --since="6 hours ago" --oneline 2>/dev/null | wc -l | tr -d ' ')

if [ "$RECENT_COMMITS" -gt 0 ]; then
    echo "[$NOW] Circuit A AUDIT active mode. $RECENT_COMMITS recent commits." >> "$LOG_DIR/$TODAY.md"
    claude -p "$(cat self/prompt.md)" \
        --allowedTools "Bash(read_only:true),Read,Write,Edit,Glob,Grep" \
        2>&1 | tee -a "$LOG_DIR/$TODAY.md"
    python3 "$SELF_DIR/scripts/prediction_metrics.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true
    python3 "$SELF_DIR/scripts/refresh_continuity.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true
else
    # No new commits — skip per PROPOSAL-003 (saves cycles)
    echo "[$NOW] Circuit A SKIPPED — no new commits in 6h." >> "$LOG_DIR/$TODAY.md"
fi

echo "[$NOW] Circuit A cycle complete." >> "$LOG_DIR/$TODAY.md"
