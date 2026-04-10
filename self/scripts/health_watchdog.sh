#!/bin/bash
# Health watchdog — checks both OpenClaw liveness and heartbeat freshness.
# Run via launchd or cron as a safety net.

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
SELF_DIR="$PROJECT_DIR/self"
LOG_DIR="$SELF_DIR/logs/daily"
CHECK_SCRIPT="$SELF_DIR/scripts/heartbeat_check.sh"
ESCALATE_SCRIPT="$SELF_DIR/scripts/heartbeat_escalate.sh"
COOLDOWN_FILE="$SELF_DIR/.last_escalation"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H%M)
DAILY_LOG="$LOG_DIR/$TODAY.md"
FALLBACK_LOG="$SELF_DIR/heartbeat_fallback.log"
MAX_STALE_SECONDS=$((6 * 3600))

mkdir -p "$LOG_DIR" 2>/dev/null || true

LOG_FILE="$DAILY_LOG"
if ! touch "$DAILY_LOG" 2>/dev/null; then
    LOG_FILE="$FALLBACK_LOG"
    touch "$LOG_FILE"
fi

log_watchdog() {
    echo "[$NOW] WATCHDOG: $1" >> "$LOG_FILE"
}

run_heartbeat_cycle() {
    local check_output=""
    local check_status=0
    local reason="watchdog-trigger"

    set +e
    check_output=$(bash "$CHECK_SCRIPT" 2>&1)
    check_status=$?
    set -e

    if [ -n "$check_output" ]; then
        printf '%s\n' "$check_output" >> "$LOG_FILE"
        reason=$(printf '%s\n' "$check_output" | tail -n 1)
    fi

    case "$check_status" in
        0)
            log_watchdog "heartbeat check quiet"
            ;;
        1)
            log_watchdog "heartbeat check requested escalation: $reason"
            bash "$ESCALATE_SCRIPT" "$reason"
            ;;
        2)
            log_watchdog "heartbeat check hit hard stop: $reason"
            ;;
        *)
            log_watchdog "heartbeat check failed with exit $check_status"
            if [ -n "$check_output" ]; then
                printf '%s\n' "$check_output" >> "$LOG_FILE"
            fi
            return "$check_status"
            ;;
    esac
}

cd "$PROJECT_DIR"

# Check if daemon is responding.
if ! curl -fsS http://127.0.0.1:18789/health >/dev/null 2>&1; then
    log_watchdog "OpenClaw daemon not responding. Restarting..."
    openclaw gateway start >> "$LOG_FILE" 2>&1 || true
fi

# If the self-improvement loop looks stale, force one cycle via the repo scripts.
if [ ! -f "$COOLDOWN_FILE" ]; then
    log_watchdog "no escalation timestamp found; running heartbeat recovery cycle"
    run_heartbeat_cycle
    exit 0
fi

LAST=$(cat "$COOLDOWN_FILE")
NOW_EPOCH=$(date +%s)
STALE_SECONDS=$(( NOW_EPOCH - LAST ))

if [ ! -f "$DAILY_LOG" ] || [ "$STALE_SECONDS" -ge "$MAX_STALE_SECONDS" ]; then
    log_watchdog "self-improvement heartbeat stale (${STALE_SECONDS}s since last escalation); running recovery cycle"
    run_heartbeat_cycle
fi
