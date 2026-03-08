# Moreau Arena Season 1 -- Balance Report

Generated: 2026-03-07 22:28:10 UTC
Games per pair: 2000

## Rankings by Win Rate

| Rank | Animal | WR | Best Matchup | Worst Matchup |
|------|--------|----|-------------|---------------|
| 1 | fox | 57.06% | buffalo (62.50%) | eagle (52.20%) |
| 2 | tiger | 55.73% | vulture (62.95%) | fox (44.90%) |
| 3 | porcupine | 52.74% | monkey (62.18%) | tiger (46.10%) |
| 4 | rhino | 52.51% | vulture (61.35%) | fox (44.82%) |
| 5 | eagle | 52.44% | vulture (62.00%) | tiger (42.45%) |
| 6 | wolf | 52.11% | vulture (60.25%) | fox (39.85%) |
| 7 | scorpion | 51.15% | vulture (56.40%) | tiger (42.65%) |
| 8 | buffalo | 48.45% | boar (59.65%) | fox (37.50%) |
| 9 | monkey | 48.28% | buffalo (58.13%) | porcupine (37.82%) |
| 10 | bear | 47.52% | panther (54.15%) | rhino (39.30%) |
| 11 | viper | 47.09% | vulture (53.65%) | fox (41.30%) |
| 12 | panther | 46.23% | vulture (53.90%) | fox (40.60%) |
| 13 | boar | 44.79% | monkey (50.85%) | tiger (39.65%) |
| 14 | vulture | 43.91% | monkey (54.80%) | tiger (37.05%) |

## Pairwise Matrix (condensed)

| | bear | buff | boar | tige | wolf | monk | porc | scor | vult | rhin | vipe | fox | eagl | pant |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bear | -- | 49% | 53% | 41% | 46% | 47% | 47% | 50% | 54% | 39% | 50% | 42% | 44% | 54% |
| buff | 51% | -- | 60% | 49% | 44% | 42% | 46% | 49% | 54% | 46% | 49% | 38% | 45% | 58% |
| boar | 47% | 40% | -- | 40% | 42% | 51% | 43% | 44% | 51% | 43% | 48% | 41% | 46% | 48% |
| tige | 59% | 51% | 60% | -- | 54% | 55% | 54% | 57% | 63% | 54% | 57% | 45% | 58% | 58% |
| wolf | 54% | 56% | 58% | 46% | -- | 47% | 52% | 51% | 60% | 50% | 55% | 40% | 51% | 56% |
| monk | 53% | 58% | 49% | 45% | 53% | -- | 38% | 46% | 45% | 52% | 54% | 40% | 47% | 46% |
| porc | 53% | 54% | 57% | 46% | 48% | 62% | -- | 50% | 59% | 49% | 54% | 47% | 49% | 57% |
| scor | 50% | 51% | 56% | 43% | 49% | 54% | 50% | -- | 56% | 51% | 53% | 48% | 49% | 55% |
| vult | 46% | 46% | 49% | 37% | 40% | 55% | 41% | 44% | -- | 39% | 46% | 44% | 38% | 46% |
| rhin | 61% | 54% | 57% | 46% | 50% | 48% | 51% | 49% | 61% | -- | 56% | 45% | 50% | 57% |
| vipe | 50% | 51% | 52% | 43% | 45% | 46% | 46% | 47% | 54% | 44% | -- | 41% | 45% | 50% |
| fox | 57% | 62% | 59% | 55% | 60% | 60% | 53% | 52% | 56% | 55% | 59% | -- | 52% | 59% |
| eagl | 56% | 55% | 54% | 42% | 49% | 53% | 51% | 51% | 62% | 50% | 55% | 48% | -- | 55% |
| pant | 46% | 42% | 52% | 42% | 44% | 54% | 43% | 45% | 54% | 43% | 50% | 41% | 45% | -- |

## Gate Results

- **G1_max_wr**: PASS -- Max WR: fox at 0.5706 (limit 0.58)
- **G2_min_wr**: PASS -- Min WR: vulture at 0.4391 (limit 0.42)
- **G3_nontransitive**: PASS -- Found 5 cycle(s)
- **G4_rng_variance**: PASS -- All matchups within tolerance
- **G5_distinct_identities**: PASS -- All animals distinct

## Non-Transitive Cycles Found

- bear > vulture > monkey > bear
- bear > panther > monkey > bear
- buffalo > vulture > monkey > buffalo
- buffalo > panther > monkey > buffalo
- wolf > panther > monkey > wolf
