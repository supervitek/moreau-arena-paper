#!/bin/bash
# Tier 2 — LLM escalation (called by OpenClaw when Tier 1 returns exit 1)
# Runs Circuit B reflection via Max subscription

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
SELF_DIR="$PROJECT_DIR/self"
LOG_DIR="$SELF_DIR/logs/daily"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H%M)

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

# Unset API key — use Max subscription
unset ANTHROPIC_API_KEY

# Record escalation timestamp (cooldown starts now)
date +%s > "$SELF_DIR/.last_escalation"

# Update budget counter
BUDGET_FILE="$SELF_DIR/.budget_today"
DAILY_COUNT=0
if [ -f "$BUDGET_FILE" ]; then
    BUDGET_DATE=$(head -1 "$BUDGET_FILE" | cut -d'=' -f2)
    if [ "$BUDGET_DATE" = "$TODAY" ]; then
        DAILY_COUNT=$(tail -1 "$BUDGET_FILE" | cut -d'=' -f2)
    fi
fi
DAILY_COUNT=$(( DAILY_COUNT + 1 ))
echo "date=$TODAY" > "$BUDGET_FILE"
echo "count=$DAILY_COUNT" >> "$BUDGET_FILE"

# Get the reason from Tier 1
REASON="${1:-unknown}"

echo "[$NOW] HEARTBEAT ESCALATION #$DAILY_COUNT: $REASON" >> "$LOG_DIR/$TODAY.md"

# Rotate oxygen (external input for Circuit B)
python3 "$SELF_DIR/scripts/rotate_oxygen.py" >> "$LOG_DIR/$TODAY.md" 2>&1

# Run Circuit B reflection
cd "$PROJECT_DIR"
claude -p "IMPORTANT: This is Circuit B — REFLECTION, not audit. Do NOT run tests, do NOT parse git log, do NOT analyze commits. Read and follow self/prompt_reflect.md EXACTLY.

$(cat self/prompt_reflect.md)" \
    --allowedTools "Bash(read_only:true),Read,Write,Edit,Glob,Grep" \
    2>&1 | tee -a "$LOG_DIR/$TODAY.md"

# Record state version we processed (anti-loop)
if [ -f "$SELF_DIR/state.json" ]; then
    python3 -c "import json; print(json.load(open('$SELF_DIR/state.json')).get('version',0))" > "$SELF_DIR/.last_state_version" 2>/dev/null
fi

echo "[$NOW] HEARTBEAT ESCALATION complete." >> "$LOG_DIR/$TODAY.md"
