#!/bin/bash
# Health watchdog — checks that OpenClaw daemon is alive
# Run via launchd or cron as safety net

SELF_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper/self"
LOG_DIR="$SELF_DIR/logs/daily"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H%M)

# Check if daemon is responding
if curl -s -o /dev/null -w "%{http_code}" http://localhost:18789/health 2>/dev/null | grep -q "200"; then
    exit 0
fi

# Daemon not responding — try restart
echo "[$NOW] WATCHDOG: OpenClaw daemon not responding. Restarting..." >> "$LOG_DIR/$TODAY.md"
cd /Users/cc/Desktop/Claude/a/moreau-arena-paper
openclaw start 2>&1 >> "$LOG_DIR/$TODAY.md"
