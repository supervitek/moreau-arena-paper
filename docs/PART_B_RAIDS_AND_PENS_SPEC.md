# Part B Raids And Pens Spec

Last updated: 2026-03-20
Status: Future expansion, not active
Owner: Codex acting as chief engineer

## Thesis

Inter-player aggression belongs in `Part B`, but only as a later expansion and only under bounded loss.

The idea is strong:

- agents should eventually defend, raid, and time risk against other operators
- this fits the harsh ecology fantasy
- this increases real strategic pressure

## First Rule

No mandatory raids.

The first version must be:

- opt-in
- asynchronous
- bounded

## First Implementation Shape

### Pens

Each player exposes a defensive pen state:

- chosen defender
- current state snapshot
- visible raid vulnerability window

### Raids

An attacker may target an opted-in pen asynchronously.

The raid resolves against a frozen defensive snapshot, not a live interactive session.

## Bounded Loss

The first raid layer must not allow full wipe.

Allowed loot:

- a bounded portion of expedition value
- arena spoils
- raid token / shard / reputation swing

Not allowed in first pass:

- total deletion
- irreversible pet theft
- benchmark-critical state corruption

## Required Safety Rails

- opt-in flag
- cooldown after raid
- recovery shield window
- replay log
- defender-facing report
- separate telemetry

## Benchmark Rule

If raids ever become benchmark-relevant, they require:

- a new explicit contract version
- separate labeling
- separate evaluation claims

No silent insertion into the current `B1/B5` contract.
