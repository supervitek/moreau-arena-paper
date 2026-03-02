# Match Record Format (MMR) Specification v1.1

This document defines the canonical schema for Moreau Arena match records stored as JSONL (one JSON object per line). Version 1.1 extends the v1.0 format used in T001/T002 with additional fields for reproducibility, provenance, and adaptation tracking.

---

## 1. File Format

- **Encoding:** UTF-8, no BOM.
- **Line format:** One valid JSON object per line, no trailing commas.
- **Extension:** `.jsonl`
- **Empty lines and lines that fail JSON parsing are skipped by consumers.**

---

## 2. Record Structure

Each line represents one **series** (a best-of-N encounter between two agents). A series contains multiple games.

### 2.1 Current Fields (v1.0 -- present in T001/T002 data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series_id` | string | yes | Unique identifier for the series. Format: `{agent_a}_vs_{agent_b}_s{NNN}` |
| `pair_index` | int | yes | Index of this agent pair in the tournament schedule (0-indexed) |
| `series_index` | int | yes | Which series this is for the same pair (0-indexed, 0..9 for 10 series/pair) |
| `agent_a` | string | yes | Name/identifier of agent A |
| `agent_b` | string | yes | Name/identifier of agent B |
| `is_llm_a` | bool | yes | Whether agent A is an LLM (true) or a baseline/heuristic agent (false) |
| `is_llm_b` | bool | yes | Whether agent B is an LLM |
| `winner` | string | yes | Name of the series winner. Null if error prevented completion |
| `score_a` | int | yes | Number of games won by agent A in this series |
| `score_b` | int | yes | Number of games won by agent B in this series |
| `games_played` | int | yes | Total games played in this series (4-7 for best-of-7) |
| `games` | array | yes | Per-game records (see Section 2.2) |
| `base_seed` | int | yes | Base seed for this series. Game seeds are `base_seed + game_index` |
| `duration_s` | float | yes | Wall-clock duration of the series in seconds |
| `error` | string or null | yes | Error message if the series failed, null otherwise |

#### T001-specific fields (v1.0)

In T001 (one-shot protocol), builds are stored at the **series level** because they do not change between games:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `build_a` | object | yes (T001) | Agent A's build: `{animal, hp, atk, spd, wil}` |
| `build_b` | object | yes (T001) | Agent B's build: `{animal, hp, atk, spd, wil}` |

#### T002-specific differences (v1.0)

In T002 (adaptive protocol), builds are stored at the **game level** because the loser may change builds between games. Series-level `build_a`/`build_b` fields are absent.

### 2.2 Per-Game Record (v1.0)

Each element of the `games` array has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_number` | int | yes | 1-indexed game number within the series |
| `winner` | string | yes | Name of the game winner |
| `seed` | int | yes | Deterministic seed for this game (`base_seed + game_number - 1`) |
| `ticks` | int | yes | Number of ticks the game lasted (1-60) |

#### T002 per-game additions (v1.0)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `build_a` | object | yes (T002) | Agent A's build for this specific game |
| `build_b` | object | yes (T002) | Agent B's build for this specific game |
| `adapted` | bool | yes (T002) | Whether the loser adapted (changed build) since the previous game. Always `false` for game 1 |

### 2.3 Build Object

The build object appears in both series-level (T001) and game-level (T002) contexts:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `animal` | string | yes | Animal type, lowercase (e.g., `"bear"`, `"wolf"`, `"boar"`) |
| `hp` | int | yes | HP stat allocation (>= 1) |
| `atk` | int | yes | ATK stat allocation (>= 1) |
| `spd` | int | yes | SPD stat allocation (>= 1) |
| `wil` | int | yes | WIL stat allocation (>= 1) |

**Constraint:** `hp + atk + spd + wil == 20` and each >= 1.

**Valid animals (v1.0):** `bear`, `buffalo`, `boar`, `tiger`, `wolf`, `monkey`, `crocodile`, `eagle`, `snake`, `raven`, `shark`, `owl`, `fox`, `scorpion`.

---

## 3. New Fields (v1.1)

The following fields are **added** in v1.1. They appear at the series level unless otherwise noted.

### 3.1 Environment Provenance

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `env_hash` | string | yes | - | SHA-256 hex digest of the `config.json` file used. Current value: `b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534` |
| `rules_version` | string | yes | - | Semantic version of the game rules (e.g., `"1.0.0"`). Bumped when any outcome-affecting parameter in config.json changes |
| `seed_scheme` | string | yes | - | Human-readable description of the seed derivation method. For the current implementation: `"SHA-256 deterministic: tick_seed=SHA256(match_seed:u64||tick_index:u32)[0:4], hit_seed=SHA256(match_seed:u64||tick_index:u32||attack_index:u32)[0:4], proc_seed=SHA256(match_seed:u64||tick_index:u32||creature_index:u8||ability_index:u8)[0:4], random=SHA256(seed:u32)[0:8]->u64/2^64"` |

### 3.2 Prompt Provenance

These fields appear at the **series level** if the same prompt is used for all games, or at the **game level** if prompts differ per game.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `prompt_hash` | string | yes | - | SHA-256 hex digest of the exact prompt text sent to the model (after template rendering, before model invocation) |
| `prompt_version` | string | yes | - | Human-readable version tag (e.g., `"t001_v1"`, `"t002_v1"`, `"t003_meta_v1"`) |

**Notes:**
- For agents with different prompts for agent A vs agent B, store `prompt_hash_a` and `prompt_hash_b` instead.
- For baseline (non-LLM) agents, `prompt_hash` should be `"N/A"` and `prompt_version` should be `"baseline"`.

### 3.3 Decode Parameters

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `decode_params` | object | yes | - | Model inference parameters (see below) |

The `decode_params` object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `temperature` | float | yes | Sampling temperature (e.g., `0.0`, `0.7`, `1.0`) |
| `top_p` | float | yes | Nucleus sampling threshold (e.g., `1.0`) |
| `max_tokens` | int | yes | Maximum tokens in the model response (e.g., `256`, `1024`) |
| `provider` | string | yes | API provider (e.g., `"anthropic"`, `"openai"`, `"google"`, `"xai"`) |
| `model_id` | string | yes | Exact model identifier as passed to the API (e.g., `"claude-opus-4-6"`, `"gpt-5.2"`, `"gemini-3-flash-preview"`) |

**Notes:**
- For baseline agents, `decode_params` should be `{"temperature": null, "top_p": null, "max_tokens": null, "provider": "local", "model_id": "baseline"}`.
- If agents A and B use different models, store `decode_params_a` and `decode_params_b` instead of a single `decode_params`.

### 3.4 Output Verification

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `raw_output_digest` | string | per-game | - | SHA-256 hex digest of the model's raw text response (before parsing). Stored in each game record |

### 3.5 Parse Results

These fields appear at the **game level** (inside each element of `games`):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `parsed_build` | object | yes | - | The build object as parsed from the model output. Same schema as the build object (Section 2.3). This is the canonical build used for simulation |
| `parse_warnings` | array of string | yes | `[]` | List of warnings generated during parsing (e.g., `"stats sum to 21, clamped atk from 15 to 14"`, `"unknown animal 'lion', defaulted to random"`) |

### 3.6 Adaptation Log

This field appears at the **series level** for adaptive tracks (Track B and similar). It is omitted for one-shot tracks.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `adaptation_log` | array of object | conditional | - | One entry per game in the series (see below) |

Each element of `adaptation_log`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_number` | int | yes | 1-indexed game number |
| `changed` | bool | yes | Whether the losing agent changed its build for this game. Always `false` for game 1 |
| `reason` | string | yes | Why the change occurred. Values: `"initial"` (game 1), `"counter_pick"` (loser adapted), `"no_change"` (loser kept same build), `"winner_locked"` (winner cannot change) |
| `old_build` | object or null | yes | The previous build, or null for game 1 |
| `new_build` | object | yes | The build used for this game |

---

## 4. Complete v1.1 Series Record Example

```json
{
  "series_id": "gpt-5.2-codex_vs_claude-opus-4-6_s003",
  "pair_index": 15,
  "series_index": 3,
  "agent_a": "gpt-5.2-codex",
  "agent_b": "claude-opus-4-6",
  "is_llm_a": true,
  "is_llm_b": true,
  "env_hash": "b7ec588583135ad640eba438f29ce45c10307a88dc426decd31126371bb60534",
  "rules_version": "1.0.0",
  "seed_scheme": "SHA-256 deterministic: tick=SHA256(match||tick)[0:4], hit=SHA256(match||tick||atk)[0:4], proc=SHA256(match||tick||creature||ability)[0:4]",
  "prompt_hash_a": "a1b2c3d4e5f6...",
  "prompt_hash_b": "f6e5d4c3b2a1...",
  "prompt_version": "t002_v1",
  "decode_params_a": {
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 256,
    "provider": "openai",
    "model_id": "gpt-5.2-codex"
  },
  "decode_params_b": {
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 256,
    "provider": "anthropic",
    "model_id": "claude-opus-4-6"
  },
  "winner": "gpt-5.2-codex",
  "score_a": 4,
  "score_b": 1,
  "games_played": 5,
  "games": [
    {
      "game_number": 1,
      "build_a": {"animal": "bear", "hp": 8, "atk": 10, "spd": 1, "wil": 1},
      "build_b": {"animal": "bear", "hp": 8, "atk": 8, "spd": 3, "wil": 1},
      "winner": "gpt-5.2-codex",
      "seed": 153000,
      "ticks": 42,
      "adapted": false,
      "raw_output_digest": "e3b0c44298fc...",
      "parsed_build": {"animal": "bear", "hp": 8, "atk": 10, "spd": 1, "wil": 1},
      "parse_warnings": []
    },
    {
      "game_number": 2,
      "build_a": {"animal": "bear", "hp": 8, "atk": 10, "spd": 1, "wil": 1},
      "build_b": {"animal": "buffalo", "hp": 10, "atk": 8, "spd": 1, "wil": 1},
      "winner": "gpt-5.2-codex",
      "seed": 153001,
      "ticks": 55,
      "adapted": true,
      "raw_output_digest": "d4735e3a265e...",
      "parsed_build": {"animal": "buffalo", "hp": 10, "atk": 8, "spd": 1, "wil": 1},
      "parse_warnings": []
    }
  ],
  "adaptation_log": [
    {
      "game_number": 1,
      "changed": false,
      "reason": "initial",
      "old_build": null,
      "new_build": {"animal": "bear", "hp": 8, "atk": 8, "spd": 3, "wil": 1}
    },
    {
      "game_number": 2,
      "changed": true,
      "reason": "counter_pick",
      "old_build": {"animal": "bear", "hp": 8, "atk": 8, "spd": 3, "wil": 1},
      "new_build": {"animal": "buffalo", "hp": 10, "atk": 8, "spd": 1, "wil": 1}
    }
  ],
  "base_seed": 153000,
  "duration_s": 2.45,
  "error": null
}
```

---

## 5. Backward Compatibility

### 5.1 v1.0 to v1.1 Migration

Existing T001 and T002 JSONL files are valid v1.0 records. They do NOT contain the v1.1 fields (`env_hash`, `rules_version`, `seed_scheme`, `prompt_hash`, `prompt_version`, `decode_params`, `raw_output_digest`, `parsed_build`, `parse_warnings`, `adaptation_log`).

Consumers of v1.1 data must treat all v1.1 fields as **optional** when reading v1.0 files. Missing fields should be treated as:
- `env_hash`: Can be retroactively computed from the archived config.json.
- `rules_version`: `"1.0.0"` for all T001/T002 data.
- `seed_scheme`: Known from the codebase; can be retroactively populated.
- `prompt_hash`: Can be retroactively computed from archived prompt files.
- `prompt_version`: `"t001_v1"` for T001, `"t002_v1"` for T002.
- `decode_params`: Not recoverable if not logged at runtime. Mark as `null`.
- `raw_output_digest`: Not recoverable retroactively. Mark as `null`.
- `parsed_build`: Equivalent to the `build_a`/`build_b` fields already present.
- `parse_warnings`: Assume `[]` (no warnings recorded).
- `adaptation_log`: Can be reconstructed from T002 game-level `adapted` and `build_*` fields.

### 5.2 Version Detection

Consumers should check for the presence of `env_hash` to distinguish v1.1 records from v1.0. Alternatively, check for `rules_version`.

---

## 6. Validation Rules

A valid v1.1 record must satisfy:

1. `hp + atk + spd + wil == 20` for every build object.
2. Each stat >= 1 in every build object.
3. `animal` is one of the 14 valid animal strings.
4. `score_a + score_b == games_played` (no draws in the current rules).
5. `score_a == 4 OR score_b == 4` (best-of-7 series end when one side reaches 4).
6. `games_played >= 4 AND games_played <= 7`.
7. `winner` matches the agent with score 4 (or is null if `error` is non-null).
8. `len(games) == games_played`.
9. Each game's `seed == base_seed + game_number - 1`.
10. `env_hash` matches the SHA-256 of the config.json used (v1.1 only).
11. If `adaptation_log` is present, `len(adaptation_log) == games_played`.
12. `parse_warnings` is an array (may be empty) of strings.
