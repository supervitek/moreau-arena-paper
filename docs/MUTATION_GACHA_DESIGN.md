# Moreau Pets — Random Mutation System Design

**Source:** Round Table Council (2026-03-10) — Claude Opus 4.6, GPT-5.4, Gemini 3.1 Pro
**Status:** Design spec, ready for implementation
**Consensus Quality:** High (3/3 core panelists aligned on architecture)

---

## Executive Summary

Replace the current "pick 1 of 3" mutation system with a **risk-tiered random mutation system** featuring symbiotic side effects, cosmetic mutations, cascade rolls, and secret synergies. Core principle: **side effects are trade-offs, not punishments.**

---

## 1. Tier Architecture

Three tiers. Not four. Maps to the brain's natural risk bucketing: safe / risky / reckless.

| Tier | Name | Mutation Pool | Side Effect Chance | Ultra-Rare Chance | Visual Mark |
|------|------|--------------|-------------------|-------------------|-------------|
| 1 | **Stable** | Common (minor stat buffs, +3-5%) | 0% | 0% | None |
| 2 | **Volatile** | Strong (ability augments, meaningful boosts) | 35% | 0% | None |
| 3 | **Forbidden** | Legendary (game-changing mutations) | 70% | 2% | Always marks pet visually |

**Why 70% not 100%:** The 30% escape chance at Tier 3 is the aspirational jackpot. A legendary mutation with zero side effects is the "clean god-roll" that drives engagement. 100% removes the gambling thrill.

**Why 3 not 4:** Four tiers creates decision paralysis. The middle two (25%/50%) lack emotional distinctiveness. Three = instinct, not spreadsheet.

---

## 2. Side Effect Taxonomy

When a side effect triggers, roll on this table:

| Category | Probability | Description | Examples |
|----------|------------|-------------|---------|
| **Symbiotic Trade-off** | 35% | Lose something, gain something unexpected | Bear loses 2 SPD, gains Quill Reflect. Fox's Trick steals a *random* ability instead of best. |
| **Cosmetic Mutation** | 25% | Visual change, zero gameplay impact | Fox's eyes glow amber. Wolf grows iridescent fur. Bear gets tiny vestigial wings. |
| **Ability Corruption** | 20% | Existing ability works differently — stronger but altered | Scorpion's Sting applies to *all* adjacent enemies but at 60% damage. |
| **Cascade** | 15% | Triggers a FREE bonus Tier 1 mutation | Slot machine within a slot machine. The dopamine engine. |
| **Personality Drift** | 5% | Soul voice shifts (Tier 3 only, opt-in preview) | Gentle Bear starts speaking in Rhino's aggressive cadence. |

### Design Rules

- **No pure stat debuffs.** Every side effect must make the player think "wait, that's actually kind of cool?" even when suboptimal.
- **Stat swaps count as Symbiotic**, not debuffs (HP↔SPD, ATK↔WIL).
- **Cascade** can chain — a cascade roll can itself trigger a side effect if Tier 2+ was the original roll. Max chain: 2 (prevents infinite loops).

---

## 3. Permanence & Curing

### Side effects are PERMANENT but OVERWRITABLE

- Each mutation slot holds one mutation + up to one side effect.
- Rolling again on that slot **replaces** both the mutation and side effect.
- This creates the natural "one more try" loop — you're not curing, you're *rerolling*.

### No premium cure. Period.

This is where games turn exploitative. The ethical line is absolute:
- **No real-money cure exists.**
- **No real-money power exists.**
- Premium currency is for cosmetics, UI skins, arena flair only.

### Stabilizer (earned item)

- **What:** Locks a mutation slot, preventing future side effects from overwriting it.
- **How to earn:** ~5 PvP wins, or 10-win streak vs AI, or milestone reward.
- **Purpose:** Protect a god-roll. Creates "should I lock this or keep rolling?" decisions.

---

## 4. Ultra-Rare Mutations (2% from Tier 3)

Fourteen unique legendaries, one per animal archetype. Fighter-specific, reference lore.

| Animal | Ultra-Rare | Effect |
|--------|-----------|--------|
| Fox | **Moreau's Briefcase** | Copy opponent's passive before fight starts |
| Tiger | **Echolocation** | Nullify accuracy penalties, double dodge |
| Bear | **Ursine Apotheosis** | Below 30% HP: all stats +25% for 3 ticks |
| Wolf | **Pack Echo** | Clone your last successful ability on next tick |
| Scorpion | **Neurotoxin Cascade** | All DOTs spread to adjacent hexes |
| Eagle | **Stratospheric Dive** | First strike from max range does 3x damage |
| Porcupine | **Living Fortress** | Reflect 100% of damage taken for 1 tick (10-tick cooldown) |
| Rhino | **Tectonic Charge** | Movement destroys terrain, creating rubble that blocks |
| Viper | **Hemotoxin Bloom** | Poison stacks convert to healing on kill |
| Vulture | **Carrion Authority** | Gain +5% all stats per dead unit on field |
| Monkey | **Chaos Theory** | Randomize one opponent stat each tick |
| Buffalo | **Immovable Object** | Cannot be moved or displaced; immune to knockback |
| Panther | **Void Step** | Teleport behind target before each attack |
| Boar | **Blood Frenzy** | Each hit increases ATK by 3% (stacks infinitely) |

Ultra-rares are **always cosmetically visible** — unique silhouette, particle effects, named transformation.

---

## 5. Secret Synergies (Apex Forms)

The killer retention feature. **Undocumented combinations** of specific mutations that unlock named transformations.

### How It Works
- Certain mutation + side effect combinations trigger an **Apex Form**.
- Not documented in-game — discovered by players, shared in community.
- Apex Forms have unique lore entries, visual silhouettes, and mechanical identities.

### Examples
| Combo | Apex Form | Effect |
|-------|-----------|--------|
| Blindness + Echolocation (Tiger) | **Spectral Stalker** | Translucent model, can't be targeted at range |
| Quill Reflect + Glass Cannon (Bear) | **The Martyr** | All damage reflected at 2x but self-HP halved |
| Poison + Cascade + Feral (Viper) | **Plague Bearer** | AOE poison cloud on death |

### Why This Works
- Transforms mutation rolling from gambling into **research and discovery**
- Community builds wikis, shares findings, creates viral "I found something" moments
- Players roll not just for power but for **combinations** — infinite engagement loop

---

## 6. Retention Mechanics

### Daily Loop
- **1 free Tier 2 roll per day** (earned by playing, not logging in)
- Extra rolls earned through wins, streaks, milestones

### Pity Timer
- After **15 Tier 2 rolls** without a rare mutation → guaranteed strong-pool result
- This is progress, not charity — fills a visible "Research Bar" toward a chosen mutation family
- **Visible near-misses**: show what you *almost* rolled. "You were 1 away from Echolocation."

### Collection
- **Mutation Codex**: tracks all discovered mutations and side effects
- Visible completion percentage — "47/93 mutations discovered"
- **"Most Mutated" leaderboard**: cosmetic mutation stacks shown publicly

### Social
- Cosmetic mutations are **visible to opponents** in PvP
- Share mutation loadout screenshots
- Apex Form discoveries announced server-wide

---

## 7. PvP Balance

### The Problem
Random mutations can create overpowered builds. This is exciting in PvE, unfair in PvP.

### Solution: Hybrid Constraint

1. **Casual PvP (Wild Mode):** No restrictions. Bring your god-roll chaos. This is where viral moments happen.
2. **Ranked PvP:** Mutation point budget — each mutation has a cost, loadouts must fit within a cap. Preserves build identity while constraining power.
3. **Seasonal Resets:** Pets "retire" to a Hall of Fame each season. Mutations wipe, meta cycles. Your legendary Bear becomes a *story*, not a permanent advantage.

---

## 8. Player Journey (Level 1→10)

### Example: Tiger named "Papik"

**Level 1-2:** Training, learning the fight system. No mutations yet.

**Level 3 — First Mutation:**
Player sees three tiers. Picks **Volatile** (Tier 2, 35% side effect).
→ Rolls **Fleet Tendons** (+8% SPD). No side effect triggers.
→ "Nice. Safe. But I wonder what Tier 3 would've given me..."

**Level 6 — Second Mutation:**
Confidence up. Picks **Forbidden** (Tier 3, 70% side effect).
→ Rolls **Shadow-Twitch** (+40% Dodge). Side effect triggers!
→ Symbiotic: **Brittle Frame** (-10% max HP, +15% crit chance).
→ "I lost HP but I crit more? That's... actually kind of broken with my dodge build."

**Level 9 — Third Mutation:**
All-in on Tier 3. Chasing the 2% ultra-rare.
→ Rolls **Ambush Wiring Variant** (first strike always crits). Side effect: **Cascade!**
→ Cascade triggers free Tier 1: **Keen Eyes** (+3% accuracy).
→ "I got a side effect that gave me a BONUS mutation. This system is insane."
→ Checks Codex: "Wait... Shadow-Twitch + Ambush Wiring is flagged as a possible synergy..."

**Post-Level 10:**
→ Player creates a second pet to chase different synergies.
→ Uses daily free rolls to reroll slots on main pet.
→ Shares "Spectral Stalker" Apex Form discovery on Moreddit.
→ Addicted.

---

## 9. Anti-Exploitation Principles

1. **Full odds transparency.** Players see exact percentages for every tier, every side effect category, every ultra-rare chance BEFORE rolling.
2. **No premium power.** Real money never buys combat advantage or mutation removal.
3. **No premium cure.** Side effects are gameplay, not punishment to monetize.
4. **Visible progress.** Pity timer + research bar prevent despair spirals from pure RNG.
5. **Player agency preserved.** Player always *chooses* the tier. Never forced into high-risk rolls.
6. **Seasonal resets prevent permanent inequality.** Hall of Fame preserves legacy without permanent advantage.

---

## 10. Implementation Priority

### Phase 1 (MVP)
- [ ] 3-tier system with mutation pools
- [ ] Side effect taxonomy (Symbiotic, Cosmetic, Cascade)
- [ ] Mutation Codex UI
- [ ] Visual marks for Tier 3 mutations

### Phase 2 (Retention)
- [ ] Daily free roll system
- [ ] Pity timer / Research Bar
- [ ] Stabilizer item
- [ ] "Most Mutated" leaderboard

### Phase 3 (Endgame)
- [ ] Ultra-rare mutations (14 animal-specific)
- [ ] Secret Synergies / Apex Forms (community discovery)
- [ ] Seasonal resets + Hall of Fame
- [ ] PvP point budget system

---

## Council Attribution

| Panelist | Key Contribution |
|----------|-----------------|
| Claude Opus 4.6 | Side effect taxonomy (35/25/20/15/5), "no premium cure period", cascade mechanic |
| GPT-5.4 | Visible near-misses with deterministic progress, mutation point budget for PvP, temporary vs permanent gradient |
| Gemini 3.1 Pro | Secret Synergies / Apex Forms (unanimously praised as best idea), symbiotic trade-offs framing, Blindness→Echolocation example |

**Consensus Quality Score:** 8A — strong alignment on architecture, productive disagreements on permanence and PvP balance resolved through hybrid approach.
