# Project Overview — Moreau Arena

## What Is Moreau Arena?

Moreau Arena is a research benchmark for measuring LLM strategic reasoning. It is the companion repository for the paper:

> **Moreau Arena: How Adaptation and Exact Formulas Transform LLM Strategic Reasoning from Systematic Failure to Baseline-Beating Performance**
>
> Victor Stasiuc (2026), Independent Researcher

The core idea: build a simple but deep combat game, have LLMs play it under different information conditions, and measure what changes.

## The Game

Two creatures fight on an 8x8 grid for up to 60 ticks. Each player:

1. Picks one of 6 animals (Bear, Buffalo, Boar, Tiger, Wolf, Monkey)
2. Distributes 20 stat points across HP, ATK, SPD, WIL (minimum 1 each)
3. Watches them fight automatically (no tactical control)

Key mechanics:
- **HP** determines max health: `50 + 10 * HP` (range: 60-250)
- **ATK** determines damage: `floor(2 + 0.85 * ATK)` (range: 2-19)
- **SPD** determines dodge chance: `max(0%, min(30%, 2.5% * (SPD-1)))`
- **WIL** determines ability resist: `min(60%, WIL * 3.3%)`
- A shrinking ring activates at tick 30, forcing engagement
- Each animal has a passive ability and 2 active abilities with proc rates

The game is deterministic given a seed (SHA-256 based RNG). Same seed + same builds = identical outcome every time.

## Why It Matters

Most LLM benchmarks test knowledge retrieval or code generation. Moreau Arena tests **strategic reasoning under uncertainty** — the ability to understand a system's rules, calculate optimal strategies, and adapt to opponents.

The benchmark is designed with several properties that make it uniquely useful:

### Contamination Resistance

The game rules are custom-designed and not present in any training data. LLMs cannot pattern-match from memorized strategies. The stat formulas, ability proc rates, and combat mechanics are unique to this system. Config hash `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` locks the rules permanently.

### Reproducibility

Every match is deterministic. Tournament results are archived as JSONL with full match records. The config is frozen and hash-verified. Anyone can re-derive the Bradley-Terry rankings from the raw data.

### Controlled Complexity

The game is simple enough to understand in minutes but deep enough that optimal play requires genuine reasoning about stat scaling, animal matchups, and opponent modeling.

## The T001/T002 Story

Two tournaments were run with the same 13 agents (8 LLM variants + 5 hand-coded baselines) on the same frozen game engine. The only difference was the information provided to the LLMs.

### Tournament 001 (T001) — "One-Shot"

- **What LLMs received:** Qualitative descriptions of stats and abilities. Basic formulas. No examples of good builds. No adaptation between games.
- **Format:** Best-of-7 series, blind pick (same build every game)
- **Result:** LLMs achieved **37.5% win rate** against baselines
- **Top agent:** SmartAgent (a hand-coded baseline with counter-pick logic)
- **779 series** played across all agent pairs

LLMs consistently made poor strategic choices. They over-invested in WIL (ability resist) and under-invested in ATK. The hand-coded SmartAgent, with simple counter-pick rules, dominated.

### Tournament 002 (T002) — "Feedback + Counter-Pick"

- **What LLMs received:** Exact stat formulas with worked examples. Top-5 winning builds from T001 as "meta context." Structured JSON output. Adaptation after losses (loser sees winner's build, can re-pick).
- **Format:** Adaptive best-of-7 (loser adapts, winner's build is locked)
- **Result:** LLMs achieved **89.75% win rate** against baselines
- **Top agent:** gpt-5.2-codex (an LLM)
- **780 series** played

The same LLMs that lost to baselines now crushed them. The leaderboard flipped 180 degrees.

## The Scientific Finding

**LLM strategic performance depends critically on scaffolding — not raw capability.**

The 52.25 percentage point improvement (37.5% to 89.75%) came from four factors:
1. **Exact formulas** — LLMs can reason about scaling when given numbers
2. **Meta context** — Examples of winning builds calibrate expectations
3. **Adaptation** — Feedback loops enable counter-picking
4. **Structured output** — JSON parsing is more reliable than free-text

This is not about LLMs "getting smarter." The same models, the same game, the same opponents — only the information wrapper changed. The implication: benchmark results that show LLMs failing at strategic tasks may reflect prompt design more than model capability.

## What This Repository Contains

- A complete, deterministic combat simulator (frozen core)
- 13 agent implementations (5 baselines + 8 LLM variants)
- Raw tournament data (T001 + T002) as immutable JSONL archives
- Reproducible analysis scripts (Bradley-Terry rankings, pairwise matrices)
- An ablation suite to isolate each T002 component's contribution
- Lab mode for interactive experimentation
- A web leaderboard
- A season system for balance patches
- A DSL (Moreau Script) for expressing strategies as code
- 89 invariant tests ensuring the frozen core stays frozen
