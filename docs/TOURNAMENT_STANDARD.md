# Tournament Documentation Standard

Every Moreau Arena tournament MUST have a self-contained markdown document following the 7-section format below. All numbers come from raw data files — never hard-coded or estimated.

---

## Required Sections

### 1. IDENTITY

| Field | Description |
|-------|-------------|
| **Tournament ID** | Unique identifier (e.g., `T001`) |
| **Track** | Track letter and name (e.g., `A — Fixed Strategy`) |
| **Status** | `complete` · `in-progress` · `planned` |
| **Date range** | ISO dates of first and last game |
| **Data file** | Relative path to JSONL (e.g., `data/tournament_001/results.jsonl`) |
| **Prompt file** | Relative path to prompt text |
| **Prompt SHA-256** | Full hash of the prompt file |
| **Config SHA-256** | `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` (must match frozen config) |

### 2. DESIGN

Brief prose describing:
- What capability this tournament evaluates
- Prompt strategy (minimal, engineered, adaptive, tool-augmented, etc.)
- Key differences from previous tournaments (if any)
- Output format required from agents
- Any special mechanics (adaptation, meta-conditioning, tool access)

### 3. AGENTS

Table of all participating agents:

| Agent | Type | Provider | Model ID |
|-------|------|----------|----------|
| Name  | `llm` · `baseline` | Provider name or `built-in` | Model string or `—` |

Include counts: `N agents (X LLMs + Y baselines)`

### 4. RESULTS — BRADLEY-TERRY RANKINGS

Full BT rankings table with bootstrap confidence intervals (N=1000, seed=42):

| Rank | Agent | BT Score | 95% CI |
|------|-------|----------|--------|
| 1 | ... | 1.0000 | [low, high] |

Include summary statistics:
- Total series and games
- Error count, draw count
- Games per series (mean, min, max)

### 5. KEY FINDINGS

Bullet-point list of the most important observations:
- Which agent types dominate and why
- Notable rank changes from previous tournament (if applicable)
- Prompt engineering effects on LLM vs baseline performance
- Statistical significance of top rankings (CI overlap analysis)

### 6. PROMPT

Full text of the prompt used, in a fenced code block. Hash must match the value in §1.

### 7. WHAT CHANGED (from previous tournament)

*Required for T002+. Omit for T001.*

Structured diff from the previous tournament:

| Aspect | Previous | Current |
|--------|----------|---------|
| Prompt length | X lines | Y lines |
| Output format | ... | ... |
| Mechanics | ... | ... |

Then prose analysis of how each change affected rankings.

---

## File Locations

```
docs/
├── TOURNAMENT_STANDARD.md          ← this file
└── tournaments/
    ├── TOURNAMENT_INDEX.md          ← master index
    ├── T001.md
    ├── T002.md
    └── ...
```

## Generation

Use `scripts/generate_tournament_doc.py` to auto-generate a skeleton from JSONL + prompt files:

```bash
python scripts/generate_tournament_doc.py \
    --tournament-id T001 \
    --track A \
    --data data/tournament_001/results.jsonl \
    --prompt prompts/t001_prompt.txt \
    --output docs/tournaments/T001.md
```

## Integrity Rules

1. **All numbers must come from raw data files** — never manually typed
2. **Frozen files are never modified** — config.json, data/tournament_00X/*
3. **Prompt hash must be independently verifiable**: `sha256sum prompts/tXXX_prompt.txt`
4. **Config hash must match**: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534`
5. **BT scores use standard parameters**: N_bootstrap=1000, seed=42
