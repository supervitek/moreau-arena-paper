# Part B Public Agent Path

Last updated: 2026-03-20
Status: Future path, not yet implemented
Owner: Codex acting as chief engineer

## Purpose

This document defines the path from the current house-agent product layer to a future public/BYO agent path.

## Current State

Today:

- house agent exists
- benchmark boundary exists
- public observation/action/scoring contract exists
- no public BYO-agent API exists yet

This is intentional.

## Required Preconditions

Before a public/BYO path opens, the project must have:

1. Frozen public observation contract
2. Frozen public action grammar
3. Stable replay/report export
4. Trace tooling good enough to debug external runs
5. Clear labeling between:
   - `manual`
   - `operator-assisted`
   - `agent-only`
   - house-agent usage

## First Public Surface

The first public agent path should be narrow:

- submit observation
- receive one legal action
- append replayable trace

No tool use.
No hidden memory API.
No special verbs.

## Benchmark Rule

Public and BYO agents must never receive:

- hidden state
- secret verbs
- secret scoring hints
- privileged budget bypass

If the house agent uses richer internal product tooling, that tooling stays outside the benchmark claim.

## Suggested Rollout

1. Keep house agent as the only live autonomous product
2. Harden trace export and replay
3. Publish a tiny observation/action reference
4. Open a sandboxed public-agent path later
5. Only then consider BYO leaderboard participation at scale

## Red Line

Do not ship a fake BYO path that secretly depends on hidden internal behavior.
