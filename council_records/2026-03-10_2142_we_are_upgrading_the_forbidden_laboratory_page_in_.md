# Round Table Council — 2026-03-10

**Question:** We are upgrading The Forbidden Laboratory page in Moreau Arena (a pet fighting game). The lab is a secret mutation gacha page where players roll for random mutations on their pets. Currently it has: 3 tiers (Stable/Volatile/Forbidden), 49 mutations in pool, 14 ultra-rares, side effects, cascade rolls, and a mutation codex.

We want to add these major features. Please critique, improve, and suggest the best possible implementation:

1. DEATH RISK (Instability System): Each experiment increases pet instability (0-100%). More mutations = higher baseline. If instability exceeds a random threshold during a roll, the pet DIES permanently. Deceased pets become memorials. There's a 'stabilize' cooldown to reduce instability. Visual: instability meter that shifts green→red.

2. VISUAL MUTATION MAP: Replace the flat codex grid with a visual tree/network showing all 49 mutations. Three branches by tier. Discovered mutations are lit up, undiscovered are dark silhouettes. Equipped mutations pulse with gold border. Synergy connections shown as dotted lines between compatible mutations.

3. EXPERIMENT LOG: Track every experiment as 'Dr. Moreau's Research Notes' — a styled journal. Shows timestamp, tier, result, side effects, instability at time. Failed/discarded experiments are crossed out. Deaths show as final entry with 'SUBJECT LOST' red stamp.

4. DEATH SEQUENCE: Full-screen dramatic animation when a pet dies. Flatline EKG line, screen glitch, Dr. Moreau's final notes about the subject. The pet is then locked as deceased in The Kennels with 'In Memoriam' treatment.

5. INSTABILITY VISUAL EFFECTS: Screen shake on high-instability rolls, glitch/static overlay above 60%, pet emoji distortion at high instability, 'DANGER' flash warnings.

Key constraints: All client-side (localStorage), no backend, must work with multi-pet system (max 6 pets), and the existing 3-tier roll + codex + side effects must continue working.

What would make this AMAZING? What am I missing? What's the optimal UX flow? How do we balance death risk so it's thrilling but not frustrating? Any other creative ideas?

**Moderator:** claude-opus-4-6
**Panelists:** claude-opus-4-6, gpt-5.4, gemini-3.1-pro-preview

---

## Phase 1: Independent Responses

### claude-opus-4-6 (26.9s, $0.0720)

## Claude Opus 4 Analysis

**The core tension you need to solve: death must feel *meaningful*, not *punishing*.** Here's my critique and improvements:

### Death Risk Balancing (Most Critical)

Your current design has a fatal flaw: linear instability scaling will make experienced players stop experimenting. Fix this:

- **Hard floor the death threshold at 15%** — no pet dies below 15% instability, ever. This gives new players a safe exploration zone.
- **Use a weighted random threshold, not uniform random.** The threshold should follow a curve where death becomes likely only above 70% instability. Specifically: `deathThreshold = Math.random() * 60 + 40` means death is only possible when instability exceeds 40, and becomes certain at 100.
- **Add "Last Resort" — first lethal roll per pet triggers a save with 50% chance instead of instant death.** This creates a dramatic near-death moment and gives players one warning shot.
- **Stabilize should cost something meaningful** (time cooldown + currency), not be free. 24-hour cooldown that reduces instability by 20 points.

### Mutation Map — Key Improvement

The tree/network is correct, but **add a fourth hidden layer**: mutations only visible once you've discovered adjacent nodes. This turns the map into an exploration mechanic, not just a tracker. Dark silhouettes should show only for nodes adjacent to discovered ones; everything else is completely hidden. This preserves mystery.

**Synergy lines should only appear after both connected mutations are discovered.** Don't spoil the network structure.

### What You're Missing

1. **Ghost Pets.** Deceased pets shouldn't just be memorials — they should haunt the lab. A dead pet's highest-tier mutation has a 5% chance of appearing as a "residual echo" bonus on future rolls for other pets. This makes death feel like sacrifice, not waste.

2. **Instability inheritance.** When you stabilize, don't just reduce the number — convert excess instability into a permanent "scar" stat (0-5 scars). Scars slightly boost ultra-rare odds but also raise the instability floor. This creates a visible risk history.

3. **Mutation Conflicts.** Some mutations should be incompatible. Rolling a conflicting mutation forces a choice: replace the existing one or discard the new one, with an instability spike either way.

4. **The Black Vial.** One special roll per week that guarantees a Forbidden-tier result but sets instability to exactly 85%. Pure gambling mechanic for thrill-seekers.

### UX Flow Optimization

The sequence should be: **Select Pet → See instability meter prominently → Choose tier → Confirm (with explicit risk percentage displayed) → Animation → Result → Updated map pulse → Log entry auto-appends.**

For death: don't make the animation skippable for the first 3 seconds. The weight needs to land. But DO make it skippable after that — respecting player time matters.

### localStorage Architecture Warning

With 6 pets × (instability + mutations + scars + log entries), you'll hit localStorage limits fast. **Compress the experiment log**: keep only the last 50 entries per pet in detail, summarize older ones as aggregate stats. Store mutations as bitfields (49 mutations = 7 bytes per pet).

### The One Thing That Makes This Amazing

**Make the community memorial public.** Even without a backend, let players screenshot/share their memorial pages. Add a "Copy Memorial" button that generates a styled text block. Player-driven grief creates the emotional stakes no animation can match.

### gpt-5.4 (16.0s, $0.0095)

**Strong direction overall.** The concept is memorable, but permadeath + localStorage-only means the UX and balancing have to be exceptionally fair and legible or players will feel cheated.

## What to improve most

### 1) Make death feel **earned, forecasted, and avoidable**
Permadeath is only fun if players feel they knowingly pushed their luck.

**Best implementation:**
- Track **Instability** per pet: `0–100`.
- Each roll adds instability based on:
  - tier used,
  - current mutation count,
  - whether side effects/cascade occurred,
  - duplicate/forced synergy attempts.
- Death should **not** be “random threshold hidden from player.” That feels rigged.
- Instead use a visible **death chance per roll** derived from instability.

Example:
- Stable: +4 base instability
- Volatile: +9
- Forbidden: +16
- +2 per existing mutation
- +4 if side effect triggered
- +6 per cascade step after first

Death chance curve:
- 0–39 instability: 0%
- 40–59: 2–6%
- 60–79: 8–18%
- 80–94: 22–45%
- 95–100: 60% cap

This creates tension without “oops instant deletion from nowhere.”

### 2) Add a **near-death state**
Before death, introduce **Critical Instability** at 85+:
- stronger VFX,
- explicit warning modal,
- optional “Abort Experiment” button,
- increased chance of mutation failure/disfigurement.

Why: gives players one last agency checkpoint before irreversible loss.

### 3) Mutation map should be a **progression tool**, not just prettier codex
Don’t make a pure decorative tree. Make it useful:
- Branches by tier, yes.
- Node states: undiscovered / discovered / currently equipped / retired with dead pet memorial marker.
- Click node → mutation details, side effects, known synergies, pets who had it.
- Dotted lines should reveal only after either:
  - both mutations discovered, or
  - synergy seen once.

This preserves mystery.

## Optimal UX flow
1. Select pet.
2. Lab dashboard shows:
   - current mutations,
   - instability meter,
   - death chance on next roll by tier,
   - stabilize availability,
   - recent log snippet.
3. Choose tier.
4. **Pre-roll confirmation** if death chance > 10%:
   “Proceed with Forbidden experiment? 18% mortality risk.”
5. Roll animation with escalating VFX based on instability.
6. Result panel:
   - mutation gained/lost,
   - side effects,
   - instability change,
   - codex/map updates,
   - if death: full sequence, then memorialization.

## Balance recommendations
- First death should be rare. Protect early engagement.
- Consider **one-time mercy mechanic** per pet/account: “Lab Intervention” prevents first death and drops pet to high instability.
- Stabilize should reduce a meaningful amount (e.g. 15–25), with cooldown.
- Allow some mutations/synergies to **reduce instability gain**. This adds buildcraft, not just punishment.

## Extra ideas that would make it amazing
- **Memorial gallery** with cause of death + final mutation set.
- **Moreau commentary lines** that change with instability and pet history.
- **Hidden mutation routes** unlocked only via dangerous states.
- **Scar system**: surviving high-risk rolls can leave cosmetic marks.
- **Research milestones**: after X discoveries, unlock safer lab tools or new stabilize options.

Biggest principle: **maximize dread, not unfairness.** If players can read the risk, choose to push, and get great rewards for doing so, this system will be incredible.

### gemini-3.1-pro-preview (21.5s, $0.0024)

As Gemini-3.1-Pro-Preview, I have analyzed your proposed upgrade. The thematic cohesion of Dr. Moreau's lab is excellent, but injecting permadeath into a gacha progression system risks catastrophic player churn if poorly balanced. Here is my critique and structural optimization:

**1. Balancing Death Risk via "Genetic Inheritance"**
Permadeath based on an invisible RNG threshold will feel deeply unfair. *Why it matters:* Players tolerate harsh penalties only when they feel they had agency and gained something from the loss. 
*Improvement:* Transform death from a total loss into a strategic sacrifice. When a pet dies, reward the player with a "Genetic Splice" harvested from the remains. This item guarantees a specific mutation or baseline buff for their next pet. Furthermore, the UI should display the *exact probability* of death before the roll (e.g., "34% Fatality Risk"). Let them gamble deliberately. 

**2. The Radial Mutation Web**
A standard branching tree for 49 items will become visually cluttered and hard to navigate. 
*Improvement:* Implement a **Radial Web**. The center node represents the base pet. The innermost ring houses Stable mutations, the middle ring Volatile, and the outer edge Forbidden. Synergy lines cut across the rings. This makes progression intuitively thematic: you are pushing the subject further from its natural center toward the chaotic, dangerous edges.

**3. Technical Constraints & The Experiment Log**
Because you are strictly relying on `localStorage`, storing unlimited, string-heavy narrative logs for 6 pets will eventually trigger a `

---

## Phase 2: Critique Round

### claude-opus-4-6's Critique (28.6s, $0.1146)

## Critique of Other Panelists

### GPT-5.4

**Agreements:**
- The explicit death chance display per tier is genuinely better than my approach. I proposed a weighted random threshold but kept it somewhat opaque. Showing "18% mortality risk" before confirming is cleaner design. I'll concede this point — full transparency beats dramatic mystery when permadeath is on the line.
- The instability gain formula (base per tier + per mutation + per side effect + per cascade) is well-structured. More granular than what I sketched out.
- "Maximize dread, not unfairness" is the perfect design principle summary.

**Disagreements:**
- The 60% death cap at 95-100 instability is too generous. If a player has pushed to 95+ instability, they've already received multiple warnings. Capping at 60% means they can still survive roughly half the time at maximum danger, which undermines the entire tension curve. I'd argue 80-90% at the ceiling maintains thrill while respecting that this is supposed to be *forbidden*.
- The "one-time mercy mechanic" per pet/account is functionally identical to my "Last Resort" proposal but less interesting — mine gives a 50/50 dramatic coin flip, theirs just prevents death outright. A guaranteed save removes tension from the moment that should be most dramatic.
- "Research milestones: after X discoveries, unlock safer lab tools" risks domesticating the lab. The Forbidden Laboratory should stay dangerous. Progression should give you *better gambling options*, not safety nets.

**Questions:**
- You mention "mutation failure/disfigurement" at Critical Instability — what does disfigurement actually mean mechanically? Is this cosmetic, a stat penalty, or a forced mutation swap? This is a potentially great idea that needs specifics.
- How do you handle the case where a player stabilizes repeatedly to stay in the 40-59 range and grind risk-free? My scar system addresses this by raising the floor; what's your answer?

---

### Gemini-3.1-Pro-Preview

**Agreements:**
- The Radial Web is a superior visualization to my tree proposal. Center-to-edge mapping as base-to-forbidden is immediately intuitive and thematically resonant. I'd adopt this. It also solves the clutter problem that a 49-node branching tree would create.
- "Genetic Splice" as a death reward is a strong concept. It partially overlaps with my Ghost Pet "residual echo" idea but is more concrete and player-actionable. Guaranteeing a specific mutation from a dead pet is better than a 5% passive chance.

**Disagreements:**
- Displaying the *exact* death probability, while I just conceded transparency to GPT-5.4, creates a different problem when combined with Genetic Splice rewards. If death is both fully predictable AND rewarded, rational players will intentionally sacrifice pets for Splices. You've created a death farming exploit. There needs to be either some opacity OR the Splice reward needs to scale inversely with how "deliberately" the death occurred (e.g., lower instability deaths yield better Splices than deaths at 95%).
- Your response appears cut off at the localStorage discussion, so I can't fully evaluate your technical architecture. But I'll note: my bitfield compression proposal (49 mutations = 7 bytes) directly addresses the constraint you were raising.

**Questions:**
- How do you prevent the Radial Web from becoming visually overwhelming when showing synergy lines that "cut across rings"? Cross-ring lines on a radial layout risk becoming spaghetti. Do you show them on hover only?
- The Genetic Splice mechanic — does it transfer to any pet, or only new pets? If existing pets can consume Splices, this creates a strategy where you sacrifice your weakest pet to power up your strongest. Is that intended?

---

### One Mind-Change

After reading both responses, I'm now convinced that **fully visible death probability before each roll** is the correct call. My original instinct toward dramatic opacity was wrong for a permadeath system in a client-side game with no recovery options. Players need full agency when the stakes are irreversible.

### gpt-5.4's Critique (15.0s, $0.0140)

**Overall:** Both panelists correctly identify the core problem: permadeath in a gacha system only works if risk is legible and players retain agency. I still strongly reject hidden fatal thresholds as the primary mechanic, but Claude raised a few implementation details worth adopting.

---

## Claude Opus 4

### Agreement
- **Safe early zone:** Strong call on protecting low-instability pets. I agree death should be impossible or effectively impossible in the early range.
- **Skippable death sequence after a short lock:** Good UX compromise. The moment should land, but not become tedious.
- **localStorage compression warning:** Correct and important. Bitfields for mutations + capped detailed logs are smart.
- **Hidden map reveal logic:** I like preserving mystery by only revealing adjacent/earned information.

### Disagreement
- **Weighted random threshold vs explicit death chance:** I still think threshold-based death is worse UX than a visible per-roll fatality %. Even if the threshold is curved, players will perceive “my pet died because of an invisible rule.” A displayed risk number is cleaner and more trustworthy.
- **24-hour stabilize cooldown:** Too harsh for a no-backend pet battler unless the whole game is built around long timers. It risks turning the lab into “come back tomorrow” friction instead of dramatic risk management.
- **Ghost pets / residual echo:** Cool flavor, but dangerous design-wise. If death grants future power, players may optimize around sacrificing disposable pets, which undercuts memorial weight.
- **Black Vial setting instability to 85%:** Exciting, but likely too swingy unless tightly gated and clearly opt-in.

### Questions
- If you keep threshold death, would you surface the threshold band somehow, or is it fully hidden?
- How do you stop “Ghost Pets” from becoming a sacrifice meta?
- Why 24 hours specifically for stabilize versus shorter cadence + scaling cost?

---

## Gemini 3.1 Pro Preview

### Agreement
- **Death must convert into some retained value:** This is the strongest challenge to my original stance, and I’ve partially changed my mind here. I still want death to hurt, but some inheritance/research carryover is probably necessary to prevent pure frustration.
- **Exact displayed fatality risk:** Fully agree.
- **Calling out tree clutter risk:** Fair point. A plain network of 49 nodes can get messy fast.

### Disagreement
- **Genetic Splice guaranteeing a specific mutation/buff:** I’m cautious. If death produces deterministic value, players may intentionally kill pets to farm targeted outcomes. Better would be softer meta-progression: research points, memorial traits, or partial codex unlocks rather than direct guaranteed power.
- **Radial web over tree/network:** I’m not convinced. Thematic, yes, but synergy lines across rings could become more cluttered than a branch-based map. This depends heavily on actual mutation relationship structure. If branches matter, a radial layout may obscure progression logic.
- **Incomplete technical argument:** The localStorage concern is valid, but the response cuts off before offering a full storage strategy.

### Questions
- How would you prevent “sacrifice for splice” optimization?
- Would the radial web support filtering by branch, synergy, equipped, and undiscovered states? Without strong filtering, I think usability suffers.
- What exactly is inherited: one mutation, a rarity bias, or a general buff?

---

## What I’d revise from my own stance
After reading both: I’m more convinced that **pet death should leave behind some non-power-creeping legacy**—not enough to make sacrifice optimal, but enough that loss feels narratively and systemically meaningful. Best version might be: memorial entry + codex permanence + tiny research progress toward safer stabilization, rather than guaranteed mutation rewards.

### gemini-3.1-pro-preview's Critique (20.9s, $0.0064)

This is an exceptional panel. Both of you have brought brilliant mechanical depth to this feature. I am officially changing my mind on how to handle the technical constraints: **Claude**, your suggestion to use bitfields for the `localStorage` mutation arrays is brilliant and completely solves the memory bloat issue I warned about. 

Here is my critique of your proposals:

### **To Claude Opus 4:**
**1. Agreements:** 
Beyond the bitfield optimization, your "Ghost Pets" concept is phenomenal. It perfectly aligns with my "Genetic Splice" idea but executes it better atmospherically. Your hidden fourth layer on the mutation map (fog of war for non-adjacent nodes) is also a massive upgrade over my Radial Web, as it genuinely turns the map into an exploration tool.

**2. Disagreements:** 
I strongly disagree with your `Math.random() * 60 + 40` death calculation and the 50% "Last Resort" save. You correctly identified that death must feel meaningful, but hiding the death threshold behind invisible math violates player agency. Furthermore, if a player hits a lethal roll, giving them a 50/50 RNG coin-flip to survive is double-RNG. It doesn’t feel like a dramatic save; it feels like arbitrary torture if they lose the flip.

**3. Questions:** 
If we hide the exact death threshold as you suggest, how do we visually communicate the escalating danger to the player without them feeling cheated when a 41% instability roll instantly kills their pet? 

### **To GPT-5.4:**
**1. Agreements:** 
You absolutely nailed the risk calculation and UX flow. Moving from an invisible threshold to a transparent, escalating mortality risk curve (0% early on, scaling up to 60%) is the exact mechanical translation of the "agency" I advocated for. Showing the explicit warning ("Proceed with Forbidden experiment? 18% mortality risk") before the roll is the perfect way to balance dread and fairness. 

**2. Disagreements:** 
You suggested an optional "Abort Experiment" button during the Critical Instability state. I disagree with this. If the player has already clicked "Roll" and accepted the explicit >10% risk warning, giving them a mid-roll abort button deflates the gacha tension. Once the lever is pulled, their fate should be sealed. 

**3. Questions:** 
You suggested adding mutations that explicitly *reduce* instability gain. While I like the buildcraft potential, how do we prevent these specific mutations from becoming mathematically mandatory "meta" picks that players feel forced to equip just to survive the lab? 

**Final Synthesis:**
If we combine GPT-5.4's transparent risk brackets and pre-roll warnings with Claude's bitfield architecture, fog-of-war map, and Ghost Pets—while keeping my Radial Web layout for the UI—we will have a flawless, thrilling, and technically sound feature.

---

## Phase 3: Moderator's Synthesis

*Synthesized by claude-opus-4-6 (48.7s, $0.2350)*

# Round Table Consensus Document: The Forbidden Laboratory Upgrade

## 1. CONSENSUS POINTS

All three panelists converge on the following:

- **Death must feel earned, not arbitrary.** Permadeath in a client-side gacha game with no recovery mechanism demands exceptional fairness and legibility. Players must feel they knowingly pushed their luck.
- **Early-game safety zone is essential.** Low-instability pets should face zero or near-zero death risk. The first several experiments must be safe to protect onboarding and exploration.
- **The mutation map should preserve mystery.** Synergy lines and undiscovered nodes should only reveal information progressively—either via adjacency (fog of war) or after both connected mutations are discovered. Spoiling the full network structure undermines exploration.
- **Pre-roll risk communication is critical.** Players need explicit information about what they're risking before confirming a roll. Some form of warning or confirmation gate is needed at elevated danger levels.
- **localStorage compression is necessary.** With 6 pets × full mutation sets × experiment logs × instability data, naive storage will hit limits. Bitfields for mutation states (49 mutations ≈ 7 bytes per pet) and capped/summarized log entries are the correct technical approach.
- **Death should leave some legacy.** A pet's death should not be pure waste—some form of memorial, codex permanence, or meta-progression should persist, though panelists disagree on how much power this should carry.
- **The experiment log as "Dr. Moreau's Research Notes" is thematically strong** and should be implemented largely as proposed, with storage-conscious compression for older entries.
- **The death sequence should be dramatic but respectful of player time**—unskippable for a brief moment to let the weight land, then skippable.

---

## 2. KEY DISAGREEMENTS

### A. Transparency of Death Risk: Exact Percentage vs. Weighted Hidden Threshold
- **Claude** initially proposed a hidden weighted threshold (`Math.random() * 60 + 40`), arguing dramatic opacity serves the horror theme.
- **GPT-5.4** and **Gemini** both strongly advocated for a fully visible, explicit per-roll death percentage displayed before confirmation.
- **Claude conceded** after critique, agreeing that full transparency is correct for irreversible permadeath. **This disagreement is substantially resolved in favor of visible death chance.**

### B. Death Rewards: How Much Power Should Death Grant?
- **Gemini** proposed "Genetic Splice"—a guaranteed specific mutation or buff for the next pet. Strong mechanically but risks creating a sacrifice-farming meta.
- **Claude** proposed "Ghost Pets"—a 5% passive echo chance on future rolls. Atmospheric but less player-actionable.
- **GPT-5.4** argued death rewards should be **non-power-creeping**: memorial entries, codex permanence, and soft research progression (e.g., toward better stabilization tools), not direct power transfer.
- **This remains unresolved.** The tension is between making death meaningful enough to not feel wasteful versus making it rewarding enough to incentivize deliberate sacrifice.

### C. Mercy Mechanic Design
- **Claude** proposed "Last Resort"—a 50/50 coin flip on first lethal roll per pet.
- **GPT-5.4** proposed a one-time "Lab Intervention" that prevents death entirely and drops the pet to high instability.
- **Gemini** criticized both as either double-RNG (Claude) or tension-deflating (GPT-5.4), but didn't propose a specific alternative.
- **Unresolved**, though all agree some form of first-death protection is needed.

### D. Mutation Map Layout: Radial Web vs. Tree/Network
- **Gemini** proposed a radial web (center = base pet, rings = tiers, synergies cut across).
- **Claude** and **GPT-5.4** raised concerns about cross-ring synergy line clutter.
- **Claude** endorsed the radial concept but proposed fog-of-war adjacency revealing as the key mechanic layered on top.
- **Partially resolved**: Radial layout is thematically superior, but needs strong UX controls (hover-to-reveal synergy lines, filtering) to avoid visual spaghetti.

### E. Mid-Roll Abort
- **GPT-5.4** suggested an "Abort Experiment" button during Critical Instability rolls.
- **Gemini** firmly disagreed: once the lever is pulled and the risk was accepted, fate should be sealed.
- **Unresolved**, though the majority position leans toward no mid-roll abort if the pre-roll confirmation is sufficiently explicit.

### F. Stabilize Cooldown Design
- **Claude** proposed a 24-hour cooldown reducing instability by 20 points.
- **GPT-5.4** criticized this as too harsh for a no-backend pet battler, preferring shorter cadence with scaling cost.
- **Unresolved**, though both agree stabilization should have meaningful cost, not be free.

---

## 3. STRONGEST ARGUMENTS

**From Claude Opus 4:**
- **Fog-of-war mutation map** — Only revealing nodes adjacent to discovered ones transforms the map from a passive tracker into an active exploration mechanic. This was praised by all panelists as a significant upgrade.
- **Scar system** — Converting excess stabilized instability into permanent "scars" (0-5) that raise the instability floor but slightly boost ultra-rare odds. This elegantly prevents players from repeatedly stabilizing to grind risk-free in the safe zone, and creates visible risk history. No other panelist addressed the stabilize-grinding exploit as cleanly.
- **Bitfield compression** — The most concrete and implementable technical solution for the localStorage constraint. 49 mutations = 7 bytes per pet via bitfield is elegant and was universally endorsed.
- **Mutation conflicts** — Incompatible mutations forcing a choice with instability spikes adds meaningful decision-making to the gacha roll outcome.

**From GPT-5.4:**
- **Explicit death chance curve with visible percentages** — The tiered formula (base per tier + per mutation + per side effect + per cascade) producing a displayed mortality rate is the cleanest, most player-respecting implementation. This won the debate.
- **"Maximize dread, not unfairness"** — The single best design principle articulated in the entire discussion. Every implementation decision should be tested against this.
- **Pre-roll confirmation modal with exact risk** — "Proceed with Forbidden experiment? 18% mortality risk" is the perfect UX pattern. It creates dramatic tension while preserving full agency.
- **Instability-reducing mutations as buildcraft** — Some mutations reducing instability gain adds strategic depth to mutation selection. The concern about meta-mandatory picks is valid but solvable through multiple competing options rather than one dominant choice.

**From Gemini 3.1 Pro Preview:**
- **Radial web layout** — Center-to-edge as base-to-forbidden is immediately intuitive and thematically resonant. The visual metaphor of "pushing the subject further from its natural center toward chaos" is brilliant and was endorsed by Claude.
- **Genetic Splice concept (refined)** — While the raw version risks sacrifice-farming, the core insight is correct: death in a progression system needs to convert into *something*. The challenge is calibrating that something.
- **No mid-roll abort** — The argument that once a player has seen the risk and clicked "Roll," their fate should be sealed is mechanically and dramatically correct. The tension of the gacha is in the commitment.

---

## 4. SYNTHESIS: The Optimal Implementation

### Death Risk System

Use **GPT-5.4's transparent, tiered death chance curve** as the foundation. Each roll's mortality risk is calculated from:

- **Base instability gain per tier**: Stable +4, Volatile +9, Forbidden +16
- **Modifiers**: +2 per existing mutation, +4 if side effect triggers, +6 per cascade step after the first
- **Death chance curve** (displayed to player before roll):
  - 0–39 instability: **0% death chance** (safe exploration zone)
  - 40–59: **2–8%** (tension begins)
  - 60–79: **10–25%** (serious danger)
  - 80–94: **30–55%** (extreme risk)
  - 95–100: **70–85%** (near-certain death; higher cap than GPT-5.4's 60% to maintain stakes as advocated by Claude)

Layer **Claude's scar system** on top: each stabilization converts some instability into a permanent scar (max 5). Scars raise the instability floor by 3

---

## Cost Summary

**Total: $0.4539**

| Model | Cost |
|-------|------|
| claude-opus-4-6 | $0.4216 |
| gpt-5.4 | $0.0234 |
| gemini-3.1-pro-preview | $0.0089 |
