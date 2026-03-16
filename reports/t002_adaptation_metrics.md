# T002 Adaptation Metrics

Computed from `data/tournament_002/results.jsonl` by comparing the loser's build between consecutive games.

## Aggregate LLM Summary
- Losses with a next game: `1630`
- Adaptations: `1095`
- Adapt rate: `67.18%`
- Adapt win rate: `50.87%`
- Stick win rate: `33.83%`

## Per-Agent Table

| Agent | Blds | Lost | Adpt | Rate | Adpt WR | Stick WR |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.2-codex | 63 | 156 | 143 | 91.67% | 58.74% | 46.15% |
| gemini-3-flash-preview | 17 | 153 | 60 | 39.22% | 73.33% | 36.56% |
| grok-4-1-fast-reasoning | 32 | 176 | 131 | 74.43% | 63.36% | 42.22% |
| claude-opus-4-6 | 6 | 220 | 116 | 52.73% | 54.31% | 30.77% |
| claude-sonnet-4-6 | 29 | 271 | 181 | 66.79% | 57.46% | 53.33% |
| gpt-5.2 | 45 | 212 | 189 | 89.15% | 43.39% | 34.78% |
| claude-haiku-4-5-20251001 | 32 | 233 | 192 | 82.40% | 35.94% | 46.34% |
| gemini-3.1-pro-preview | 23 | 209 | 83 | 39.71% | 33.73% | 11.90% |

## Note
This derivation is fully reproducible from committed JSONL. If these values disagree with the paper or older derived artifacts, the direct JSONL-derived output should be treated as canonical.
