# Canonical Formulas — What the Code Uses vs What Models Saw

> All formulas below are extracted directly from `simulator/config.json` and prompt files.
> Discrepancies between the engine and what LLMs were told are flagged.

---

## Source of Truth: `simulator/config.json`

Config hash: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`

### Stat System

| Parameter | Value |
|-----------|-------|
| Total stat points | 20 |
| Minimum per stat | 1 |
| Stats | hp, atk, spd, wil |

### Core Formulas (from `config.json → stat_system.formulas`)

| Stat | Formula in Config | Notes |
|------|------------------|-------|
| Max HP | `50 + 10 * hp` | Range: 60 (hp=1) to 220 (hp=17) |
| Base Damage | `floor(2 + 0.85 * atk)` | Range: 2 (atk=1) to 16 (atk=17) |
| Movement | `1 if spd<=3, 2 if spd<=6, 3 if spd>=7` | Tiles per tick |
| Dodge | `max(0, min(0.30, 0.025 * (spd - 1)))` | Cap: 30%. spd=1 → 0%, spd=13 → 30% |
| Ability Range | `min(4, ceil(wil / 2))` | Tiles |
| Resist | `max(0, min(0.35, 0.03 * (wil - 1)))` | Cap: 35%. wil=1 → 0%, wil=12 → 33% |
| Ability Power | `1.0 + 0.05 * wil` | Multiplier on ability effects |

### Combat Formulas (from `config.json → combat`)

| Parameter | Value |
|-----------|-------|
| Damage formula | `floor(base_dmg * ability_mod)` |
| Armor cap | 0.5 (50% max damage reduction) |
| Damage variance (epsilon) | [-0.05, +0.05] |
| Minimum damage | 1 |
| Initiative | `spd + seeded_random(0.0, 0.49)` |

### Proc Rates (from `config.json → proc_rates`)

| Tier | Base Rate | Abilities |
|------|----------|-----------|
| Strong | 3.5% | berserker_rage, last_stand, gore, mimic, iron_will, dive, blood_frenzy_ability |
| Standard | 4.5% | All other abilities |
| WIL bonus | +0.08% per WIL point | Additive to base proc rate |
| WIL resist | `min(0.60, wil * 0.033)` | Chance to negate opponent proc |

### Arena

| Parameter | Value |
|-----------|-------|
| Grid | 8 x 8 |
| Max ticks | 60 |
| Ring starts | Tick 30 |
| Ring damage | 2% max HP per tick |

---

## What T001 Prompt Told LLMs

Source: `prompts/t001_prompt.txt`

### Formulas as stated in T001 prompt:

| Stat | T001 Prompt Says |
|------|-----------------|
| Max HP | `max_hp = 50 + 10 * HP` |
| Base Damage | `base_dmg = floor(2 + 0.85 * ATK)` |
| Dodge | `SPD * 2.5% (capped 30%)` |
| Resist | `min(60%, WIL * 3.3%)` |

### Animals offered in T001: 6

Bear, Buffalo, Boar, Tiger, Wolf, Monkey

### Output format: Free text

`Respond ONLY in this exact format: ANIMAL HP ATK SPD WIL`

---

## What T002 Prompt Told LLMs

Source: `prompts/t002_prompt.txt`

### Formulas as stated in T002 prompt:

| Stat | T002 Prompt Says |
|------|-----------------|
| Max HP | `max_hp = 50 + 10 * HP` |
| Base Damage | `base_dmg = floor(2 + 0.85 * ATK)` |
| Dodge | `max(0%, min(30%, 2.5% * (SPD - 1)))` |
| Resist | `min(60%, WIL * 3.3%)` |
| Proc bonus | `WIL * 0.08%` additive |

### Animals offered in T002: 6

Bear, Buffalo, Boar, Tiger, Wolf, Monkey (same as T001)

### Output format: Structured JSON

`{"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}`

### Additional T002 content:

- Worked examples for each formula
- Meta context: top-5 builds from T001 with win rates
- Ability details with proc rates and numeric effects

---

## Discrepancies Between Config and Prompts

### 1. Dodge formula

| Source | Formula |
|--------|---------|
| **config.json** | `max(0, min(0.30, 0.025 * (spd - 1)))` |
| **T001 prompt** | `SPD * 2.5% (capped 30%)` |
| **T002 prompt** | `max(0%, min(30%, 2.5% * (SPD - 1)))` |

**Analysis:** Config and T002 agree: `0.025 * (spd - 1)` with cap at 0.30. T001 simplifies to `SPD * 2.5%` without the `- 1` offset. This means T001 overstates dodge for any given SPD by 2.5 percentage points. At SPD=1, config gives 0% dodge but T001 implies 2.5%.

**Impact:** LLMs in T001 may have slightly overvalued SPD due to this discrepancy.

### 2. Resist formula

| Source | Formula |
|--------|---------|
| **config.json** | `max(0, min(0.35, 0.03 * (wil - 1)))` → cap 35% |
| **T001 prompt** | `min(60%, WIL * 3.3%)` → cap 60% |
| **T002 prompt** | `min(60%, WIL * 3.3%)` → cap 60% |

**Analysis:** Significant discrepancy. The engine caps resist at 35% using `0.03 * (wil - 1)`, but both prompts state `WIL * 3.3%` capped at 60%. Additionally, the `proc_rates` section has a separate WIL resist formula: `min(0.60, wil * 0.033)` which matches the prompts, not the stat_system formula.

**Impact:** The engine has two resist-related calculations — one in stat_system (35% cap) and one in proc_rates (60% cap). The prompts reference the proc_rates version. This is a known complexity in the system, not a bug — the 35%-cap resist affects ability power scaling while the 60%-cap resist affects ability proc resistance.

### 3. Animals available vs animals in roster

| Source | Animal Count |
|--------|-------------|
| **config.json** | 14 animals defined (bear, buffalo, boar, tiger, wolf, monkey, crocodile, eagle, snake, raven, shark, owl, fox, scorpion) |
| **T001 prompt** | 6 animals offered (bear, buffalo, boar, tiger, wolf, monkey) |
| **T002 prompt** | 6 animals offered (same 6) |
| **Baselines** | Use animals from full roster (RandomAgent uses raven) |

**Impact:** LLMs could only choose from 6/14 animals. Baselines like RandomAgent used `raven`, which was not offered to LLMs. This is documented as a known asymmetry — see the Animals section in RESULTS_SUMMARY.md.

### 4. Damage formula simplification

| Source | Formula |
|--------|---------|
| **config.json** | `base_dmg = floor(2 + 0.85 * atk)` |
| **T001 prompt** | `base_dmg = floor(2 + 0.85 * ATK)` |
| **T002 prompt** | `base_dmg = floor(2 + 0.85 * ATK)` |

**Analysis:** All three agree exactly.

### 5. HP formula

| Source | Formula |
|--------|---------|
| **config.json** | `max_hp = 50 + 10 * hp` |
| **T001 prompt** | `max_hp = 50 + 10 * HP` |
| **T002 prompt** | `max_hp = 50 + 10 * HP` |

**Analysis:** All three agree exactly.
