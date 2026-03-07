# WIL Redesign -- Season 1

## What Changed

In Season 1, **WIL now grants +0.25% max HP regeneration per tick per WIL point.**

This is a flat, linear scaling. Every point of WIL gives you a steady stream of healing throughout the fight, turning WIL investment into a real survival stat rather than a minor modifier.

---

## The Math

Fights last up to 60 ticks. Here's what different WIL investments yield:

| WIL | Regen/Tick | Total Regen (60 ticks) | Notes |
|-----|-----------|----------------------|-------|
| 1 (minimum) | 0.25% max HP | 15% max HP | Barely noticeable |
| 5 (balanced) | 1.25% max HP | 75% max HP | Solid sustain |
| 10 (heavy) | 2.50% max HP | 150% max HP | Massive survivability |
| 15 (extreme) | 3.75% max HP | 225% max HP | Enormous regen, but only 60 HP and low damage |

### Concrete Example

A **Bear with stats 5/5/5/5** has 100 HP.

- WIL 5 = 1.25% max HP per tick = **1.25 HP per tick**
- Over a full 60-tick fight: **75 HP regenerated**
- That's effectively 175 HP total durability from a 100 HP pool

Compare to a Bear at 5/10/2/3 (ATK-heavy): only 0.75% per tick = 45 HP over the fight. More burst damage, but far less staying power.

---

## Why It Matters

WIL regen creates a genuine **ATK > WIL sustain > HP tank > ATK** triangle:

- **ATK builds** kill before regen matters -- they burst through WIL sustain
- **WIL sustain builds** out-heal chip damage from HP tanks over long fights
- **HP tank builds** absorb burst from ATK stackers with their massive health pools
- **ATK builds** punch through HP tanks with raw damage... and the cycle continues

Without meaningful WIL regen, HP stacking dominates because there's no way to out-sustain a large health pool. The redesign gives WIL a distinct identity.

---

## WIL's Full Effect List

WIL does more than just regen. Each point of WIL provides:

| Effect | Description |
|--------|-------------|
| **Regeneration** | +0.25% max HP per tick (the new addition) |
| **Resist** | Reduces opponent's ability proc rates against you |
| **Proc Bonus** | Increases your own ability proc rates |
| **Ability Power** | Scales the strength of your ability effects |

High WIL makes your abilities fire more often, hit harder, and makes the opponent's abilities fire less -- on top of constant healing.

---

## Interaction with Scorpion

**Scorpion's Venom Gland halves WIL regen.**

A WIL 10 build normally regenerates 2.5% max HP per tick. Against Scorpion, that drops to 1.25% -- equivalent to WIL 5. This is why Scorpion is the designated counter to WIL-heavy strategies. If you're running a sustain build, Scorpion is your nightmare matchup.

---

## Build Archetypes

Stats are distributed across 4 attributes: **HP / ATK / SPD / WIL** (20 points total).

| Build | Stats (HP/ATK/SPD/WIL) | HP Pool | Regen/Tick | Playstyle |
|-------|----------------------|---------|-----------|-----------|
| **Glass Cannon** | 3/14/2/1 | 60 HP | 0.15 HP (0.25%) | Maximum burst. Kill before you die. No safety net. |
| **Balanced** | 5/5/5/5 | 100 HP | 1.25 HP (1.25%) | Moderate everything. Flexible, no hard counters. |
| **Sustain Fighter** | 5/3/2/10 | 100 HP | 2.50 HP (2.50%) | Low damage but massive regen. Wins attrition wars. |
| **Speed Demon** | 3/3/13/1 | 60 HP | 0.15 HP (0.25%) | Dodge and mobility focused. Relies on evasion, not healing. |
| **WIL Tank** | 8/1/1/10 | 160 HP | 4.00 HP (2.50%) | Huge HP pool + regen. Extremely durable, but almost no damage. |

### Key Takeaways

- **Glass Cannon** and **Speed Demon** essentially ignore WIL -- they win or lose before regen matters.
- **Balanced** gets surprising value: 75 HP healed over a fight is significant on a 100 HP body.
- **Sustain Fighter** regens 150 HP over a fight on a 100 HP body -- you effectively have 250 HP of durability if you survive the early game.
- **WIL Tank** combines the largest HP pool with the highest flat regen (4 HP/tick), but deals almost no damage. Wins by never dying... unless the opponent has Scorpion or enough burst to overwhelm the healing.
