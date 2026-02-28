# Moreau Arena — Weekend Development Sprint

## PROJECT CONTEXT (read once, reference throughout)

Repository: moreau-arena-paper (PUBLIC)
Location: ~/Documents/Claude/a/moreau-arena-paper
Remote: https://github.com/supervitek/moreau-arena-paper

Structure:
```
moreau-arena-paper/
├── simulator/     # Game engine (engine.py, types.py, abilities.py, grid.py, seed.py, config.json)
├── agents/        # Baselines + LLM agents
├── prompts/       # Verbatim T001/T002 prompts + meta_extractor.py
├── data/          # Tournament results (JSONL + reports)
├── analysis/      # BT ranking, pairwise matrix scripts
├── paper/         # moreau_arena.tex (final arXiv version)
└── README.md, LICENSE (MIT), .gitignore
```

The paper describes two tournaments (T001, T002) with 13 agents (8 LLMs + 5 baselines).
Simulator: 8x8 grid, 60 ticks, animals with stats HP/ATK/SPD/WIL summing to 20.
Config is frozen in config.json with a hash for reproducibility.

## RULES FOR ALL TASKS

1. Work in order: Task 1 → 2 → 3 → 4 → 5
2. After completing each task: `git add -A && git commit -m "Task N: <description>" && git push`
3. After each task: append status to PROGRESS.md (create if not exists)
4. If a task fails or is blocked: document why in PROGRESS.md, skip to next task
5. Do NOT modify paper/moreau_arena.tex (except Task 1)
6. Do NOT delete existing files
7. All new code must have docstrings and be runnable with `python -m <module>`
8. Use only stdlib + packages already in analysis/requirements.txt (add new deps there if needed)

---

## TASK 1: Fix paper LaTeX (30 min)

### 1a: Fix pgfplots error bars in Figures 1 and 2

The two horizontal bar charts (BT scores) use `error bars/.cd, x dir=both, x explicit` 
which does not render whiskers in pgfplots 1.18.1.

Fix approach — replace the error bar syntax. For each `\addplot` in Figures 1 and 2,
use explicit `\draw` lines for CI whiskers after the axis, OR fix the pgfplots options 
to use the correct syntax for your version. 

Test: compile `pdflatex paper/moreau_arena.tex` twice. Open PDF, visually confirm 
that BOTH Figure 1 and Figure 2 show horizontal whisker lines (confidence intervals) 
on every bar. If whiskers are not visible, the fix failed — try alternative syntax.

### 1b: Add GitHub URL to Conclusion

In Section 11 (Conclusion), find the sentence:
"We release the complete prompts, configuration hash, match records, and analysis code to support reproducibility and follow-up studies."

Replace with:
"We release the complete prompts, configuration hash, match records, and analysis code at \url{https://github.com/supervitek/moreau-arena-paper} to support reproducibility and follow-up studies."

### 1c: Add challenge platform sentence to Future Work

In Section 9 (Future Work), add as the LAST paragraph before Section 10:

"We also plan to release a public challenge platform where users can submit custom agent configurations and compete on a live leaderboard, providing crowd-sourced data for future analysis of prompt sensitivity and strategic adaptation."

### Verify: compile twice, 0 errors, error bars visible, URL clickable in PDF.
### Commit: "Task 1: Fix error bars, add GitHub URL and challenge platform to paper"

---

## TASK 2: Standalone Simulator CLI (1-2 hours)

Create `simulator/__main__.py` so the simulator can be run directly from command line.

### 2a: Single match mode

```bash
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 100
```

Output:
```
Moreau Arena — Standalone Simulator
Config: config.json (hash: <first 8 chars>)

Build 1: bear 3/14/2/1 (max_hp=80, base_dmg=13, dodge=5.0%, resist=3.3%)
Build 2: buffalo 8/6/4/2 (max_hp=130, base_dmg=7, dodge=10.0%, resist=6.6%)

Simulating 100 games...

Results:
  Build 1 wins: 73 (73.0%)
  Build 2 wins: 27 (27.0%)
  Draws: 0
  Avg game length: 38.2 ticks

Build 1 (bear 3/14/2/1) wins.
```

### 2b: Round-robin mode

```bash
python -m simulator --round-robin \
  --builds "bear 3 14 2 1" "buffalo 8 6 4 2" "wolf 5 10 3 2" "tiger 6 8 5 1" \
  --games 100
```

Output: pairwise win-rate matrix, plus which build has highest average win rate.

### 2c: Series mode (best-of-7)

```bash
python -m simulator --series --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --series-count 10
```

Output: series results (e.g., "Build 1 wins 8/10 series") matching tournament format.

### Implementation notes:
- Import from existing simulator modules (engine.py, types.py, etc.)
- Use argparse for CLI
- Use config.json for game parameters (load automatically)
- Print computed stats (hp, dmg, dodge, resist) so user can verify formulas
- Support `--seed <int>` for reproducibility
- Support `--verbose` flag that prints tick-by-tick combat log for one game
- Handle invalid inputs gracefully (stats not summing to 20, unknown animals, etc.)

### Test: run all three modes, verify output makes sense.
### Commit: "Task 2: Standalone simulator CLI with single/round-robin/series modes"

---

## TASK 3: Challenge Script (2-3 hours)

Create `run_challenge.py` in repository root.

This script lets anyone test their LLM against our 5 baselines using the same 
tournament protocol from the paper.

### Arguments:
```
--provider    (openai|anthropic|google|xai)  required
--model       (model string)                  required
--protocol    (t001|t002)                     default: t002
--series      (int, per baseline)             default: 10
--api-key     (string, or read from env)      optional
--dry-run     (flag: use random instead of API) optional
--output-dir  (path)                          default: results/
```

### Environment variables (fallback for --api-key):
- OPENAI_API_KEY
- ANTHROPIC_API_KEY  
- GOOGLE_API_KEY (or GEMINI_API_KEY)
- XAI_API_KEY

### Flow:

1. Parse arguments, validate provider/model
2. Load config.json, load appropriate prompt (t001 or t002)
3. Print estimated cost and number of API calls:
   ```
   Challenge Configuration:
     Model: claude-sonnet-4-5 (anthropic)
     Protocol: T002
     Baselines: SmartAgent, HighVarianceAgent, ConservativeAgent, GreedyAgent, RandomAgent
     Series per baseline: 10
     Estimated API calls: ~250
     Estimated cost: $2-5

   Proceed? [Y/n]
   ```
4. For each baseline × N series: run best-of-7 series using the protocol
   - T001: one-shot, send prompt once, get build, play series with that build
   - T002: per-game adaptation, after each loss send opponent build info, get new build
5. Progress bar or periodic status updates
6. After completion, print results:
   ```
   === CHALLENGE RESULTS ===
   
   Your model: claude-sonnet-4-5 (anthropic)
   Protocol: T002
   
   Pairwise Results (series W-L):
     vs SmartAgent:     8-2
     vs HighVariance:   7-3
     vs Conservative:   9-1
     vs Greedy:         10-0
     vs Random:         10-0
   
   Total: 44-6 (88.0%)
   
   Bradley-Terry score: 0.312
   
   Comparison with paper results (T002):
     Your model would rank between #5 (Cl. Sonnet, BT=0.252) 
     and #4 (Cl. Opus, BT=0.252)
     
     Above: GPT-5.2-Codex (1.000), Gemini Flash (0.679), 
            Grok (0.650)
     Similar: Cl. Opus (0.252), Cl. Sonnet (0.252), GPT-5.2 (0.252)
     Below: Cl. Haiku (0.226), Gemini Pro (0.188)
   ```
7. Save full results to `results/challenge_<model>_<timestamp>.jsonl`

### For the LLM agent integration:
- Look at existing agents/llm_agent.py and agents/llm_agent_v2.py for how API calls are made
- Reuse the same prompt loading from prompts/
- Support the same JSON schema enforcement as T002
- For --dry-run: replace API calls with random build generation (for testing)

### For baselines:
- Import from agents/baselines.py
- Each baseline should work as-is from the existing code

### For BT score computation:
- Reuse analysis/bt_ranking.py or implement simplified version
- Compare against hardcoded paper BT scores for ranking placement

### Test: run with --dry-run flag, verify full flow works end to end.
### Commit: "Task 3: Challenge script for testing any LLM against paper baselines"

---

## TASK 4: Laboratory Mode Prototype (2-3 hours)

Create `lab_mode.py` in repository root.

This is the "iteration efficiency curve" experiment: give an LLM access to 
unlimited local simulation, measure how it improves over rounds.

### Arguments:
```
--provider         (openai|anthropic|google|xai)  required
--model            (model string)                  required
--builds-per-round (int)                           default: 20
--games-per-pair   (int)                           default: 50
--rounds           (int)                           default: 10
--api-key          (string or env)                 optional
--dry-run          (flag)                          optional
--output-dir       (path)                          default: results/
```

### Flow per round:

Round 1:
1. Send LLM a prompt:
   ```
   You are participating in Moreau Arena, a combat game.
   [include full game rules and stat formulas from T002 prompt]
   
   Your task: propose {builds_per_round} different builds to test.
   Each build is an animal + stat allocation (HP+ATK+SPD+WIL=20, each >= 1).
   
   Respond with a JSON array:
   [{"animal":"BEAR","hp":3,"atk":14,"spd":2,"wil":1}, ...]
   
   Try to explore diverse strategies. You want to find the strongest possible build.
   ```
2. Parse response → list of builds
3. Run local round-robin: all builds vs all builds, games_per_pair games each
   (builds_per_round × builds_per_round × games_per_pair simulations)
4. Compute win rates for each build

Round 2+:
1. Send LLM results from previous round:
   ```
   Results from round {N-1}:
   
   Build Rankings (by avg win rate vs field):
   1. bear 3/14/2/1 — 87.3% win rate
   2. bear 8/10/1/1 — 82.1% win rate  
   ...
   20. monkey 5/5/5/5 — 23.4% win rate
   
   Pairwise matrix:
   [abbreviated matrix showing key matchups]
   
   Now propose {builds_per_round} new builds for the next round.
   You may keep good builds from before and replace weak ones.
   Respond with JSON array.
   ```
2. Parse → simulate → rank → repeat

### After all rounds, output:

```
=== LABORATORY MODE RESULTS ===

Model: claude-sonnet-4-5
Rounds: 10 | Builds/round: 20 | Games/pair: 50
Total simulations: 200,000
Total API calls: 10
Estimated cost: $0.30

Iteration Curve:
  Round  1: best = bear 5/11/3/1  (81.2%)
  Round  3: best = bear 3/14/2/1  (89.7%)
  Round  5: best = bear 3/14/2/1  (89.7%)  [converged]
  Round 10: best = bear 2/15/2/1  (91.3%)

Improvement: 81.2% → 91.3% (+10.1pp over 10 rounds)
Convergence: round 3 (first round with <1pp improvement)

Best build found: bear 2/15/2/1
  max_hp=70, base_dmg=14, dodge=5.0%, resist=3.3%
  Win rate vs SmartAgent's bear 3/14/2/1: 54.2%
```

### Save iteration curve data to results/lab_<model>_<timestamp>.json:
```json
{
  "model": "claude-sonnet-4-5",
  "provider": "anthropic",
  "rounds": 10,
  "builds_per_round": 20,
  "games_per_pair": 50,
  "curve": [
    {"round": 1, "best_build": "bear 5/11/3/1", "best_wr": 0.812, "all_builds": [...]},
    {"round": 2, "best_build": "bear 3/14/2/1", "best_wr": 0.897, "all_builds": [...]},
    ...
  ],
  "total_simulations": 200000,
  "total_api_calls": 10
}
```

### Test: run with --dry-run --rounds 3, verify full flow.
### Commit: "Task 4: Laboratory mode prototype with iteration curves"

---

## TASK 5: Documentation and README update (1 hour)

### 5a: Update README.md

Replace current README with expanded version that includes:

```markdown
# Moreau Arena

Companion repository for:

**Moreau Arena: How Adaptation and Exact Formulas Transform LLM Strategic Reasoning 
from Systematic Failure to Baseline-Beating Performance**

Victor Stasiuc (2026) — Independent Researcher  
arXiv: [link TBD]

## Key Result

Same 13 agents, same game, different scaffolding → leaderboard flips 180°.
LLMs go from losing to bots (37.5% win rate) to crushing them (89.75%).

## What you can do

### Verify our results
```bash
pip install -r analysis/requirements.txt
python -m analysis.bt_ranking     # reproduce BT scores
python -m analysis.pairwise       # reproduce pairwise matrices
```

### Explore the simulator (no API key needed)
```bash
python -m simulator --build1 "bear 3 14 2 1" --build2 "buffalo 8 6 4 2" --games 1000
python -m simulator --round-robin --builds "bear 3 14 2 1" "wolf 5 10 3 2" "tiger 6 8 5 1" --games 100
```

### Challenge: test YOUR model against our baselines
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python run_challenge.py --provider anthropic --model claude-sonnet-4-5 --protocol t002
```

### Laboratory Mode: give your model unlimited simulation
```bash
python lab_mode.py --provider openai --model gpt-4o --rounds 10
```

## Game Rules (quick summary)

Choose 1 of 6 animals: bear, buffalo, boar, tiger, wolf, monkey.
Allocate 20 stat points: HP + ATK + SPD + WIL (each ≥ 1).
Combat: 8×8 grid, 60 ticks, closing ring at tick 30.
Key insight: ATK stacking dominates (but can you find something better?).

## Animals
[brief table: animal, passive, abilities]

## Citation
```bibtex
@article{stasiuc2026moreau,
  title={Moreau Arena: How Adaptation and Exact Formulas Transform LLM Strategic Reasoning},
  author={Stasiuc, Victor},
  journal={arXiv preprint},
  year={2026}
}
```

## License
MIT
```

### 5b: Create MECHANICS.md in docs/

Full game rules explained simply:
- Stat formulas with examples
- Animal passives and abilities with proc rates  
- Ring mechanics
- Series format (best-of-7)
- Why ATK stacking works (the math)

### 5c: Create CONTRIBUTING.md in docs/

How to add your own model:
- Implement the agent interface
- Required methods (get_build, adapt_build for T002)
- Example: minimal custom agent
- How to run challenge with your agent
- How to submit results (open GitHub issue with JSONL)

### Test: verify all markdown renders on GitHub.
### Commit: "Task 5: Documentation — README, MECHANICS, CONTRIBUTING"

---

## COMPLETION CHECKLIST

When all tasks are done, write final PROGRESS.md entry:

```
## Final Status

- [ ] Task 1: Paper fixes (error bars, URL, challenge sentence)
- [ ] Task 2: Standalone simulator (single/round-robin/series)
- [ ] Task 3: Challenge script (run_challenge.py)
- [ ] Task 4: Laboratory mode (lab_mode.py)
- [ ] Task 5: Documentation (README, MECHANICS, CONTRIBUTING)

Total commits: X
Total time: ~X hours
Any issues/blockers: [describe]
```
