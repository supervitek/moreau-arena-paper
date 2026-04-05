#!/bin/bash
# Tier 1 — Deterministic heartbeat check (no LLM, no tokens)
# Called by OpenClaw heartbeat. Exit codes:
#   0 = all quiet, nothing to do
#   1 = something changed, escalate to LLM (Tier 2)
#   2 = HARD STOP — constitution changed, alert human

set -euo pipefail

SELF_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper/self"
STATE="$SELF_DIR/state.json"
MARKERS_DIR="$SELF_DIR/session_markers"
CONSTITUTION="$SELF_DIR/constitution.md"
HASH_FILE="$SELF_DIR/.constitution_hash"
COOLDOWN_FILE="$SELF_DIR/.last_escalation"
PAUSE_FILE="$SELF_DIR/.paused"
BUDGET_FILE="$SELF_DIR/.budget_today"
TODAY=$(date +%Y-%m-%d)
DAILY_LOG="$SELF_DIR/logs/daily/$TODAY.md"

# --- PAUSE CHECK ---
if [ -f "$PAUSE_FILE" ]; then
    exit 0
fi

# --- CONSTITUTION INTEGRITY ---
if [ -f "$HASH_FILE" ]; then
    PINNED=$(cat "$HASH_FILE")
    CURRENT=$(shasum -a 256 "$CONSTITUTION" | cut -d' ' -f1)
    if [ "$PINNED" != "$CURRENT" ]; then
        echo "HARD STOP: constitution.md changed!"
        exit 2
    fi
fi

# --- BUDGET CHECK ---
DAILY_COUNT=0
if [ -f "$BUDGET_FILE" ]; then
    BUDGET_DATE=$(head -1 "$BUDGET_FILE" | cut -d'=' -f2)
    if [ "$BUDGET_DATE" = "$TODAY" ]; then
        DAILY_COUNT=$(tail -1 "$BUDGET_FILE" | cut -d'=' -f2)
    fi
fi
if [ "$DAILY_COUNT" -ge 15 ]; then
    # Budget exhausted for today
    exit 0
fi

# --- SYMLINK HEALTH CHECK ---
if [ ! -d "$SELF_DIR/thinking" ]; then
    echo "WARNING: self/thinking symlink broken" >> "$DAILY_LOG"
fi

# --- COOLDOWN CHECK (30 min) ---
if [ -f "$COOLDOWN_FILE" ]; then
    LAST=$(cat "$COOLDOWN_FILE")
    NOW=$(date +%s)
    DIFF=$(( NOW - LAST ))
    if [ "$DIFF" -lt 1800 ]; then
        # Still in cooldown
        exit 0
    fi
fi

# --- CHECK 1: New session markers ---
MARKER_COUNT=$(find "$MARKERS_DIR" -name "*.md" ! -name "README.md" -newer "$COOLDOWN_FILE" 2>/dev/null | wc -l | tr -d ' ')
if [ "$MARKER_COUNT" -gt 0 ]; then
    echo "ESCALATE: $MARKER_COUNT new session markers"
    exit 1
fi

# --- CHECK 2: state.json version changed ---
if [ -f "$STATE" ]; then
    CURRENT_VER=$(python3 -c "import json; print(json.load(open('$STATE')).get('version',0))" 2>/dev/null || echo "0")
    LAST_VER=$(cat "$SELF_DIR/.last_state_version" 2>/dev/null || echo "0")
    if [ "$CURRENT_VER" != "$LAST_VER" ]; then
        # Check if WE processed this already (anti-loop)
        LAST_BY=$(python3 -c "import json; print(json.load(open('$STATE')).get('last_updated_by',''))" 2>/dev/null || echo "")
        if echo "$LAST_BY" | grep -q "heartbeat"; then
            # We wrote this ourselves, skip
            exit 0
        fi
        echo "ESCALATE: state.json version changed ($LAST_VER -> $CURRENT_VER)"
        exit 1
    fi
fi

# --- CHECK 3: Staleness (6h without any LLM call) ---
if [ -f "$COOLDOWN_FILE" ]; then
    LAST=$(cat "$COOLDOWN_FILE")
    NOW=$(date +%s)
    DIFF=$(( NOW - LAST ))
    if [ "$DIFF" -ge 21600 ]; then
        echo "ESCALATE: 6h staleness — time for reflection"
        exit 1
    fi
else
    # No cooldown file = never ran → escalate
    echo "ESCALATE: first run"
    exit 1
fi

# --- ALL QUIET ---
exit 0
