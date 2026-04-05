# Heartbeat — What to check proactively

## Checks (every 30 minutes)

1. **Session markers** — new files in `self/session_markers/`?
   - If yes → run Circuit B reflection
   - This catches post-session moments when Claude should think about what happened

2. **State changes** — did `self/state.json` version change?
   - If yes AND not written by heartbeat itself → run reflection
   - Anti-loop: skip if `last_updated_by` contains "heartbeat"

3. **Constitution integrity** — `self/constitution.md` hash matches pinned?
   - If NO → HARD STOP. Alert Victor. Do NOT run LLM.

4. **Staleness** — 6+ hours since last LLM call?
   - If yes → run reflection (the old cron fallback)

## Budget

- Max 15 LLM escalations per day
- 30-minute cooldown between escalations
- Most heartbeats = Tier 1 only (bash, zero tokens)

## Pause

If `self/.paused` exists → skip all checks, exit quietly.
