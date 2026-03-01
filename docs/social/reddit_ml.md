# [R] Moreau Arena: A Strategic Combat Benchmark for Evaluating LLM Reasoning Under Uncertainty

## Motivation

Evaluating LLM strategic reasoning is harder than it looks. Popular game benchmarks — chess, poker, Diplomacy — suffer from training data contamination: models have likely seen thousands of strategies, openings, and transcripts during pre-training. Static reasoning benchmarks (MMLU, GSM8K, ARC) test isolated skills in non-adversarial settings, missing the core challenge of strategic decision-making: making a single commitment that integrates multiple mechanics under competition with an adaptive opponent.

We wanted a benchmark where:

1. **No model has seen the game before.** The rules are novel, authored specifically for this benchmark, with a frozen configuration hash to verify no post-hoc tuning.
2. **A single decision carries real weight.** Agents must allocate limited resources across competing stats, with no opportunity to brute-force through trial and error within a single game.
3. **The optimal strategy is derivable but not obvious.** Given exact formulas, a careful reasoner can identify the dominant approach. With vague descriptions, even frontier models fail systematically.
4. **Adaptation is measurable.** A series format (best-of-7) with loser-sees-winner feedback lets us distinguish models that learn from losses versus models that lock into a single strategy.

Existing benchmarks rarely test all four properties simultaneously. Moreau Arena does.

## Method

### Build Allocation

Each agent selects one of six animals (Bear, Buffalo, Boar, Tiger, Wolf, Monkey) and distributes 20 stat points across four attributes: HP, ATK, SPD, and WIL (minimum 1 each). Each animal has a unique passive ability and two active abilities that proc stochastically during combat. The stat allocation determines derived values — max hit points, base damage per tick, dodge chance, and ability resist — through explicit formulas.

### Turn-Based Combat

Two creatures fight on an 8x8 grid for up to 60 ticks. Each tick, creatures move, attack if adjacent, and abilities may trigger based on proc rates modified by WIL. A shrinking ring activates at tick 30, dealing 2% max HP per tick to creatures outside the safe zone, preventing stalling. The creature that kills its opponent or has more HP when time expires wins.

### Series Format

We ran two 13-agent round-robin tournaments (8 frontier LLMs + 5 hand-coded baselines):

- **Tournament 001 (T001):** Blind pick, best-of-7. Each agent submits one build for all games. Qualitative ability descriptions only. 779 series, 3652 games.
- **Tournament 002 (T002):** Adaptive best-of-7. The loser sees the winner's exact build and may re-pick. Exact numerical formulas provided. Meta context injected (top builds from T001). Structured JSON output enforced. 780 series, 4015 games.

Same agents. Same game. Different scaffolding. The question: does the scaffolding change the outcome?

## Key Results

### The Leaderboard Flips

In T001, baselines dominate. The top 3 agents by Bradley-Terry rating are all non-LLM baselines. LLMs win only 37.5% of LLM-vs-baseline series. The strongest LLM (Claude 3.5 Sonnet) ranks 4th overall.

In T002, every LLM outranks every baseline. LLMs win 89.75% of LLM-vs-baseline series. GPT-5.2-Codex achieves the largest BT gain (+0.881, rank 9 to rank 1).

### The WIL Trap

In T001, several models — notably GPT-4o and Gemini 2.0 Flash — systematically over-invest in WIL (willpower). WIL adds only 0.08% proc bonus per point to your own abilities and 3.3% resist per point against opponent abilities. Meanwhile, each ATK point contributes ~51 total damage over 60 ticks versus 10 HP absorbed per HP point. The math overwhelmingly favors ATK, but without explicit formulas, models pattern-match to RPG archetypes where "willpower" is typically powerful.

### Adaptation Curves

Across all LLM agents in T002, changing builds after a loss yields a 51.06% win rate in subsequent games — barely above coin flip. Several top models (GPT-5.2-Codex, Claude 3.5 Sonnet) win primarily by finding strong builds early rather than through game-by-game counter-picking. Adaptation matters, but convergence speed matters more.

### Bear Dominance

The meta-defining build is Bear 8/10/1/1 (or variants like 3/14/2/1), achieving a 78% win rate across 887 uses in T002. Bear's Fury Protocol passive (+ATK below 50% HP) creates a death spiral: as the bear takes damage, it hits harder, finishing fights before opponents can leverage defensive stats.

### Non-Transitive Dynamics

T002 exhibits 12 strict 3-cycles (A beats B beats C beats A) in the pairwise win-rate matrix. T001 has zero. With feedback and adaptation, the meta supports genuine rock-paper-scissors dynamics rather than a strict linear hierarchy.

## Open Challenge

We release the full benchmark as an open challenge. Testing your own model requires:

```bash
git clone https://github.com/supervitek/moreau-arena-paper
pip install -r requirements.txt
python run_challenge.py --provider openai --model your-model-id --protocol t002
```

The script runs a full round-robin against all 13 agents, computes Bradley-Terry rankings, and outputs detailed JSONL match records. A `--dry-run` mode lets you test the pipeline without API keys.

We also provide a laboratory mode for interactive experimentation:

```bash
python lab_mode.py --provider anthropic --model claude-sonnet-4-5 --rounds 10
```

This runs an iterative loop where your model proposes builds, the simulator evaluates them in round-robin, and the model receives performance feedback each round — useful for studying convergence behavior and build-space exploration.

## Links

- **Paper + Code + Data:** [github.com/supervitek/moreau-arena-paper](https://github.com/supervitek/moreau-arena-paper)
- **Full game mechanics:** [docs/MECHANICS.md](https://github.com/supervitek/moreau-arena-paper/blob/main/docs/MECHANICS.md)
- **How to add your model:** [docs/CONTRIBUTING.md](https://github.com/supervitek/moreau-arena-paper/blob/main/docs/CONTRIBUTING.md)

All match records (1559 series, 7667 games), verbatim prompts, frozen config hash, and analysis scripts are included. MIT licensed.

The arena is open. Show us what your model can do.
