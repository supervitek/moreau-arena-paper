# Season 2 Meta Report

**Data:** `data/tournament_002/results.jsonl`
**Agents:** 13
**Series:** 780
**Total games:** 780

## Leaderboard

| Rank | Agent | BT Score | 95% CI | Elo | Games |
|------|-------|----------|--------|-----|-------|
| 1 | gpt-5.2-codex | 1.0000 | [0.7925, 1.0000] | 1934 | 120 |
| 2 | gemini-3-flash-preview | 0.6793 | [0.3930, 1.0000] | 1731 | 120 |
| 3 | grok-4-1-fast-reasoning | 0.6496 | [0.3656, 1.0000] | 1858 | 120 |
| 4 | claude-opus-4-6 | 0.2520 | [0.1429, 0.3934] | 1530 | 120 |
| 5 | claude-sonnet-4-6 | 0.2520 | [0.1297, 0.4266] | 1746 | 120 |
| 6 | gpt-5.2 | 0.2520 | [0.1398, 0.4217] | 1663 | 120 |
| 7 | claude-haiku-4-5-20251001 | 0.2258 | [0.1269, 0.3592] | 1562 | 120 |
| 8 | gemini-3.1-pro-preview | 0.1882 | [0.1043, 0.3108] | 1496 | 120 |
| 9 | SmartAgent | 0.0926 | [0.0490, 0.1465] | 1272 | 120 |
| 10 | HighVarianceAgent | 0.0698 | [0.0379, 0.1081] | 1288 | 120 |
| 11 | ConservativeAgent | 0.0614 | [0.0308, 0.1029] | 1234 | 120 |
| 12 | GreedyAgent | 0.0426 | [0.0209, 0.0761] | 1191 | 120 |
| 13 | RandomAgent | 0.0066 | [0.0038, 0.0101] | 994 | 120 |

## Pairwise Win Rates

| Agent | ConservativeAgent | GreedyAgent | HighVarianceAgent | RandomAgent | SmartAgent | claude-haiku-4-5-202 | claude-opus-4-6 | claude-sonnet-4-6 | gemini-3-flash-previ | gemini-3.1-pro-previ | gpt-5.2 | gpt-5.2-codex | grok-4-1-fast-reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ConservativeAgent | -- | 100% | 0% | 100% | 70% | 0% | 0% | 40% | 0% | 0% | 0% | 30% | 0% |
| GreedyAgent | 0% | -- | 10% | 100% | 30% | 0% | 0% | 60% | 0% | 0% | 50% | 10% | 0% |
| HighVarianceAgent | 100% | 90% | -- | 100% | 20% | 30% | 0% | 10% | 0% | 10% | 10% | 0% | 0% |
| RandomAgent | 0% | 0% | 0% | -- | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| SmartAgent | 30% | 70% | 80% | 100% | -- | 40% | 0% | 90% | 0% | 30% | 0% | 0% | 0% |
| claude-haiku-4-5-202 | 100% | 100% | 70% | 100% | 60% | -- | 30% | 40% | 0% | 90% | 70% | 10% | 10% |
| claude-opus-4-6 | 100% | 100% | 100% | 100% | 100% | 70% | -- | 0% | 0% | 50% | 50% | 10% | 30% |
| claude-sonnet-4-6 | 60% | 40% | 90% | 100% | 10% | 60% | 100% | -- | 60% | 70% | 50% | 20% | 50% |
| gemini-3-flash-previ | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 40% | -- | 100% | 80% | 30% | 10% |
| gemini-3.1-pro-previ | 100% | 100% | 90% | 100% | 70% | 10% | 50% | 30% | 0% | -- | 50% | 10% | 20% |
| gpt-5.2 | 100% | 50% | 90% | 100% | 100% | 30% | 50% | 50% | 20% | 50% | -- | 20% | 50% |
| gpt-5.2-codex | 70% | 90% | 100% | 100% | 100% | 90% | 90% | 80% | 70% | 90% | 80% | -- | 80% |
| grok-4-1-fast-reason | 100% | 100% | 100% | 100% | 100% | 90% | 70% | 50% | 90% | 80% | 50% | 20% | -- |

## Non-Transitive Cycles (A > B > C > A)

**12 cycle(s) detected:**

1. ConservativeAgent > GreedyAgent > claude-sonnet-4-6 > ConservativeAgent
2. ConservativeAgent > SmartAgent > HighVarianceAgent > ConservativeAgent
3. ConservativeAgent > SmartAgent > claude-sonnet-4-6 > ConservativeAgent
4. GreedyAgent > claude-sonnet-4-6 > HighVarianceAgent > GreedyAgent
5. GreedyAgent > claude-sonnet-4-6 > claude-haiku-4-5-20251001 > GreedyAgent
6. GreedyAgent > claude-sonnet-4-6 > claude-opus-4-6 > GreedyAgent
7. GreedyAgent > claude-sonnet-4-6 > gemini-3-flash-preview > GreedyAgent
8. GreedyAgent > claude-sonnet-4-6 > gemini-3.1-pro-preview > GreedyAgent
9. SmartAgent > claude-sonnet-4-6 > claude-haiku-4-5-20251001 > SmartAgent
10. SmartAgent > claude-sonnet-4-6 > claude-opus-4-6 > SmartAgent
11. SmartAgent > claude-sonnet-4-6 > gemini-3-flash-preview > SmartAgent
12. SmartAgent > claude-sonnet-4-6 > gemini-3.1-pro-preview > SmartAgent

**Agents involved in cycles:** ConservativeAgent, GreedyAgent, HighVarianceAgent, SmartAgent, claude-haiku-4-5-20251001, claude-opus-4-6, claude-sonnet-4-6, gemini-3-flash-preview, gemini-3.1-pro-preview

## Signature Builds

| Agent | Top Build | HP | ATK | SPD | WIL | Usage |
|-------|-----------|----|----|-----|-----|-------|
| ConservativeAgent | buffalo | 8 | 6 | 4 | 2 | 605/605 (100%) |
| GreedyAgent | boar | 8 | 8 | 3 | 1 | 637/637 (100%) |
| HighVarianceAgent | bear | 3 | 14 | 2 | 1 | 598/598 (100%) |
| RandomAgent | raven | 3 | 3 | 2 | 12 | 480/480 (100%) |
| SmartAgent | bear | 3 | 14 | 2 | 1 | 276/611 (45%) |
| claude-haiku-4-5-20251001 | bear | 8 | 10 | 1 | 1 | 198/633 (31%) |
| claude-opus-4-6 | bear | 8 | 8 | 3 | 1 | 257/640 (40%) |
| claude-sonnet-4-6 | buffalo | 10 | 8 | 1 | 1 | 249/696 (36%) |
| gemini-3-flash-preview | bear | 8 | 10 | 1 | 1 | 447/615 (73%) |
| gemini-3.1-pro-preview | boar | 8 | 8 | 3 | 1 | 228/607 (38%) |
| gpt-5.2 | buffalo | 10 | 8 | 1 | 1 | 96/625 (15%) |
| gpt-5.2-codex | buffalo | 9 | 9 | 1 | 1 | 113/637 (18%) |
| grok-4-1-fast-reasoning | bear | 8 | 8 | 3 | 1 | 234/646 (36%) |

## Balance Assessment

**3 agent(s) exceed 70% overall win rate (potentially overpowered):**

| Agent | Overall Win Rate |
|-------|-----------------|
| gpt-5.2-codex | 86.7% |
| gemini-3-flash-preview | 80.0% |
| grok-4-1-fast-reasoning | 79.2% |

## Adaptation Metrics

| Agent | Unique Builds | Adapted Games | Recovery Rate |
|-------|--------------|---------------|---------------|
| gpt-5.2-codex | 63 | 517 | 58% (90/156) |
| gpt-5.2 | 45 | 505 | 42% (90/212) |
| claude-haiku-4-5-20251001 | 32 | 513 | 38% (88/233) |
| grok-4-1-fast-reasoning | 32 | 526 | 58% (102/176) |
| claude-sonnet-4-6 | 29 | 576 | 56% (152/271) |
| gemini-3.1-pro-preview | 23 | 487 | 21% (43/209) |
| gemini-3-flash-preview | 17 | 495 | 51% (78/153) |
| claude-opus-4-6 | 6 | 520 | 43% (95/220) |
| SmartAgent | 5 | 491 | 30% (82/276) |
| ConservativeAgent | 1 | 485 | 21% (61/287) |
| GreedyAgent | 1 | 517 | 20% (61/306) |
| HighVarianceAgent | 1 | 478 | 24% (71/294) |
| RandomAgent | 1 | 360 | 0% (0/360) |

## Season Comparison (S1 vs S2)

| Agent | S1 BT | S2 BT | Delta |
|-------|----------|----------|-------|
| ConservativeAgent | 0.6426 | 0.0614 | -0.5811 |
| GreedyAgent | 0.2388 | 0.0426 | -0.1962 |
| HighVarianceAgent | 0.9541 | 0.0698 | -0.8844 |
| RandomAgent | 0.0054 | 0.0066 | +0.0011 |
| SmartAgent | 1.0000 | 0.0926 | -0.9074 |
| claude-haiku-4-5-20251001 | 0.0564 | 0.2258 | +0.1695 |
| claude-opus-4-6 | 0.0173 | 0.2520 | +0.2348 |
| claude-sonnet-4-6 | 0.0656 | 0.2520 | +0.1864 |
| gemini-3-flash-preview | 0.5028 | 0.6793 | +0.1765 |
| gemini-3.1-pro-preview | 0.4553 | 0.1882 | -0.2671 |
| gpt-5.2 | 0.2296 | 0.2520 | +0.0224 |
| gpt-5.2-codex | 0.1193 | 1.0000 | +0.8807 |
| grok-4-1-fast-reasoning | 0.4373 | 0.6496 | +0.2123 |
