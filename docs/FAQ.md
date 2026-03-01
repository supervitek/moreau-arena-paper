# Moreau Arena — Frequently Asked Questions

---

### 1. What is Moreau Arena?

Moreau Arena is a contamination-resistant benchmark for evaluating LLM strategic reasoning. Agents design a "build" (an animal plus a stat allocation) for a novel stochastic combat game whose rules are specified only in the prompt. The game is original — it does not exist in any training corpus — so models cannot rely on memorized strategies.

---

### 2. What does the benchmark actually measure?

It measures whether an LLM can derive a strong strategy from a compact rule description under competition. Specifically, it tests formula comprehension, quantitative trade-off reasoning, adaptation to opponent behavior, and the ability to break prior assumptions when given new evidence.

---

### 3. Why two tournaments instead of one?

The two tournaments form a controlled experiment. Tournament 001 (Track A) uses vague descriptions and no feedback — it reveals how models behave with incomplete information. Tournament 002 (Track B) provides exact formulas, meta context, and per-game adaptation. Comparing the same 13 agents across both conditions isolates what changes performance: not model capability itself, but the information scaffolding around it.

---

### 4. What is the "WIL trap"?

In T001, several LLMs systematically over-invested in willpower (WIL), a stat with low marginal utility under the true game mechanics. The qualitative prompt describes WIL as providing "ability resistance" and a "proc bonus," which sounds valuable — but the actual formulas make its returns negligible compared to ATK or HP. Models that pattern-matched RPG archetypes fell into this trap; baselines that allocated stats numerically did not.

---

### 5. How are agents ranked?

The primary ranking method is Bradley-Terry (BT), computed from series outcomes (not individual games) with 95% confidence intervals via 1000-round bootstrap resampling. Elo is computed as a secondary display metric but is not used for formal claims. Each evaluation track has its own independent leaderboard — rankings are never compared across tracks.

---

### 6. Can I submit my own model?

Yes. See `docs/CONTRIBUTING.md` for instructions. You implement the `MoreauAgent` interface (one method for initial build, one for adaptation), specify which track you are running, and submit your JSONL results. Your agent runs against the same frozen config and the same baseline opponents.

---

### 7. Why not use an existing game (chess, poker, Diplomacy)?

Existing games are heavily represented in training data. An LLM that plays chess well may be retrieving openings, not reasoning strategically. Moreau Arena is a novel game — no corpus contains its rules, optimal strategies, or match transcripts. This makes it harder for models to shortcut via memorization and more likely that observed performance reflects actual reasoning.

---

### 8. Is the simulator deterministic?

Yes, given the same seed. Each game in a series uses a deterministic seed derived from the series base seed and the game number. This means any individual game can be replayed exactly. Stochasticity comes from ability procs and movement, but all randomness flows from the seed. The variance budget invariant ensures RNG explains less than 25% of outcomes.

---

### 9. What are the four evaluation tracks?

- **Track A (One-Shot):** Qualitative rules, no feedback, no examples. Run as T001.
- **Track B (Feedback + Counter-Pick):** Exact formulas, meta context, per-game adaptation. Run as T002.
- **Track C (Meta-Conditioned):** Qualitative rules + top-5 build examples, no formulas, no adaptation. Specified but not yet run.
- **Track D (Tool-Augmented):** Exact formulas + limited simulator access, no examples, no adaptation. Specified but not yet run.

Each track isolates one dimension. See `docs/TRACKS.md` for full protocols.

---

### 10. What does "frozen core" mean?

The game configuration (`config.json`) is cryptographically locked. Its SHA-256 hash is verified before every test run. No stat formula, proc rate, grid size, or combat mechanic can change without creating an entirely new core snapshot — which would invalidate all existing tournament data. This guarantees that T001 and T002 results are measured against identical game rules and that future submissions are compared on the same playing field.
