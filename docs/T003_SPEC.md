# Tournament 003: Exact-Only Cleanroom (No Meta Context)

## Hypothesis

T002 introduced four changes over T001 simultaneously: exact formulas, meta-context (top builds), JSON output format, and loser-adapts-build adaptation. LLM average win rate jumped from 46.5% to 60.9%. **Which change drove the improvement?**

T003 isolates one variable: **meta-context is removed while all other T002 improvements are retained.** If LLMs maintain >70% average win rate without being told "BEAR 8/8/3/1 had 100% win rate," then comprehension of exact mechanics — not copy-paste of winning strategies — was the bottleneck in T001.

## Design

| Aspect | T001 | T002 | T003 |
|--------|------|------|------|
| Exact stat formulas | Yes (brief) | Yes (with examples) | **Yes (with examples)** |
| Exact ability parameters | No | Yes | **Yes** |
| Combat tick order | No | Yes | **Yes** |
| Meta-context (top builds) | No | Yes | **No** |
| Output format | Text | JSON | **JSON** |
| Adaptation (loser re-picks) | No | Yes | **Yes** |
| Animals available | 6 | 6 | **6** |

T003 = T002 minus meta-context. This is the cleanest ablation possible: same formulas, same JSON schema, same adaptation mechanic, but zero strategy hints.

## What Was Removed from T002 Prompt

The following lines from `prompts/t002_prompt.txt` are absent in `prompts/t003_prompt.txt`:

```
META CONTEXT (top builds from previous tournament, ranked by win rate):
  1. BEAR 8/8/3/1 — 100% win rate (22 games)
  2. BEAR 8/10/1/1 — 100% win rate (19 games)
  3. BEAR 10/8/1/1 — 100% win rate (11 games)
  4. BEAR 9/9/1/1 — 100% win rate (4 games)
  5. WOLF 7/10/2/1 — 100% win rate (4 games)
  Note: These builds were tested in blind pick (no adaptation). You can counter them or use them as a starting point.
```

This block gives LLMs three advantages that T003 removes:
1. **Animal selection bias** — 4/5 top builds are Bear, heavily biasing LLMs toward Bear
2. **Stat distribution hints** — all top builds dump ATK (8–10), minimize SPD and WIL (1–3)
3. **Strategy anchoring** — "you can counter them or use them as a starting point" frames the problem as iteration, not exploration

## Configuration

| Field | Value |
|-------|-------|
| **Tournament ID** | `T003` |
| **Track** | Exact-Only Cleanroom |
| **Config SHA-256** | `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` |
| **Prompt file** | `prompts/t003_prompt.txt` |
| **Prompt SHA-256** | `a599ca7dacb21a59ebeda1ed434463c6ddcf3fdcba280e4ff2e9afc5335e524b` |
| **Baselines** | SmartAgent, ConservativeAgent, GreedyAgent, HighVarianceAgent, RandomAgent (5) |
| **LLMs** | 10 (see roster below) |
| **Seeds** | Same seed schedule as T001/T002 |
| **Series per pair** | 10 (15 agents × C(15,2) = 105 pairs × 10 = 1050 series) |
| **Adaptation** | Loser re-picks build after seeing opponent's build (same as T002) |

## Agent Roster

### Core (T001/T002 veterans)

| # | Display Name | Provider | Model ID | API | Status |
|---|-------------|----------|----------|-----|--------|
| 1 | Cl. Opus 4.6 | Anthropic | `claude-opus-4-6` | Messages | PASS |
| 2 | Cl. Sonnet 4.6 | Anthropic | `claude-sonnet-4-6` | Messages | PASS |
| 3 | Cl. Haiku 4.5 | Anthropic | `claude-haiku-4-5-20251001` | Messages | PASS |
| 4 | GPT-5.2 | OpenAI | `gpt-5.2` | Chat Completions | PASS |
| 5 | GPT-5.2-Codex | OpenAI | `gpt-5.2-codex` | Responses | PASS |
| 6 | Gemini Flash | Google | `gemini-3-flash-preview` | GenerativeAI | PASS |
| 7 | Gemini Pro | Google | `gemini-3.1-pro-preview` | GenerativeAI | PASS |
| 8 | Grok-4.1 Fast | xAI | `grok-4-1-fast-reasoning` | OpenAI-compat | PASS |

### New Challengers

| # | Display Name | Provider | Model ID | API | Status |
|---|-------------|----------|----------|-----|--------|
| 9 | GPT-5.4 | OpenAI | `gpt-5.4` | Chat Completions | PASS |
| 10 | GPT-5.3-Codex | OpenAI | `gpt-5.3-codex` | Responses | PASS |

### API Notes

- **OpenAI Chat Completions**: Uses `max_completion_tokens` (not `max_tokens`) for gpt-5.x models
- **OpenAI Responses API**: Codex models (gpt-5.2-codex, gpt-5.3-codex) do not support Chat Completions; use `/v1/responses` endpoint instead
- **xAI**: Reasoning models reject `max_completion_tokens` / `max_tokens` — omit token limit and let server default.
- **gpt-5.4-mini**: Does NOT exist in OpenAI model list (404). Removed from roster.

## Success Criteria

**If LLMs maintain >70% average win rate:**
- Comprehension was the bottleneck, not strategy hints
- Exact formulas + worked examples are sufficient for LLMs to derive strong builds independently
- Meta-context in T002 was helpful but not necessary
- Implication: LLMs can reason from mechanics, they just need unambiguous specifications

## Failure Criteria

**If LLMs drop back toward T001 levels (~46.5% avg win rate):**
- Meta-context was doing the heavy lifting
- LLMs struggle to derive strategy from formulas alone despite having exact numbers
- The T002 improvement was largely "give the model good starting builds to copy/counter"
- Implication: LLMs need worked examples of strategy, not just mechanics

## Intermediate Outcomes

**If LLMs land between 50–70% average win rate:**
- Meta-context provided a meaningful boost but wasn't the sole driver
- Formulas contribute some independent improvement over T001
- Suggests a partial comprehension effect — LLMs can reason somewhat from formulas but benefit significantly from strategic examples

## Execution Checklist

- [x] Prompt created (`prompts/t003_prompt.txt`)
- [x] Prompt hash verified
- [x] Meta-context lines confirmed removed
- [x] Exact formulas confirmed retained
- [x] JSON output format confirmed retained
- [ ] Tournament runner configured for T003
- [ ] All 780 series completed
- [ ] Results written to `data/tournament_003/results.jsonl`
- [ ] BT rankings computed
- [ ] T003 tournament doc created (`docs/tournaments/T003.md`)
- [ ] Comparative analysis: T003 vs T001 vs T002
