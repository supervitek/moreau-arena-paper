# Moreau Arena -- Game Mechanics

Complete reference for the Variant C combat engine used in both tournaments.

## Overview

Two creatures fight on an 8x8 grid for up to 60 ticks. Each creature selects one of 6 animals and distributes 20 stat points across four attributes (HP, ATK, SPD, WIL), with a minimum of 1 in each. The creature that kills its opponent or has more HP when time runs out (or when the ring closes) wins.

## Stat Formulas

### Hit Points

```
max_hp = 50 + 10 * HP
```

| HP | max_hp |
|----|--------|
| 1  | 60     |
| 3  | 80     |
| 8  | 130    |
| 14 | 190    |

### Base Damage

```
base_dmg = floor(2 + 0.85 * ATK)
```

| ATK | base_dmg |
|-----|----------|
| 1   | 2        |
| 5   | 6        |
| 8   | 8        |
| 14  | 13       |

### Dodge Chance

```
dodge = max(0%, min(30%, 2.5% * (SPD - 1)))
```

SPD 1 gives 0% dodge. Each additional point of SPD adds 2.5%, capped at 30%.

| SPD | dodge |
|-----|-------|
| 1   | 0%    |
| 3   | 5%    |
| 5   | 10%   |
| 13  | 30%   |

### Ability Resist

```
resist = min(60%, WIL * 3.3%)
```

Resist reduces the chance that an opponent's ability procs against you.

| WIL | resist |
|-----|--------|
| 1   | 3.3%   |
| 5   | 16.5%  |
| 10  | 33%    |
| 18  | 59.4%  |

### Ability Proc Bonus

```
proc_bonus = WIL * 0.08% (additive)
```

Each point of WIL adds 0.08% to your own abilities' proc rate.

## Animals

### Bear

**Passive -- Fury Protocol:** When HP drops below 50%, Bear gains bonus ATK. The enraged bear hits harder the closer it gets to death.

**Abilities:**
- **Berserker Rage** (strong tier, 3.5% base proc): Temporary massive damage boost. Devastating when combined with Fury Protocol at low HP.
- **Last Stand** (strong tier, 3.5% base proc): Survives a killing blow with 1 HP and retaliates. A single-use lifeline.

### Buffalo

**Passive -- Thick Hide:** The first hit received deals 50% reduced damage. Gives Buffalo a free cushion at the start of every fight.

**Abilities:**
- **Thick Hide Block** (standard tier, 4.5% base proc): Blocks incoming damage entirely for one hit.
- **Iron Will** (strong tier, 3.5% base proc): Temporary resist boost, reducing incoming ability effects.

### Boar

**Passive -- Charge:** The first attack Boar lands deals 1.5x damage. Rewards aggressive openers.

**Abilities:**
- **Stampede** (standard tier, 4.5% base proc): AoE knockback-style attack.
- **Gore** (strong tier, 3.5% base proc): High-damage single-target hit with bonus penetration.

### Tiger

**Passive -- Ambush:** If Tiger has higher SPD than the opponent, the first attack deals 2x damage. Rewards SPD investment.

**Abilities:**
- **Pounce** (standard tier, 4.5% base proc): Gap-closing attack that ignores distance.
- **Hamstring** (standard tier, 4.5% base proc): Reduces opponent's SPD temporarily, making follow-up attacks harder to dodge.

### Wolf

**Passive -- Pack Sense:** Adds a flat +1.5% to all ability proc rates. Makes Wolf the most ability-reliant animal.

**Abilities:**
- **Pack Howl** (standard tier, 4.5% base proc): Buff that increases Wolf's stats temporarily.
- **Rend** (standard tier, 4.5% base proc): Bleeding effect that deals damage over time.

### Monkey

**Passive -- Primate Cortex:** Copies a random ability from the opponent. The wildcard animal -- strongest when facing strong-ability opponents.

**Abilities:**
- **Chaos Strike** (standard tier, 4.5% base proc): Randomized damage with high variance.
- **Mimic** (strong tier, 3.5% base proc): Copies the opponent's passive for the rest of the fight.

## Ability Proc Rates

Abilities have two tiers:

| Tier | Base Proc Rate | Abilities |
|------|---------------|-----------|
| Strong | 3.5% | Berserker Rage, Last Stand, Gore, Mimic, Iron Will |
| Standard | 4.5% | Stampede, Pounce, Hamstring, Pack Howl, Rend, Chaos Strike |

The actual proc chance per tick is:

```
effective_proc = base_proc + proc_bonus - opponent_resist
```

Where `proc_bonus = WIL * 0.08%` and `opponent_resist = min(60%, opponent_WIL * 3.3%)`.

## Ring Mechanics

The ring creates a closing danger zone that forces combat and prevents stalling.

- **Tick 30:** The ring activates. A safe zone is defined on the grid.
- **Tick 31+:** The safe zone shrinks each tick.
- **Damage:** Creatures outside the safe zone take **2% of their max_hp per tick** as ring damage.
- **Purpose:** Forces creatures toward the center, guaranteeing that fights end before tick 60.

A creature with high HP does not gain extra survivability against the ring -- ring damage is percentage-based. This prevents HP-stacking stall strategies.

## Series Format

### Tournament 001 -- Blind Pick Best-of-7

Each agent submits a build once (animal + stat allocation). The same build is used for all 7 games in the series. Neither agent knows what the other picked. First to 4 wins takes the series.

### Tournament 002 -- Adaptive Best-of-7

First to 4 wins takes the series. After each game, the **loser** sees the winner's exact build (animal, HP, ATK, SPD, WIL). The loser then re-picks their build for the next game. The winner keeps their build. This tests an agent's ability to **adapt** -- to analyze why it lost and construct a counter-build.

Key implications:
- Winning game 1 with a dominant build is valuable (opponent must crack it while you hold).
- Adaptation ability separates top models from weak ones.
- The meta shifts toward builds that are hard to counter.

## Why ATK Stacking Works

The dominant meta in Tournament 002 is BEAR 8/10/1/1 and similar high-ATK builds. Here is why:

**Damage scaling outpaces HP scaling.**

- Each point of ATK adds roughly 0.85 base damage per tick.
- Each point of HP adds 10 max HP.
- Over 60 ticks, 1 ATK point contributes ~51 total damage (0.85 * 60).
- 1 HP point absorbs 10 damage.
- The ratio is roughly **5:1 in favor of ATK**.

**Concrete comparison:**

| Build | max_hp | base_dmg | Potential damage (60 ticks) |
|-------|--------|----------|-----------------------------|
| ATK-heavy: Bear 3/14/2/1 | 80 | 13 | 780 |
| HP-heavy: Buffalo 14/3/2/1 | 190 | 4 | 240 |

The ATK-heavy build kills the HP-heavy build in roughly 15 ticks (190 / 13). The HP-heavy build needs roughly 20 ticks (80 / 4). ATK wins the expected value race.

**Additional factors:**
- Bear's Fury Protocol adds even more ATK below 50% HP, creating a death spiral for the opponent.
- SPD=2 gives 2.5% dodge, which is marginal. The opportunity cost of investing in SPD or WIL is losing ATK.
- The only viable counter is extreme dodge builds (SPD 13+), but those sacrifice damage.

This is why BEAR 8/10/1/1 achieved a 78% win rate across 887 uses in Tournament 002 -- it is the meta-defining build.
