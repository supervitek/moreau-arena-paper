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
HASH_FILE_LEGACY="$SELF_DIR/.constitution_hash"
HASH_FILE_PINNED="$SELF_DIR/pinned_constitution_hash"
COOLDOWN_FILE="$SELF_DIR/.last_escalation"
PAUSE_FILE="$SELF_DIR/.paused"
BUDGET_FILE="$SELF_DIR/.budget_today"
TODAY=$(date +%Y-%m-%d)
DAILY_LOG="$SELF_DIR/logs/daily/$TODAY.md"
CONTINUITY="$SELF_DIR/CONTINUITY.md"
FALLBACK_LOG="$SELF_DIR/heartbeat_fallback.log"

LOG_FILE="$DAILY_LOG"
if ! touch "$DAILY_LOG" 2>/dev/null; then
    LOG_FILE="$FALLBACK_LOG"
    touch "$LOG_FILE"
fi

append_log() {
    printf '%s\n' "$1" >> "$LOG_FILE"
}

# --- PAUSE CHECK ---
if [ -f "$PAUSE_FILE" ]; then
    exit 0
fi

# --- CONSTITUTION INTEGRITY ---
HASH_FILE=""
if [ -f "$HASH_FILE_PINNED" ]; then
    HASH_FILE="$HASH_FILE_PINNED"
elif [ -f "$HASH_FILE_LEGACY" ]; then
    HASH_FILE="$HASH_FILE_LEGACY"
fi

if [ -n "$HASH_FILE" ]; then
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
    append_log "WARNING: self/thinking symlink broken"
fi
if [ ! -d "$SELF_DIR/logs/daily" ]; then
    append_log "WARNING: self/logs/daily symlink broken"
fi
if [ ! -f "$SELF_DIR/predictions.csv" ]; then
    append_log "WARNING: self/predictions.csv symlink broken"
fi

# --- SLEEP PRESSURE CHECK ---
SLEEP_SIGNAL=$(python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
state = json.loads((root / "state.json").read_text(encoding="utf-8"))
reflect = json.loads((root / "state_reflect.json").read_text(encoding="utf-8"))
mirror = (root / "mirror.md").read_text(encoding="utf-8")
sleep = state.get("sleep", {})
budget = int(state.get("open_threads_budget", 7))
threads = len(reflect.get("open_threads", []))
chain = state.get("chain_tracking", {})
chain_len = int(chain.get("current_chain_length", 0))
chain_max = int(chain.get("max_chain_length", 999))
stale_threshold = int(sleep.get("stale_hypothesis_threshold", 3))
preamble_limit = int(sleep.get("preamble_max_chars", 5000))
continuity_limit = int(sleep.get("continuity_max_age_hours", 12))

stale = 0
inside = False
for line in mirror.splitlines():
    if line.startswith("## Active Hypotheses"):
        inside = True
        continue
    if inside and line.startswith("## "):
        break
    if inside and "TTL status:" in line and ("STALE" in line or "EXPIRED" in line):
        stale += 1

preamble_chars = len((root / "preamble.md").read_text(encoding="utf-8"))
cont_age = 0.0
cont = root / "CONTINUITY.md"
if cont.exists():
    modified = datetime.fromtimestamp(cont.stat().st_mtime, tz=timezone.utc)
    cont_age = max(0.0, (datetime.now(timezone.utc) - modified).total_seconds() / 3600.0)

required = []
recommended = []
if threads > budget:
    required.append(f"open_threads_exceeded:{threads}/{budget}")
elif threads == budget and budget > 0:
    recommended.append(f"thread_budget_full:{threads}/{budget}")
if chain_len >= chain_max and chain_max > 0:
    required.append(f"chain_saturated:{chain_len}/{chain_max}")
if stale >= stale_threshold:
    required.append(f"stale_hypotheses:{stale}/{stale_threshold}")
if preamble_chars > preamble_limit:
    required.append(f"preamble_too_long:{preamble_chars}>{preamble_limit}")
if cont_age > continuity_limit:
    required.append(f"continuity_stale:{cont_age:.1f}h>{continuity_limit}h")

if required:
    print("required|" + ",".join(required))
elif recommended:
    print("recommended|" + ",".join(recommended))
else:
    print("ok|")
PY
)

SLEEP_LEVEL="${SLEEP_SIGNAL%%|*}"
SLEEP_REASONS="${SLEEP_SIGNAL#*|}"
if [ "$SLEEP_LEVEL" = "required" ]; then
    append_log "ESCALATE: sleep_required — $SLEEP_REASONS"
    echo "ESCALATE: sleep_required — $SLEEP_REASONS"
    exit 1
fi
if [ "$SLEEP_LEVEL" = "recommended" ]; then
    append_log "NOTICE: sleep_recommended — $SLEEP_REASONS"
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
