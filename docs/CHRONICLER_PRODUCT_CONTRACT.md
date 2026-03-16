# Chronicler Product Contract

Last updated: 2026-03-16
Status: Phase 1 contract

## Prototype Scope

Entity:
- `Chronicler`

Surface:
- `/island/home`

Role:
- diegetic advisory layer

Not in scope:
- auto-play
- mutation automation
- public API
- second surface

---

## Invocation Model

Chronicler is not automatic on page load.

The user must explicitly invoke it from the dashboard.

Reason:
- preserves human primacy
- keeps usage measurement meaningful
- avoids the "assistant attached to every session" feeling

---

## Response Contract

Each response contains:
- `observation`
- `prompt`
- optional `suggestion`
- optional `suggested_action`
- `uncertainty`

Where:
- `observation` = what Chronicler thinks it sees
- `prompt` = question or warning
- `suggestion` = bounded, optional nudge
- `suggested_action` = one tracked action id or `none`
- `uncertainty` = explicit limit marker

---

## Suggested Action Vocabulary

Allowed tracked actions:
- `none`
- `train`
- `caretaker`
- `lab`
- `dreams`
- `prophecy`
- `pact`
- `rivals`
- `tides`
- `deep_tide`
- `profile`
- `menagerie`

Chronicler should prefer `none` unless the context clearly supports one narrow nudge.

Prototype 1 suggestion budget:
- no more than 2 actionable suggestions per pet/session/day
- only every third reading may carry a non-`none` suggested action

This exists to prevent Chronicler from becoming an authority through repetition.

---

## UI Contract

The dashboard surface should:
- feel in-world
- not look like chat
- not look like a dashboard recommendation card
- remain visually secondary to the pet itself

The panel should contain:
- title
- one short framing line
- response block
- one explicit invocation button
- one refresh button only after a response exists

No chat history is shown in Prototype 1.

---

## Follow / Override Definitions

### Followed Advice

A response counts as "followed" only if:
- `suggested_action` is not `none`
- the user clicks the matching tracked action within 10 minutes of the response

### Override

A response counts as "overridden" only if:
- `suggested_action` is not `none`
- the user clicks a different tracked action within 10 minutes of the response

### No Decision

If neither happens, the response remains advisory but not behaviorally classified.

---

## Measurement Contract

Required event types:
- `open`
- `response`
- `dismiss`
- `refresh`
- `action_click`
- `page_exit`

Each event should include:
- `trace_id`
- `route`
- `session_id`
- `suggested_action` if present
- `action_id` when relevant
- `relation` when relevant: `follow`, `override`, or `neutral`

---

## Fallback Contract

If model generation fails or cost cap is reached:
- Chronicler still responds
- output remains in the same contract shape
- fallback must remain diegetic
- fallback must not degrade into error-message prose

---

## Kill-Switch Contract

Prototype 1 must be fully disableable by configuration.

If disabled:
- UI remains present but quiet, or hides cleanly
- no model calls fire
- no broken page states occur

---

## Success Condition for Prototype 1

Prototype 1 is successful only if:
- people use it
- people still make their own decisions
- it feels specifically Moreau
- it stays inside guardrails

If it becomes merely useful, it has failed.
