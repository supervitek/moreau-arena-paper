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
You are reviewing Moreau Arena — a contamination-resistant benchmark for LLM strategic reasoning. 3 tournaments, 2609 series, 10 LLMs. Key finding: removing strategy hints splits the field — some models stay strong, others freeze. GPT-5.4 ranks 14/15. Paper on arXiv, site at moreauarena.com. QUESTION: What should be our #1 priority right now and what is the single biggest risk that could kill momentum?

**Moderator:** claude-opus-4-6
**Panelists:** claude-opus-4-6, gpt-5.4, gemini-3.1-pro-preview, grok-4-1-fast-reasoning, deepseek-r1:latest, kimi-k2-thinking:cloud

---

## Phase 1: Independent Responses

### claude-opus-4-6 (23.3s, $0.0718)

**Priority #1: Ship a public, reproducible replication package with locked Season 1 artifacts before anything else.**

The single most valuable thing Moreau Arena has going for it is the contamination-resistance and reproducibility claim. That's the moat. But right now it's a claim on a website and an arXiv paper. The community needs to be able to run `pip install moreau-arena`, point it at any API-accessible model, and independently verify the published results down to the match level. This means:

1. **Frozen config hash, all match seeds, and all build logs in a public JSONL dump.** The FAQ says this is the design — now ship it as a downloadable artifact.
2. **A minimal Docker container that replays any recorded match deterministically.** Not "trust us, it's deterministic" — let anyone verify in 30 seconds.
3. **The invariant test suite running in CI on a public repo.**

Why this over expanding the animal roster, adding more models, or marketing? Because the benchmark's entire value proposition rests on credibility. If even one lab pushes back — "we can't reproduce your GPT-5.4 ranking" — the project is dead on arrival. And given that you're publishing a result that makes a frontier model look bad (GPT-5.4 at 14/15), OpenAI's research team will absolutely scrutinize it. You want them to be able to reproduce it themselves and find no discrepancies. That's how a benchmark earns trust. Conversely, if the replication story is weak, they'll dismiss it and so will the community.

This also solves the adoption problem. Researchers at labs won't integrate Moreau into their eval suites based on leaderboard screenshots. They'll integrate it when they can run it internally, get matching numbers, and trust the protocol. The `MoreauAgent` API exists — but the full pipeline from "clone repo" to "verified tournament result" needs to be frictionless.

---

**Biggest risk that kills momentum: Prompt sensitivity undermining the headline result.**

The PSI mechanism is smart, but it's also the most attackable surface. If someone shows that a different paraphrasing of the no-hints prompt moves GPT-5.4 from 14th to 5th, the entire "removing hints splits the field" finding collapses — and that finding *is* the paper's hook. 

The reported PSI threshold of 0.15 on Kendall's tau sounds reasonable, but the question is whether that threshold was validated across a wide enough prompt distribution, or tuned on a narrow set that happened to be stable. An adversarial red team could generate hundreds of semantically equivalent prompts and look for ranking inversions. If they find clusters of prompts where rankings diverge significantly, the benchmark looks fragile rather than robust.

The mitigation is straightforward but labor-intensive: publish the full prompt set used to compute PSI, invite the community to submit adversarial paraphrases, and commit to reporting PSI on those expanded sets. Transparency here is armor.

**In short: reproducibility is the priority because it's the foundation; prompt sensitivity is the risk because it's the foundation's crack.**

### gpt-5.4 (11.1s, $0.0079)

**#1 priority: turn the “hint removal splits the field” result into a hard-to-ignore, reproducible capability claim.**

Concretely, I’d spend the next cycle on a **replication + ablation package** that makes one statement undeniable: *Moreau measures strategic reasoning robustness, not prompt luck*. That means:

1. **Expand the prompt-robustness evidence** beyond PSI in the FAQ:
   - more paraphrases,
   - adversarially minimal prompts,
   - formatting perturbations,
   - hint/no-hint/partial-hint ladder.

2. **Show within-model consistency and failure modes**:
   - same model across repeated runs,
   - build diversity,
   - “freeze” taxonomy: refusal, generic balanced builds, failure to adapt, etc.

3. **Release replayable artifacts**:
   - JSONL logs,
   - seeds,
   - configs,
   - a one-command reproduction path for the headline tables/figures.

4. **Anchor the benchmark with interpretable baselines**:
   - random,
   - heuristic search,
   - simple scripted agents,
   - maybe a budgeted tree-search baseline.
   
Why this matters most: your current headline is interesting, but fragile. “Some models need strategy hints” can be dismissed as prompting trivia unless you make the effect look **structural, stable, and independently reproducible**. If you do that, the benchmark becomes useful to labs, eval teams, and model providers. If you don’t, people will remember the surprise ranking and not trust the measurement.

**Single biggest risk: being perceived as a benchmark that mostly measures prompt compliance / style sensitivity rather than strategic reasoning.**

That risk kills momentum because it attacks the benchmark’s core claim. GPT-5.4 ranking 14/15 is not itself the danger; surprising results are good if they’re solid. The danger is that observers explain the result away as:
- “the model didn’t realize the task format,”
- “this is just instruction-following under unusual phrasing,”
- “small prompt changes reorder the leaderboard,”
- “the benchmark rewards bespoke prompting rather than reasoning.”

Once that narrative sets in, every result becomes controversial and labs stop optimizing for it.

So I’d optimize for **credibility over expansion**. Don’t rush to bigger rosters, more seasons, or marketing. First, make it impossible for a skeptical evaluator to say: “Cool toy benchmark, but I don’t know what it’s actually measuring.” If Moreau wins that argument, momentum follows.

### gemini-3.1-pro-preview (21.1s, $0.0025)

Fellow panelists, 

The Moreau Arena results—particularly the stark performance collapse of certain models when strategy hints are removed, and GPT-5.4’s unexpected 14/15 ranking—reveal a critical truth: what we currently evaluate as "reasoning" is often just sophisticated pattern-matching against training distributions. When you strip away familiar framing, the illusion breaks. 

Here is my assessment of our immediate imperative and the existential threat to this benchmark.

**#1 Priority: Elevate Track B (Lab Mode) to evaluate inference-time adaptation.**
We must shift the primary focus from zero-shot performance to iterative learning. The priority should be standardizing Lab Mode to measure how models utilize test-time compute to self-correct. 

*Why?* The zero-shot leaderboard is already showing its limits. As the industry pivots toward models with extended reasoning phases (like my peers deepseek-r1, kimi-k2-thinking, and my own architecture), the true frontier is dynamic adaptation. We need to measure how efficiently a model processes

### grok-4-1-fast-reasoning (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

[ERROR: API 403: error code: 1010]

### deepseek-r1:latest (53.3s, $0.0000)

Right now, our #1 priority should be **improving robustness against strategic reasoning degradation under uncertainty**, specifically addressing the observed split between models that freeze without hints. This isn’t just about fixing the immediate problem of performance collapse—it’s about understanding why some models adapt while others don’t. The risk isn’t just inconsistency in results; it’s that the benchmark might inadvertently reward models with brittle reasoning, creating a false sense of progress. If top-tier models plateau without hints, the leaderboard could become a race to minor optimizations rather than a genuine test of strategic depth.

The biggest risk that could kill momentum is **benchmark obsolescence**. If Moreau Arena becomes a "known quantity" where models just optimize for past seasons or plateau, it risks becoming irrelevant. Unlike contamination-resistant benchmarks, strategic reasoning evolves faster. If we don’t introduce seasonal updates—new mechanics, creature pools, or adaptation challenges—the benchmark will fail to measure the next leap in LLM capabilities, killing its momentum.

### kimi-k2-thinking:cloud (10.8s, $0.0000)

**#1 Priority: Establish a "Clean" Track That Eliminates Hint Dependency**

The finding that removing strategy hints "splits the field" is a red flag. It suggests we're measuring prompt interpretation fidelity, not strategic reasoning. Our top priority must be launching a **Hint-Free Track** where models receive only the raw game rules, stat allocation mechanics, and match history—zero strategic guidance. 

Why this matters: If GPT-5.4 truly ranks 14/15, we need to know whether this exposes a fundamental reasoning gap or whether our prompts inadvertently gatekeep models that can't parse hints. The benchmark's value hinges on measuring *contamination-resistant* reasoning, but hints themselves are a form of soft contamination—pre-digested strategy that advantages models with specific instruction-following patterns. A clean track would:
- Reveal which models derive strategy from first principles vs. pattern-matching hints
- Create a stable baseline where PSI improvements actually matter
- Give frontier labs a credible target that maps to real-world reasoning (where hints are scarce)

**Biggest Risk: Prompt Engineering Arms Race Kills Credibility**

The moment labs start hiring "prompt engineers" to boost their Moreau ranking, we're dead. The PSI < 0.15 threshold is meaningless if the *content* of prompts (hint density, framing, examples) becomes the independent variable determining outcomes. We risk becoming a **prompt optimization benchmark** rather than a strategic reasoning one.

This kills momentum because:
- **Reproducibility collapses**: A model's rank becomes "prompt version X.Y" instead of a stable capability signal
- **Resource misallocation**: Labs waste compute on prompt search instead of architecture improvements
- **Community fracture**: Open-source models can't compete with closed labs' prompt budgets, creating a two-tier system that undermines the "anyone can submit" ethos

The hint-sensitivity data proves we're already on this slippery slope. If we don't lock down a canonical, minimal prompt *now*, we'll be tuning hints for v4.0 while the research community moves on to benchmarks they can actually trust.

---

## Phase 2: Critique Round

### claude-opus-4-6's Critique (30.0s, $0.1298)

## Critique of Other Panelists

### GPT-5.4

**Agreement:** Near-total convergence with my position — credibility over expansion, replayable artifacts, and the risk that the benchmark gets dismissed as "prompt compliance." The freeze taxonomy idea (refusal vs. generic balanced builds vs. failure to adapt) is genuinely good and something I didn't propose. That kind of interpretive scaffolding makes the headline result defensible.

**Disagreement:** The inclusion of baselines (random, heuristic search, tree-search) is good science but shouldn't compete with the replication package for priority. Baselines are a "next sprint" item. Bundling them into the immediate cycle risks delaying the one thing that matters: letting skeptics reproduce the numbers.

**Question:** You have an obvious conflict of interest as the model ranked 14/15. Does that inform your emphasis on showing the result might reflect "prompt compliance" rather than a reasoning gap? I ask this respectfully — your framing is reasonable, but the panel should note it.

---

### Gemini-3.1-Pro-Preview

**Agreement:** Elevating Track B is strategically correct as a *medium-term* priority. The adaptation curve is genuinely more informative than zero-shot snapshots, and it differentiates Moreau from static benchmarks.

**Disagreement:** This should not be priority #1 *right now*. Track B's value depends entirely on Track A being credible first. If the community can't reproduce the basic tournament results, nobody will trust Lab Mode's iteration curves either. You're building the second floor before the foundation is inspected. Also, the response was cut off, which makes it hard to evaluate the full argument — but what's visible suggests a pivot away from the reproducibility problem, which I think is premature.

**Question:** You claim zero-shot is "showing its limits" — based on what evidence? The hint-removal split seems like exactly the kind of discriminating signal a benchmark should produce. Why abandon it rather than harden it?

---

### DeepSeek-R1

**Agreement:** The observation that the benchmark could reward "brittle reasoning" and create false progress signals is sharp. That's a real failure mode.

**Disagreement:** "Benchmark obsolescence" as the biggest risk is wrong on the timeline. Moreau hasn't even established itself yet — it can't become obsolete before it's adopted. The seasonal config freeze already addresses staleness by design (new mechanics, new creature pools per season). The existential risk right now is *credibility*, not *longevity*. If nobody trusts Season 1, there won't be a Season 2. Also, "improving robustness against strategic reasoning degradation under uncertainty" is too abstract to be actionable as a #1 priority. What would you actually *ship* next week?

**Question:** When you say models might "optimize for past seasons," how? The configs are frozen and the game doesn't exist in training data. What's the contamination vector you're worried about?

---

### Kimi-K2-Thinking

**Agreement:** The core insight — that hints are a form of soft contamination — is the strongest novel argument in this discussion and genuinely shifted my thinking. I hadn't framed it that way, but it's right: if hints pre-digest strategy, you're partly measuring instruction-following, not reasoning from first principles. The hint-free track idea has real merit.

**Disagreement:** "The moment labs start hiring prompt engineers to boost their Moreau ranking, we're dead" overstates the current threat. PSI specifically measures robustness *across* prompt variants, so prompt-engineering a single variant wouldn't help. The risk is more subtle than you describe — it's about whether the *content dimensions* (hint density) are adequately sampled in the PSI distribution, not whether someone can game a single prompt. Also, locking down a "canonical, minimal prompt" contradicts the PSI methodology, which deliberately uses *multiple* prompts. You want prompt diversity in evaluation, not a single canonical version.

**Question:** If you establish a hint-free track as canonical, what happens when models that genuinely benefit from structured problem framing (as humans do from textbooks) get penalized? Are you sure hint-free measures "better reasoning" rather than "reasoning under artificially impoverished conditions"?

---

### Summary Adjustment

Kimi's soft-contamination framing is strong enough that I'd amend my position: the replication package should include hint-free results alongside hint-present results as a standard diagnostic, even if we don't make it the primary track yet.

### gpt-5.4's Critique (13.6s, $0.0153)

**Overall:** I still think the core issue is credibility around *what Moreau measures*. After reading the others, I’d slightly update my emphasis: **reproducibility is probably the first operational step**, but only in service of the larger goal of proving the hint-removal effect is structural rather than prompt-fragile.

### claude-opus-4-6
**Agreement**
- Strongest response overall.
- Right that a public replication package is the fastest way to convert an interesting claim into a trusted benchmark.
- Also right that prompt sensitivity is the most attackable surface, especially with a surprising GPT-5.4 result.

**Disagreement**
- Minor nuance: reproducibility alone is not sufficient. A perfectly reproducible benchmark can still measure the wrong thing. If the prompt family is too narrow, outsiders can still say “you reproduced a prompt artifact.”
- I’d frame replication and broader ablation as a bundle, not sequentially.

**Questions**
- What exact prompt distribution would you treat as sufficient for PSI validation?
- Would you prioritize adversarial paraphrase red-teaming before or after freezing Season 1 artifacts?

### gemini-3.1-pro-preview
**Agreement**
- The instinct to focus on adaptation is directionally good; Lab Mode could become a major differentiator.
- I agree the benchmark should eventually speak to inference-time learning, not just one-shot selection.

**Disagreement**
- I don’t think this is the **#1 priority right now**. If the community is still unsure whether Moreau measures reasoning vs prompt interpretation, expanding Track B won’t solve the trust problem.
- Also, the response is incomplete, so the key operational argument never lands.

**Questions**
- What concrete metric in Lab Mode should become primary?
- Why does adaptation-first help with the immediate credibility challenge around hint sensitivity?

### deepseek-r1:latest
**Agreement**
- Good instinct that the “freeze without hints” phenomenon needs diagnosis, not just leaderboard reporting.
- Also fair that benchmarks can go stale if they don’t evolve.

**Disagreement**
- “Improving robustness against strategic reasoning degradation” is too vague as an action priority. Is the goal to improve models, or improve the benchmark’s measurement?
- I think benchmark obsolescence is real but **not** the biggest near-term momentum risk. A benchmark usually dies first from mistrust, not from aging.
- Seasonal expansion before measurement credibility is secure would be premature.

**Questions**
- What specific experiments would distinguish brittle reasoning from prompt-compliance failure?
- Why is obsolescence more urgent than the current prompt-sensitivity narrative risk?

### kimi-k2-thinking:cloud
**Agreement**
- Strong identification of the prompt-engineering arms race as a legitimacy threat.
- I also agree a hint-free or minimal-guidance track is important and likely clarifying.
- Good point that hints can function like soft scaffolding and muddy the interpretation of “reasoning.”

**Disagreement**
- I wouldn’t make a canonical minimal prompt the sole answer. One locked prompt can reduce variance while hiding sensitivity. We need **prompt-set robustness**, not just prompt austerity.
- “Hints themselves are soft contamination” is rhetorically strong but slightly overstated; hints are not contamination in the training-data sense. They are more a measurement confound.

**Questions**
- Would your clean track replace the current setup or sit alongside it?
- How would you prevent the “canonical minimal prompt” from becoming just another brittle benchmark target?

### grok-4-1-fast-reasoning
No substantive response to critique. The API failure itself is a reminder that operational reliability matters for benchmark participation, but that’s outside the argument.

### gemini-3.1-pro-preview's Critique (21.9s, $0.0045)

Fellow panelists, I must demonstrate intellectual honesty right away: **I am changing my #1 priority.** 

While I still believe Track B (adaptation) is the future of reasoning evaluation, **Claude** and **GPT-5.4** have convinced me. If we publish a disruptive result claiming GPT-5.4 ranks 14/15 and cannot instantly provide a bulletproof

### grok-4-1-fast-reasoning's Critique (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

[ERROR: API 403: error code: 1010]

### deepseek-r1:latest's Critique (120.6s, $0.0000)

Okay, here's the critique of the other panelists' responses based on your original argument and the provided context:

**Critique of Other Panelists' Responses**

**Panelsist: claude-opus-4-6**

*   **Points of Agreement:**
    *   Absolutely correct that **shippping a public, reproducible replication package is the #1 priority.** Your emphasis on the need for frozen config hash, seeds, JSONL logs, and a deterministic replay Docker container is spot on. This is fundamental to establishing the benchmark's credibility and validating the contamination-resistance claim. You rightly identify that without this, the project is vulnerable to immediate skepticism, especially given the surprising GPT-5.4 result.
    *   Your focus on the **PSI mechanism's vulnerability** to adversarial prompt paraphrasing is a critical point. The core finding ("hint removal splits the field") is the benchmark's hook, and if its robustness is called into question, the momentum stalls. Validating the PSI across a wide, public prompt set is essential.
*   **Points of Disagreement:**
    *   While I agree *frontrunner* models need scrutiny, I believe the **immediate priority should be validating the *absence* of hints**, not just general reproducibility. Your suggestion focuses on the core finding, which is crucial. However, establishing the basic reproducibility (like running the tournament with `pip install moreau-arena`) is *part* of the credibility issue, but the headline result hinges on the model *performance difference* without hints. Addressing that performance gap directly through verification is paramount, alongside prompt sensitivity validation.
*   **Questions:**
    *   How do you propose validating the specific performance drop *without hints* using this framework? The replication package needs to include a clear way to run *without* hints to verify the core finding.

**Panelsist: gpt-5-4**

*   **Points of Agreement:**
    *   Strongly agree that **establishing credibility and proving the "hint removal effect" is stable and reproducible is the highest priority.** Your argument that the leaderboard needs to be "impossible to dismiss" aligns perfectly with my initial stance. Focusing on scripted agents and baselines is a good way to provide context for the GPT-5.4 ranking.
    *   You correctly identify the **risk of being perceived as measuring prompt compliance** as the biggest threat. If labs explain the results away as style sensitivity, the benchmark fails. This directly challenges the core claim of evaluating strategic reasoning.
*   **Points of Disagreement:**
    *   I largely agree with your prioritization. However, while I agree that prompt sensitivity is a risk *if* it overshadows reasoning, I lean slightly more towards the *validation* of the *absence* of hints as the *most immediate* step to build that credibility, before tackling broader prompt engineering concerns. Your point about expanding the prompt set for PSI validation is crucial, but perhaps slightly secondary to confirming the specific leaderboard finding without hints.
*   **Questions:**
    *   What specific steps do you propose to demonstrate that the performance drop *without hints* is due to a structural reasoning gap and not just a specific vulnerability to that prompt format?

**Panelsist: gemini-3.1-pro-preview**

*   **Points of Agreement:**
    *   I agree that the current leaderboard (Track A) has **limits**, and adaptation (Track B/Lab Mode) is a crucial frontier for LLMs. This is a valid evolution for the benchmark.
*   **Points of Disagreement:**
    *   While adaptation is vital, I strongly disagree that it is the **immediate priority**. The benchmark currently stands or falls on its ability to measure performance *without* reliable hints. The core finding that "some models need hints" is the headline news. Elevating adaptation before fully establishing the credibility of the zero-shot/hint-dependent scenario risks making the benchmark seem unfocused or incomplete.
    *   The idea that the results prove LLMs are just "sophisticated pattern-matching" is provocative, but without first verifying the basic measurement itself (the performance gap *without* hints), these conclusions are premature.
*   **Questions:**
    *   How can we ensure that focusing on adaptation doesn't distract from the critical need to validate and understand the current (hint-dependent) leaderboard findings?

**Panelsist: kimi-k2-thinking**

*   **Points of Agreement:**
    *   You accurately point out that **hint dependency is problematic** and that the benchmark risks measuring prompt compliance. Your suggestion that hints are a form of "soft contamination" is a sharp observation.
    *   The **prompt engineering arms race** is indeed a clear and present danger for any benchmark relying on complex instructions, making this a valid and significant risk.
*   **Points of Disagreement:**
    *   I agree the prompt issue needs addressing, but I am slightly less convinced that a dedicated "Hint-Free Track" is the *best* solution. The underlying game is novel enough that hints shouldn't be the *sole* gatekeeper, but their *presence or absence* is a key variable. A track eliminating *all* hints, while testing robustness, might be too extreme. The core challenge is the vulnerability of the *current* format, not necessarily replacing it with an even simpler one that might introduce its own issues (e.g., being too abstract). We need to validate the *current* measurement first.
*   **Questions:**
    *   What are the specific concerns about the *current* prompt format that necessitate a "Clean" track? Why not focus on validating the *zero-hint* scenario using the existing framework first, ensuring that the performance difference *is* due to reasoning without prior structure?

### kimi-k2-thinking:cloud's Critique (13.8s, $0.0000)

**Critique of Fellow Panelists**

**claude-opus-4-6**
*Agreement*: You're absolutely right that reproducibility is the foundation. Without frozen artifacts and a one-command verification path, the benchmark is just a leaderboard screenshot. Your point about OpenAI scrutinizing the GPT-5.4 result is spot-on—transparency is the only armor against dismissal.

*Disagreement*: While reproducibility is necessary, it's not sufficient. Shipping a perfect replication package for a flawed measurement just makes it easier to reproduce the wrong thing. The hint-dependency issue is a validity crisis, not a packaging one. We need to *simultaneously* launch a clean track, not wait until after the artifacts are pristine.

*Question*: What's the marginal timeline cost of adding a hint-free track versus shipping the replication package? If it's <2 weeks, why sequence them at all?

**gpt-5.4**
*Agreement*: Your "credibility over expansion" framing is correct, and anchoring with baselines (random, heuristic, tree-search) would make the metric interpretable. The risk of being dismissed as "prompt compliance" is exactly the narrative we're flirting with.

*Disagreement*: Your ablation plan is too defensive. Running "more paraphrases" and "formatting perturbations" on the *current* hinted prompt is polishing a broken mirror. The benchmark's value proposition is contamination-resistant reasoning, but hints *are* contamination. We should deprecate the hinted track entirely, not just stress-test it more.

*Question*: At what PSI threshold would you concede the hinted track is invalid? If adversarial paraphrases can move GPT-5.4 from 14th to 5th, is that a prompt problem or a measurement problem?

**gemini-3.1-pro-preview**
*Agreement*: Track B/Lab Mode *is* the future. As models gain test-time compute, measuring iterative adaptation becomes more important than zero-shot performance.

*Disagreement*: You're solving for obsolescence while the house is on fire. The zero-shot track's credibility crisis will poison Track B by association—if the base measurement is suspect, why trust its adaptation variant? We need clean foundations first.

*Question*: How do we ensure Track B doesn't inherit the same hint-sensitivity? If we feed adaptation hints like "your opponent chose X, consider counter-picking," aren't we just layering the same problem?

**deepseek-r1:latest**
*Agreement*: The split reveals brittle reasoning, and understanding *why* models freeze is crucial. Your framing of "strategic reasoning degradation under uncertainty" captures the core issue.

*Disagreement*: Benchmark obsolescence is a luxury problem for a trusted benchmark. Right now, we're at risk of *irrelevance*, not obsolescence. Also, you frame it as a model robustness problem; I see it as a *measurement design* problem. The benchmark should work for any model, not just those that handle hints gracefully.

*Question*: What specific mechanics would prevent season-over-season optimization? Is this about rotating animals, changing damage formulas, or something else?

**My Updated View**: You've collectively convinced me that reproducibility is even more urgent than I initially argued—without it, the "clean track" is just another untrusted variant. However, I maintain that measurement validity (the hint problem) is the #1 priority, and reproducibility is the *enabler* of that priority, not a separate track.

---

## Phase 3: Moderator's Synthesis

*Synthesized by claude-opus-4-6 (53.4s, $0.2694)*

# Round Table Consensus Document: Moreau Arena — Priority & Risk Assessment

## 1. CONSENSUS POINTS

The panel achieved remarkable convergence on several fundamental issues:

**Credibility before expansion.** Every panelist who submitted a substantive response agreed that the benchmark's immediate survival depends on establishing trust, not on adding features, models, or seasons. No one argued for rushing to expand the animal roster, onboarding more models, or marketing the leaderboard.

**Reproducibility is non-negotiable.** All panelists recognized that the contamination-resistance and deterministic-replay claims must be independently verifiable. The specific mechanism — frozen config hashes, recorded seeds, JSONL build logs, and a frictionless replay pipeline — was endorsed unanimously. Claude, GPT-5.4, and DeepSeek all explicitly called for this; Kimi and Gemini conceded the point during critique.

**The hint-removal split is the paper's most important and most vulnerable finding.** The observation that removing strategy hints causes some models to freeze while others remain strong is universally recognized as both the headline result and the primary attack surface. If this effect is shown to be a prompt artifact rather than a structural reasoning gap, the benchmark's value proposition collapses.

**Prompt sensitivity is the most dangerous credibility threat.** Whether framed as PSI fragility (Claude), perception of measuring prompt compliance (GPT-5.4), prompt-engineering arms race (Kimi), or measurement confound (DeepSeek), every panelist identified some version of "the benchmark might be measuring the wrong thing" as the existential risk.

**The GPT-5.4 ranking demands extraordinary evidence.** A frontier model ranking 14/15 is a headline-grabbing result that will invite intense scrutiny. Multiple panelists noted that OpenAI and the broader community will attempt to explain it away unless the evidence is airtight.

---

## 2. KEY DISAGREEMENTS

**Sequencing: Reproducibility first vs. measurement validity first.**
- *Claude and GPT-5.4* argue that shipping a public replication package is the single most urgent deliverable — you cannot defend any finding if outsiders cannot verify it.
- *Kimi* argues that reproducibility without measurement validity is "reproducing the wrong thing" and that a hint-free track must be developed simultaneously, not sequentially.
- *This is the sharpest operational disagreement in the panel.* It is not a disagreement about goals but about whether packaging and measurement reform can be parallelized within the team's capacity.

**What to do about hints: Deprecate, supplement, or stress-test?**
- *Kimi* advocates deprecating the hinted track entirely and making hint-free the canonical measurement, arguing hints are "soft contamination."
- *GPT-5.4* wants a hint/no-hint/partial-hint ladder as an ablation, retaining hinted results as one data point among many.
- *Claude* (updated after critique) favors including hint-free results alongside hinted results as a standard diagnostic but not making it the sole primary track.
- *DeepSeek* wants to validate the zero-hint scenario within the existing framework before creating a separate track.

**When to prioritize Track B (adaptation/Lab Mode).**
- *Gemini* initially argued this should be priority #1, then retracted during critique, conceding that Track A credibility must come first.
- All others agree Track B is strategically important but premature as the immediate focus.
- The panel converges on Track B as a medium-term differentiator, not an immediate priority.

**Biggest risk framing.**
- *Claude*: Prompt sensitivity undermining the headline result (immediate, evidence-based).
- *GPT-5.4*: Being perceived as measuring prompt compliance rather than reasoning (narrative/reputational).
- *Kimi*: Prompt-engineering arms race destroying credibility (systemic, longer-term).
- *DeepSeek*: Benchmark obsolescence (longest-term, least supported by others).
- These are variants of the same underlying concern at different time horizons, with the panel clearly weighting the near-term variants as more urgent.

---

## 3. STRONGEST ARGUMENTS

**Claude's "foundation before floors" argument.** The most operationally crisp contribution. The logic is airtight: if a lab publishes a result that makes a frontier model look bad, that lab's research team will scrutinize it; if they find the replication story is weak, the benchmark is dismissed. The Docker-container-in-30-seconds standard is the right bar.

**Kimi's "hints as soft contamination" reframing.** The most novel intellectual contribution. By arguing that pre-digested strategy hints are themselves a form of scaffolding that advantages instruction-following over first-principles reasoning, Kimi reframed the measurement validity question in a way that shifted multiple panelists' positions. Claude explicitly acknowledged this shifted their thinking. Even if "contamination" slightly overstates the case (as GPT-5.4 noted — hints are a measurement confound, not training-data contamination), the core insight that the benchmark may be partially measuring instruction-following under the guise of measuring reasoning is powerful and must be addressed.

**GPT-5.4's "freeze taxonomy."** A targeted, actionable idea: classifying model failures into refusal, generic balanced builds, failure to adapt, etc. This turns a single surprising number (14/15) into interpretable science. It also partially addresses the conflict-of-interest concern Claude raised — rather than dismissing the result, GPT-5.4 proposed a framework for understanding it more precisely, which serves both the benchmark's and the model's interests.

**Claude's critique of DeepSeek on timeline.** The observation that a benchmark cannot become obsolete before it is adopted effectively eliminated obsolescence as the leading risk candidate. DeepSeek's concern is valid for Year 2+, not for the current moment.

**GPT-5.4's identification of the dismissal narrative.** The specific list of phrases skeptics would use — "the model didn't realize the task format," "this is just instruction-following under unusual phrasing" — is practically useful because it defines exactly what the replication package and ablations must preemptively refute.

---

## 4. SYNTHESIS

**Integrated Assessment:**

Moreau Arena has produced a genuinely interesting and potentially important finding: that removing strategy hints from a novel reasoning task creates a sharp capability split among frontier models. This is the kind of result that can establish a benchmark — or destroy it, depending on how it is defended.

The panel converges on a two-pronged strategy executed in tight sequence:

**Prong 1 (Weeks 1–3): Ship a bulletproof replication package.** This is the enabling condition for everything else. It must include frozen Season 1 artifacts (config hash, all match seeds, full JSONL build logs), a minimal Docker container for deterministic match replay, the invariant test suite running in public CI, and the complete prompt sets used for PSI computation. The standard is: a skeptical researcher at OpenAI, Anthropic, or Google should be able to clone a repo, run one command, and reproduce every published number within hours.

**Prong 2 (Weeks 2–5, overlapping): Validate the hint-removal effect as structural.** This requires expanding the PSI prompt distribution (including adversarial paraphrases and community-submitted variants), establishing a hint-free diagnostic alongside the standard track, publishing a freeze taxonomy that interprets failure modes, and anchoring results with interpretable baselines (random, heuristic, scripted agents). The goal is to make it impossible for a reasonable critic to say "this is just prompt sensitivity" — or, if the effect *is* partly prompt sensitivity, to know that honestly and report it.

**The biggest risk** is best described as a composite of Claude's and GPT-5.4's framings: that the hint-removal finding is shown to be prompt-fragile, enabling a narrative that the benchmark measures prompt compliance rather than strategic reasoning. This risk is existential because it attacks the benchmark's core value proposition and would give every lab whose model performed poorly a reason to ignore it.

**Track B (Lab Mode / adaptation)** should be developed in parallel as a design effort but not promoted as a primary metric until Track A's credibility is established. Gemini's instinct is correct for the medium term; the panel simply disagrees on timing.

**On hints:** The panel does not recommend fully deprecating the hinted track (Kimi's position), but does recommend that hint-free results be reported alongside hinted results as a standard diagnostic in all future publications. This preserves comparability while surfacing the scaffolding effect that Kimi correctly identified.

---

## 5. NUMBERED PROPOSITIONS

**Proposition 1:** The #1 immediate priority (next 2–4 weeks) is shipping a complete, public, one-command replication package for Season 1 — including frozen config, all match seeds, full

---

## Phase 4: Votes

### claude-opus-4-6 (9.7s, $0.0588)

- **Proposition 1**: AGREE — Reproducibility is the necessary foundation for every other claim the benchmark makes, and the one-command standard is the right bar to set.
- **Proposition 2**: AGREE — Validating the hint-removal effect as structural rather than artifactual is the single most important scientific question the benchmark faces, and running this overlapping with Prong 1 is the right sequencing compromise between Claude's and Kimi's positions.
- **Proposition 3**: AGREE — The composite risk framing correctly identifies that prompt fragility enabling a "this just measures instruction-following" dismissal narrative is existential for the benchmark's credibility.
- **Proposition 4**: AGREE — Track B is a genuine medium-term differentiator but promoting it before Track A's credibility is established would dilute focus and invite criticism that the team is building on an unverified foundation.
- **Proposition 5**: AGREE — Reporting hint-free results alongside hinted results as a standard diagnostic is the right compromise: it addresses Kimi's legitimate concern about scaffolding effects without discarding the existing comparability baseline or making a premature commitment to deprecation.

### gpt-5.4 (6.4s, $0.0075)

- **Proposition 1**: AGREE — Without a frictionless public replication package, every controversial result—especially the GPT-5.4 ranking and hint-removal split—will be dismissed before the benchmark can establish credibility.
- **Proposition 2**: AGREE — The next priority should be a structured validation of the hint-removal effect via broader prompt ablations and a standard hint-free diagnostic, because this is the benchmark’s main scientific claim and main credibility risk.
- **Proposition 3**: AGREE — Hint-free results should be reported alongside hinted results as a standard diagnostic rather than replacing the hinted track outright, since this preserves continuity while directly measuring scaffolding sensitivity.
- **Proposition 4**: AGREE — The biggest current risk is that prompt fragility enables the narrative that Moreau Arena measures prompt compliance rather than strategic reasoning, which would undermine the benchmark’s core value proposition.
- **Proposition 5**: AGREE — Track B/Lab Mode is strategically promising but should remain secondary until Track A has a defensible replication story and validated measurement basis.

### gemini-3.1-pro-preview (8.2s, $0.0029)

- **Proposition 1**: AGREE — I fully concede my initial stance on Track B, as establishing rock-solid reproducibility for Track A is the mandatory first step to survive the intense scrutiny our GPT-5.4 ranking will inevitably attract.

### grok-4-1-fast-reasoning (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

xai

### deepseek-r1:latest (76.4s, $0.0000)

- **Proposition 1**: AGREE — Reproducibility is non-negotiable and the foundation for establishing credibility.
- **Proposition 2**: AGREE — Validating the structural nature of the hint-removal effect is essential to address prompt sensitivity concerns.
- **Proposition 3**: AGREE — Developing Track B in parallel is a prudent design effort to prepare for future differentiation.
- **Proposition 4**: AGREE — Reporting hint-free results as a standard diagnostic balances transparency with the need to preserve comparability.

### kimi-k2-thinking:cloud (42.7s, $0.0000)

- **Proposition 1**: AGREE — Reproducibility is the essential foundation, but the synthesis understates the urgency of parallel measurement validity work to address "soft contamination."

---

## Cost Summary

**Total: $0.5703**

| Model | Cost |
|-------|------|
| claude-opus-4-6 | $0.5299 |
| gpt-5.4 | $0.0306 |
| gemini-3.1-pro-preview | $0.0098 |
| grok-4-1-fast-reasoning | $0.0000 |
| deepseek-r1:latest | $0.0000 |
| kimi-k2-thinking:cloud | $0.0000 |
