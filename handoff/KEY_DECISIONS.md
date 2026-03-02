# Key Decisions — Why We Made the Choices We Made

This document explains the design rationale behind Moreau Arena's key parameters and architectural decisions.

---

## Why 6 Animals?

Six animals provide enough strategic diversity for meaningful matchups without overwhelming the decision space. Each animal fills a distinct archetype:

| Animal | Archetype | Role |
|--------|-----------|------|
| Bear | Berserker | Gets stronger as health drops |
| Buffalo | Tank | Damage reduction and survival |
| Boar | Burst | High first-hit damage |
| Tiger | Assassin | Speed advantage exploitation |
| Wolf | Utility | Proc bonus and DoT |
| Monkey | Wildcard | Copies opponent abilities |

With 6 animals and 20 stat points, the build space is large enough for genuine exploration (thousands of valid builds) but small enough that brute-force analysis is feasible for validation. The number was later expanded to 14 core + 4 extended animals for the ability grammar, but tournaments use the original 6.

---

## Why 20 Stat Points?

The budget of 20 points across 4 stats (minimum 1 each) creates meaningful trade-offs:

- **16 free points** to distribute (after the 4 mandatory minimums)
- Extreme builds are possible (e.g., ATK=17 leaving 1/1/1 elsewhere)
- Balanced builds are viable (5/5/5/5)
- The math works cleanly with the stat formulas

Higher budgets would reduce the cost of diversification (you could stack everything). Lower budgets would make all builds feel similar. 20 hits the sweet spot where ATK stacking is strong but not trivially dominant — there are genuine counter-strategies.

---

## Why 8x8 Grid?

The grid serves two purposes:
1. **Spatial dimension** for movement and positioning
2. **Ring mechanic** for forcing engagement

8x8 was chosen because:
- Large enough that starting positions matter (creatures don't immediately engage)
- Small enough that the ring mechanic meaningfully restricts space
- Matches chess-board familiarity for intuition
- Grid pathfinding (Chebyshev distance) is computationally trivial

The ring mechanic (activating at tick 30, shrinking the safe zone) prevents stalling strategies and ensures games resolve within 60 ticks.

---

## Why Best-of-7?

Best-of-7 series serve multiple purposes:

1. **Variance reduction** — A single game has significant RNG (ability procs, hit rolls). Best-of-7 reduces noise.
2. **Adaptation measurement** — In T002/Track B, the loser adapts after each game. 7 games provides enough adaptation cycles to observe learning.
3. **BT compatibility** — Bradley-Terry works on series outcomes (win/loss), not individual games. Series aggregate multiple data points into one clean signal.
4. **Practical runtime** — Each game takes milliseconds. 7 games per series is computationally negligible. The bottleneck is LLM API calls, and even there, 7 calls per series is manageable.

Why not best-of-5? Fewer adaptation cycles. Why not best-of-11? More API calls with diminishing returns on variance reduction.

---

## Why Bradley-Terry Over Elo?

Both BT and Elo produce rankings from pairwise outcomes. We chose BT as the primary metric for several reasons:

1. **Maximum likelihood estimation** — BT finds the rating vector that maximizes the likelihood of the observed outcomes. Elo approximates this with sequential updates that depend on game order.
2. **Bootstrap confidence intervals** — BT naturally supports bootstrap CI (resample matches N=1000 times, recompute ratings). This gives rigorous uncertainty bounds.
3. **No order dependence** — BT ratings are the same regardless of what order you process the games. Elo ratings can differ based on game order.
4. **Non-transitivity detection** — BT residuals reveal non-transitive matchups (rock-paper-scissors cycles) that Elo smooths away.

Elo is still computed and displayed (it's familiar to gamers), but all scientific claims use BT scores.

---

## Why Freeze the Core?

The frozen core design (hash-verified config, immutable tournament data) is the most important architectural decision:

**Problem:** If you change the rules after running experiments, all previous results become invalid. You can't compare T001 and T002 if the game changed between them.

**Solution:** Lock the config with a SHA-256 hash. Lock tournament data with per-file hashes. Run 89 invariant tests on every commit to verify nothing changed.

**What is frozen:**
- `config.json` — All game parameters (stats, formulas, abilities, ring, grid)
- `data/tournament_001/*` — T001 results and report
- `data/tournament_002/*` — T002 results, chunks, report, adaptation analysis
- Stat formulas in `engine.py`
- Seed derivation in `seed.py`

**What can change:**
- New agents (agents/ directory)
- New experiments (run_*.py scripts)
- New analysis (analysis/ directory)
- Web UI, documentation, seasons, DSL
- Everything that doesn't affect how existing matches simulate

This means new features are built *around* the frozen core, never modifying it. The invariant test suite is the alarm system — if any frozen file changes, tests fail and the commit is blocked.

---

## Why Ablations Before New Features?

The development roadmap prioritized ablation studies (decomposing the T001→T002 improvement) before adding new features (seasons, DSL, web platform). This was deliberate:

1. **Scientific rigor** — The paper claims that formulas + meta + adaptation drive the improvement. Ablations prove (or disprove) this claim by isolating each factor.
2. **Credibility** — Releasing ablation results alongside the paper strengthens the contribution. "We ran 5 ablation variants" is more convincing than "we ran 2 tournaments."
3. **Foundation** — The ablation infrastructure (run_ablation.py, PSI suite, measurement spec) creates reusable tools. Every future experiment uses the same measurement methodology.
4. **Focus** — Building features before validating claims risks building on shaky ground. If ablations showed the improvement was entirely due to structured output (not formulas), the whole narrative would change.

---

## Why SHA-256 Seeding?

The simulator uses SHA-256 for deterministic random number generation:

```
tick_seed = SHA256(match_seed || tick_index)
hit_seed = SHA256(match_seed || tick_index || attack_index)
proc_seed = SHA256(match_seed || tick_index || creature_index || ability_index)
```

**Why not stdlib random?**
- `random.Random` state is hard to inspect and reproduce across Python versions
- SHA-256 is deterministic across all platforms and languages
- Each random value has an explicit, inspectable derivation
- No hidden state — given the match seed, every random value is independently computable

**Why not simpler hashing?**
- SHA-256 has excellent avalanche properties (small input changes produce uncorrelated outputs)
- No statistical bias in the output distribution
- Industry-standard and auditable

---

## Why 6 Animals With Different Ability Tiers?

Abilities are classified into two proc rate tiers:
- **Strong tier:** 3.5% proc rate (powerful effects like Last Stand, Iron Will)
- **Standard tier:** 4.5% proc rate (moderate effects like Pack Howl, Rend)

This tiering creates a natural risk/reward trade-off: powerful abilities fire less often. WIL modifies proc rates (+0.08% per point) but within hard bounds [2.5%, 5.5%], preventing either extreme.

The two-tier system was chosen over continuous proc rates because:
1. Easier to reason about (LLMs and humans alike)
2. Creates clear "strong vs. reliable" ability choices
3. Simpler to balance — only two knobs to tune per season

---

## Why the MoreauAgent Interface?

The public submission API uses a simple two-method interface:

```python
class MoreauAgent:
    def get_build(self, prompt, game_state) -> dict
    def adapt_build(self, prompt, opponent_build, my_build, result, game_state) -> dict
```

**Why not a more complex interface?**
- Two methods cover all tracks (get_build for A/C/D, adapt_build for B)
- Any LLM can be wrapped in this interface with minimal code
- Non-LLM agents (scripts, heuristics) can also implement it
- The interface doesn't leak simulator internals — agents only see prompts and game state

**Why separate get_build and adapt_build?**
- They serve fundamentally different purposes (initial strategy vs. reactive counter-picking)
- Track A/C/D only call get_build; Track B calls both
- Separating them makes the protocol unambiguous

---

## Why Ablation Variants Use the Same Baseline Agents?

All ablation variants (formulas-only, meta-only, etc.) test the LLM against the same 5 baseline agents from T001/T002. This ensures:

1. **Controlled comparison** — The only variable is the LLM's information; the opponents are constant
2. **Direct comparability** — Win rates from different ablation variants can be directly compared
3. **Baseline calibration** — SmartAgent provides a known upper bound for non-adaptive play; RandomAgent provides a floor

The baselines are hand-coded and deterministic (given a seed), so they don't add noise.
