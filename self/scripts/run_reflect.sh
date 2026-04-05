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

# Rotate oxygen (external input)
python3 "$SELF_DIR/scripts/rotate_oxygen.py" >> "$LOG_DIR/$TODAY.md" 2>&1

claude -p "IMPORTANT: This is Circuit B — REFLECTION. Read and follow self/prompt_reflect.md EXACTLY.

$(cat self/prompt_reflect.md)" \
    --allowedTools "Bash(read_only:true),Read,Write,Edit,Glob,Grep" \
    2>&1 | tee -a "$LOG_DIR/$TODAY.md"

echo "[$NOW] Circuit B REFLECT cycle complete." >> "$LOG_DIR/$TODAY.md"
