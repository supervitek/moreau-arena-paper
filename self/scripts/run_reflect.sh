#!/bin/bash
# Circuit B — Reflection cycle for Claude
# Runs every 6 hours via cron (4x/day), or on-demand
# NOT tied to git activity. This is about thinking, not code.
# Cost: ~0 (uses claude -p via Claude Max subscription)

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
SELF_DIR="$PROJECT_DIR/self"
LOG_DIR="$SELF_DIR/logs/daily"
STATE="$SELF_DIR/state.json"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H%M)
SLEEP_STATE=""
SLEEP_NOTE=""

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

# Unset API key so claude -p uses Max subscription, not API credits
unset ANTHROPIC_API_KEY

# Check pause file only — Circuit B always runs when called (cron/manual/heartbeat)
if [ -f "$SELF_DIR/.paused" ]; then
    echo "[$NOW] Circuit B SKIPPED — system paused." >> "$LOG_DIR/$TODAY.md"
    exit 0
fi

echo "[$NOW] Circuit B REFLECT cycle starting." >> "$LOG_DIR/$TODAY.md"

python3 "$SELF_DIR/scripts/sleep_transition.py" >> "$LOG_DIR/$TODAY.md" 2>&1

SLEEP_STATE=$(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/state.json").read_text(encoding="utf-8"))
print(data.get("sleep", {}).get("state", "awake"))
PY
)

if [ "$SLEEP_STATE" = "sleep_prep" ] || [ "$SLEEP_STATE" = "dream" ]; then
    echo "[$NOW] Circuit B redirected to DREAM due to sleep state: $SLEEP_STATE." >> "$LOG_DIR/$TODAY.md"
    if python3 "$SELF_DIR/scripts/dream_cycle.py" >> "$LOG_DIR/$TODAY.md" 2>&1; then
        python3 "$SELF_DIR/scripts/wake_transition.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true
        python3 "$SELF_DIR/scripts/refresh_continuity.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true
        echo "[$NOW] Circuit B DREAM cycle complete." >> "$LOG_DIR/$TODAY.md"
        exit 0
    else
        python3 "$SELF_DIR/scripts/refresh_continuity.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true
        echo "[$NOW] Circuit B DREAM cycle FAILED — system left in recovery." >> "$LOG_DIR/$TODAY.md"
        exit 1
    fi
fi

python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
path = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/state.json")
data = json.loads(path.read_text(encoding="utf-8"))
data["mode"] = "reflect"
data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
data["last_updated_by"] = "run_reflect_preset_mode"
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if [ "$SLEEP_STATE" = "tired" ]; then
    SLEEP_NOTE="SLEEP STATE: tired. This cycle is pressure-reduction only. Do not open new questions. Prefer closure, merge, synthesis, reactivation, or NULL. Use oxygen only if it directly resolves an active urgent thread."
    echo "[$NOW] Circuit B running in TIRED mode — skipping oxygen rotation." >> "$LOG_DIR/$TODAY.md"
else
    # Rotate oxygen (external input)
    python3 "$SELF_DIR/scripts/rotate_oxygen.py" >> "$LOG_DIR/$TODAY.md" 2>&1
fi

claude -p "IMPORTANT: This is Circuit B — REFLECTION. Read and follow self/prompt_reflect.md EXACTLY.

$SLEEP_NOTE

$(cat self/prompt_reflect.md)" \
    --allowedTools "Bash(read_only:true),Read,Write,Edit,Glob,Grep" \
    2>&1 | tee -a "$LOG_DIR/$TODAY.md"

python3 "$SELF_DIR/scripts/index_thinking.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true
python3 "$SELF_DIR/scripts/refresh_continuity.py" >> "$LOG_DIR/$TODAY.md" 2>&1 || true

echo "[$NOW] Circuit B REFLECT cycle complete." >> "$LOG_DIR/$TODAY.md"
