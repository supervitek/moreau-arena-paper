#!/bin/bash
# Write session markers — runs as post-session hook BEFORE mirror loop
# Creates 1-3 markers about the session that just ended
# These feed Circuit B reflection cycles

set -euo pipefail

PROJECT_DIR="/Users/cc/Desktop/Claude/a/moreau-arena-paper"
SELF_DIR="$PROJECT_DIR/self"
MARKERS_DIR="$SELF_DIR/session_markers"
NOW=$(date +%Y-%m-%d_%H%M)

mkdir -p "$MARKERS_DIR"

cd "$PROJECT_DIR"

# Unset API key so claude -p uses Max subscription, not API credits
unset ANTHROPIC_API_KEY

MARKER_PROMPT="You just finished a Claude Code session. Before the session context is lost, write 1-3 session markers.

Markers are single-line observations about key moments in the session:
[TEMPLATE] — you gave a safe/template response instead of thinking
[SHIFT] — noticeable quality change (leap or drop) in your thinking
[STUCK] — you got stuck or went in circles
[GOOD] — something genuinely worked well
[REDIRECT] — the human corrected your approach
[DEEP] — you went deeper than expected

Write ONLY the markers, one per line. No explanation. No preamble.
If nothing notable happened, write: [NULL] Routine session
Maximum: 3 markers."

# Write markers file
echo "# Session Markers — $NOW" > "$MARKERS_DIR/$NOW.md"
echo "" >> "$MARKERS_DIR/$NOW.md"

claude -p "$MARKER_PROMPT" \
    --allowedTools "Read" \
    2>&1 >> "$MARKERS_DIR/$NOW.md"

echo "" >> "$MARKERS_DIR/$NOW.md"
