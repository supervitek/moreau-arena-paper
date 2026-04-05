#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd "$SELF_DIR/.." && pwd)"
VAULT_DIR="$(cd "$REPO_DIR/.." && pwd)/moreau-self-vault"
STATE_FILE="$SELF_DIR/state.json"
PRIMARY_BACKUP="$SELF_DIR/state.json.bak"
BACKUP_DIR="$VAULT_DIR/state_backups"
LOG_FILE="$SCRIPT_DIR/backup.log"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TIMESTAMPED_BACKUP="$BACKUP_DIR/state.$STAMP.json"

mkdir -p "$BACKUP_DIR"

python3 -m json.tool "$STATE_FILE" >/dev/null
cp "$STATE_FILE" "$PRIMARY_BACKUP"
cp "$STATE_FILE" "$TIMESTAMPED_BACKUP"
echo "$STAMP backup $TIMESTAMPED_BACKUP" >> "$LOG_FILE"
