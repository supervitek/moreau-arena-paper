# Season 1 Meta Report

**Data:** `data/tournament_001/results.jsonl`
**Agents:** 13
**Series:** 779
**Total games:** 779

## Leaderboard

| Rank | Agent | BT Score | 95% CI | Elo | Games |
|------|-------|----------|--------|-----|-------|
| 1 | SmartAgent | 1.0000 | [0.6100, 1.0000] | 1746 | 120 |
| 2 | HighVarianceAgent | 0.9541 | [0.5546, 1.0000] | 1706 | 120 |
| 3 | ConservativeAgent | 0.6426 | [0.3718, 0.9170] | 1774 | 120 |
| 4 | gemini-3-flash-preview | 0.5028 | [0.2669, 0.7714] | 1731 | 120 |
| 5 | gemini-3.1-pro-preview | 0.4553 | [0.2465, 0.6782] | 1669 | 119 |
| 6 | grok-4-1-fast-reasoning | 0.4373 | [0.2298, 0.6645] | 1747 | 119 |
| 7 | GreedyAgent | 0.2388 | [0.1277, 0.3456] | 1447 | 120 |
| 8 | gpt-5.2 | 0.2296 | [0.1217, 0.3425] | 1509 | 120 |
| 9 | gpt-5.2-codex | 0.1193 | [0.0665, 0.1675] | 1469 | 120 |
| 10 | claude-sonnet-4-6 | 0.0656 | [0.0336, 0.0973] | 1370 | 120 |
| 11 | claude-haiku-4-5-20251001 | 0.0564 | [0.0301, 0.0805] | 1300 | 120 |
| 12 | claude-opus-4-6 | 0.0173 | [0.0094, 0.0242] | 1037 | 120 |
| 13 | RandomAgent | 0.0054 | [0.0030, 0.0078] | 994 | 120 |

## Pairwise Win Rates

| Agent | ConservativeAgent | GreedyAgent | HighVarianceAgent | RandomAgent | SmartAgent | claude-haiku-4-5-202 | claude-opus-4-6 | claude-sonnet-4-6 | gemini-3-flash-previ | gemini-3.1-pro-previ | gpt-5.2 | gpt-5.2-codex | grok-4-1-fast-reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ConservativeAgent | -- | 100% | 0% | 100% | 0% | 100% | 100% | 100% | 60% | 60% | 90% | 100% | 80% |
| GreedyAgent | 0% | -- | 10% | 100% | 30% | 100% | 100% | 80% | 20% | 40% | 50% | 80% | 30% |
| HighVarianceAgent | 100% | 90% | -- | 100% | 40% | 100% | 100% | 100% | 50% | 70% | 70% | 100% | 60% |
| RandomAgent | 0% | 0% | 0% | -- | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| SmartAgent | 100% | 70% | 60% | 100% | -- | 100% | 100% | 100% | 70% | 60% | 70% | 100% | 60% |
| claude-haiku-4-5-202 | 0% | 0% | 0% | 100% | 0% | -- | 80% | 70% | 20% | 0% | 0% | 40% | 0% |
| claude-opus-4-6 | 0% | 0% | 0% | 100% | 0% | 20% | -- | 0% | 0% | 0% | 0% | 0% | 0% |
| claude-sonnet-4-6 | 0% | 20% | 0% | 100% | 0% | 30% | 100% | -- | 10% | 0% | 30% | 0% | 50% |
| gemini-3-flash-previ | 40% | 80% | 50% | 100% | 30% | 80% | 100% | 90% | -- | 50% | 80% | 80% | 50% |
| gemini-3.1-pro-previ | 40% | 60% | 30% | 100% | 40% | 100% | 100% | 100% | 50% | -- | 70% | 90% | 22% |
| gpt-5.2 | 10% | 50% | 30% | 100% | 30% | 100% | 100% | 70% | 20% | 30% | -- | 70% | 20% |
| gpt-5.2-codex | 0% | 20% | 0% | 100% | 0% | 60% | 100% | 100% | 20% | 10% | 30% | -- | 30% |
| grok-4-1-fast-reason | 20% | 70% | 40% | 100% | 40% | 100% | 100% | 50% | 50% | 78% | 80% | 70% | -- |

## Non-Transitive Cycles (A > B > C > A)

No 3-cycles detected. The ranking is fully transitive.

## Signature Builds

| Agent | Top Build | HP | ATK | SPD | WIL | Usage |
|-------|-----------|----|----|-----|-----|-------|
| ConservativeAgent | buffalo | 8 | 6 | 4 | 2 | 545/545 (100%) |
| GreedyAgent | boar | 8 | 8 | 3 | 1 | 591/591 (100%) |
| HighVarianceAgent | bear | 3 | 14 | 2 | 1 | 588/588 (100%) |
| RandomAgent | raven | 3 | 3 | 2 | 12 | 480/480 (100%) |
| SmartAgent | bear | 3 | 14 | 2 | 1 | 611/611 (100%) |
| claude-haiku-4-5-20251001 | tiger | 4 | 7 | 6 | 3 | 297/590 (50%) |
| claude-opus-4-6 | wolf | 3 | 8 | 1 | 8 | 445/516 (86%) |
| claude-sonnet-4-6 | wolf | 4 | 8 | 5 | 3 | 436/596 (73%) |
| gemini-3-flash-preview | bear | 8 | 10 | 1 | 1 | 64/526 (12%) |
| gemini-3.1-pro-preview | tiger | 6 | 8 | 5 | 1 | 90/564 (16%) |
| gpt-5.2 | tiger | 6 | 8 | 5 | 1 | 208/562 (37%) |
| gpt-5.2-codex | tiger | 6 | 7 | 5 | 2 | 164/569 (29%) |
| grok-4-1-fast-reasoning | bear | 8 | 8 | 3 | 1 | 107/566 (19%) |

## Balance Assessment

**3 agent(s) exceed 70% overall win rate (potentially overpowered):**

| Agent | Overall Win Rate |
|-------|-----------------|
| SmartAgent | 82.5% |
| HighVarianceAgent | 81.7% |
| ConservativeAgent | 74.2% |
