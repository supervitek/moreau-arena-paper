# OpenClaw Repo Boundary

This repo now separates the OpenClaw/self system into two layers.

## Operational truth source

The **live** OpenClaw daemon does **not** read the repo-local
`/Users/cc/Desktop/Claude/a/moreau-arena-paper/openclaw.json` as its runtime
source of truth.

The live daemon runs from:

- `~/.openclaw/openclaw.json`

and uses the **native OpenClaw heartbeat loop** (`agents.defaults.heartbeat`),
not the repo-local `command` / `onTrigger` wiring model.

That means:

- `~/.openclaw/openclaw.json` = **live operational canon**
- repo `openclaw.json` = **reference artifact / repo-side wiring spec**
- `self/scripts/heartbeat_check.sh` = deterministic safety / recovery layer
- `self/scripts/heartbeat_escalate.sh` = manual or fallback escalation path
- `self/scripts/health_watchdog.sh` = daemon safety net, not the primary loop

Do **not** infer live runtime behavior from the repo-local `openclaw.json`
alone.

## Main repo: live operational scaffolding

The main repo keeps the code and stable scaffolding that the live OpenClaw/self
runtime depends on directly, plus one reference config artifact:

- `openclaw.json` (reference only; not the live config source)
- `ai-gateway/`
- `HEARTBEAT.md`
- stable `self/` prompts and scripts
- canonical operational files that still live at the same paths

## Public site boundary

The public Island site and the private OpenClaw/self layer are **not** the same
surface.

Rules:

- public Island pages must not depend on half-live self telemetry
- self/OpenClaw API routes are disabled by default in the public web build
- local lab exposure requires explicit opt-in via `MOREAU_ENABLE_SELF_LAB=1`
- internal self artifacts may exist in the repo for local work without being
  part of the public Island UX

This prevents a mixed state where the website exposes partial private telemetry,
broken panels, or internal operational artifacts that only make sense on the
local machine.

## Sibling vault: heavy research memory

The sibling vault at:

- `/Users/cc/Desktop/Claude/a/moreau-self-vault`

holds the heavier research layer and archive surfaces:

- `self/thinking/`
- `self/logs/`
- `self/graveyard/`
- `self/docs/`
- `self/experiments/`
- `self/.learnings/`
- `self/session_markers/`
- `self/predictions.csv`
- additional local research sidecars moved under `repo_sidecar/`

These are surfaced back into `self/` via symlinks, so the live system keeps the
same paths while the main repo stays lighter.

## Why this split exists

There are two different "epochs" in the repo:

1. a repo-native wiring idea (`openclaw.json` with explicit shell hooks)
2. the live OpenClaw-native runtime (`~/.openclaw/openclaw.json` +
   native heartbeat)

The live system currently works through the second path.

We intentionally keep the repo-local `openclaw.json` as a **reference** because
it still documents:

- the intended repo-side safety model,
- recovery scripts,
- sandbox expectations,
- and the repo architecture around self/OpenClaw.

But it is no longer treated as the live daemon's primary truth source.

## Git hygiene rule

We version stable scaffolding and code in the main repo. We do **not** version
volatile OpenClaw runtime state here (for example `self/state.json`,
`self/questions.md`, `self/dialogues.md`, `self/mirror.md`, local backup logs,
or `.openclaw/workspace-state.json`).

That keeps the working tree clean without tearing apart the live self/OpenClaw
ecosystem.

## Operator rule

When debugging live OpenClaw behavior, inspect in this order:

1. `~/.openclaw/openclaw.json`
2. `openclaw health`
3. `openclaw gateway health`
4. `~/.openclaw/cron/jobs.json`
5. `self/logs/daily/`
6. repo-local scripts under `self/scripts/`

Treat repo-local `openclaw.json` as documentation unless and until the runtime
is explicitly migrated.

## Backup reinstall on a new machine

The live hourly state backup is installed locally through LaunchAgent.
To recreate it on a new machine:

1. Open [`self/scripts/launchagent.plist.template`](/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/scripts/launchagent.plist.template)
2. Replace `__REPO_ROOT__` with the absolute repo path
3. Copy it to `~/Library/LaunchAgents/com.moreau.self.backup.plist`
4. Run `launchctl load ~/Library/LaunchAgents/com.moreau.self.backup.plist`
