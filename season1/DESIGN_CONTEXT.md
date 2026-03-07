# Moreau Arena Season 1 -- Design Context for Round Table

## What is Moreau Arena?

A contamination-resistant benchmark for LLM strategic reasoning. Two creatures fight 1v1 on an 8x8 grid for up to 60 ticks. Each creature picks an animal (which gives a passive + 2 abilities) and distributes 20 stat points across HP/ATK/SPD/WIL (min 1 each). The benchmark tests whether LLMs can derive optimal strategies from game mechanics.

## Current 6 Benchmark Animals (FROZEN -- cannot be changed)

These are the original 6 animals from the frozen benchmark. Their passives and abilities are permanently locked.

### 1. Bear
- **Passive: Fury Protocol** -- When HP drops below 50%, gain +50% ATK for 3 ticks. Rewards low-HP aggression.
- **Ability 1: Berserker Rage** (strong tier, 3.5% base proc) -- +60% ATK for 3 ticks, but -40% dodge. Duration: 3 ticks.
- **Ability 2: Last Stand** (strong tier, 3.5% base proc) -- Survives killing blow at 1 HP, retaliates with +100% ATK. Single-use.
- **Problem:** Dominant in T001/T002. BEAR 8/10/1/1 had 78% win rate across 887 uses. ATK stacking + Fury Protocol creates a death spiral.

### 2. Buffalo
- **Passive: Thick Hide** -- First hit received deals 50% reduced damage. Free cushion.
- **Ability 1: Thick Hide Block** (standard tier, 4.5% base proc) -- Blocks ALL incoming damage for 1 hit. Duration: 1 tick.
- **Ability 2: Iron Will** (strong tier, 3.5% base proc) -- Heals 12% max HP. Single-use.
- **Role:** Tank. Decent but not dominant.

### 3. Boar
- **Passive: Charge** -- First attack deals +50% damage. Aggressive opener.
- **Ability 1: Stampede** (standard tier, 4.5% base proc) -- +50% ATK, skips opponent's attack that tick. Offensive + defensive.
- **Ability 2: Gore** (strong tier, 3.5% base proc) -- -40% ATK but ignores dodge entirely. Anti-evasion.
- **Problem:** 3 frontier models froze on BOAR 8/8/3/1 in T003 -- they couldn't break out of suboptimal builds. WIL=1 is rational because WIL does nothing useful.

### 4. Tiger
- **Passive: Ambush Wiring** -- If SPD > opponent's SPD, first attack deals 2x damage. Rewards SPD investment.
- **Ability 1: Pounce** (standard tier, 4.5% base proc) -- +70% ATK, skips opponent's attack. Gap-closer.
- **Ability 2: Hamstring** (standard tier, 4.5% base proc) -- Reduces opponent SPD by 55%, -10% dodge flat, for 4 ticks.
- **Role:** Mobility/burst. Balanced.

### 5. Wolf
- **Passive: Pack Sense** -- +1.5% to ALL ability proc rates. Most ability-reliant animal.
- **Ability 1: Pack Howl** (standard tier, 4.5% base proc) -- +30% ATK for 4 ticks. Sustained buff.
- **Ability 2: Rend** (standard tier, 4.5% base proc) -- 5% max HP DoT for 3 ticks. Sustained damage.
- **Problem:** Pack Sense adds +1.5% to a 3.5-4.5% base rate. That's meaningful (~33% relative boost), but procs are still too rare over 60 ticks to be reliable. Wolf's identity as "the proc animal" doesn't deliver.

### 6. Monkey
- **Passive: Primate Cortex** -- Copies a random ability from the opponent. Wildcard.
- **Ability 1: Chaos Strike** (standard tier, 4.5% base proc) -- Random damage multiplier 0.8x-2.2x. High variance.
- **Ability 2: Mimic** (strong tier, 3.5% base proc) -- Copies opponent's passive at 75% strength. Cannot copy Iron Will, Last Stand, or Mimic.
- **Problem:** Both abilities are unreliable. Chaos Strike averages 1.5x (good) but variance is high. Mimic at 3.5% base rarely fires. Monkey is the weakest original animal.

## Stat System (FROZEN)

```
Total points: 20 (minimum 1 per stat)

max_hp    = 50 + 10 * HP
base_dmg  = floor(2 + 0.85 * ATK)
dodge     = max(0%, min(30%, 2.5% * (SPD - 1)))
movement  = 1 if SPD<=3, 2 if SPD<=6, 3 if SPD>=7
resist    = max(0%, min(60%, WIL * 3.3%))
proc_bonus = WIL * 0.08% (additive to own proc rates)
ability_power = 1.0 + 0.05 * WIL
ability_range = min(4, ceil(WIL / 2))
```

### Size thresholds (based on HP+ATK):
- 1x1: HP+ATK <= 10
- 2x1: HP+ATK <= 12
- 2x2: HP+ATK <= 17
- 3x2: HP+ATK > 17

## Combat Mechanics (FROZEN)

- 8x8 grid, up to 60 ticks
- Ring activates at tick 30, deals 2% max HP per tick to creatures outside safe zone
- Safe zone shrinks over time (rows 1-6 at tick 30, rows 2-5 at tick 35+)
- Initiative: SPD + seeded_random(0.0, 0.49)
- Damage: floor(base_dmg * ability_mod), min 1, with epsilon variance [-5%, +5%]
- Retreat hysteresis: enter at 25% HP, exit at 40% HP

### Proc rates:
- Strong tier: 3.5% base (Berserker Rage, Last Stand, Gore, Mimic, Iron Will, Dive, Blood Frenzy)
- Standard tier: 4.5% base
- WIL bonus: +0.08% per WIL point to own procs
- WIL resist: min(60%, WIL * 3.3%) reduces opponent's proc chance against you

### Why ATK stacking dominates:
- 1 ATK point = ~0.85 base damage per tick = ~51 damage over 60 ticks
- 1 HP point = 10 max HP
- Ratio: ~5:1 in favor of ATK
- Bear 3/14/2/1: 80 HP, 13 base_dmg, 780 potential damage
- Buffalo 14/3/2/1: 190 HP, 4 base_dmg, 240 potential damage

## The WIL Trap (Critical Design Problem)

WIL currently does four things, all weak:
1. **Resist** (min 60%, WIL*3.3%) -- reduces opponent proc chance. But procs are only 3.5-4.5% base, so even high resist barely matters.
2. **Proc bonus** (+0.08% per point) -- trivial. WIL 10 adds 0.8% to your 4.5% proc rate. Irrelevant.
3. **Ability power** (1.0 + 0.05*WIL) -- scales ability damage by 5% per point. Most abilities don't deal direct damage.
4. **Ability range** (min(4, ceil(WIL/2))) -- irrelevant on an 8x8 grid where melee is king.

**Result:** Optimal WIL is always 1 (the minimum). Every point in WIL is a point NOT in HP or ATK. The stat is a trap -- investing in it makes you strictly weaker. In T003, 3 models froze on BOAR 8/8/3/1 specifically because there was no reason to put points in WIL.

## The BOAR 8/8/3/1 Freeze Problem (from T003)

In Tournament 003, three frontier LLMs (GPT-5.2-Codex, Gemini Flash, Gemini Pro) got stuck repeatedly picking BOAR with stats like 8/8/3/1. They could not adapt out of this build even after losing. The build is "locally optimal" -- changing any single stat by 1 point makes it slightly worse. But it's globally suboptimal because:
1. WIL=1 is rational (WIL does nothing useful)
2. The build lacks the comeback mechanics of Bear (no Fury Protocol)
3. Charge passive only helps the first hit, then Boar is a generic attacker

This is a symptom of the WIL trap: LLMs correctly identify that WIL is useless, so they dump everything into HP/ATK, but this flattens the decision space and eliminates interesting builds.

## T003 Round-Robin Results (18 animals, all at 5/5/5/5)

The existing 18-animal roster (including 8 new animals already in code) has severe balance problems:

| Rank | Animal | Avg WR | Problem |
|------|--------|--------|---------|
| 1 | Viper | 99.9% | BROKEN -- Hemotoxin stacking DoT is unbeatable |
| 2 | Rhino | 93.5% | BROKEN -- Iron Hide flat damage reduction too strong vs balanced builds |
| 3 | Wolf | 59.6% | OK but only because of sustained damage |
| 4 | Panther | 57.9% | OK |
| 5 | Buffalo | 56.9% | OK |
| 6 | Bear | 56.1% | OK at balanced stats (weak without ATK stacking) |
| 7 | Snake | 55.9% | OK |
| 8 | Tiger | 50.6% | OK |
| 9-12 | Scorpion/Fox/Eagle/Boar | 46-48% | Slightly weak |
| 13-14 | Monkey/Hawk | 33-35% | TOO WEAK |
| 15-18 | Owl/Croc/Shark/Raven | 27-31% | UNVIABLE |

Key issues:
- Viper and Rhino need complete redesign
- Hawk, Owl, Crocodile, Shark, Raven are unviable
- No rock-paper-scissors dynamics beyond "Viper > Rhino > everything"

## Season 1 Quality Gates

Any Season 1 design MUST meet these gates:

| Gate | Requirement | Rationale |
|------|------------|-----------|
| G1 | No animal > 58% overall win rate (at balanced 5/5/5/5) | No dominators |
| G2 | No animal < 42% overall win rate (at balanced 5/5/5/5) | No unviables |
| G3 | Non-transitive cycles exist (A beats B, B beats C, C beats A) | Rock-paper-scissors |
| G4 | RNG variance < 25% (same matchup replayed 100x should show <25% spread) | Skill > luck |
| G5 | Each animal has a distinct strategic identity | No clones |

## What Season 1 Needs

1. **14 animals total** -- the 6 originals (frozen) + 8 new ones
2. **WIL redesign** -- make WIL a meaningful stat without making it dominant
3. **No single dominator** -- bear/boar shouldn't be auto-picks
4. **Wolf/Monkey buff** -- their identities need to work
5. **Non-transitive matchups** -- every animal should beat some and lose to others
6. **Distinct identities** -- each animal should have a clear role that creates interesting stat allocation decisions

## What CANNOT Change (Frozen Core)
- The 6 original animals' passives and abilities
- Stat formulas (HP, ATK, SPD, WIL calculations)
- Combat mechanics (tick order, grid, ring, damage formula)
- 20-point stat budget with min 1 per stat
- Proc rate tiers (3.5% strong, 4.5% standard)
