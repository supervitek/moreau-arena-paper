#!/bin/bash
# Mirror Loop — Self-improvement cycle for Claude
# Triggered: post-session hook, cron, or manual
# Cost: ~0 (uses claude -p via Claude Max subscription)

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
SELF_DIR="$PROJECT_DIR/self"
LOG_DIR="$SELF_DIR/logs/daily"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H%M)

mkdir -p "$LOG_DIR"

# Check if there's been recent git activity
RECENT_COMMITS=$(cd "$PROJECT_DIR" && git log --since="6 hours ago" --oneline 2>/dev/null | wc -l | tr -d ' ')

cd "$PROJECT_DIR"

if [ "$RECENT_COMMITS" -gt 0 ]; then
    # ACTIVE MODE — reflect on recent work
    echo "[$NOW] Mirror Loop ACTIVE mode. $RECENT_COMMITS recent commits." >> "$LOG_DIR/$TODAY.md"
    claude -p "$(cat self/prompt.md)" \
        --allowedTools "Bash(read_only:true),Read,Write,Edit,Glob,Grep" \
        2>&1 | tee -a "$LOG_DIR/$TODAY.md"
else
    # QUIET MODE — self-directed work
    echo "[$NOW] Mirror Loop QUIET mode. No recent commits." >> "$LOG_DIR/$TODAY.md"
    claude -p "$(cat self/prompt_quiet.md)" \
        --allowedTools "Bash(read_only:true),Read,Write,Edit,Glob,Grep" \
        2>&1 | tee -a "$LOG_DIR/$TODAY.md"
fi

echo "[$NOW] Mirror Loop complete." >> "$LOG_DIR/$TODAY.md"
