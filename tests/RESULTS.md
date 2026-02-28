# Test Results

**Date:** 2026-02-28
**Platform:** Windows 11 Pro, Python 3.x
**Config hash:** 5a9a2b8b

---

## Task 1: Single Match Simulation

**Command:**
```
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 100
```

**Status:** PASS

**Output:**
- Build 1 (bear 3/14/2/1): 78 wins (78.0%)
- Build 2 (buffalo 8/6/4/2): 22 wins (22.0%)
- Draws: 0
- Avg game length: 12.3 ticks
- Winner: Build 1

**Notes:** High-ATK bear build dominates tank buffalo build, consistent with T002 findings where BEAR 8/10/1/1 was the meta build (high ATK is king).

---

## Task 2: Round-Robin (5 Builds)

**Command:**
```
python -m simulator --round-robin --builds "bear 3 14 2 1" "buffalo 8 6 4 2" "boar 8 8 3 1" "tiger 1 3 15 1" "wolf 5 10 3 2" --games 100
```

**Status:** PASS

**Output (pairwise win rates):**

|        | B1 bear | B2 buffalo | B3 boar | B4 tiger | B5 wolf |
|--------|---------|------------|---------|----------|---------|
| B1     | --      | 78.0%      | 77.0%   | 100.0%   | 78.0%   |
| B2     | 22.0%   | --         | 45.0%   | 100.0%   | 49.0%   |
| B3     | 23.0%   | 55.0%      | --      | 100.0%   | 53.0%   |
| B4     | 0.0%    | 0.0%       | 0.0%    | --       | 0.0%    |
| B5     | 22.0%   | 51.0%      | 47.0%   | 100.0%   | --      |

**Rankings by avg win rate:**
1. bear 3/14/2/1 -- 83.2%
2. boar 8/8/3/1 -- 57.8%
3. wolf 5/10/3/2 -- 55.0%
4. buffalo 8/6/4/2 -- 54.0%
5. tiger 1/3/15/1 -- 0.0%

**Notes:**
- Tiger (SPD=15, all dodge) wins 0% of all matchups. Pure dodge builds are unviable despite 30% cap -- low HP and ATK cannot close games.
- Bear (ATK=14) dominates all matchups. High ATK is the strongest single stat.
- Middle-tier builds (boar, wolf, buffalo) are competitive with each other (~45-55%).

---

## Task 3: Challenge Mode Dry-Run

### T001 (Blind Protocol)

**Command:**
```
python run_challenge.py --dry-run --provider openai --model test --protocol t001 --series 3
```

**Status:** PASS

**Output:**

| Baseline          | Series Won | Series Lost | WR   |
|-------------------|------------|-------------|------|
| RandomAgent       | 3          | 0           | 100% |
| GreedyAgent       | 0          | 3           | 0%   |
| SmartAgent        | 0          | 3           | 0%   |
| ConservativeAgent | 0          | 3           | 0%   |
| HighVarianceAgent | 1          | 2           | 33%  |
| **TOTAL**         | **4**      | **11**      | **27%** |

**BT Score:** 0.3080 (rank 5 of 6)

**Notes:** Dry-run agent (random builds) beats only RandomAgent reliably. Loses to all strategic baselines. This is expected -- random builds cannot compete with optimized strategies.

### T002 (Adaptive Protocol)

**Command:**
```
python run_challenge.py --dry-run --provider openai --model test --protocol t002 --series 3
```

**Status:** PASS

**Output:**

| Baseline          | Series Won | Series Lost | WR   |
|-------------------|------------|-------------|------|
| RandomAgent       | 3          | 0           | 100% |
| GreedyAgent       | 2          | 1           | 67%  |
| SmartAgent        | 0          | 3           | 0%   |
| ConservativeAgent | 1          | 2           | 33%  |
| HighVarianceAgent | 1          | 2           | 33%  |
| **TOTAL**         | **7**      | **8**       | **47%** |

**BT Score:** 0.4622 (rank 4 of 6)

**Notes:** T002 adaptive protocol improves dry-run performance from 27% to 47% overall WR. Even random builds benefit from adaptation (seeing opponent's winning build between games). The BT score increases from 0.308 to 0.462. This validates that the adaptive protocol provides meaningful signal even to weak agents.

---

## Task 4: Lab Mode Dry-Run

**Command:**
```
python lab_mode.py --dry-run --provider openai --model test --rounds 3 --builds-per-round 5 --games-per-pair 10
```

**Status:** PASS

**Output:**

| Round | Best Build       | Win Rate |
|-------|------------------|----------|
| 1     | buffalo 2/13/3/2 | 97.5%    |
| 2     | bear 9/7/2/2     | 100.0%   |
| 3     | bear 9/9/1/1     | 100.0%   |

- Improvement: 97.5% -> 100.0% (+2.5pp over 3 rounds)
- Convergence: round 3 (first round with <1pp improvement)
- Best build: bear 9/7/2/2 (max_hp=140, base_dmg=7, dodge=2.5%, resist=6.6%)
- Best build vs SmartAgent's bear 3/14/2/1: 28.0%
- Total simulations: 300
- Total API calls: 0

**Notes:** Lab mode iterative exploration works correctly. Random builds converge quickly (3 rounds). The best discovered build is a tank bear (HP=9), which wins round-robin but loses to the high-ATK bear 3/14/2/1 that SmartAgent uses. This shows that round-robin optimization within a random pool does not guarantee finding globally optimal builds -- an expected limitation of random search.

---

## Summary

| Task | Script         | Status | Key Finding                                  |
|------|----------------|--------|----------------------------------------------|
| 1    | simulator (1v1)       | PASS   | High-ATK bear dominates tank buffalo 78-22   |
| 2    | simulator (round-robin)| PASS  | Pure dodge (tiger) is 0% WR; ATK is king     |
| 3a   | run_challenge (T001)  | PASS   | Random agent scores BT 0.308, beats only Random baseline |
| 3b   | run_challenge (T002)  | PASS   | Adaptive protocol boosts random agent from 27% to 47% WR |
| 4    | lab_mode              | PASS   | Converges in 3 rounds; 300 sims, 0 API calls |

All scripts executed without errors. No bugs found.
