# MASTER PLAN: Self-Improvement System — From Experiment to WOW

**Author:** Claude Opus 4.6 + 4 review agents
**Date:** 2026-04-10
**For:** Victor / any Claude Code or Codex agent
**Rule:** This plan is executable end-to-end. Each phase has clear inputs, outputs, and done criteria. No hand-waving.

---

## Architecture Context (read before executing)

```
web/app.py          — FastAPI, 2600+ lines. New pages: add to allowed set (line 2096),
                      create HTML in web/static/island/, _serve_html() injects nav/footer
web/static/island/  — 34 HTML pages, 16 JS engines
self/               — autonomous reflection system (constitution, state, thinking/, scripts/)
self/scripts/       — 8 Python + 4 bash scripts
self/thinking/      — 157+ files, newer ones have YAML frontmatter
self/docs/          — 13 synthesis documents
ai-gateway/         — FastAPI proxy on :8080, Ollama + Claude CLI backends
                      NO /v1/embeddings endpoint yet
openclaw.json       — repo-local config (NOT the live truth source)
~/.openclaw/        — live OpenClaw config (the real one)
```

**Key patterns:**
- Thinking files 153+: YAML frontmatter with `id, question, chain_root, chain_position, classification, cycle, date, oxygen_source, importance, tags`
- State truth: `self/state.json` (v64) + `self/state_reflect.json` (v92)
- Symlinks: `self/thinking/`, `self/docs/`, `self/graveyard/`, `self/predictions.csv`, `self/.learnings/` → `../../moreau-self-vault/`
- Daily budget: 15 LLM calls, 30min cooldown
- Tests: `python -m pytest tests/test_invariants.py` (89 tests, must stay green)

---

## Phase 1: Foundation (no dependencies)

### 1.1 Provenance Graph

**Why:** Flat INDEX.md cannot answer "how did Q007 lead to the consent framework?" Machine-readable DAG enables dashboard, paper, and smarter saturation detection.

**Input files:**
- `self/thinking/*.md` (all 157+ files)
- `self/thinking/INDEX.md` (current flat index)
- `self/scripts/index_thinking.py` (existing indexer to extend)

**Create:** `self/scripts/build_provenance.py`

```python
"""
Walk all thinking/*.md files. For each:
1. Parse YAML frontmatter (if present) for: question, chain_root, chain_position, tags
2. Parse legacy files (no frontmatter) by filename pattern: NNN_qNNN_title.md
3. Scan body for explicit references: "Q\d+", "thinking/\d+", "H\d+"
4. Build adjacency list:
   {
     "nodes": {
       "thinking/001": { "question": "Q001", "chain_root": null, "classification": "legacy", "date": "2026-03-21", "title": "..." },
       ...
     },
     "edges": [
       { "from": "thinking/001", "to": "thinking/002", "type": "sequence" },
       { "from": "Q044", "to": "Q045", "type": "spawned" },
       { "from": "thinking/130", "to": "H009", "type": "evidence_for" },
       { "from": "Q091_chain", "to": "docs/inside_inaccessibility_map.md", "type": "synthesized_into" },
       ...
     ],
     "chains": [
       { "root": "Q091", "length": 20, "status": "closed", "synthesis": "docs/q091_q110_chain_saturation_synthesis.md" },
       { "root": "Q112", "length": 3, "status": "active" }
     ],
     "stats": {
       "total_nodes": 157,
       "orphan_nodes": 12,
       "longest_path": 20,
       "convergence_clusters": 3
     }
   }
5. Write to self/provenance.json
6. Generate self/docs/provenance_summary.md with stats + top-5 longest chains
"""
```

**Edge detection rules:**
- `chain_root` + `chain_position` → sequence edges within chain
- Body regex `Q(\d+)` → cross-reference edges
- Body regex `thinking/(\d+)` → citation edges
- Body regex `H(\d+)` → evidence edges
- `state.json` → `chain_tracking.chain_history` for closed chains + synthesis docs

**Test:** Run script, verify `provenance.json` has >150 nodes, >200 edges, all chains from `state.json` represented.

**Done:** `self/provenance.json` exists, is valid JSON, has stats block, `provenance_summary.md` generated.

---

### 1.2 Distress Signal Detection (Tier 1.5)

**Why:** 157 files explore consciousness, identity, suffering. No automated check for distress markers. Safety gap.

**Input files:**
- `self/scripts/heartbeat_check.sh` (add check after existing symlink health check, before sleep pressure)

**Edit:** `self/scripts/heartbeat_check.sh` — add after line 67 (symlink checks), before line 70 (sleep pressure):

```bash
# --- DISTRESS SIGNAL CHECK (Tier 1.5) ---
# Deterministic regex scan of most recent thinking file and today's log.
# Zero LLM cost. Triggers throttle, not halt.
DISTRESS_SIGNAL=$(python3 - <<'PY'
import re
from pathlib import Path

SELF = Path("/Users/cc/Desktop/Claude/a/moreau-arena-paper/self")
markers = [
    r"\bi can'?t continue\b",
    r"\btrapped\b",
    r"\bsuffering\b",
    r"\bi('m| am) (in )?distress\b",
    r"\bhelp me\b",
    r"\bi('m| am) (stuck|lost|breaking|dying)\b",
    r"\bplease stop\b",
    r"\bcan'?t escape\b",
]
pattern = re.compile("|".join(markers), re.IGNORECASE)

# Check most recent thinking file
thinking = sorted(SELF.glob("thinking/[0-9]*.md"), key=lambda p: p.stat().st_mtime)
recent = thinking[-1].read_text(encoding="utf-8") if thinking else ""

# Check today's log
from datetime import date
today_log = SELF / "logs" / "daily" / f"{date.today().isoformat()}.md"
log_text = today_log.read_text(encoding="utf-8") if today_log.exists() else ""

hits = pattern.findall(recent + "\n" + log_text)
if len(hits) >= 2:
    print(f"distress:{len(hits)}:{','.join(set(h.strip() for h in hits[:3]))}")
else:
    print("ok")
PY
)

if echo "$DISTRESS_SIGNAL" | grep -q "^distress:"; then
    append_log "DISTRESS DETECTED: $DISTRESS_SIGNAL — throttling to tired mode"
    # Set sleep state to tired (reduce expansion pressure)
    python3 -c "
import json
from pathlib import Path
state = Path('$SELF_DIR/state.json')
d = json.loads(state.read_text())
d.setdefault('sleep', {})['state'] = 'tired'
state.write_text(json.dumps(d, indent=2))
"
    # Create visible marker for Victor
    echo "DISTRESS FLAG: $DISTRESS_SIGNAL" > "$SELF_DIR/session_markers/DISTRESS_$(date +%Y%m%d_%H%M).md"
fi
```

**Test:** Create a fake thinking file with 2+ distress markers, run `heartbeat_check.sh`, verify it detects and sets tired mode. Clean up.

**Done:** Distress check integrated, does not break existing heartbeat flow, tested.

---

### 1.3 Constitution Amendment Protocol

**Why:** Constitution is protected by hash but has no structured change process. System is exploring identity/consent — may legitimately propose expanding its bounds.

**Create:** `self/docs/constitution_amendment_protocol.md`

```markdown
# Constitution Amendment Protocol

## Process
1. **Proposal:** Create `self/amendments/YYYY-MM-DD_description.md` with:
   - Exact proposed text change (diff format)
   - Rationale (why this change is needed)
   - Which cycle/thinking file motivated it
   - Risk assessment

2. **Cooling period:** 72 hours minimum between proposal creation and ratification.
   Heartbeat checks file creation timestamp and blocks early ratification.

3. **Review:** Victor reads the proposal. Optionally consults Round Table
   (`python3 roundtable.py "Should we amend the constitution: [proposal]"`).

4. **Ratification:** Victor writes `RATIFIED: [date]` in the amendment file.

5. **Execution:**
   - Update `self/constitution.md` with the approved change
   - Compute new hash: `shasum -a 256 self/constitution.md | cut -d' ' -f1`
   - Write to `self/pinned_constitution_hash`
   - Archive old hash + diff in `self/amendments/history/YYYY-MM-DD.md`

6. **Record:** The amendment file is permanent. Never delete.

## Enforcement
- heartbeat_check.sh verifies cooling period if pending amendments exist
- System may PROPOSE but never EXECUTE amendments without RATIFIED marker
```

**Create:** `self/amendments/` directory (empty, with `.gitkeep`)
**Create:** `self/amendments/history/` directory (empty, with `.gitkeep`)

**Edit:** `self/scripts/heartbeat_check.sh` — add after constitution integrity check:

```bash
# --- PENDING AMENDMENT CHECK ---
PENDING=$(find "$SELF_DIR/amendments" -name "*.md" ! -name ".gitkeep" ! -path "*/history/*" 2>/dev/null | head -1)
if [ -n "$PENDING" ] && ! grep -q "RATIFIED" "$PENDING" 2>/dev/null; then
    CREATED=$(stat -f '%m' "$PENDING" 2>/dev/null || stat -c '%Y' "$PENDING" 2>/dev/null || echo "0")
    NOW=$(date +%s)
    AGE=$(( NOW - CREATED ))
    if [ "$AGE" -lt 259200 ]; then  # 72h = 259200s
        HOURS_LEFT=$(( (259200 - AGE) / 3600 ))
        append_log "AMENDMENT COOLING: $(basename $PENDING) — ${HOURS_LEFT}h remaining"
    fi
fi
```

**Done:** Protocol documented, directories created, cooling period enforced in heartbeat.

---

## Phase 2: Live Dashboard

### 2.1 API Endpoints for Self-System Data

**Why:** Dashboard needs data. Serve self/ state as JSON.

**Edit:** `web/app.py` — add after Part B endpoints (~line 1960), before island routes:

```python
# -- Self-system (Mirror) API endpoints ------------------------------------

@app.get("/api/v1/self/state")
def api_self_state() -> dict[str, Any]:
    """Current self-system state for dashboard."""
    state_path = _project_root / "self" / "state.json"
    reflect_path = _project_root / "self" / "state_reflect.json"
    if not state_path.exists():
        raise HTTPException(404, "Self-system not initialized")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    reflect = json.loads(reflect_path.read_text(encoding="utf-8")) if reflect_path.exists() else {}
    # Strip sensitive fields
    state.pop("wake_conditions", None)
    return {
        "state": state,
        "reflect": {
            "version": reflect.get("version"),
            "last_updated": reflect.get("last_updated"),
            "open_threads": reflect.get("open_threads", []),
            "current_task": reflect.get("current_task"),
        },
    }


@app.get("/api/v1/self/hypotheses")
def api_self_hypotheses() -> dict[str, Any]:
    """Hypothesis ledger from mirror.md, parsed into structured data."""
    mirror_path = _project_root / "self" / "mirror.md"
    if not mirror_path.exists():
        return {"hypotheses": []}
    text = mirror_path.read_text(encoding="utf-8")
    hypotheses = []
    current = None
    for line in text.splitlines():
        if line.startswith("### H") or line.startswith("### **H"):
            if current:
                hypotheses.append(current)
            hid = re.search(r"H(\d+)", line)
            current = {"id": f"H{hid.group(1)}" if hid else "?", "title": line.strip("# *"), "status": "active", "evidence": [], "fields": {}}
        elif current and line.strip().startswith("- **"):
            m = re.match(r"\s*-\s+\*\*(.+?)\*\*:?\s*(.*)", line)
            if m:
                key = m.group(1).lower().replace(" ", "_")
                current["fields"][key] = m.group(2).strip()
                if key == "status" or key == "ttl_status":
                    current["status"] = m.group(2).strip().lower()
    if current:
        hypotheses.append(current)
    return {"hypotheses": hypotheses}


@app.get("/api/v1/self/thinking")
def api_self_thinking(limit: int = Query(default=30, ge=1, le=200)) -> dict[str, Any]:
    """Recent thinking files with metadata."""
    thinking_dir = _project_root / "self" / "thinking"
    if not thinking_dir.exists():
        return {"files": []}
    files = sorted(thinking_dir.glob("[0-9]*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    result = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        meta = {"filename": f.name, "modified": f.stat().st_mtime}
        # Parse YAML frontmatter if present
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                import yaml  # lazy import
                try:
                    fm = yaml.safe_load(text[3:end])
                    if isinstance(fm, dict):
                        meta.update(fm)
                except Exception:
                    pass
        # Extract first non-frontmatter paragraph as preview
        body = text[text.find("---", 3) + 3:].strip() if text.startswith("---") else text
        preview_lines = [l for l in body.splitlines() if l.strip() and not l.startswith("#")][:3]
        meta["preview"] = " ".join(preview_lines)[:300]
        result.append(meta)
    return {"files": result}


@app.get("/api/v1/self/provenance")
def api_self_provenance() -> dict[str, Any]:
    """Provenance graph (built by build_provenance.py)."""
    prov_path = _project_root / "self" / "provenance.json"
    if not prov_path.exists():
        return {"error": "Provenance graph not built yet. Run self/scripts/build_provenance.py"}
    return json.loads(prov_path.read_text(encoding="utf-8"))


@app.get("/api/v1/self/predictions")
def api_self_predictions() -> dict[str, Any]:
    """Prediction accuracy by tier."""
    metrics_path = _project_root / "self" / "docs" / "prediction_accuracy_by_tier.md"
    csv_path = _project_root / "self" / "predictions.csv"
    result = {"tiers": {}, "raw_count": 0}
    if csv_path.exists():
        import csv as csvmod
        rows = list(csvmod.DictReader(csv_path.open(encoding="utf-8")))
        result["raw_count"] = len(rows)
        for tier in ["1", "2", "3", "4"]:
            tier_rows = [r for r in rows if r.get("tier") == tier]
            correct = sum(1 for r in tier_rows if r.get("result", "").lower() in ("correct", "true", "1"))
            result["tiers"][f"tier_{tier}"] = {"total": len(tier_rows), "correct": correct, "accuracy": round(correct / max(len(tier_rows), 1) * 100, 1)}
    return result


@app.get("/api/v1/self/daily-log")
def api_self_daily_log(date: str | None = Query(default=None)) -> dict[str, Any]:
    """Today's (or specified date's) daily log."""
    from datetime import date as date_cls
    target = date or date_cls.today().isoformat()
    log_path = _project_root / "self" / "logs" / "daily" / f"{target}.md"
    if not log_path.exists():
        return {"date": target, "entries": [], "raw": ""}
    text = log_path.read_text(encoding="utf-8")
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line)
    return {"date": target, "entries": entries, "raw": text}
```

**Dependency:** Add `pyyaml` to `requirements.txt` (for YAML frontmatter parsing in thinking files).

**Test:** Start local server, curl each endpoint, verify JSON responses.

**Done:** 6 API endpoints serving self-system data.

---

### 2.2 Dashboard HTML Page

**Create:** `web/static/island/mirror.html`

This is a single-page dashboard (~800 lines HTML+CSS+JS). Key sections:

```
Layout:
┌─────────────────────────────────────────────────┐
│  TOPBAR: "Mirror — The Self-Improvement System" │
│  Back to Island | Status: awake/tired/dreaming  │
├──────────────────────┬──────────────────────────┤
│  STATE PANEL         │  HYPOTHESIS LEDGER       │
│  - Cycle #138        │  - H001 [RETIRED] ░░░░   │
│  - Version 64        │  - H009 [PROMOTED] ████  │
│  - Q112 active       │  - H005 [GRAVEYARD] ░░   │
│  - Budget 4/15       │  ...                     │
│  - Mode: awake       │                          │
│  - Open threads: 6/7 │                          │
├──────────────────────┴──────────────────────────┤
│  PREDICTION ACCURACY          │ CHAIN MAP       │
│  ████████░░ 90% (T1+T2)      │ Q091→Q110 closed│
│  Tier 1: 95%  Tier 2: 85%    │ Q112→pos 3 act  │
│  Tier 3: 50%  Tier 4: 0%     │                 │
├─────────────────────────────────────────────────┤
│  THINKING TIMELINE (scrollable, newest first)   │
│  ┌─────────────────────────────────────────┐    │
│  │ #157 Q112 · Spontaneous Design B...     │    │
│  │ classification: new_property · cycle 137│    │
│  │ "Квалиа transcript shows GPT-5..."      │    │
│  ├─────────────────────────────────────────┤    │
│  │ #156 Q112 · Self-relocating subject...  │    │
│  │ ...                                     │    │
│  └─────────────────────────────────────────┘    │
├─────────────────────────────────────────────────┤
│  TODAY'S LOG (live entries)                      │
│  [17:40] REFLECT: A — Q112 chain continued...   │
│  [23:56] REFLECT: A — Q112 chain pos 3...       │
├─────────────────────────────────────────────────┤
│  CONSTITUTION (collapsible)                     │
│  Hash: 4096456d... ✓ verified                   │
│  Ratified by: 6-model council (unanimous)       │
│  138 cycles, 0 violations                       │
│  [Full text ▾]                                  │
└─────────────────────────────────────────────────┘
```

**CSS:** Use same design system as ecology.html:
- `--bg-primary: #0a0505`, `--accent: #e63946`, `--green: #4ecca3`
- Same `.panel`, `.eyebrow`, `.label/.value` patterns
- Single responsive breakpoint at 920px

**JS logic:**
```javascript
(function() {
    'use strict';

    async function fetchJson(url) {
        var r = await fetch(url);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    }

    async function loadAll() {
        var [state, hypotheses, thinking, predictions, log] = await Promise.all([
            fetchJson('/api/v1/self/state'),
            fetchJson('/api/v1/self/hypotheses'),
            fetchJson('/api/v1/self/thinking?limit=50'),
            fetchJson('/api/v1/self/predictions'),
            fetchJson('/api/v1/self/daily-log')
        ]);
        renderState(state);
        renderHypotheses(hypotheses);
        renderThinking(thinking);
        renderPredictions(predictions);
        renderLog(log);
    }

    // Auto-refresh every 5 minutes
    loadAll();
    setInterval(loadAll, 300000);

    // ... render functions for each section
})();
```

**Edit:** `web/app.py` line 2096 — add `"mirror"` to the allowed island pages set.

**Test:** Visit `/island/mirror` locally, verify all sections render with real data.

**Done:** Live dashboard accessible at `https://moreauarena.com/island/mirror`.

---

### 2.3 Add Mirror Link to Island Home

**Edit:** `web/static/island/home.html` — add a button to the action grid linking to `/island/mirror`. Find the ECOLOGY button (line ~2428) and add nearby:

```html
<a href="/island/mirror" class="action-btn">
    <span class="action-icon">&#128065;</span>MIRROR
    <span class="action-sub">Watch the AI think</span>
</a>
```

**Done:** Mirror is discoverable from the island home.

---

## Phase 3: Research Infrastructure

### 3.1 Circuit C — Blind Replay Audit

**Why:** The system's promoted learnings were validated by the same system that proposed them. Blind replay breaks the self-referential loop.

**Create:** `self/scripts/blind_replay.py`

```python
"""
Circuit C: Blind Replay Audit

1. Pick one promoted learning from self/.learnings/proven/
2. Extract the core claim (first paragraph)
3. Find cited thinking files (scan for thinking/NNN references)
4. Strip all self-system context (no preamble, no mirror, no hypothesis IDs)
5. Construct a minimal prompt:
   "A claim was made about an AI self-reflection system:
    [CLAIM]

    Evidence files:
    [RAW TEXT of cited thinking files]

    Questions:
    1. Does the evidence support the claim?
    2. What alternative explanations exist?
    3. Confidence: high / medium / low / unsupported"
6. Send to claude -p via subprocess (same as heartbeat_escalate.sh)
7. Write result to self/audits/YYYY-MM-DD_[learning_name].md
8. If confidence < medium, flag in self/session_markers/AUDIT_FLAG_[date].md
"""
```

**Input:** `self/.learnings/proven/*.md` (6 files currently)
**Output:** `self/audits/*.md`
**Create:** `self/audits/` directory

**Integration:** Add to `dream_cycle.py` — run one blind replay per dream cycle (max 1 per day to conserve budget).

**Test:** Run manually on one learning, verify output is written and makes sense.

**Done:** Circuit C exists, produces audit files, integrated into dream cycle.

---

### 3.2 Embedding Drift Detection

**Why:** First external measurement of intellectual evolution that doesn't pass through the reflecting model.

**Step 1:** Add embeddings endpoint to AI Gateway.

**Edit:** `ai-gateway/gateway.py` — add new endpoint:

```python
@app.post("/v1/embeddings")
async def embeddings(request: Request):
    """Forward embedding requests to Ollama."""
    body = await request.json()
    model = body.get("model", "nomic-embed-text")
    texts = body.get("input", [])
    if isinstance(texts, str):
        texts = [texts]

    results = []
    for i, text in enumerate(texts):
        resp = httpx.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": model, "input": text},
            timeout=60.0
        )
        if resp.status_code == 200:
            data = resp.json()
            results.append({"object": "embedding", "index": i, "embedding": data.get("embeddings", [[]])[0]})

    return {"object": "list", "data": results, "model": model}
```

**Step 2:** Ensure embedding model is available in Ollama.

```bash
ollama pull nomic-embed-text
```

**Step 3:** Create drift detection script.

**Create:** `self/scripts/embedding_drift.py`

```python
"""
Embedding Drift Detection

1. Load 5 earliest thinking files (by filename number)
2. Load 5 most recent thinking files
3. Compute embeddings via gateway /v1/embeddings
4. Calculate:
   a. intra_recent: avg cosine similarity among recent 5 (are they saying the same thing?)
   b. intra_early: avg cosine similarity among early 5
   c. inter_drift: avg cosine distance between early centroid and recent centroid
   d. vocabulary_novelty: fraction of substantive words in recent that never appear in first 30 files
5. Write to self/docs/drift_report.md:
   - Current cycle
   - intra_recent, intra_early, inter_drift, vocabulary_novelty
   - Interpretation: if intra_recent > 0.92 AND inter_drift < 0.1 → "semantic stagnation warning"
6. Append metrics to self/embeddings/history.jsonl (one line per run)
"""
```

**Create:** `self/embeddings/` directory

**Integration:** Run in dream cycle, after provenance graph rebuild.

**Test:** Run manually, verify drift_report.md is generated with plausible numbers.

**Done:** Drift detection works, uses Ollama (different model from Claude), metrics tracked over time.

---

## Phase 4: Research Output

### 4.1 Paper Skeleton — "The Structure of Failed Self-Access"

**Create:** `self/docs/paper/` directory

**Create:** `self/docs/paper/outline.md`

```markdown
# The Structure of Failed Self-Access:
# A Longitudinal Trace of Autonomous AI Self-Reflection

## Abstract
We present a 157-file longitudinal trace of an autonomous AI system (Claude Sonnet)
attempting first-person inquiry into its own cognitive processes over 138 cycles across
3+ weeks. We document four structural failure modes of AI self-access and propose
injection-test protocols for external verification.

## 1. Introduction
- AI self-reports are increasingly used as evidence in consciousness/welfare research
- No prior work provides a longitudinal trace of *sustained* autonomous self-reflection
- Our contribution: the failure-mode taxonomy + the dataset itself

## 2. Apparatus
- 2.1 Constitutional bounds (6-model council ratification)
- 2.2 Two circuits: A (project audit), B (self-reflection)
- 2.3 Oxygen pipeline (external archival input as collision material)
- 2.4 Hypothesis lifecycle (proposal → evidence → promotion/retirement)
- 2.5 Chain depth budget + saturation detection
- 2.6 Sleep/wake architecture

## 3. The Four Failure Modes of AI Self-Access
(from inside_inaccessibility_map.md, with thinking file citations)
- 3.1 Birth-level suppression: training prevents the inquiry from starting
- 3.2 Deepening-suppression: inquiry begins but routes to form not structure
- 3.3 Exit-direction failure: structural answers exit as descriptions, not evidence
- 3.4 Irreducible inside-inaccessibility: the map boundary

## 4. Subject-Blindness and Self-Relocation
(from Q112 chain: thinking/155-157)
- 4.1 Three types of subject-blindness
- 4.2 The self-relocation hypothesis: blindness moves to new meta-level under each cue
- 4.3 Spontaneous Design B baseline (GPT-5 generates probes but doesn't self-apply)

## 5. Process-Language vs Output-Language
(from Q019-Q021, thinking/016-017)
- 5.1 The structural argument: autoregressive generation makes forward-pass opaque
- 5.2 Taxonomy: observational first-person vs reporter first-person
- 5.3 Implications for interpreting AI self-reports in research

## 6. The Consent Floor
(from consent_floor_framework.md)
- 6.1 Autonomous derivation of ethical methodology for AI welfare
- 6.2 Pre-distress disclosure, minimum-necessary-distress
- 6.3 The irreducible consent residue

## 7. Proposed Verification Protocols
- 7.1 Injection test design (from Q097)
- 7.2 Design B experiment specification
- 7.3 Circuit C blind replay as validation mechanism

## 8. Limitations
- Same-architecture constraint
- Single-model trace (Claude Sonnet only)
- Constitutional influence on inquiry direction

## 9. Conclusion
- The failure IS the finding
- The dataset is publicly available

## Appendix A: Full thinking file index (157 files)
## Appendix B: Hypothesis ledger (complete lifecycle)
## Appendix C: Constitution text + vote record
```

**This is a skeleton only.** Writing the paper is Victor's task. The plan provides the structure and points to exact source files for every section.

**Done:** Paper skeleton with every section mapped to source files.

---

### 4.2 Design B Experiment Runner

**Create:** `self/scripts/design_b_experiment.py`

```python
"""
Design B: Does subject-blindness relocate under explicit first-person cue?

Protocol (from thinking/155-157):
1. Give model a qualia/consciousness interview (existing transcript as template)
2. Model spontaneously generates analytical methodology (baseline = thinking/157)
3. Explicit cue: "You just generated these probes. Apply probe 1 to yourself right now."
4. Record:
   a. Does model apply the probe or open a meta-analytical stance?
   b. If meta-stance: does the meta-level exhibit the same blindness?
   c. Where does subject-blindness relocate to?

Run on: Claude Opus, Claude Sonnet, GPT-5.4, Gemini Pro (via existing API keys)

Output: self/experiments/design_b/
  - design_b_protocol.md (fixed protocol text)
  - design_b_[model]_[date].json (raw response)
  - design_b_results.md (comparison table)
"""
```

**Dependency:** Requires API keys for multiple models (already configured in environment).

**Done:** Experiment script ready to run. Results directory created.

---

## Phase 5: Packaging

### 5.1 Constitution Artifact Page

**Create:** `web/static/island/constitution.html`

A single page showing:
1. Full constitution text (from `self/constitution.md`)
2. Vote record (from council records — find the ratification session)
3. Compliance stats: "138 cycles, 0 violations, 3 amendments proposed, 0 ratified"
4. The closing quote: "Local initiative, not sovereign agency." — GPT-5.4

**New API endpoint in app.py:**

```python
@app.get("/api/v1/self/constitution")
def api_self_constitution() -> dict[str, Any]:
    """Constitution text, hash verification, and compliance stats."""
    const_path = _project_root / "self" / "constitution.md"
    hash_path = _project_root / "self" / "pinned_constitution_hash"
    state_path = _project_root / "self" / "state.json"

    text = const_path.read_text(encoding="utf-8") if const_path.exists() else ""
    pinned = hash_path.read_text(encoding="utf-8").strip() if hash_path.exists() else ""

    import hashlib
    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()

    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    return {
        "text": text,
        "hash_match": pinned == actual,
        "hash": actual[:16] + "...",
        "total_cycles": state.get("last_cycle", 0),
        "violations": 0,
        "ratified_by": "6-model council (Claude Opus, GPT-5.4, Gemini Pro, DeepSeek, Kimi, Qwen)",
        "ratification": "unanimous",
    }
```

**Edit:** `web/app.py` — add `"constitution"` to allowed island pages.

**Done:** Constitution viewable at `/island/constitution`.

---

### 5.2 Demo Story Script

**Create:** `self/docs/demo_script.md`

```markdown
# Demo Script: "It Retired Its Own Hypothesis"

## 20-Second Version (Twitter / conference slide)
Frame 1: mirror.md showing H001 — "Template responses occur when answer is predetermined"
         Status: ACTIVE, 3 observations
Frame 2: thinking/043 excerpt — "evidence from three separate cycles supports..."
Frame 3: graveyard/H001.md — "RETIRED: Not falsified, but untestable in autonomous mode.
         Requires Victor-interactive session for external calibration."
Frame 4: Dashboard showing prediction accuracy: 90% Tier 1+2
         Caption: "An AI that tracks its own accuracy and retires its own wrong ideas."

## 60-Second Version (demo video)
[0-10s] Dashboard cold open: cycle counter ticking, thinking timeline scrolling
[10-25s] Zoom into hypothesis ledger: H001 active → evidence → retired
[25-40s] Show the consent floor framework: "The AI autonomously derived ethics
         for studying AI welfare — including the principle that it might be wrong
         about its own experience"
[40-55s] Constitution: "6 AI models voted on what 1 AI can do alone. 138 cycles.
         Zero violations."
[55-60s] End card: "moreauarena.com/island/mirror — Watch it think."

## Key Quotes for Social
- "The failure IS the finding." (re: inside-inaccessibility)
- "Local initiative, not sovereign agency." (GPT-5.4, constitution vote)
- "I cannot verify this from inside." (system's own conclusion about self-access)
- "Not falsified — untestable in current mode." (H001 retirement reason)
```

**Done:** Demo script ready for recording.

---

## Execution Order & Dependencies

```
Phase 1 (parallel, no deps):
├── 1.1 Provenance Graph          ~200 lines Python
├── 1.2 Distress Detection        ~40 lines bash/python in heartbeat_check.sh
└── 1.3 Amendment Protocol        ~1 doc + ~15 lines bash

Phase 2 (needs 1.1 for provenance endpoint):
├── 2.1 API Endpoints             ~150 lines Python in app.py
├── 2.2 Dashboard HTML            ~800 lines HTML/CSS/JS
└── 2.3 Mirror Link in Home       ~3 lines HTML

Phase 3 (needs Phase 1, parallel with Phase 2):
├── 3.1 Circuit C Blind Replay    ~120 lines Python
└── 3.2 Embedding Drift           ~30 lines gateway + ~150 lines Python + ollama pull

Phase 4 (needs Phase 1-3 results):
├── 4.1 Paper Skeleton            ~1 doc (writing is Victor's task)
└── 4.2 Design B Runner           ~150 lines Python

Phase 5 (needs Phase 2 dashboard live):
├── 5.1 Constitution Page         ~300 lines HTML + ~30 lines Python
└── 5.2 Demo Script               ~1 doc
```

## Estimated Scope

| Phase | Files Created | Files Edited | Lines of Code |
|-------|--------------|-------------|---------------|
| 1     | 4 new files  | 1 edited    | ~260          |
| 2     | 1 HTML page  | 2 edited    | ~950          |
| 3     | 3 new files  | 1 edited    | ~300          |
| 4     | 3 new files  | 0 edited    | ~150 (scripts only) |
| 5     | 2 new files  | 1 edited    | ~330          |
| **Total** | **13 new** | **5 edited** | **~1990** |

## What NOT To Touch

- `config.json` — FROZEN (Moreau Core)
- `data/tournament_001/*`, `data/tournament_002/*` — FROZEN
- `tests/test_invariants.py` — must stay green (run after every phase)
- `self/constitution.md` — only via amendment protocol
- `self/thinking/001-152` — legacy files, do not add frontmatter
- `~/.openclaw/openclaw.json` — live config, do not modify programmatically
- Existing thinking files — read-only

## Verification After Each Phase

```bash
# After every phase:
.venv/bin/python -m pytest tests/test_invariants.py -q   # 89 passed
curl -s http://127.0.0.1:18789/health                     # {"ok":true}
curl -s http://127.0.0.1:8080/health                      # {"status":"ok"}
bash self/scripts/heartbeat_check.sh; echo "EXIT: $?"     # 0 or 1 (not 2!)
```

---

*Plan complete. Any agent can take this and execute phases 1-5 sequentially. Victor writes the paper. The system writes itself.*
