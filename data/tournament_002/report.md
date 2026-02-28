# Tournament 002 Report — Adaptive Play

**Date:** 2026-02-27 03:51 UTC
**Config hash:** `b7ec588583135ad6...`
**Agents:** 13
**Series completed:** 780
**Series with errors:** 0
**Best-of:** 7
**Series per pair:** 10
**Format:** Adaptive (loser sees winner's build, re-picks)

## Bradley-Terry Rankings (95% CI)

| Rank | Agent | BT Score | CI Lower | CI Upper | Games |
|------|-------|----------|----------|----------|-------|
| 1 | gpt-5.2-codex | 1.0000 | 0.7925 | 1.0000 | 120 |
| 2 | gemini-3-flash-preview | 0.6793 | 0.3930 | 1.0000 | 120 |
| 3 | grok-4-1-fast-reasoning | 0.6496 | 0.3656 | 1.0000 | 120 |
| 4 | claude-opus-4-6 | 0.2520 | 0.1429 | 0.3934 | 120 |
| 5 | claude-sonnet-4-6 | 0.2520 | 0.1297 | 0.4266 | 120 |
| 6 | gpt-5.2 | 0.2520 | 0.1398 | 0.4217 | 120 |
| 7 | claude-haiku-4-5-20251001 | 0.2258 | 0.1269 | 0.3592 | 120 |
| 8 | gemini-3.1-pro-preview | 0.1882 | 0.1043 | 0.3108 | 120 |
| 9 | SmartAgent | 0.0926 | 0.0490 | 0.1465 | 120 |
| 10 | HighVarianceAgent | 0.0698 | 0.0379 | 0.1081 | 120 |
| 11 | ConservativeAgent | 0.0614 | 0.0308 | 0.1029 | 120 |
| 12 | GreedyAgent | 0.0426 | 0.0209 | 0.0761 | 120 |
| 13 | RandomAgent | 0.0066 | 0.0038 | 0.0101 | 120 |

## Elo Rankings

| Rank | Agent | Elo |
|------|-------|-----|
| 1 | grok-4-1-fast-reasoning | 1900 |
| 2 | gpt-5.2-codex | 1879 |
| 3 | gpt-5.2 | 1758 |
| 4 | claude-sonnet-4-6 | 1709 |
| 5 | gemini-3-flash-preview | 1672 |
| 6 | claude-haiku-4-5-20251001 | 1553 |
| 7 | gemini-3.1-pro-preview | 1527 |
| 8 | claude-opus-4-6 | 1526 |
| 9 | SmartAgent | 1336 |
| 10 | HighVarianceAgent | 1335 |
| 11 | ConservativeAgent | 1286 |
| 12 | GreedyAgent | 1262 |
| 13 | RandomAgent | 757 |

## Pairwise Win Rates (row vs column)

| Agent | grok-4-1-fas | gpt-5.2-code | gpt-5.2 | claude-sonne | gemini-3-fla | claude-haiku | gemini-3.1-p | claude-opus- | SmartAgent | HighVariance | Conservative | GreedyAgent | RandomAgent |
|-------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| grok-4-1-fast-reasoning | --- | 20% | 50% | 50% | 90% | 90% | 80% | 70% | 100% | 100% | 100% | 100% | 100% |
| gpt-5.2-codex | 80% | --- | 80% | 80% | 70% | 90% | 90% | 90% | 100% | 100% | 70% | 90% | 100% |
| gpt-5.2 | 50% | 20% | --- | 50% | 20% | 30% | 50% | 50% | 100% | 90% | 100% | 50% | 100% |
| claude-sonnet-4-6 | 50% | 20% | 50% | --- | 60% | 60% | 70% | 100% | 10% | 90% | 60% | 40% | 100% |
| gemini-3-flash-preview | 10% | 30% | 80% | 40% | --- | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| claude-haiku-4-5-20251001 | 10% | 10% | 70% | 40% | 0% | --- | 90% | 30% | 60% | 70% | 100% | 100% | 100% |
| gemini-3.1-pro-preview | 20% | 10% | 50% | 30% | 0% | 10% | --- | 50% | 70% | 90% | 100% | 100% | 100% |
| claude-opus-4-6 | 30% | 10% | 50% | 0% | 0% | 70% | 50% | --- | 100% | 100% | 100% | 100% | 100% |
| SmartAgent | 0% | 0% | 0% | 90% | 0% | 40% | 30% | 0% | --- | 80% | 30% | 70% | 100% |
| HighVarianceAgent | 0% | 0% | 10% | 10% | 0% | 30% | 10% | 0% | 20% | --- | 100% | 90% | 100% |
| ConservativeAgent | 0% | 30% | 0% | 40% | 0% | 0% | 0% | 0% | 70% | 0% | --- | 100% | 100% |
| GreedyAgent | 0% | 10% | 50% | 60% | 0% | 0% | 0% | 0% | 30% | 10% | 0% | --- | 100% |
| RandomAgent | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | --- |

## Adaptation Metrics

| Agent | Build Diversity | Adapted Games |
|-------|----------------|---------------|
| grok-4-1-fast-reasoning | 32 | 150 |
| gpt-5.2-codex | 63 | 163 |
| gpt-5.2 | 45 | 191 |
| claude-sonnet-4-6 | 29 | 207 |
| gemini-3-flash-preview | 17 | 64 |
| claude-haiku-4-5-20251001 | 32 | 193 |
| gemini-3.1-pro-preview | 23 | 93 |
| claude-opus-4-6 | 6 | 117 |
| SmartAgent | 5 | 110 |
| HighVarianceAgent | 1 | 0 |
| ConservativeAgent | 1 | 0 |
| GreedyAgent | 1 | 0 |
| RandomAgent | 1 | 0 |
