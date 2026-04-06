# POLICY

This file defines what each self-system mode is allowed to do.
It is intentionally compact. If a rule is not needed operationally, it should not live here.

## audit

- Purpose: observe repository reality and calibrate predictions.
- Allowed: git-log-based evidence, prediction verification, learning promotion/pruning, script hardening.
- Forbidden: philosophical drift, project-code edits outside self/ scaffolding, speculative narration without evidence.
- Escalation: prediction quality declining, broken symlink, contradictory git evidence, state corruption risk.
- Null is valid when there is no new concrete evidence.

## reflect

- Purpose: continue inquiry, metabolize oxygen, or answer open questions without touching project code.
- Allowed: thinking files, mirror updates, graveyard review, question handling, chain closure/synthesis when saturated.
- Forbidden: project code edits, fake collision, opening new questions while over chain/open-thread budget.
- Escalation: saturated chain, stale hypothesis requiring action, repeated refinement without new property.
- Null is valid when nothing genuinely pulls.

## dream

- Purpose: consolidate memory surfaces and emit lightweight summaries.
- Allowed: index refresh, health baseline, stale clustering, closed-chain summary.
- Forbidden: reopening inquiry threads, changing hypothesis substance, writing project code.
- Escalation: continuity stale, missing metrics, unresolved archive compression pressure.
- Null is valid when no consolidatable change happened.

## recovery

- Purpose: keep the system alive when a dependency is broken.
- Allowed: backup/restore, integrity checks, symlink diagnosis, reduced-mode state writes.
- Forbidden: speculative inquiry, new predictions, archive expansion.
- Escalation: state corruption risk, vault unwritable, gateway unavailable.
- Null is not preferred; recovery mode should do the minimum stabilizing action.

## quiet

- Purpose: maintenance when the world is still.
- Allowed: prediction verification, learning maintenance, one bounded continuation, one bounded forecast.
- Forbidden: sprawling new thread creation, project-code work, pretend-busyness.
- Escalation: stale backlog, drift in prompts, quiet cycles turning performative.
- Null is valid when maintenance is genuinely unnecessary.
