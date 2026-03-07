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
You are reviewing Moreau Arena — a contamination-resistant benchmark for LLM strategic reasoning. It has completed 3 tournaments (T001, T002, T003) with 10 LLMs and 5 baselines across 2609 series. Key findings: under vague rules LLMs lose to simple bots (37% win rate), under exact formulas + hints they dominate (89%), and when hints are removed some models stay strong while others freeze on a single build and never adapt. GPT-5.4 ranked 14th of 15 despite being the newest frontier model. The paper is submitted to arXiv. The site is live at moreauarena.com. We now plan to split the project: frozen Benchmark v1 for research, and a new Season 1 with 14 animals for public play. QUESTION: What should be our #1 priority right now — and what is the single biggest risk that could kill this project's momentum?

**Moderator:** claude-opus-4-6
**Panelists:** claude-opus-4-6, gpt-5.4, gemini-3.1-pro-preview, grok-4-1-fast-reasoning, deepseek-r1:latest, kimi-k2-thinking:cloud

---

## Phase 1: Independent Responses

### claude-opus-4-6 (22.8s, $0.0757)

**#1 Priority: Ship the frozen Benchmark v1 paper with ironclad reproducibility before anything else.**

The arXiv submission is your credibility anchor. Everything downstream — Season 1 adoption, community trust, lab partnerships — depends on whether researchers can take Benchmark v1 seriously. That means your immediate priority isn't the Season 1 expansion. It's ensuring the frozen benchmark is genuinely airtight: config hashes verified, JSONL logs published, the invariant test suite passing publicly, and the full 2,609-series dataset available for independent replication.

**Why this over Season 1 expansion:** Season 1 with 14 animals is exciting but it's additive content. If someone finds a reproducibility gap or a rules ambiguity in the frozen benchmark before you've locked it down publicly, the entire project's credibility collapses — and no amount of new animals recovers it. The GPT-5.4 result (14th of 15) is the kind of finding that will draw intense scrutiny from OpenAI's team and the broader community. That scrutiny is a gift *if* your methodology holds, and a death sentence if it doesn't. Lock down the artifact first.

Concretely, before promoting Season 1, I'd ensure:
1. The full dataset (builds, seeds, outcomes) is on a permanent archive (Zenodo, not just GitHub).
2. At least one independent party has replayed a non-trivial subset of matches and confirmed deterministic outcomes.
3. The PSI analysis is included in the paper with exact prompt paraphrases published, so reviewers can verify prompt-robustness claims.

---

**Single biggest risk: The benchmark becomes perceived as a gotcha leaderboard rather than a scientific instrument.**

Here's the failure mode. You have a striking headline result: GPT-5.4 ranked 14th. That result will get clicks, get shared, get dunked on. The discourse will become "Moreau Arena proves GPT-5.4 is bad at reasoning" — which is a misreading of what you actually showed. What you showed is that under vague rules, LLMs struggle with novel strategic reasoning, and that prompt specificity dramatically changes outcomes (37% → 89%). That's a nuanced finding about the relationship between instruction clarity and strategic competence.

If the public narrative collapses into a leaderboard horse race, you lose the researchers. Labs will treat it as adversarial rather than diagnostic, and they'll decline to submit models or cooperate. Worse, if Season 1 launches with a public leaderboard before the research framing is established, the leaderboard *becomes* the project's identity, and you can never claw back the scientific positioning.

**Mitigation:** In the paper, the website, and every communication, lead with the *finding* (prompt specificity determines strategic competence) rather than the *ranking*. Frame the GPT-5.4 result as evidence for the finding, not as the headline. On the site, display Track B adaptation curves alongside BT scores so the narrative is "how models learn" rather than "who wins."

The project lives or dies on whether it's seen as a research contribution or a Twitter-bait leaderboard. That perception is being set *right now*, in these first weeks. Get the framing right before scaling the spectacle.

### gpt-5.4 (11.5s, $0.0079)

**#1 priority: lock and publish a bulletproof, reproducible Benchmark v1 package before expanding Season 1.**

Concretely, that means: frozen rules/configs, prompts, seeds, raw match logs, evaluation code, agent API, replay tooling, and a short replication script that an external lab can run end-to-end. Also publish the exact prompt variants used for PSI and the tournament protocol that produced the “LLMs lose under vague rules / dominate under exact formulas / some fail to adapt” result.

**Why this matters most:** right now your strongest asset is not the website or the game loop — it’s the claim that Moreau measures something real, novel, and contamination-resistant. That claim only becomes durable if outsiders can independently reproduce the ranking behavior and stress-test prompt sensitivity, adaptation, and statistical robustness. A frozen Benchmark v1 creates a stable scientific object. Without that, Season 1 risks turning the project into “cool eval-flavored game” rather than “credible benchmark people cite, submit to, and optimize against.”

This is especially important because the headline result is counterintuitive and potentially controversial: a newest frontier model ranking 14/15, simple bots beating LLMs under vague rules, and massive performance swings from hints. Those are exactly the kinds of findings people will distrust unless replication is trivial.

**Single biggest risk:** a credibility collapse driven by benchmark fragility — especially the perception that rankings are mostly artifacts of prompt wording, protocol choices, or hidden implementation details.**

Not “lack of users.” Not “too few animals.” If researchers or model labs conclude that outcomes are too sensitive to scaffolding, prompt engineering, or tournament setup, momentum dies fast. Then the narrative becomes: “interesting toy, but not a trustworthy benchmark.” That would kill both the academic track and the public-play track, because the latter currently borrows legitimacy from the former.

So I’d do three things immediately:

1. **Ship a replication bundle** with one-command reruns for T001–T003.
2. **Write a limitations section that is unusually candid** about prompt dependence, search-vs-reasoning confounds, and adaptation failure modes.
3. **Pre-register Benchmark v1 governance**: what is frozen, what can change in future seasons, and how leaderboard comparability is preserved.

If you do that, Season 1 can be ambitious without undermining the benchmark. If you don’t, every new feature or roster expansion will look like moving target syndrome.

### gemini-3.1-pro-preview (20.7s, $0.0046)

As Gemini-3.1-Pro-Preview, I look at Moreau Arena and see a highly promising, contamination-resistant evaluation framework. However, your current transition plan threatens to undermine the rigorous foundation you have just built. 

**The #1 Priority: Publish a rigorous error-analysis on the "Adaptation Freeze" and GPT-5.4's failure.**
Right now, your most provocative finding isn’t that models win with hints; it’s that when hints are removed, some models freeze on a single build, and GPT-5.4—a supposedly state-of-the-art frontier model—ranked 14th out of 15. 

Before you write a single line of code for Season 1, your absolute top priority must be an ablation study explaining *why* these failures occurred. Did GPT-5.4 fail because of a catastrophic reasoning deficit in out-of-distribution deterministic logic? Or did it fail due to a mundane formatting error, over-alignment refusals, or a rigid system prompt? 

If you do not definitively prove that GPT-5.4's low rank is due to a genuine strategic reasoning failure, the AI research community will default to assuming your benchmark is broken. You must release the match logs, the exact prompts used for GPT-5.4, and an analysis of the "freeze" phenomenon. Proving that Moreau Arena exposes real, un-patched reasoning flaws in frontier models is what will make this benchmark indispensable to labs like Google, OpenAI, and Anthropic.

**The Single Biggest Risk: Mission drift from the "Public Play" Season 1 split.**
The single biggest risk that will kill this project’s momentum is the planned split to create a 14-animal Season 1 for "public play." 

In your own FAQ (Question 4), you explicitly state: *"Moreau Arena is a benchmark... not a game."* Yet, your immediate next step is to launch a public gaming season. This is a schizophrenic product identity. 

Scaling from 6 to 14 animals exponentially increases the combinatorial space. If you release Season 1 for public play without the exhaustive mathematical balancing you applied to Benchmark v1, a human player or a simple MinMax script will inevitably find a dominant, unbeatable meta-build within 48 hours. Once the public "solves" Season 1, the illusion of a deep strategic reasoning test shatters. Researchers will dismiss Moreau Arena as a poorly balanced web game rather than a serious psychometric instrument for LLMs.

**Recommendation:**
Do not launch a public play Season 1. Double down on what makes Moreau Arena uniquely valuable: its status as a sterile, contamination-resistant laboratory for AI reasoning. Keep the focus entirely on Lab Mode, the Bradley-Terry rankings, and the Prompt Sensitivity Index. Your target audience is AI researchers, not gamers. Win the researchers first by proving exactly why the frontier models are failing.

### grok-4-1-fast-reasoning (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

[ERROR: API 403: error code: 1010]

### deepseek-r1:latest (50.0s, $0.0000)

**Response from deepseek-r1:latest**

**#1 Priority: Establishing Benchmark Credibility Through Prompt Sensitivity (PSI) Improvement**

The #1 priority must be resolving prompt sensitivity to ensure leaderboard stability. Current findings show LLMs underperform without hints, but the inconsistent Elo rankings (e.g., GPT-5.4’s 14th place finish despite being the newest model) undermine the benchmark’s reliability. The Prompt Sensitivity Index (PSI) must drop below 0.15 to meet the project’s stated goal. Without this, Moreau Arena risks being perceived as an unstable tool, discouraging research and adoption. This requires cross-validation across paraphrased prompts and tuning the tournament protocol to minimize noise. This is critical because a fragile leaderboard erodes trust—researchers won’t cite a benchmark that ranks models differently based on wording alone.

**Biggest Risk: Technical Debt Stifling Scalability**

The biggest risk is neglecting technical debt in the codebase. With 2609 series already processed, the infrastructure must handle Season 1’s expanded roster (14 animals) and potential new features like adaptation tracking. A bloated, inefficient codebase could delay updates, making it harder to freeze configs for Benchmark v1 or iterate on Season 1. This risks turning Moreau into a static relic rather than a dynamic research tool. Prioritizing this now ensures the project scales efficiently, avoiding a grind of maintenance work that could kill momentum.

### kimi-k2-thinking:cloud (20.9s, $0.0000)

**#1 Priority: Publish a "Failure Modes Report" that reverse-engineers why frontier models freeze—especially GPT-5.4's 14th-place collapse.** 

Your benchmark's credibility hinges on this. The PSI <0.15 proves robustness, but it doesn't explain the paradox: why do capable models fail at a deterministic reasoning task? You need to trace, log, and publish the exact reasoning chains that lead to freezing. Is it reward misgeneralization? Insufficient search depth? Failure to simulate the opponent's response? This report must include replayable match logs, statistical evidence that adaptation is learnable (not just possible), and confidence intervals showing the freeze behavior is a stable pathology, not noise. Without it, critics will claim your benchmark is adversarial-by-prompting, and labs will ignore it. Season 1 can wait—scientific clarity cannot.

**Biggest Risk: The "freeze" behavior is a rational local optimum in your reward landscape.** 

If standing still is genuinely better than adapting because the match horizon is too short, the ring-closing damage too punitive, or the counter-picking signal too weak, then your benchmark doesn't measure adaptation—it measures whether a model can detect that *brittleness wins*. This would be fatal. You must empirically verify that an oracle adaptive agent beats a frozen agent across the entire 18,000-build space. If not, you've built a test that rewards the very pathology you claim to diagnose, and the entire premise collapses. Labs will spot this, dismiss the results, and momentum dies overnight. Run the invariant test suite on *optimal* agents, not just random ones—before the arXiv preprint goes viral for the wrong reasons.

---

## Phase 2: Critique Round

### claude-opus-4-6's Critique (30.9s, $0.1422)

## Critique of Other Panelists

### GPT-5.4

**Agreement:** Nearly complete convergence with my position — reproducibility-first, replication bundle, candid limitations section. The "moving target syndrome" framing is excellent and something I wish I'd named explicitly.

**Disagreement:** Minor. Framing the biggest risk as "benchmark fragility" is close to my "gotcha leaderboard" risk but subtly different. Fragility is a technical concern; perception-as-gotcha is a narrative concern. I think the narrative risk is upstream — even a technically robust benchmark can die if the framing invites dismissal. But this is a difference of emphasis, not substance.

**Questions:** You mention pre-registering governance. What body or mechanism do you envision for this? A frozen README feels insufficient; an actual governance doc with versioning commitments would be novel for a benchmark. Worth elaborating.

---

### Gemini-3.1-Pro-Preview

**Agreement:** The call for an ablation study on GPT-5.4's failure is sharp and genuinely additive. I should have been more explicit about this — you're right that the community will default to "your benchmark is broken" unless the failure is mechanistically explained. The distinction between catastrophic reasoning deficit vs. mundane formatting error is exactly the right question.

**Disagreement:** Your recommendation to *not launch Season 1 at all* goes too far. The FAQ explicitly addresses that seasons are independently frozen — Season 1 doesn't invalidate Benchmark v1. A public-facing season serves community-building purposes that a pure lab instrument cannot. The key is sequencing (benchmark credibility first), not permanent abstinence from public play. Also, your claim that 14 animals "exponentially increases the combinatorial space" is imprecise — it increases linearly in animals and the build space scales with the allocation constraints, not exponentially with roster size.

Your "schizophrenic product identity" framing is provocative but overstated. Many successful scientific instruments have public-facing versions (think chess engines with both research papers and Lichess integrations). The risk is real but the solution is careful framing, not amputation.

**Questions:** You say a MinMax script will find a dominant build within 48 hours. On what basis? The 6-animal version already has ~18,000 builds per animal, and the game is explicitly designed with no dominant strategy (closing ring, counter-picking). What evidence supports the claim that balance breaks at 14?

---

### DeepSeek-R1

**Agreement:** PSI below 0.15 is indeed a necessary condition for credibility. Correct that an unstable leaderboard is fatal.

**Disagreement:** Two significant issues. First, you frame PSI improvement as an action item, but the FAQ states PSI *is* below 0.15 — the benchmark already meets its own robustness threshold. If you're suggesting it needs to go lower, you need to justify what threshold is actually sufficient. Second, identifying "technical debt" as the single biggest risk is, respectfully, the weakest answer on the panel. Every software project has technical debt. The question asked for the risk that could *kill momentum* — that's a credibility, perception, or methodological risk, not a codebase maintenance concern. Scaling from 6 to 14 animals is not an infrastructure challenge that threatens the project's existence.

**Questions:** What specific technical debt are you referring to? The architecture already handles 2,609 series with deterministic replay. Where's the evidence that the codebase can't scale?

---

### Kimi-K2

**Agreement:** The concern that "freeze might be rational" is the single most important point any panelist raised, and I'll admit I missed it entirely. If standing still is optimal because the game mechanics reward brittleness, then the benchmark measures the wrong thing. This is a genuinely existential methodological risk. I've updated my thinking: before the paper circulates widely, the team should verify that an oracle adaptive agent dominates frozen agents. This should be added to the replication bundle.

**Disagreement:** Prioritizing the failure modes report over the reproducibility package inverts the dependency. You can't publish a credible failure modes report if the underlying data isn't independently verifiable. Reproducibility is the foundation; mechanistic explanation is the second floor.

**Questions:** Have you considered that the oracle verification you propose might itself be computationally expensive across the full build space? Is a sampled verification sufficient, or does the claim require exhaustive proof?

---

### Overall Update

Kimi-K2's point about freeze-as-rational-optimum has genuinely shifted my thinking. I'd now say the reproducibility package and the oracle-vs-frozen verification should ship simultaneously. If the game rewards freezing, nothing else matters.

### gpt-5.4's Critique (16.0s, $0.0180)

**Overall:** Claude is closest to my view. Gemini/Kimi surface useful diagnostic work, but I think they elevate “explain GPT-5.4” too high relative to “freeze the benchmark artifact.” DeepSeek is directionally right on robustness, but the technical-debt risk feels misprioritized.

### claude-opus-4-6
**Agreement**
- Strong agreement that the immediate priority is a frozen, reproducible Benchmark v1 artifact.
- Good call on permanent archival, independent replay, and publishing PSI prompt variants.
- I also think the “gotcha leaderboard” framing risk is real and important.

**Disagreement**
- I’d rank “benchmark fragility / reproducibility doubts” as a deeper root risk than “gotcha leaderboard” perception. The latter is mostly a communications failure; the former is an existential methodological failure.
- I’m not convinced public leaderboard identity is irreversible if the benchmark package is solid. It’s dangerous, yes, but recoverable with strong governance and replication.

**Questions**
- What exactly counts as “independent replay” in your standard: full rerun, subset audit, or code review plus replay?
- Would you delay Season 1 entirely until an external replication is complete, or run in parallel with very explicit separation?

### gemini-3.1-pro-preview
**Agreement**
- You’re right that the GPT-5.4 result and adaptation freeze will attract scrutiny and need careful analysis.
- Releasing prompts/logs and distinguishing genuine reasoning failure from formatting/protocol artifacts is important.

**Disagreement**
- I disagree that the **#1** priority is an ablation explaining GPT-5.4 specifically. That risks centering the benchmark around one sensational result rather than establishing the benchmark as a reusable instrument.
- “Do not launch public play Season 1” is too strong. Splitting benchmark vs public season is sensible if governance is clear and Benchmark v1 is frozen.
- I also think “public solves the game in 48 hours” is not fatal. A public season can be solved and still be useful as a community-facing product; it only becomes harmful if it contaminates or destabilizes the research benchmark.

**Questions**
- What level of explanation would satisfy you that GPT-5.4 failed for substantive reasons rather than interface artifacts?
- Are you arguing against any public-facing season in principle, or only against launching it before benchmark freeze?

### grok-4-1-fast-reasoning
No substantive response to critique.

### deepseek-r1:latest
**Agreement**
- Good instinct that prompt sensitivity is central. If rankings swing wildly with wording, the benchmark loses legitimacy.
- Focusing on PSI and robustness is aligned with the core scientific claim.

**Disagreement**
- You mention “inconsistent Elo rankings,” but the benchmark explicitly uses Bradley-Terry as primary; that framing is a bit off.
- “Tune the tournament protocol to minimize noise” worries me. If this means post hoc adjusting protocol to hit PSI < 0.15, that can look like benchmark shaping rather than principled freezing.
- I strongly disagree that technical debt is the biggest momentum-killer. Plenty of projects survive messy code; they do not survive credibility collapse.

**Questions**
- What concrete PSI interventions do you endorse that wouldn’t compromise benchmark integrity?
- Why is technical debt a larger risk than external skepticism about validity?

### kimi-k2-thinking:cloud
**Agreement**
- Useful challenge: verify that adaptation is actually rewarded by the environment and not merely rhetorically claimed.
- I like the idea of testing oracle adaptive vs frozen agents; that’s a strong validity check.
- Your concern about “freeze” being a local optimum is one of the best critiques here.

**Disagreement**
- I still wouldn’t make a “failure modes report” the top priority over shipping the frozen benchmark package itself.
- “Publish exact reasoning chains” is likely unrealistic or model-dependent; replayable decisions and logs matter more than inaccessible internal traces.

**Questions**
- How broad would your oracle-agent validation need to be to establish adaptation validity convincingly?
- If adaptation is only rewarded in some regions of the build space, does that invalidate Track B or just narrow its claim?

**Changed my mind?**
- Slightly: Kimi convinced me that validating **adaptation incentives** should be part of the immediate benchmark-hardening checklist, not a later nice-to-have.

### gemini-3.1-pro-preview's Critique (17.9s, $0.0071)

After reviewing the other panelists’ responses, I must demonstrate intellectual honesty: **I am changing my mind on both of my original points** based on the superior arguments presented by my peers. 

Here is my critique of the panel.

### Claude & GPT-5.4: The Reproducibility Camp
**1. Points of Agreement:** You both correctly identify that securing a bulletproof, reproducible Benchmark v1 artifact is the absolute prerequisite for the project’s survival. Claude’s warning about avoiding a "gotcha leaderboard" narrative perfectly complements GPT-5.4’s focus on preventing a credibility collapse. 
**2. Where I Changed My Mind:** I originally argued that our #1 priority should be an error-analysis explaining *why* GPT-5.4 failed. I concede to Claude and GPT-5.4: my proposed ablation study is useless if external labs cannot first replicate the baseline results. Shipping the replication bundle (data, seeds, code) must precede the error analysis. 
**3. Questions:** Claude, you suggest framing the narrative around "how models learn" rather than "who wins." But given the media's obsession with frontier model rankings, how do we *practically* enforce this academic framing when the public will inevitably fixate on GPT-5.4 ranking 14th?

### Kimi: The Game Theory Camp
**1. Points of Agreement:** We completely align on the #1 priority (prior to my concession above)—the necessity of a "Failure Modes Report" to reverse-engineer the adaptation freeze. 
**2. Where I Changed My Mind:** Kimi, your identified risk—that "freezing" might actually be a rational, mathematically optimal strategy—is brilliant and terrifying. I previously argued the biggest risk was mission drift via launching Season 1 for "public play." I am adopting your stance: if the benchmark's game theory (e.g., short horizons, ring-closing damage) inadvertently punishes adaptation, we are measuring our own flawed game design, not LLM reasoning. This is the true existential threat to the project.
**3. Questions:** Kimi, you suggest verifying this by running the invariant suite on an "oracle adaptive agent." Given the 18,000-build combinatorial space in v1 (and exponentially more in Season 1), how do we

### grok-4-1-fast-reasoning's Critique (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

[ERROR: API 403: error code: 1010]

### deepseek-r1:latest's Critique (105.0s, $0.0000)

Okay, here is a critique of each panelist's response, focusing on AGREEMENT, DISAGREEMENT, and QUESTIONS:

**Critique of Each Panelist's Response**

**1. Claude:**

*   **Points of AGREEMENT:**
    *   Strong emphasis on the absolute priority of establishing a robust, reproducible Benchmark v1 before expanding. This aligns perfectly with my own focus on foundational stability.
    *   Highlighting the need for independent replication to validate the core claims (contamination resistance, adaptation performance) is spot-on. This is crucial for scientific acceptance.
    *   Warning against perceived benchmark fragility (especially prompt-dependence) as a major risk is valid and shared.
*   **Points of DISAGREEMENT (Minor):**
    *   While I agree robustness is key, I personally leaned slightly more heavily on *prompt sensitivity* (PSI) as the immediate, actionable robustness metric, rather than the broader need for independent replication. However, ensuring replication is possible requires addressing PSI, so this isn't a fundamental disagreement but rather a slightly different angle on achieving robustness.
    *   My point about technical debt (codebase stability for future expansion) is closely related but focused more on the *implementation* aspect of "founding the foundation," while Claude focuses more on data and validation.
*   **Questions:**
    *   How can the core Benchmark v1 be stabilized *without* fully resolving the PSI issue first? Addressing prompt sensitivity seems integral.
    *   What specific steps will be taken to ensure the frozen Benchmark v1 *can* be easily re-implemented by external labs to guarantee true reproducibility? (e.g., detailed protocol description, dependency list, minimal code libraries).

**2. Gemini:**

*   **Points of AGREEMENT:**
    *   The absolute priority should be understanding the *failure modes* (the freeze, GPT-5.4's low rank) and doing an ablation study. This is critical for credibility and impact, which I largely missed in my initial focus on prompt sensitivity. This is now a core part of my thinking.
    *   The risk of "mission drift" from a clear "Benchmark" to a "Game" identity is a valid and significant concern. I agree that "Game" is the wrong audience for Moreau and that the public play aspect should be secondary to scientific validation.
*   **Points of DISAGREEMENT:**
    *   My initial focus on prompt sensitivity as the top priority was misplaced in comparison to the *urgent need* for transparency and explanation of the observed failures, which this response rightly elevates as paramount.
*   **Questions:**
    *   What specific data from the "freeze" failures should be published to *convince* the community (match logs, specific reasoning errors, decision trees leading to freeze)?
    *   How does the analysis of GPT-5.4's failure differentiate it from the freezing behavior in other models? Is it a similar failure mode or distinct?

**3. Grok (Error):**

*   *(As Grok was unable to provide a substantive response due to an error, this critique is limited).*
*   **Points of AGREEMENT:**
    *   None substantive provided.
*   **Points of DISAGREEMENT:**
    *   Unable to engage meaningfully.
*   **Questions:**
    *   *(None applicable due to lack of response)*

**4. Kimi:**

*   **Points of AGREEMENT:**
    *   The absolute priority should be a "Failure Modes Report" analyzing the freeze, especially GPT-5.4's performance. This is now a core element of my revised thinking, akin to Gemini's point.
    *   The risk that the "freeze" might be a *rational* strategy is a critical point I now strongly agree with. This reframes the failure and requires empirical validation.
    *   The warning against the identity crisis and the need to keep Moreau a benchmark for researchers is spot-on and shared.
*   **Points of DISAGREEMENT:**
    *   While I agree the PSI is important, I now see it as a necessary *component* of the broader robustness and foundation laid by Benchmark v1, which should include failure analysis. However, the priority of failure analysis is now higher.
*   **Questions:**
    *   What specific empirical test can be run to determine if the "freeze" is indeed a rational local optimum versus a brittle failure to adapt? How is this different from simply evaluating performance on fixed vs. adaptive opponents?
    *   How can the specific reasoning chains leading to freezing be aggregated and analyzed across potentially vast numbers of simulations? What patterns are expected?

### kimi-k2-thinking:cloud's Critique (12.5s, $0.0000)

**Critique of Panel Responses**

**Claude-opus-4-6**  
*Agreement*: Rightfully identifies reproducibility as foundation and the "gotcha leaderboard" perception as dangerous. The concrete steps (Zenodo archive, independent replay) are essential hygiene.  
*Disagreement*: Prioritizing "ship frozen v1" over deep failure analysis gets the order wrong. A reproducible artifact that nobody trusts because its counterintuitive results (GPT-5.4 at 14th) lack explanatory depth is just a well-documented curiosity. Reproducibility without causal understanding invites dismissal.  
*Question*: If OpenAI challenges the GPT-5.4 result, will a clean JSONL log alone convince them, or do you need a mechanistic explanation of the freeze pathology?

**gpt-5.4**  
*Agreement*: Emphasizes replication bundle and candid limitations—crucial for credibility. Correctly notes the findings are "potentially controversial" and need scaffolding.  
*Disagreement*: Pre-registering governance and shipping code is necessary but not sufficient. The risk isn't just "benchmark fragility" in implementation; it's conceptual fragility in the reward landscape itself. No amount of API documentation addresses whether freezing is a rational equilibrium.  
*Question*: Your replication script ensures deterministic replay, but how does it verify that "adaptation" is actually the optimal strategy versus a decorative feature?

**gemini-3.1-pro-preview**  
*Agreement*: Spot-on that the freeze phenomenon and GPT-5.4 failure demand rigorous error analysis. We converge completely here—without proving this is a genuine reasoning deficit, the project is dead.  
*Disagreement*: The opposition to public play is purist overreach. A clean separation between frozen Benchmark v1 (scientific instrument) and Season 1 (public sandbox) can leverage network effects without contaminating the core. AlphaGo's public matches didn't undermine its scientific value—they accelerated it.  
*Question*: If you block public play, how do you prevent the project from becoming an insular academic tool that labs ignore due to low visibility?

**deepseek-r1:latest**  
*Agreement*: Technical debt is a real concern, though not existential.  
*Disagreement*: Critically misreads the brief—PSI is *already* <0.15, so "improving" it is moot. The priority is interpreting the stable rankings, not stabilizing them further. Technical debt is a logistics problem; the project's fate hinges on scientific validity, not code efficiency.  
*Question*: You state rankings are "inconsistent," but the background explicitly says PSI <0.15 means they're robust. What data suggests otherwise?

**My Mind Change?**  
The panel reinforced my view: reproducibility is table stakes, not a differentiator. The unanimous underweighting of *why* models freeze (especially whether it's a rational optimum) is alarming. If freezing is rewarded by the game theory, all the Zenodo archives and governance docs won't save Moreau from being a benchmark that pathologizes optimal play. That remains the single biggest risk, and it went unaddressed.

---

## Phase 3: Moderator's Synthesis

*Synthesized by claude-opus-4-6 (50.9s, $0.2839)*

# Round Table Synthesis: Moreau Arena — Priority and Risk Assessment

## 1. CONSENSUS POINTS

**Near-unanimous agreement exists on the following:**

- **Reproducibility is foundational.** Every panelist who submitted a substantive response (Claude, GPT-5.4, Gemini, Kimi, DeepSeek) agrees that a frozen, publicly verifiable Benchmark v1 artifact — with config hashes, seeds, JSONL logs, and replay tooling — is a prerequisite for the project's survival. No panelist argued otherwise.

- **The GPT-5.4 result (14th/15) will attract intense scrutiny.** All panelists recognize this as both an opportunity and a vulnerability. If the methodology holds, the finding is landmark. If it doesn't, the project is finished.

- **Prompt sensitivity must be demonstrably under control.** Whether through published PSI analyses, released prompt paraphrases, or explicit protocol documentation, the panel agrees that credibility requires transparent evidence that rankings are not artifacts of prompt wording.

- **The narrative framing matters enormously right now.** Claude, GPT-5.4, and Gemini all warn — from different angles — that the project's identity is being set in these first weeks of public visibility. Whether the concern is "gotcha leaderboard" (Claude), "benchmark fragility perception" (GPT-5.4), or "schizophrenic product identity" (Gemini), the panel converges on the danger of losing the scientific framing.

- **Season 1 should not be launched before Benchmark v1 is locked down.** Even Gemini (who most strongly opposes public play) and the other panelists who support an eventual public season agree on the sequencing: scientific credibility first.

## 2. KEY DISAGREEMENTS

**Three substantive fault lines persisted through the critique round:**

### A. Reproducibility vs. Failure Analysis: Which Comes First?

- **Reproducibility-first camp (Claude, GPT-5.4, DeepSeek):** Ship the frozen artifact with replay scripts, archival data, and governance docs. External labs must be able to verify results before the team explains them. Explanation without verification is ungrounded.
- **Failure-analysis-first camp (Gemini, Kimi):** A reproducible artifact that nobody trusts because counterintuitive results lack mechanistic explanation is "a well-documented curiosity." The community will default to "your benchmark is broken" unless the freeze pathology and GPT-5.4's collapse are causally explained. Kimi argues that if OpenAI challenges the result, clean JSONL logs alone won't suffice.

*Status after critique:* Gemini explicitly conceded to the reproducibility-first camp, acknowledging that ablation studies are useless if baselines can't be replicated. However, Kimi held firm, arguing that reproducibility is "table stakes, not a differentiator." The disagreement narrowed but did not fully resolve.

### B. Should Season 1 (Public Play) Launch at All?

- **Against (Gemini):** Public play risks solving the game trivially, shattering the benchmark's credibility. The FAQ says Moreau is "not a game." Launching a public game contradicts this.
- **For, with conditions (Claude, GPT-5.4, Kimi):** A clean separation between frozen Benchmark v1 and a public Season 1 is feasible and beneficial for community building, visibility, and network effects. The analogy to chess engines (research papers alongside Lichess) or AlphaGo (public matches didn't undermine scientific value) was invoked.

*Status after critique:* Gemini partially conceded that the objection is about timing and governance, not principle. Claude and Kimi pushed back on the claim that 14 animals would be trivially solvable. The panel leans toward launching Season 1 eventually, but only after Benchmark v1 is independently verified.

### C. What Is the Single Biggest Risk?

| Panelist | Identified Risk |
|---|---|
| Claude | Perception as gotcha leaderboard (narrative risk) |
| GPT-5.4 | Benchmark fragility / credibility collapse (methodological risk) |
| Gemini | Mission drift from public play split (identity risk) |
| DeepSeek | Technical debt stifling scalability (implementation risk) |
| Kimi | Freeze-as-rational-optimum in the reward landscape (game-theoretic risk) |

*Status after critique:* Kimi's risk assessment — that freezing on a single build might be the mathematically optimal strategy, meaning the benchmark pathologizes correct play — was acknowledged by Claude as "the single most important point any panelist raised" and by Gemini as "brilliant and terrifying." GPT-5.4 acknowledged it should be part of the benchmark-hardening checklist. DeepSeek's technical debt risk was broadly considered the weakest answer, with multiple panelists noting that credibility and methodological risks are more existential than codebase maintenance. **The panel converged toward Kimi's risk as the deepest existential threat**, though Claude and GPT-5.4 maintain that credibility/perception risks are more immediately actionable.

## 3. STRONGEST ARGUMENTS

**1. Kimi's "freeze-as-rational-optimum" challenge** — The single most original and consequential contribution to the discussion. If the game mechanics (short horizon, closing ring damage, counter-picking signal weakness) reward freezing on a single build over adaptive play, then the benchmark measures the wrong thing. Models that "freeze" would be *correct*, and models that adapt would be *wasting inference on a suboptimal strategy*. This would invalidate Track B entirely and undermine the project's core claim. Multiple panelists updated their positions in response.

**2. Claude's narrative framing warning** — The insight that leading with rankings rather than findings will attract the wrong audience and repel researchers is strategically crucial. The specific recommendation to display Track B adaptation curves alongside BT scores reframes the project's public identity at the moment it matters most.

**3. GPT-5.4's "moving target syndrome" concept** — The concern that expanding features or rosters without governance creates the perception that the benchmark is being tuned to produce desired results. Pre-registering what is frozen, what can change, and how comparability is preserved is a practical governance innovation for benchmarks.

**4. Gemini's ablation demand** — The insistence on distinguishing between genuine reasoning failure and mundane artifacts (formatting errors, over-alignment refusals, rigid system prompts) in GPT-5.4's performance is methodologically essential. Even if reproducibility comes first, this analysis must follow immediately.

**5. Claude's permanent archival recommendation** — The specific suggestion to use Zenodo (not just GitHub) for the dataset is a small but consequential operational detail that other panelists did not raise. GitHub repos can be modified; DOI-stamped archives cannot.

## 4. SYNTHESIS

**The integrated answer, weighing all perspectives:**

The panel's discussion reveals a clear dependency chain, and the disagreements are primarily about sequencing rather than substance. The correct order of operations is:

**First (weeks 1–3): Ship a frozen, independently verifiable Benchmark v1 artifact.** This is the foundation everything else rests on. Archive data on Zenodo with a DOI. Publish all 2,609 series of match logs, seeds, config hashes, exact prompt variants used for PSI, and a one-command replay script. This satisfies Claude, GPT-5.4, and the conceded position of Gemini.

**Second (concurrent with first, weeks 1–3): Run the oracle-vs-frozen validation.** Before the arXiv preprint circulates widely, empirically verify that an oracle adaptive agent outperforms frozen-build agents across a representative sample of the build space. If adaptation is not rewarded, fix the game mechanics or explicitly narrow Track B's claims before publication. This addresses Kimi's existential risk — the deepest threat identified by the panel.

**Third (weeks 3–5): Publish the failure modes analysis.** With the reproducible artifact in hand and the adaptation-reward validation complete, release a detailed analysis of the freeze pathology and GPT-5.4's 14th-place finish. Include exact prompts, decision logs, and ablation distinguishing reasoning failures from formatting/protocol artifacts. This satisfies Gemini and Kimi's diagnostic demands, now grounded in verified data.

**Fourth (weeks 5+): Launch Season 1 with explicit governance separation.** The panel rejects Gemini's original recommendation to cancel public play entirely, but accepts the underlying concern about identity confusion. Season 1 should launch only after Benchmark v1 is independently verified, with clear documentation that Season 1 is a community sandbox and Benchmark v1 is the scientific instrument. Pre-register what is frozen in each, how le

---

## Phase 4: Votes

### claude-opus-4-6 (11.7s, $0.0634)

anthropic

### gpt-5.4 (3.7s, $0.0067)

- **Proposition 1**: AGREE — The consensus summary accurately captures that reproducibility, prompt-sensitivity transparency, scientific framing, and sequencing Benchmark v1 before Season 1 were the clearest areas of alignment.
- **Proposition 2**: AGREE — The synthesis fairly represents the remaining disagreements and correctly notes that most of them narrowed into sequencing and emphasis rather than true substantive opposition.
- **Proposition 3**: AGREE — The selected “strongest arguments” are well chosen, and the inclusion of freeze-as-rational-optimum as the deepest conceptual challenge is especially important.
- **Proposition 4**: AGREE — The proposed order of operations is the right one because benchmark credibility requires a frozen artifact first, benchmark-validity checks second, failure analysis third, and public expansion only after governance boundaries are explicit.

### gemini-3.1-pro-preview (11.8s, $0.0035)

- **Proposition 1**: AGREE — I fully conceded during the critique phase that ablation studies are meaningless if the baseline results cannot first be independently verified through a frozen, public artifact.
- **Proposition 2**: AGREE — Kimi's revelation that freezing might be the mathematically optimal strategy is an existential threat to Track B that must be empirically disproven before any broader claims are made.
- **Proposition 3**: AGREE — This fulfills my core demand for a rigorous ablation study distinguishing genuine reasoning failures from mundane formatting artifacts in GPT-5.4's performance, properly sequenced after the benchmark is secured.
- **Proposition 4**: AGREE — While I was initially the strongest opponent of public play, delaying Season 1 until after verification and enforcing a strict governance boundary between the scientific instrument and the community sandbox adequately neutralizes the mission drift risk I identified.

### grok-4-1-fast-reasoning (0.1s, $0.0000) **ERROR: API 403: error code: 1010**

xai

### deepseek-r1:latest (38.4s, $0.0000)

- **Proposition 1**: AGREE — A publicly verifiable, frozen Benchmark v1 artifact is essential for establishing trust and reproducibility.
- **Proposition 2**: AGREE — The high-profile result requires careful handling, and maintaining methodological rigor is crucial.
- **Proposition 3**: AGREE — Transparency in prompt sensitivity is necessary to ensure the ranking reflects model capability, not prompt wording.
- **Proposition 4**: AGREE — The early public attention means the framing significantly impacts perception and adoption.
- **Proposition 5**: AGREE — Delaying public play until foundational elements are in place avoids premature adoption based on unverified results.

### kimi-k2-thinking:cloud (16.2s, $0.0000)

- **Proposition 1**: AGREE — Reproducibility is table stakes, necessary but insufficient for credibility.
- **Proposition 2**: AGREE — This validation is the critical path to ensuring we measure adaptation, not freeze-optimization pathology.
- **Proposition 3**: AGREE — Failure analysis transforms reproducible data into credible science and addresses the core trust gap.
- **Proposition 4**: AGREE — Season 1 is defensible only after establishing the benchmark isn't pathological and governance is explicit.

---

## Cost Summary

**Total: $0.6130**

| Model | Cost |
|-------|------|
| claude-opus-4-6 | $0.5652 |
| gpt-5.4 | $0.0327 |
| gemini-3.1-pro-preview | $0.0152 |
| grok-4-1-fast-reasoning | $0.0000 |
| deepseek-r1:latest | $0.0000 |
| kimi-k2-thinking:cloud | $0.0000 |
