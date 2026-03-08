# Brainstorm Comparison: 8 Models, 2 Councils

Two Round Table sessions brainstormed Moreau Arena Seasons 2-5.

## Session 1: Frontier APIs ($0.94)
**Models**: claude-opus-4-6, claude-sonnet-4-6, gpt-5.4, gpt-5.2
**Moderator**: claude-opus-4-6
**Full results**: `council_records/2026-03-08_0501_*.md`

## Session 2: Ollama Cloud ($0.00)
**Models**: deepseek-v3.2:cloud, kimi-k2.5:cloud, qwen3-next:80b-cloud, cogito-2.1:671b-cloud
**Moderator**: kimi-k2.5:cloud
**Full results**: `council_records/2026-03-08_0512_*.md`

---

## Cross-Council Consensus (appeared in BOTH sessions)

These ideas were endorsed by models from both councils — strongest signal:

| # | Idea | API Council | Ollama Council |
|---|------|-------------|----------------|
| 1 | **Hex grid** with 6-directional movement | 4/4 | 3/3* |
| 2 | **Elevation tiles** (high ground bonuses) | 4/4 | 3/3 |
| 3 | **Ice tiles** (slide 2 extra tiles) | 4/4 | 3/3 |
| 4 | **Destructible walls** (shatter into rubble) | 4/4 | 3/3 |
| 5 | **Fog of war** (limited vision) | 4/4 | 3/3 |
| 6 | **Flooding/rising water** | 4/4 | 3/3 |
| 7 | **Teleporter pairs** | 4/4 | 3/3 |
| 8 | **Bleeding/DoT stacking** | 4/4 | 3/3 |
| 9 | **Persistent limb damage** across series | 4/4 | 3/3 |
| 10 | **Fatigue/stamina** system | 4/4 | 3/3 |
| 11 | **Adrenaline surge** (low HP burst) | 4/4 | 3/3 |
| 12 | **Combo/sequencing** attacks | 4/4 | 3/3 |
| 13 | **2v2 team battles** | 4/4 | 3/3 |
| 14 | **King of the Hill** mode | 4/4 | 3/3 |
| 15 | **Mutation/evolution between rounds** | 4/4 | 3/3 |
| 16 | **Breeding/hybrid animals** | 4/4 | 3/3 |
| 17 | **Boss creatures** | 4/4 | 3/3 |
| 18 | **Prediction markets** | 4/4 | 3/3 |
| 19 | **Replay analysis tools** | 4/4 | 3/3 |
| 20 | **Community map editor** | 4/4 | 3/3 |
| 21 | **Modding API** | 4/4 | 3/3 |
| 22 | **Lava/fire zones** | 3/4 | 3/3 |
| 23 | **Lightning strikes** | 3/4 | 3/3 |
| 24 | **Earthquake events** | 3/4 | 3/3 |
| 25 | **Day/night cycle** | 4/4 | 3/3 |
| 26 | **Draft/ban system** | 4/4 | implied |
| 27 | **Faction lore** | 4/4 | 3/3 |
| 28 | **Seasonal championships** | 3/4 | 3/3 |

*DeepSeek V3.2 returned empty responses; scores are out of 3 responding models.

---

## Unique Gems (single council only)

### API Council Only
- **Symbiote attachment** (Opus) — parasite granting passive ability, animal-flavored equipment
- **Corpse mechanic** (Opus) — scavengers eat fallen opponents for healing
- **Pack tactics 3v3 micro** (Opus) — control 3 weaker animals
- **Asymmetric nest defense** (Opus) — attacker/defender roles with swap
- **Trap-setting mechanic** (Sonnet) — species-specific area denial
- **Spectator crowd voting** (Sonnet, rejected for ranked — casual mode only)

### Ollama Council Only
- **Echo Positioning** (Cogito) — afterimages showing positions from 5 ticks ago
- **Dynamic sound propagation** (Cogito) — combat noise attracts neutral predators
- **Firewalk mechanic** (Kimi) — lava immunity when adjacent to water
- **DNA Splicer** (Kimi) — JSON-based custom animal creation
- **Equipment durability** (Kimi) — gear breaks after N blocks
- **Quadrant rotation** (Kimi, controversial — rejected by others as disorienting)
- **Pre-combat negotiation** (Qwen) — 10-tick alliance formation with betrayal

---

## Rejected by Both Councils
- **Quantum superposition** (existing in multiple tiles)
- **Gravity inversion** (180° board flips)
- **Random stat variance** (hidden numerical fuzz)
- **Mid-combat breeding** (disrupts pacing)
- **Spectator voting in ranked** (competitive integrity)

---

## Proposed Season Roadmap (merged from both councils)

### Season 2: "The Thaw"
- Hex grid (12-radius), 3-tier elevation, ice slide physics
- Persistent limb damage, adrenaline surge, fatigue system
- Destructible walls, fog of war with blood-trail reveals
- Draft/ban phase for competitive play

### Season 3: "Echoes"
- Echo Positioning (temporal afterimages)
- Elemental terrain synergies (firewalk, electric water)
- 2v2 Symbiotic Mode with support mechanics
- Replay tools: heatmaps, decision-point annotations

### Season 4: "The Shifting Earth"
- Dynamic hazards: spreading lava, rising floods, seismic shifts
- Sound propagation attracting neutral predators
- Community map editor + modding API
- Boss creatures as seasonal PvE content

### Season 5: "The Grand Tournament"
- Between-round breeding/mutation (genetic splicing)
- Prediction markets + seasonal championships
- Faction wars altering terrain themes
- Pre-combat negotiation for high-stakes matches

---

## Cost Comparison

| Session | Models | Cost | Ideas |
|---------|--------|------|-------|
| API Council | Opus, Sonnet, GPT-5.4, GPT-5.2 | $0.94 | 200 (50 × 4) |
| Ollama Cloud | DeepSeek V3.2, Kimi K2.5, Qwen3 80B, Cogito 671B | $0.00 | ~150 (50 × 3, DeepSeek empty) |
| **Total** | **8 models** | **$0.94** | **~350 ideas** |

The Ollama Cloud council produced comparable quality synthesis at zero cost, though
DeepSeek V3.2 failed to respond (known issue with empty outputs). Kimi K2.5 was the
strongest Ollama performer both as panelist and moderator.
