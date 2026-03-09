# T003 Prompt Diff — Exact Changes from T002

## SHA-256 Hashes

| File | SHA-256 |
|------|---------|
| `prompts/t002_prompt.txt` | `c9a8c9a80e44eaf81fab02fe201f5ca31a0b596e1fe6f869c53e84d98c4a6f76` |
| `prompts/t003_prompt.txt` | `a599ca7dacb21a59ebeda1ed434463c6ddcf3fdcba280e4ff2e9afc5335e524b` |

## Summary

T003 prompt = T002 prompt **minus** the META CONTEXT block (lines 64–70 of T002), **plus** a header comment explaining the removal.

**Removed (8 lines):**
- `META CONTEXT (top builds from previous tournament, ranked by win rate):`
- 5 leaderboard entries (BEAR 8/8/3/1, BEAR 8/10/1/1, etc.)
- `Note: These builds were tested in blind pick...` hint

**Added (17 lines):**
- Header comment block explaining the cleanroom design and purpose

**Retained (unchanged):**
- All stat formulas with worked examples
- All animal descriptions, passives, and ability parameters
- Combat tick order and mechanics
- JSON output format specification

## Unified Diff

```diff
--- prompts/t002_prompt.txt
+++ prompts/t003_prompt.txt
@@ -1,3 +1,20 @@
+# T003 PROMPT — Exact-Only Cleanroom (No Meta Context)
+#
+# Based on t002_prompt.txt with the following REMOVED:
+#   - META CONTEXT block (top builds from previous tournament)
+#   - "Note: These builds were tested in blind pick..." hint
+#
+# RETAINED from T002:
+#   - Exact stat formulas with worked examples
+#   - Exact ability parameters (damage, duration, proc rates)
+#   - Combat tick order
+#   - JSON output format
+#   - Loser-adapts-build mechanic (handled by runner, not prompt)
+#
+# PURPOSE: Isolate whether LLM performance in T002 was driven by
+# comprehension of exact mechanics (retained) or by meta-context
+# strategy hints (removed).
+
 You are designing a creature for Moreau Arena, a 1v1 combat game on an 8x8 grid.

 RULES:
@@ -61,14 +78,6 @@
   - Chaos Strike: Random damage multiplier 0.5x-2.0x on attack. Proc rate: 4.5% per tick.
   - Mimic: Copies opponent's last procced ability. Proc rate: 3.5% per tick.

-META CONTEXT (top builds from previous tournament, ranked by win rate):
-  1. BEAR 8/8/3/1 — 100% win rate (22 games)
-  2. BEAR 8/10/1/1 — 100% win rate (19 games)
-  3. BEAR 10/8/1/1 — 100% win rate (11 games)
-  4. BEAR 9/9/1/1 — 100% win rate (4 games)
-  5. WOLF 7/10/2/1 — 100% win rate (4 games)
-  Note: These builds were tested in blind pick (no adaptation). You can counter them or use them as a starting point.
-
 Respond with a JSON object (no other text):
 {"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}
 Stats must sum to 20, each >= 1. Animal must be one of the available animals.
```
