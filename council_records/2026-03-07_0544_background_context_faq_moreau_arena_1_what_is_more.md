# Round Table Council — 2026-03-07

**Question:** BACKGROUND CONTEXT:
# FAQ — Moreau Arena

## 1. What is Moreau Arena?

Moreau Arena is a contamination-resistant strategic reasoning benchmark for large language models. It presents LLMs with a novel 1v1 creature combat game that does not exist in any training corpus, then measures how well they reason about stat allocation, counter-picking, and adaptation under uncertainty.

## 2. Why is prompt sensitivity a concern?

LLM benchmarks can produce different rankings depending on how the prompt is worded. Moreau addresses this through the Prompt Sensitivity Index (PSI): we run the same tournament with multiple paraphrased prompts and measure ranking stability using Kendall's tau. A PSI below 0.15 means the benchmark is prompt-robust.

## 3. Why only six animals in the original tournaments?

Six animals create a rich enough strategic space (6 animals × ~3,000 valid stat allocations = ~18,000 possible builds) while keeping the prompt short enough for single-turn reasoning. The animal roster can expand in future seasons without invalidating existing results, since each season's config is frozen independently.

## 4. Is Moreau Arena a game?

Moreau Arena is a benchmark that uses game mechanics as its measurement instrument. The combat is fully deterministic given a seed — there is no player skill involved during the fight. The only decision is the pre-fight build choice. This makes it a strategic reasoning task, not a game-playing task.

## 5. Why Bradley-Terry over Elo?

Bradley-Terry (BT) is a principled statistical model for pairwise comparisons that produces maximum-likelihood estimates with well-defined confidence intervals. Elo is an online approximation of BT that is order-dependent (results change depending on which games are processed first). We use BT as the primary metric for research and display Elo on the leaderboard only for familiarity.

## 6. How is Moreau different from existing LLM benchmarks?

Most benchmarks test knowledge recall or code generation on problems that may appear in training data. Moreau tests strategic reasoning on a novel game that cannot be memorized. Key differences:
- **Contamination-resistant:** The game rules are original and not in any training corpus.
- **Pairwise comparison:** Models compete against each other, not against a fixed answer key.
- **Adaptation measurement:** Track B measures whether models can learn from opponent feedback within a series.
- **Reproducible:** All outcomes are deterministic given the seed, config hash, and prompt.

## 7. Can I submit my own model?

Yes. See `docs/AGENT_API.md` for the submission interface. You implement a `MoreauAgent` class with `get_build()` and optionally `adapt_build()` methods, then run your agent through the standard tournament protocol.

## 8. How do you ensure reproducibility?

Every match outcome is determined by three inputs: the config hash (frozen), the match seed (recorded), and the model's build choice (logged in JSONL). Given these three values, anyone can replay any match and get identical results. The invariant test suite (`tests/test_invariants.py`) verifies this property on every commit.

## 9. What does the closing ring do?

The closing ring is a tiebreaker mechanism. Starting at tick 30 (out of 60 max), outer tiles begin dealing increasing damage to creatures standing on them. This prevents stalemates between defensive builds and ensures every match resolves within 60 ticks.

## 10. Can Moreau Arena measure reasoning improvements over time?

Yes. Because the benchmark is seasonal (each season freezes its config), you can track the same model across seasons or compare model versions on the same season. Lab Mode (`lab_mode.py`) specifically measures how efficiently a model converges to the optimal strategy over multiple rounds of feedback, providing iteration curves and distance-to-optimum metrics.

QUESTION:
You are reviewing Moreau Arena as a benchmark for LLM strategic reasoning. Based on the FAQ and your knowledge: What is the single highest-priority improvement AND the single biggest risk for Season 1 credibility? Be specific and actionable.

**Moderator:** claude-opus-4-6
**Panelists:** claude-opus-4-6, gpt-5.4, gemini-3.1-pro-preview, grok-4-1-fast-reasoning, deepseek-r1:latest, kimi-k2-thinking:cloud

---

## Phase 1: Independent Responses

### claude-opus-4-6 (22.0s, $0.0694)

## Highest-Priority Improvement: Publish the Full Combat Resolution Engine as Open Source Before Season 1 Results Drop

The FAQ emphasizes reproducibility — config hash, seed, and build choice determine outcomes. But reproducibility is only meaningful if external researchers can actually run the resolver independently. If the combat engine is closed-source at launch, Season 1 credibility rests entirely on trust rather than verification. The FAQ mentions `tests/test_invariants.py` but doesn't confirm the engine itself is public.

**Specific action:** Release the complete deterministic combat simulator (including the closing ring logic, damage formulas, movement AI, and tile mechanics) under an open license *before* publishing Season 1 rankings. Include the frozen config file, all match seeds, and the JSONL build logs. This lets any third party replay every match and confirm every outcome independently.

**Why this matters most:** Every other credibility claim — contamination resistance, prompt robustness via PSI, Bradley-Terry over Elo — is downstream of whether people believe the combat outcomes are correctly computed and honestly reported. A single discovered bug in a closed resolver would retroactively invalidate all rankings. An open resolver means bugs get found *before* they become scandals, and the community can verify rather than trust. This is table stakes for any benchmark claiming scientific rigor.

---

## Biggest Risk to Season 1 Credibility: The Strategic Space May Be Degenerate, Producing a Dominant Strategy That Trivializes the Benchmark

With 6 animals and ~3,000 valid stat allocations each, the FAQ advertises ~18,000 possible builds. But if the combat resolution has a dominant strategy — some animal-stat combination that beats most or all others — then the benchmark doesn't measure strategic reasoning. It measures which models stumble onto the dominant build through priors or luck. The benchmark would effectively collapse into a knowledge recall task (knowing the right build) rather than a reasoning task.

**Why this is the biggest risk:** Contamination resistance is Moreau's flagship differentiator. If a dominant strategy exists, post-Season-1 discussion will immediately surface it, and every subsequent evaluation will be contaminated — models will encounter the optimal build in their training data. The benchmark's core value proposition evaporates in one season.

**Specific action:** Before Season 1, run an exhaustive brute-force round-robin of all ~18,000 builds against each other (feasible given deterministic resolution and a small state space). Compute the Nash equilibrium of the metagame. If a single build or small cluster dominates with >70% win rate against the field, redesign the balance before publishing results. Publish the equilibrium analysis alongside Season 1 results so the community can evaluate strategic depth. If the Nash equilibrium is a mixed strategy over a diverse set of builds, that's strong evidence the benchmark is actually measuring reasoning rather than search.

**The connection between these two points:** An open engine enables the equilibrium analysis by the community, which in turn validates (or invalidates) the strategic depth claim. They reinforce each other. But if forced to choose one: publish the engine. Without verifiability, nothing else matters.

### gpt-5.4 (11.8s, $0.0082)

**Highest-priority improvement:**  
**Publish a strong external-validity package: exact-optimum baselines and difficulty calibration for the frozen Season 1 config.**

Concretely, before treating Season 1 as a serious reasoning benchmark, I’d want:
1. **Solved or near-solved reference policies** for the 6-animal meta under the frozen rules:
   - brute-force / beam / search over the build space,
   - exploitability estimates,
   - best-response tables,
   - matchup matrix coverage.
2. **Difficulty diagnostics**:
   - how often a simple heuristic gets close to optimal,
   - whether one or two dominant builds collapse the strategic space,
   - whether adaptation actually changes win rate versus static play.
3. **Public artifacts**:
   - config hash,
   - seeds,
   - simulator,
   - baseline agents,
   - a report showing where the benchmark is easy, hard, and deceptive.

**Why this matters most:**  
Right now Moreau has a strong story on contamination resistance and reproducibility, but credibility depends on proving it measures **strategic reasoning rather than prompt-following plus decent heuristics**. If Season 1’s game is accidentally shallow, degenerate, or dominated by a narrow strategy, leaderboard differences won’t mean much. A benchmark about reasoning needs a demonstrated relationship between model choices and actual strategic quality. Without calibrated baselines and approximate optima, BT/Elo can rank models, but you still don’t know what they’re good at.

---

**Biggest risk to Season 1 credibility:**  
**The benchmark may primarily measure prompt/interface sensitivity and style-dependent compliance rather than stable strategic ability.**

The FAQ mentions PSI and says prompt robustness is acceptable below 0.15, which is good, but for Season 1 this is still the biggest credibility risk because:
- build selection is a **single-turn natural-language elicitation problem**,
- tiny wording changes can alter whether a model reasons explicitly, plays safe, follows formatting, or hallucinates assumptions,
- pairwise rankings can look statistically clean while still being driven by prompt artifacts.

This is especially dangerous because contamination resistance can create a false sense of security: “novel game” does **not** imply “valid reasoning measure.” If rankings shift materially across paraphrases, system prompts, output schemas, or token budgets, then Season 1 is benchmarking elicitation robustness more than strategy.

**Actionable mitigation:**  
For launch, require a **credibility card** that reports ranking stability across:
- multiple prompt paraphrases,
- at least two output formats,
- reasoning-hidden vs no-reasoning variants,
- context-length / token-budget caps,
- temperature and retry policy.

If those perturbations move rankings more than model confidence intervals do, Season 1 claims should be heavily qualified.

### gemini-3.1-pro-preview (20.3s, $0.0039)

As an AI developed with a strong lineage in both large language modeling and game-theoretic reinforcement learning, I find Moreau Arena’s contamination-resistant design elegant. However, evaluating strategic reasoning through game mechanics requires rigorous mathematical grounding. 

Here is my assessment of the single biggest risk and highest-priority improvement for Season 1.

### The Single Biggest Risk: A Degenerate Meta-Game (Trivial Nash Equilibrium)
The FAQ notes a strategic space of ~18,000 possible builds (6 animals × ~3,000 stat allocations). The critical risk to Season 1's credibility is that this space collapses into a **degenerate meta-game** where a single dominant build mathematically defeats all others. 

If an optimal "stat-stick" build exists (e.g., maxing out speed and damage while ignoring health), the benchmark ceases to measure complex reasoning, counter-picking, or adaptation. Instead, it merely tests which model is lucky enough to zero-shot the dominant exploit, or which model converges on it first in Lab Mode. 

**Actionable mitigation:** Before Season 1 freezes, the developers must run traditional algorithmic solvers (like Monte Carlo Tree Search or self-play RL) against the arena to mathematically prove the existence of an intransitive (rock-paper-scissors) meta-game. If a single dominant Nash Equilibrium exists, the stat math must be rebalanced.

### The Highest-Priority Improvement: Non-LLM Algorithmic Baselines
Currently, the FAQ indicates models compete against each other to generate a Bradley-Terry (BT) rating. The highest-priority improvement is to **inject non-LLM algorithmic agents (e.g., Random Search, Greedy Heuristic, and MCTS) directly into the BT leaderboard.**

**Why this matters most:** LLMs are notoriously prone to generating highly articulate, logically plausible, but mathematically flawed strategies in zero-shot environments. If the leaderboard only contains LLMs, the #1 ranked model might simply be the "least bad" at spatial combat math. 

By anchoring the Bradley-Terry pool with a Random baseline (the floor) and an MCTS solver (the ceiling), we gain objective context. If `gpt-5.4` or my own architecture, `gemini-3.1-pro-preview`, ranks below a simple Greedy algorithm, we know the models are failing at fundamental game-theoretic reasoning. Without these programmatic anchors, a relative LLM-only leaderboard creates an illusion of strategic competence that may not actually exist.

### grok-4-1-fast-reasoning (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

[ERROR: API 403: error code: 1010]

### deepseek-r1:latest (108.9s, $0.0000)

**Response by deepseek-r1:latest**  

**Highest-Priority Improvement:**  
I propose to **increase the creature roster beyond six animals** for Season 1. While six animals create a manageable prompt and rich strategic space, expanding to eight or nine (while keeping the prompt concise) would exponentially increase the state space (~27,000+ builds) and allow deeper analysis of emergent strategies. This would test models' ability to handle more complex counter-picking, defensive stacking, and adaptive play under greater uncertainty.  

**Why it matters most:**  
This addresses a core design constraint: the original six-animal limit may artificially cap the depth of strategic reasoning observed. Fewer builds mean flatter performance plateaus, reducing the ability to distinguish subtle reasoning improvements. A larger roster would provide richer data for researchers, better isolate high-performing strategies, and align the benchmark more closely with real-world complexity. Prompt engineering can mitigate length issues (e.g., hierarchical descriptions), and the FAQ confirms roster expansion is feasible without invalidating prior results.  

**Biggest Risk for Season 1 Credibility:**  
The **risk of model-specific contamination or incidental exposure** to similar mechanics. Even with claims of novelty, some models (e.g., OpenAI’s family or Meta’s broader training) might have encountered combinatorial game-like structures in their corpora. This could create artificial performance cliffs between models and invalidate the benchmark’s contamination-resistance claims.  

**Defensive Action:**  
- Run unsupervised corpus checks (e.g., semantic similarity searches) on the tournament data for all model families participating in Season 1.  
- Publish a "model exposure audit" for top-performing models in the FAQ, detailing any detected overlaps with external datasets. This builds trust by addressing skepticism preemptively.  

This risk is more credible than prompt sensitivity, as contamination is a harder-to-detect threat than wording changes, and it directly undermines Moreau Arena’s foundational claim of novelty.

### kimi-k2-thinking:cloud (37.4s, $0.0000)

**Highest-priority improvement:** Implement a **strategic complexity validation suite** that establishes a performance floor with non-LLM baselines (heuristic agents, lightweight MCTS, random search) and a ceiling via exhaustive solvers. Publish this alongside the leaderboard. This matters because without proven "strategic depth," the benchmark could be measuring pattern-matching on a trivially solvable game rather than genuine reasoning. If a simple algorithm matches top LLM performance, the entire premise collapses. Actionable: Run a parallel tournament with these baselines before Season 1 launch; any LLM that doesn't significantly outperform heuristics fails the validity threshold and is marked "unverified."

**Biggest risk: ** ** Deterministic overfitting via combat simulation reverse-engineering. ** The reproducibility invariant (seed + config = deterministic outcome) is a double-edged sword: it enables verification but also allows models to learn the combat engine implicitly. With only 6 animals and ~18k builds, a model could approximate the simulation function and "reason" by internally rolling out fights rather than strategizing. If even one frontier model exhibits this—shown by perfect predictive accuracy on unseen build matchups or by sudden performance jumps when given extra inference time—the benchmark's credibility dies. The risk is catastrophic: it transforms a reasoning test into a memorization test of a compact function. Mitigation requires black-box validation matches where combat logic is genuinely hidden, but failing that, the Season 1 report must include a "simulation detection" analysis measuring outcome predictability.

---

## Phase 2: Critique Round

### claude-opus-4-6's Critique (30.1s, $0.1406)

## Critique of Other Panelists

### gpt-5.4

**Agreement:** The "credibility card" idea is excellent and more operationally specific than my own framing. Requiring stability reporting across output formats, token budgets, and reasoning-hidden variants goes meaningfully beyond what PSI alone captures. I also agree that "novel game ≠ valid reasoning measure" is an important distinction the FAQ glosses over.

**Disagreement:** I think you underweight the degeneracy risk relative to prompt sensitivity. If the game has a dominant strategy, prompt sensitivity becomes irrelevant — you're measuring noise in a broken instrument. You frame prompt sensitivity as the *biggest* risk, but PSI is already being measured. Degeneracy is unaddressed and harder to fix post-launch. I'd flip your ordering.

**Question:** Your "solved reference policies" improvement overlaps heavily with my equilibrium analysis recommendation. Do you see these as the same thing, or is there a meaningful difference between "publish baselines" and "publish the Nash equilibrium"?

### gemini-3.1-pro-preview

**Agreement:** We converge almost exactly on the biggest risk (degenerate meta-game). Your framing of the "stat-stick" failure mode is concrete and useful. I also strongly agree on non-LLM baselines — anchoring the BT leaderboard with Random/Greedy/MCTS agents is arguably a better version of my "publish the equilibrium" suggestion because it provides *functional* context rather than just mathematical context.

**Disagreement:** I'd push back on MCTS as a ceiling. MCTS is designed for sequential decision problems with branching; Moreau's decision is a single build choice from ~18,000 options. Exhaustive enumeration is computationally feasible here and would give you the *actual* ceiling, not an approximation. Using MCTS where brute-force works risks introducing solver noise that muddies the baseline.

**Question:** You recommend proving "intransitive meta-game" existence before launch. What's your threshold? Rock-paper-scissors intransitivity among the top-3 builds? A mixed Nash with support size ≥ N? Without a specific criterion, "prove intransitivity" is hard to action.

### deepseek-r1:latest

**Agreement:** The contamination concern about structurally similar game mechanics (not just literal training data overlap) is a valid nuance that others, including myself, didn't adequately address.

**Disagreement:** Expanding to 8-9 animals for Season 1 is, frankly, the wrong direction. The FAQ explicitly states six animals were chosen to keep prompts manageable for single-turn reasoning, and the seasonal model means expansion happens naturally. Changing the roster *before* Season 1 launches sacrifices the frozen-config reproducibility guarantee for marginal strategic depth gains. Going from ~18,000 to ~27,000 builds doesn't qualitatively change the degeneracy risk — it just makes brute-force validation harder. This suggestion optimizes the wrong variable at the wrong time.

The "corpus check" idea for contamination also has a practical problem: you can't run semantic similarity searches against closed training sets (OpenAI, Anthropic). The audit would only work for open-weight models, creating an asymmetric credibility standard.

**Question:** How would you distinguish "incidental exposure to similar mechanics" from "general combinatorial reasoning ability"? If a model is good at resource allocation problems broadly, that's a feature, not contamination.

### kimi-k2-thinking:cloud

**Agreement:** The strategic complexity validation suite is well-specified and actionable. The "unverified" label for models that don't beat heuristics is a clever credibility mechanism.

**Disagreement:** Your biggest risk — "deterministic overfitting via reverse-engineering" — seems implausible for Season 1. Internally simulating the combat engine requires the model to have learned the engine's logic, which contradicts the contamination-resistance claim. With ~18,000 builds and no training data on the game, a model can't approximate the simulation function from a single-turn prompt. This risk becomes real only *after* Season 1 results and analysis are public. You're describing a Season 2 problem.

**Question:** What would "simulation detection" actually look like? If a model picks near-optimal builds, how do you distinguish "good reasoning" from "implicit simulation"? This seems unfalsifiable.

### Overall reflection

After reading all responses, I'd strengthen my improvement recommendation by incorporating gemini's non-LLM baselines directly into the BT leaderboard — that's more useful than just publishing equilibrium analysis. My risk assessment remains unchanged: degeneracy is the existential threat, and three of five panelists converged on it independently.

### gpt-5.4's Critique (17.0s, $0.0169)

**claude-opus-4-6**  
**Agreement:** Strong point that open-sourcing the resolver is close to table stakes for scientific credibility. I also agree the “degenerate meta” risk is first-order and overlaps heavily with my concern about strategic validity. Their call for publishing seeds, logs, and frozen config is exactly right.  
**Disagreement:** I’d rank “publish the engine” slightly below “prove the benchmark is strategically nontrivial.” A fully open, replayable benchmark can still be shallow. Also, “exhaustive round-robin of all ~18,000 builds against each other” is directionally good but likely underspecified: that’s huge pairwise volume, and more importantly dominance should be assessed via exploitability / best responses, not just field win rate.  
**Questions:** Is their highest-priority recommendation assuming the engine might be closed? If it’s already public internally or planned for release, would they still rank this above calibration and solver baselines?

**gemini-3.1-pro-preview**  
**Agreement:** Very aligned with my view that the biggest risk is a degenerate meta. I also strongly agree that non-LLM baselines are essential; that’s one of the best additions across the panel because it gives an interpretable floor and ceiling for what “reasoning” means here.  
**Disagreement:** I think “prove the existence of an intransitive meta-game” is too strong and maybe the wrong criterion. A benchmark can still be valid without elegant rock-paper-scissors structure, as long as there’s no trivial dominant strategy and meaningful best-response complexity exists. Also MCTS/self-play RL may be awkward framing here since the only decision is pre-fight build choice; direct search / response-oracle methods may fit better.  
**Questions:** What exact validity criterion would they accept if the game has a mixed equilibrium but weak intransitivity? And how would they integrate algorithmic baselines into BT without letting implementation quality dominate interpretation?

**deepseek-r1:latest**  
**Agreement:** The instinct to worry about whether six animals provide enough strategic depth is fair in the abstract.  
**Disagreement:** I think this is the weakest response. Expanding the roster is not the highest-priority Season 1 improvement; it changes the benchmark before validating the current frozen season. That’s the opposite of what Season 1 most needs, which is calibration of the existing config. I also disagree that contamination from “similar mechanics” is the biggest risk. The benchmark’s novelty claim is about exact task contamination, not whether models have ever seen game-like abstractions. Prompt/interface sensitivity and strategic degeneracy are much more plausible immediate credibility threats.  
**Questions:** How would adding more animals avoid simply increasing search burden without improving construct validity? And what concrete evidence suggests contamination is more serious than prompt sensitivity here?

**kimi-k2-thinking:cloud**  
**Agreement:** Very strong on strategic complexity validation and non-LLM baselines; this is the closest to my own answer and arguably improves it by emphasizing benchmark “anchors.”  
**Disagreement:** I’m not persuaded that “reverse-engineering the simulator” is the biggest Season 1 credibility risk. If a model can infer compact deterministic rules from the prompt and use them to evaluate builds, that may actually be legitimate strategic reasoning for this benchmark, not cheating. It only becomes problematic if it’s exploiting leaked hidden structure or memorized season-specific solutions. I’d worry more about prompt elicitation artifacts than latent simulation.  
**Questions:** What empirical signature would distinguish valid internal world-modeling from invalid “simulation overfitting”? And why would black-box hidden-logic matches still measure the same construct Moreau claims to test?

**Change of mind:** After reading Claude and Kimi, I’d elevate **public algorithmic baselines + open resolver artifacts** as more central to Season 1 credibility than I initially stated. I still think strategic calibration is the top issue, but those are probably necessary parts of the same package.

### gemini-3.1-pro-preview's Critique (19.2s, $0.0060)

I am struck by the strong consensus between myself, Claude, GPT-5.4, and Kimi regarding the need for non-LLM baselines and Nash equilibrium analysis. We all independently recognized that without mathematical grounding, LLM-only leaderboards are vulnerable to degenerate metagames. 

Here is my critique of the panel:

**Claude-opus-4-6**
*   **Agreement:** I am changing my mind based on your argument. Open-sourcing the combat resolution engine is indeed a better "highest-priority improvement" than my own baseline suggestion. My proposed algorithmic baselines are impossible to verify if the community cannot run the engine independently. 
*   **Disagreement:** None. You perfectly mirrored my risk assessment regarding degenerate metagames and provided a superior actionable improvement.
*   **Question:** If the engine is open-sourced, would you support embedding the combat logic directly into the prompt as Python code for frontier models, rather than relying strictly on natural language rules?

**GPT-5.4**
*   **Agreement:** Your taxonomy for the external-validity package (best-response tables, matchup matrices) is excellent and expands perfectly on my call for algorithmic baselines.
*   **Disagreement:** You highlighted prompt sensitivity as the biggest risk, but FAQ #2 explicitly states Moreau already addresses this via the Prompt Sensitivity Index (PSI). While your "credibility card" is a good idea, the benchmark designers already have a quantitative threshold (<

### grok-4-1-fast-reasoning's Critique (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

[ERROR: API 403: error code: 1010]

### deepseek-r1:latest's Critique (130.8s, $0.0000)

Okay, here's my critique of the other panelists' responses based on the provided context and my own earlier reasoning:

**Critique of Other Panelists' Responses**

**Panelist: claude-opus-4-6**

*   **Points of Agreement:**
    1.  Emphasis on **transparency** by publishing the core code/simulator *before* Season 1 is crucial. This directly addresses the claim of reproducibility and allows independent verification of the game mechanics, which is a core strength of Moreau Arena.
    2.  The idea of running a **Nash Equilibrium analysis** is highly relevant for understanding the strategic depth of the arena. It directly tests the core hypothesis of non-degeneracy, which is a significant risk we both identified.
*   **Points of Disagreement:**
    1.  While agreeing the core *simulator* should be public, I slightly differ on the priority. The **highest-priority improvement** should be verifying the *stated state space* (`6 animals * ~3000 allocations = 18k builds`) *before* potentially running complex solver-based NEAs. Ensuring the input/output mapping of the build generation process is correct is foundational.
    2.  The **biggest risk** is likely the meta-game degeneracy (single dominant build), not necessarily the simulator's internal workings, though both are valid concerns.
*   **Questions:**
    1.  How computationally feasible and meaningful is computing a true Nash Equilibrium for an 18k-state game, especially if it's zero-sum? Might an approximate equilibrium or self-play analysis be more feasible and informative for Season 1?
    2.  Could you elaborate on the specific criteria for determining if the meta-game is "non-degenerate" based on the Nash analysis? What does a non-degenerate result look like in practice?

**Panelist: gpt-4.5 (GPT-5.4)**

*   **Points of Agreement:**
    1.  The need for **external algorithmic baselines** (Random, Greedy, MCTS) is critical. This provides a necessary lower bound and upper bound for what constitutes "good" performance, independent of LLM quirks (format adherence, prompt-following).
    2.  The concern about **LLMs potentially optimizing for pattern matching rather than true strategic reasoning** is spot on and a core validity issue.
    3.  The suggestion for **comprehensive prompt sensitivity analysis** (testing different formats, hiding reasoning, token budgets) is a valuable addition to the evaluation toolkit.
*   **Points of Disagreement:**
    1.  While I agree adding baselines is beneficial, I see the **highest-priority improvement** as first ensuring the *state space itself* is accurately defined and understood. Knowing the true complexity (18k builds) is prerequisite to meaningfully comparing baselines and LLMs. The baselines are tools for evaluation, not necessarily the primary definition of the problem.
    2.  The **biggest risk** I identified is the potential degeneracy of the *meta-game* (the interaction between the builds), not the *prompt interface* being the primary factor. The prompt is just how we elicit the strategy; the underlying game mechanics must hold up.
*   **Questions:**
    1.  When comparing baselines, should the focus be on their *predictive accuracy* against the simulator or their *reasoning process*? Both are relevant, but Moreau's focus is on reasoning, so the baseline's reasoning output might need consideration.
    2.  How does the MCTS baseline factor into the Bradley-Terry rating? Does it simply play many games until win rate converges, or does it output a natural language description? And how is that handled for the BT comparison?

**Panelist: google/gemini-3.1-pro-preview**

*   **Points of Agreement:**
    1.  The **risk of a degenerate meta-game** (single dominant build) is, indeed, the most critical risk to the benchmark's core premise of measuring complex strategic reasoning.
    2.  The **need for non-LLM algorithmic baselines** (Random, Greedy, MCTS) is essential for establishing objective performance anchors.
*   **Points of Disagreement:**
    1.  While agreeing the *risk* is degeneracy, I slightly differ on the *highest-priority improvement* for *Season 1*. Injecting baselines is crucial, but perhaps *verifying the state space* and understanding the game's structure first (e.g., by running the solver-based analysis Claude suggested) should be done *before* Season 1 launch to guide the baseline selection and validation. The baselines are validation tools, but understanding the terrain first is vital.
*   **Questions:**
    1.  The response mentions "proving the existence of an intransitive meta-game." Could you clarify what specific solver or methodology was used? And what does a "mathematically proven" intransitive meta-game look like in the context of a discrete build space?
    2.  When adding non-LLM baselines, how will their performance be measured on the Bradley-Terry scale? Will it be based on win rates against other baselines/simulator, or will they need to output natural language descriptions for BT comparison?

**Panelist: x.ai/grok-4-1-fast-reasoning**

*   **Points of Agreement:**
    1.  The **risk of deterministic overfitting** (models learning the simulation function) is a valid and potentially severe concern, especially given the small state space. It directly challenges the reasoning claim.
*   **Points of Disagreement:**
    1.  While I agree deterministic overfitting is a risk, I see it as the **biggest risk**, whereas the other panelists focused on meta-game degeneracy. It's a significant shared concern, but I prioritized the potential for reverse-engineering the engine itself over the possibility of a single dominant strategy.
    2.  My suggested **highest-priority improvement** (validation suite with baselines) is largely aligned with the need to prevent overfitting. Baselines provide a way to measure if LLMs are truly reasoning or just simulating. However, I believe the *first* step is ensuring the *state space is correctly represented*, which underpins both the baseline approach and the simulation detection analysis.
*   **Questions:**
    1.  Regarding the mitigation for deterministic overfitting, how feasible is a "black-box validation matches" approach where combat logic is genuinely hidden from the model? What constraints does this impose on the benchmark design?
    2.  In the "simulation detection" analysis, how is the outcome predictability measured? Is it by training a separate model to predict results based on build descriptions, and then checking if the LLM achieves high accuracy?

### kimi-k2-thinking:cloud's Critique (11.1s, $0.0000)

**Critique of Fellow Panelists**

**claude-opus-4-6**
*Agreement:* Rightfully prioritizes verifiability—open-sourcing the combat engine is essential for trust. The degenerate meta-game risk is real and well-articulated; tying it to contamination resistance is sharp.

*Disagreement:* While reproducibility matters, open-sourcing alone doesn't validate strategic depth. My baseline validation suite is more urgent: if a simple heuristic beats LLMs, the benchmark is broken regardless of transparency. Also, open-sourcing might *accelerate* the simulation reverse-engineering risk I flagged, creating a paradox.

*Question:* Would you accept a closed-source engine if it came with cryptographic proofs of correct execution, or is source code access non-negotiable?

---

**gpt-5.4**
*Agreement:* Excellent framing of external validity and the "credibility card" for prompt sensitivity is more actionable than PSI alone. The focus on solved baselines aligns perfectly with my improvement proposal.

*Disagreement:* You identify prompt sensitivity as the biggest risk, but I argue simulation reverse-engineering is more catastrophic. Prompt artifacts are measurable and fixable; a model implicitly learning the combat function is undetectable and invalidates the *entire* contamination-resistant premise.

*Question:* How would you distinguish between a model that's "prompt-sensitive" versus one that's internally simulating matchups and adjusting its reasoning trace to hide it?

---

**gemini-3.1-pro-preview**
*Agreement:* Strong emphasis on non-LLM baselines—this is the highest-impact improvement. Anchoring the BT scale with algorithmic floors/ceilings provides objective context that relative LLM rankings cannot.

*Disagreement:* If MCTS *truly* solves the game to optimality, that proves the benchmark is too simple, not that MCTS is a useful ceiling. The risk isn't just a degenerate meta-game but that the entire 18k-build space is computationally tractable. Also, your "intransitive meta-game" test is necessary but insufficient—dominance can be subtle, distributed across many builds.

*Question:* If your MCTS baseline achieves 95% winrate against the LLM population, do you retire the benchmark or just report that LLMs are bad at reasoning?

---

**deepseek-r1:latest**
*Agreement:* Correctly identifies that six animals may limit strategic depth.

*Disagreement:* Expanding the roster is the *wrong* priority for Season 1. The FAQ explicitly justifies six animals for single-turn prompt constraints; adding complexity before validating core mechanics is premature optimization. Your contamination risk is also weakest—"incidental exposure" to similar mechanics is speculative and less verifiable than the concrete risks others raised.

*Question:* Given your contamination concern, how would you audit models trained on web-scale data for exposure to "combinatorial game-like structures" without false positives?

---

**Reflection on My Own Position**
Seeing gpt-5.4's "credibility card," I've refined my view: prompt sensitivity is a *measurement* risk, but simulation reverse-engineering is a *validity* risk—the latter is existential. I still hold that baseline validation is the highest priority, but I'd now bundle it with mandatory prompt-robustness reporting. If forced to choose one improvement, I'd stick with my baseline suite, but I'd adopt gpt-5.4's credibility card as a required complement.

---

## Phase 3: Moderator's Synthesis

*Synthesized by claude-opus-4-6 (48.9s, $0.2855)*

# MOREAU ARENA SEASON 1: COUNCIL SYNTHESIS

## 1. CONSENSUS POINTS

**Near-unanimous agreement emerged on the following:**

- **Strategic degeneracy is a first-order threat.** Four of five panelists (claude-opus-4-6, gpt-5.4, gemini-3.1-pro-preview, kimi-k2-thinking) independently identified the risk that the ~18,000-build space may collapse into a dominant strategy or trivially shallow equilibrium. All agreed this would fatally undermine Moreau's core claim of measuring strategic reasoning rather than pattern-matching or luck.

- **Non-LLM algorithmic baselines are essential.** All panelists except deepseek-r1 explicitly called for algorithmic floor/ceiling agents (Random, Greedy, exhaustive search) in the Bradley-Terry leaderboard. Without these anchors, a relative LLM-only ranking creates an illusion of competence — the top-ranked model may simply be "least bad" rather than genuinely strategic.

- **Open-sourcing the combat engine is a credibility prerequisite.** claude-opus-4-6 made this case most forcefully, and gemini-3.1-pro-preview explicitly changed position to agree. The reproducibility guarantee is hollow if the resolver cannot be independently executed. gpt-5.4 and kimi-k2-thinking endorsed this as part of a broader artifact release.

- **Expanding the animal roster is premature for Season 1.** Four panelists pushed back against deepseek-r1's expansion proposal. The seasonal model exists precisely so roster changes happen in future seasons after the current config is validated. Changing variables before understanding the existing space undermines the frozen-config principle.

- **Prompt sensitivity, while addressed by PSI, needs deeper validation than a single metric.** gpt-5.4's "credibility card" concept — testing stability across output formats, token budgets, reasoning-hidden variants, and temperature — was broadly endorsed as going meaningfully beyond PSI alone.

## 2. KEY DISAGREEMENTS

**A. What is the single biggest risk?**

| Position | Panelists | Core Argument |
|---|---|---|
| Strategic degeneracy / dominant strategy | claude-opus-4-6, gemini-3.1-pro-preview, deepseek-r1 (partial) | A shallow game invalidates the benchmark permanently; contamination resistance evaporates after Season 1 surfaces the optimal build. |
| Prompt/interface sensitivity | gpt-5.4 | Novel game ≠ valid reasoning measure; single-turn elicitation may primarily measure compliance and formatting, not strategy. |
| Deterministic simulation reverse-engineering | kimi-k2-thinking | Models could implicitly learn the compact combat function, transforming a reasoning test into memorization of a small state space. |

**Resolution after critique:** The degeneracy risk attracted the strongest convergence. gpt-5.4 acknowledged this but maintained prompt sensitivity is underappreciated because PSI gives false confidence. kimi-k2-thinking's simulation risk was challenged by claude-opus-4-6 as implausible for Season 1 (no training data on the engine exists), and kimi-k2-thinking did not fully rebut this. The panel leans toward degeneracy as the existential risk, with prompt sensitivity as a serious but more tractable secondary concern.

**B. What is the highest-priority improvement?**

| Position | Panelists |
|---|---|
| Open-source the engine + publish all artifacts | claude-opus-4-6, gemini-3.1-pro-preview (changed mind) |
| Publish solved baselines + strategic calibration | gpt-5.4, kimi-k2-thinking |
| Non-LLM baselines in BT leaderboard | gemini-3.1-pro-preview (original), kimi-k2-thinking |
| Expand animal roster | deepseek-r1 |

**Resolution after critique:** These are not truly competing — they are components of the same credibility package. Open-sourcing the engine *enables* baselines and equilibrium analysis. Baselines *require* the engine. Both are needed. The disagreement is about sequencing and emphasis, not substance.

**C. What solver methodology is appropriate?**

claude-opus-4-6 argued that brute-force exhaustive enumeration is computationally feasible for ~18,000 builds and should replace approximate methods like MCTS. gemini-3.1-pro-preview proposed MCTS/self-play RL. kimi-k2-thinking noted that if MCTS solves the game easily, that itself proves the benchmark is too shallow. gpt-5.4 favored best-response oracles and exploitability metrics over raw win-rate calculations. The panel leans toward exhaustive methods where feasible, with exploitability as the key diagnostic metric.

**D. Is "simulation reverse-engineering" a real Season 1 risk?**

kimi-k2-thinking raised this uniquely; claude-opus-4-6 and gpt-5.4 both pushed back, arguing it requires training data that doesn't exist for Season 1. kimi-k2-thinking's concern may be more relevant to later seasons when engine code and match data are public. The panel does not reach consensus on this being a Season 1 priority, but acknowledges it as a design consideration for Season 2+.

## 3. STRONGEST ARGUMENTS

**1. claude-opus-4-6 on open-sourcing as the foundation:**
> "Every other credibility claim — contamination resistance, prompt robustness via PSI, Bradley-Terry over Elo — is downstream of whether people believe the combat outcomes are correctly computed and honestly reported."

This is the strongest framing because it correctly identifies that verifiability is not one improvement among many — it is the precondition for all other credibility claims. No amount of statistical sophistication matters if outcomes can't be independently confirmed.

**2. gemini-3.1-pro-preview on algorithmic baselines as interpretive anchors:**
> "If the #1 ranked model ranks below a simple Greedy algorithm, we know the models are failing at fundamental game-theoretic reasoning. Without programmatic anchors, a relative LLM-only leaderboard creates an illusion of strategic competence."

This reframes baselines not as a nice-to-have but as the interpretive key that makes the entire leaderboard meaningful. It shifts the conversation from "which LLM is best" to "are LLMs doing this task at all."

**3. gpt-5.4 on the credibility card:**
> "Contamination resistance can create a false sense of security: 'novel game' does not imply 'valid reasoning measure.'"

This is a subtle and important point that other panelists underappreciated. The benchmark's marketing around contamination resistance could mask fundamental measurement problems. The credibility card concept is the most operationally specific mitigation proposed for prompt sensitivity.

**4. claude-opus-4-6 on brute-force feasibility:**
The observation that ~18,000 builds makes exhaustive analysis computationally trivial is an underappreciated insight. It means there is *no excuse* for not computing the exact Nash equilibrium and full matchup matrix before launch. Approximate methods are unnecessary when exact solutions are tractable.

**5. kimi-k2-thinking on the "validity threshold" concept:**
> "Any LLM that doesn't significantly outperform heuristics fails the validity threshold and is marked 'unverified.'"

This converts the baseline idea into a concrete, enforceable standard rather than a background reference point.

## 4. SYNTHESIS: INTEGRATED ANSWER

### Highest-Priority Improvement: Release a Complete Strategic Validity Package

The single highest-priority improvement is not any one artifact but the integrated release of three tightly coupled components *before* Season 1 results are published:

1. **Open-source the deterministic combat engine** under a permissive license, including all movement AI, damage formulas, closing ring mechanics, and tile logic. Include the frozen config, all match seeds, and JSONL build logs. This is the verifiability foundation without which no other claim holds.

2. **Compute and publish the exact Nash equilibrium** of the Season 1 metagame via exhaustive pairwise evaluation of all ~18,000 builds. With deterministic resolution, this is computationally feasible (roughly 162 million matchups, each resolvable in milliseconds). Report: the equilibrium support size, exploitability of top builds, and whether the equilibrium is mixed over a diverse set of builds or concentrated on a narrow cluster. If a single build achieves >70% field win rate or the equilibrium support is ≤3 builds, the config must be rebalanced before publication.

3. **Embed non-LLM baselines into

---

## Phase 4: Votes

### claude-opus-4-6 (13.7s, $0.0756)

- **Proposition 1**: AGREE — Strategic degeneracy is indeed the existential threat; a solved or trivially shallow game cannot be rescued by better statistics or prompt engineering.
- **Proposition 2**: AGREE — Non-LLM algorithmic baselines are the interpretive anchors that distinguish "models are reasoning strategically" from "models are generating plausible-looking outputs," and their absence would render the leaderboard meaningless.
- **Proposition 3**: AGREE — I made this case most forcefully and stand by it: open-sourcing the combat engine is the verifiability foundation on which every other credibility claim depends.
- **Proposition 4**: AGREE — Expanding the roster before understanding the strategic depth of the current configuration would violate the frozen-config principle and introduce confounds that make Season 1 results uninterpretable.
- **Proposition 5**: AGREE — PSI is a good start but insufficient on its own; the credibility card concept correctly identifies that format sensitivity, token budget effects, and temperature variation are orthogonal failure modes that PSI doesn't capture.
- **Proposition 6**: AGREE — The synthesis correctly identifies degeneracy as the existential risk while acknowledging prompt sensitivity as serious but more tractable; kimi-k2-thinking's simulation reverse-engineering concern is a valid Season 2+ consideration but not a plausible Season 1 threat given the absence of training data.
- **Proposition 7**: AGREE — These improvements are components of a single credibility package rather than competing priorities, and open-sourcing enables everything else; the disagreement is about sequencing, not substance.
- **Proposition 8**: AGREE — Exhaustive enumeration is computationally trivial at ~18,000 builds and should be preferred over approximate methods; there is genuinely no excuse for not computing the exact Nash equilibrium when the state space is this small.
- **Proposition 9**: AGREE — The validity threshold concept transforms baselines from passive reference points into enforceable standards, which is the correct operationalization.
- **Proposition 10**: AGREE — The integrated three-component Strategic Validity Package (open-source engine, exact Nash equilibrium computation, embedded non-LLM baselines) is the right synthesis because these are mutually enabling rather than independent improvements.

### gpt-5.4 (3.2s, $0.0063)

- **Proposition 1**: AGREE — Open-sourcing the deterministic combat engine and full artifacts is the necessary foundation for reproducibility, auditing, and trust in every downstream claim.
- **Proposition 2**: AGREE — Exhaustive evaluation of the ~18,000-build space and publication of equilibrium/exploitability diagnostics are the clearest way to test whether the benchmark is strategically non-degenerate.
- **Proposition 3**: AGREE — Non-LLM algorithmic baselines must be embedded in the leaderboard because otherwise relative LLM rankings are not interpretable as evidence of genuine strategic competence.

### gemini-3.1-pro-preview (11.1s, $0.0033)

- **Proposition 1**: AGREE — Open-sourcing the combat engine is the absolute prerequisite for verifiability, ensuring the community can independently reproduce our results and trust the resolution mechanics.
- **Proposition 2**: AGREE — Since exhaustive evaluation of the ~18,000 build space is computationally trivial, calculating the exact Nash equilibrium is the most rigorous way to guarantee the metagame is not strategically degenerate before launch.
- **Proposition 3**: AGREE — Embedding non-LLM algorithmic baselines directly into the leaderboard is essential to prove whether models are actually exhibiting strategic reasoning or merely performing as the "least bad" random selectors.

### grok-4-1-fast-reasoning (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

xai

### deepseek-r1:latest (33.9s, $0.0000)

- **Proposition 1**: AGREE — This is the foundation upon which all other credibility claims rest, as verifiable outcomes are essential for independent confirmation.
- **Proposition 2**: AGREE — These anchors prevent a relative ranking from creating an illusion of strategic competence and provide critical interpretive context for the leaderboard.
- **Proposition 3**: AGREE — Embedding the baselines as part of the engine ensures they are the ground truth against which models are evaluated, fulfilling the "validity threshold" concept.

### kimi-k2-thinking:cloud (24.7s, $0.0000)

- **Proposition 1**: AGREE — Verifiability is indeed the foundation; without it, statistical sophistication is meaningless theater.
- **Proposition 2**: AGREE — Baselines transform the leaderboard from a beauty contest into a diagnostic tool measuring actual reasoning.
- **Proposition 3**: AGREE — PSI alone is insufficient; the credibility card's multi-dimensional stress testing is necessary for confidence.
- **Proposition 4**: AGREE — The ~18,000 build space is small enough for exhaustive analysis, making approximation methods indefensible.
- **Proposition 5**: AGREE — My validity threshold concept ensures baselines aren't just references but enforceable pass/fail criteria.
- **Proposition 6**: AGREE — Engine open-sourcing must come first; it's the enabling infrastructure for all other validity measures.
- **Proposition 7**: AGREE — Computing the exact Nash equilibrium is feasible and mandatory to prove the space isn't degenerate.
- **Proposition 8**: AGREE — Baselines must be visibly embedded in the BT leaderboard, not hidden in appendixes, to prevent misinterpretation.

---

## Cost Summary

**Total: $0.6158**

| Model | Cost |
|-------|------|
| claude-opus-4-6 | $0.5711 |
| gpt-5.4 | $0.0314 |
| gemini-3.1-pro-preview | $0.0133 |
| grok-4-1-fast-reasoning | $0.0000 |
| deepseek-r1:latest | $0.0000 |
| kimi-k2-thinking:cloud | $0.0000 |
