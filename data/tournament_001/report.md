# Full Multi-Model Tournament Report

**Date:** 2026-02-26 09:03 UTC
**Config hash:** `b7ec588583135ad6...`
**Agents:** 13
**Series completed:** 779
**Series with errors:** 1
**Best-of:** 7
**Series per pair:** 10

## Bradley-Terry Rankings (95% CI)

| Rank | Agent | BT Score | CI Lower | CI Upper | Games |
|------|-------|----------|----------|----------|-------|
| 1 | SmartAgent | 1.0000 | 0.6100 | 1.0000 | 120 |
| 2 | HighVarianceAgent | 0.9541 | 0.5546 | 1.0000 | 120 |
| 3 | ConservativeAgent | 0.6426 | 0.3718 | 0.9170 | 120 |
| 4 | gemini-3-flash-preview | 0.5028 | 0.2669 | 0.7714 | 120 |
| 5 | gemini-3.1-pro-preview | 0.4553 | 0.2465 | 0.6782 | 119 |
| 6 | grok-4-1-fast-reasoning | 0.4373 | 0.2298 | 0.6645 | 119 |
| 7 | GreedyAgent | 0.2388 | 0.1277 | 0.3456 | 120 |
| 8 | gpt-5.2 | 0.2296 | 0.1217 | 0.3425 | 120 |
| 9 | gpt-5.2-codex | 0.1193 | 0.0665 | 0.1675 | 120 |
| 10 | claude-sonnet-4-6 | 0.0656 | 0.0336 | 0.0973 | 120 |
| 11 | claude-haiku-4-5-20251001 | 0.0564 | 0.0301 | 0.0805 | 120 |
| 12 | claude-opus-4-6 | 0.0173 | 0.0094 | 0.0242 | 120 |
| 13 | RandomAgent | 0.0054 | 0.0030 | 0.0078 | 120 |

## Elo Rankings

| Rank | Agent | Elo |
|------|-------|-----|
| 1 | grok-4-1-fast-reasoning | 1865 |
| 2 | ConservativeAgent | 1780 |
| 3 | gemini-3-flash-preview | 1718 |
| 4 | gemini-3.1-pro-preview | 1682 |
| 5 | SmartAgent | 1672 |
| 6 | HighVarianceAgent | 1632 |
| 7 | claude-sonnet-4-6 | 1528 |
| 8 | gpt-5.2-codex | 1477 |
| 9 | gpt-5.2 | 1439 |
| 10 | claude-haiku-4-5-20251001 | 1396 |
| 11 | GreedyAgent | 1362 |
| 12 | claude-opus-4-6 | 1194 |
| 13 | RandomAgent | 757 |

## Pairwise Win Rates (row vs column)

| Agent | grok-4-1-fas | Conservative | gemini-3-fla | gemini-3.1-p | SmartAgent | HighVariance | claude-sonne | gpt-5.2-code | gpt-5.2 | claude-haiku | GreedyAgent | claude-opus- | RandomAgent |
|-------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| grok-4-1-fast-reasoning | --- | 20% | 50% | 78% | 40% | 40% | 50% | 70% | 80% | 100% | 70% | 100% | 100% |
| ConservativeAgent | 80% | --- | 60% | 60% | 0% | 0% | 100% | 100% | 90% | 100% | 100% | 100% | 100% |
| gemini-3-flash-preview | 50% | 40% | --- | 50% | 30% | 50% | 90% | 80% | 80% | 80% | 80% | 100% | 100% |
| gemini-3.1-pro-preview | 22% | 40% | 50% | --- | 40% | 30% | 100% | 90% | 70% | 100% | 60% | 100% | 100% |
| SmartAgent | 60% | 100% | 70% | 60% | --- | 60% | 100% | 100% | 70% | 100% | 70% | 100% | 100% |
| HighVarianceAgent | 60% | 100% | 50% | 70% | 40% | --- | 100% | 100% | 70% | 100% | 90% | 100% | 100% |
| claude-sonnet-4-6 | 50% | 0% | 10% | 0% | 0% | 0% | --- | 0% | 30% | 30% | 20% | 100% | 100% |
| gpt-5.2-codex | 30% | 0% | 20% | 10% | 0% | 0% | 100% | --- | 30% | 60% | 20% | 100% | 100% |
| gpt-5.2 | 20% | 10% | 20% | 30% | 30% | 30% | 70% | 70% | --- | 100% | 50% | 100% | 100% |
| claude-haiku-4-5-20251001 | 0% | 0% | 20% | 0% | 0% | 0% | 70% | 40% | 0% | --- | 0% | 80% | 100% |
| GreedyAgent | 30% | 0% | 20% | 40% | 30% | 10% | 80% | 80% | 50% | 100% | --- | 100% | 100% |
| claude-opus-4-6 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 20% | 0% | --- | 100% |
| RandomAgent | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | --- |

## Error Summary

- **gemini-3.1-pro-preview:** 1 errors
- **grok-4-1-fast-reasoning:** 1 errors
