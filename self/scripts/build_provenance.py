#!/usr/bin/env python3
"""Build a provenance graph (nodes + edges + chains + stats) for the
self-improvement thinking archive.

Walks every .md file in self/thinking/, parses YAML frontmatter when
present, falls back to filename heuristics for legacy files, scans body
text for cross-references, and writes:

  self/provenance.json   — full machine-readable graph
  self/docs/provenance_summary.md — human-readable stats
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SELF_DIR = Path(__file__).resolve().parent.parent          # .../self
THINKING_DIR = SELF_DIR / "thinking"
STATE_JSON = SELF_DIR / "state.json"
OUTPUT_JSON = SELF_DIR / "provenance.json"
OUTPUT_MD = SELF_DIR / "docs" / "provenance_summary.md"

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
# Legacy filename: NNN_qNNN_title.md  or  NNN_title.md
FILENAME_NUM_RE = re.compile(r"^(\d+)")
FILENAME_Q_RE = re.compile(r"_q(\d+)_", re.IGNORECASE)

# Body cross-references
REF_Q_RE = re.compile(r"\bQ(\d+)\b")
REF_THINKING_RE = re.compile(r"thinking/(\d+)")
REF_H_RE = re.compile(r"\bH(\d+)\b")
REF_DOC_RE = re.compile(r"docs/(\w+)")

# Date patterns in legacy files
DATE_LINE_RE = re.compile(r"Date:\s*(\d{4}-\d{2}-\d{2})")
CYCLE_LINE_RE = re.compile(r"Cycle[:\s]+(\d+)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# YAML frontmatter parser (no external deps)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body) from a markdown file's text.

    Handles the simple key: value YAML used in thinking files.  Values
    that look like lists (start with ``[``) are left as strings — they
    are not needed for the graph.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end():]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        data[key] = value
    return data, body


# ---------------------------------------------------------------------------
# Node extraction
# ---------------------------------------------------------------------------

def title_from_stem(stem: str) -> str:
    """Convert filename stem like ``155_q112_subject_blindness_first_person_cue``
    into a readable title."""
    # Strip leading number
    parts = stem.split("_", 1)
    if len(parts) > 1 and parts[0].isdigit():
        rest = parts[1]
    else:
        rest = stem
    # Strip leading qNNN_ if present
    m = re.match(r"q\d+_(.*)", rest, re.IGNORECASE)
    if m:
        rest = m.group(1)
    return rest.replace("_", " ")


def extract_node(filepath: Path) -> dict | None:
    """Parse a single thinking file into a node dict, or None on failure."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    if not text.strip():
        return None

    fm, body = parse_frontmatter(text)
    stem = filepath.stem
    name = filepath.name

    # --- Determine numeric id from filename ---
    num_match = FILENAME_NUM_RE.match(stem)
    if num_match:
        file_num = num_match.group(1).lstrip("0") or "0"
        node_id = f"thinking/{num_match.group(1)}"
    else:
        # Non-numeric files: daily_findings_*, Q*_findings, etc.
        node_id = f"thinking/{stem}"
        file_num = None

    # --- question ---
    question = fm.get("question", "")
    if not question:
        q_match = FILENAME_Q_RE.search(stem)
        if q_match:
            question = f"Q{q_match.group(1)}"
        else:
            # Try body first line / title for Q refs
            q_body = REF_Q_RE.search(body[:500]) if body else None
            if q_body:
                question = f"Q{q_body.group(1)}"

    # --- chain_root & chain_position ---
    chain_root = fm.get("chain_root", None)
    chain_position_raw = fm.get("chain_position", None)
    chain_position = int(chain_position_raw) if chain_position_raw and chain_position_raw.isdigit() else None

    # --- classification ---
    classification = fm.get("classification", "legacy" if not fm else "unknown")

    # --- date ---
    date = fm.get("date", "")
    if not date:
        dm = DATE_LINE_RE.search(body[:500]) if body else None
        if dm:
            date = dm.group(1)

    # --- cycle ---
    cycle_raw = fm.get("cycle", "")
    if cycle_raw and str(cycle_raw).isdigit():
        cycle = int(cycle_raw)
    else:
        cm = CYCLE_LINE_RE.search(body[:500]) if body else None
        cycle = int(cm.group(1)) if cm else None

    # --- title ---
    title = ""
    # Try first H1 in body
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break
    if not title:
        title = title_from_stem(stem)
    # Clean title: strip the "thinking/NNN — " prefix if present
    title = re.sub(r"^thinking/\d+\s*[—–-]\s*", "", title)
    # Strip leading "Мысль NNN — " prefix
    title = re.sub(r"^Мысль\s+\d+\s*[—–-]\s*", "", title)

    # --- importance ---
    importance_raw = fm.get("importance", None)
    importance = float(importance_raw) if importance_raw else None

    node = {
        "question": question or None,
        "chain_root": chain_root,
        "chain_position": chain_position,
        "classification": classification,
        "date": date or None,
        "title": title,
        "cycle": cycle,
        "file": name,
    }
    if importance is not None:
        node["importance"] = importance

    return node_id, node


def extract_body_refs(filepath: Path) -> dict:
    """Extract cross-references from the body text of a file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"questions": set(), "thinking": set(), "hypotheses": set(), "docs": set()}

    _, body = parse_frontmatter(text)

    return {
        "questions": set(REF_Q_RE.findall(body)),
        "thinking": set(REF_THINKING_RE.findall(body)),
        "hypotheses": set(REF_H_RE.findall(body)),
        "docs": set(REF_DOC_RE.findall(body)),
    }


# ---------------------------------------------------------------------------
# Edge building
# ---------------------------------------------------------------------------

def build_edges(nodes: dict, all_refs: dict) -> list[dict]:
    """Build the edges list from chain sequences and cross-references."""
    edges: list[dict] = []
    seen: set[tuple] = set()

    def add_edge(src: str, dst: str, etype: str):
        key = (src, dst, etype)
        if key not in seen:
            seen.add(key)
            edges.append({"from": src, "to": dst, "type": etype})

    # --- Sequence edges: consecutive files sharing a chain_root ---
    # Group nodes by chain_root
    chain_groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for node_id, node in nodes.items():
        if node.get("chain_root") and node.get("chain_position") is not None:
            chain_groups[node["chain_root"]].append(
                (node["chain_position"], node_id)
            )

    for root, members in chain_groups.items():
        members.sort()
        for i in range(len(members) - 1):
            pos_a, id_a = members[i]
            pos_b, id_b = members[i + 1]
            if pos_b == pos_a + 1:
                add_edge(id_a, id_b, "sequence")

    # --- Cross-reference edges ---
    for node_id, refs in all_refs.items():
        if node_id not in nodes:
            continue
        node = nodes[node_id]

        # Extract this file's own number to avoid self-references
        own_num_match = re.match(r"thinking/(\d+)", node_id)
        own_num = own_num_match.group(1) if own_num_match else None

        # Question references → "explores" edges
        for q_num in refs["questions"]:
            q_id = f"Q{q_num}"
            # Skip if this question is the node's own question
            if node.get("question") == q_id:
                continue
            add_edge(node_id, q_id, "explores")

        # Thinking file references → "references" edges
        for t_num in refs["thinking"]:
            t_id = f"thinking/{t_num}"
            # Skip self-reference
            if t_id == node_id:
                continue
            # Skip if the referenced id is just the leading digits of our own id
            if own_num and t_num == own_num:
                continue
            if t_id in nodes:
                add_edge(node_id, t_id, "references")
            else:
                # Still record the edge even if target is unknown
                add_edge(node_id, t_id, "references")

        # Hypothesis references → "evidence_for" edges
        for h_num in refs["hypotheses"]:
            h_id = f"H{h_num}"
            add_edge(node_id, h_id, "evidence_for")

        # Doc references → "cites_doc" edges
        for doc_name in refs["docs"]:
            doc_id = f"docs/{doc_name}"
            add_edge(node_id, doc_id, "cites_doc")

    return edges


# ---------------------------------------------------------------------------
# Chain summary
# ---------------------------------------------------------------------------

def build_chain_summary(nodes: dict, state_chains: list) -> list[dict]:
    """Merge chain info from nodes and state.json chain_history."""
    chains: list[dict] = []

    # From state.json
    for ch in state_chains:
        chains.append({
            "root": ch.get("root"),
            "end_question": ch.get("end_question"),
            "length": ch.get("length"),
            "status": ch.get("status", "unknown"),
            "closed_at": ch.get("closed_at"),
            "synthesis_doc": ch.get("synthesis_doc"),
            "summary": ch.get("summary"),
        })

    # Detect active chains from nodes
    chain_groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for node_id, node in nodes.items():
        if node.get("chain_root") and node.get("chain_position") is not None:
            chain_groups[node["chain_root"]].append(
                (node["chain_position"], node_id)
            )

    closed_roots = {ch["root"] for ch in chains if ch.get("root")}
    for root, members in sorted(chain_groups.items()):
        if root in closed_roots:
            continue
        members.sort()
        chains.append({
            "root": root,
            "length": len(members),
            "status": "active",
            "nodes": [nid for _, nid in members],
        })

    return chains


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(nodes: dict, edges: list[dict], chains: list[dict]) -> dict:
    """Compute summary statistics."""
    # Find orphan nodes (no edges at all)
    connected = set()
    for e in edges:
        connected.add(e["from"])
        connected.add(e["to"])
    orphans = [nid for nid in nodes if nid not in connected]

    # Longest chain
    longest = 0
    for ch in chains:
        length = ch.get("length", 0)
        if length and length > longest:
            longest = length

    # Edge type counts
    edge_types: dict[str, int] = defaultdict(int)
    for e in edges:
        edge_types[e["type"]] += 1

    # Classification counts
    class_counts: dict[str, int] = defaultdict(int)
    for node in nodes.values():
        class_counts[node.get("classification", "unknown")] += 1

    return {
        "total_nodes": len(nodes),
        "orphan_nodes": len(orphans),
        "longest_chain": longest,
        "total_edges": len(edges),
        "edge_types": dict(edge_types),
        "classifications": dict(class_counts),
        "orphan_ids": orphans,
    }


# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------

def write_summary(stats: dict, chains: list[dict], output: Path) -> None:
    """Write a human-readable provenance summary."""
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Provenance Graph Summary",
        "",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total nodes | {stats['total_nodes']} |",
        f"| Total edges | {stats['total_edges']} |",
        f"| Orphan nodes (no edges) | {stats['orphan_nodes']} |",
        f"| Longest chain | {stats['longest_chain']} |",
        "",
        "## Edge Types",
        "",
        "| Type | Count |",
        "|------|-------|",
    ]
    for etype, count in sorted(stats.get("edge_types", {}).items()):
        lines.append(f"| {etype} | {count} |")

    lines += [
        "",
        "## Classifications",
        "",
        "| Classification | Count |",
        "|----------------|-------|",
    ]
    for cls, count in sorted(stats.get("classifications", {}).items()):
        lines.append(f"| {cls} | {count} |")

    lines += [
        "",
        "## Chains",
        "",
        "| Root | Length | Status |",
        "|------|--------|--------|",
    ]
    for ch in chains:
        root = ch.get("root", "?")
        length = ch.get("length", "?")
        status = ch.get("status", "?")
        lines.append(f"| {root} | {length} | {status} |")

    if stats.get("orphan_ids"):
        lines += [
            "",
            "## Orphan Nodes",
            "",
        ]
        for oid in sorted(stats["orphan_ids"]):
            lines.append(f"- `{oid}`")

    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not THINKING_DIR.exists():
        print(f"ERROR: thinking directory not found: {THINKING_DIR}", file=sys.stderr)
        sys.exit(1)

    # Collect all target files
    files: list[Path] = []
    for p in sorted(THINKING_DIR.iterdir()):
        if not p.is_file() or p.suffix != ".md":
            continue
        if p.name == "INDEX.md":
            continue
        stem = p.stem
        # Match: starts with digit, or daily_findings_*, or Q*_findings
        if (
            re.match(r"\d", stem)
            or re.match(r"daily_findings_", stem, re.IGNORECASE)
            or re.match(r"Q\d+_findings", stem, re.IGNORECASE)
        ):
            files.append(p)

    print(f"Scanning {len(files)} files in {THINKING_DIR} ...")

    # Build nodes
    nodes: dict[str, dict] = {}
    all_refs: dict[str, dict] = {}

    for filepath in files:
        result = extract_node(filepath)
        if result is None:
            continue
        node_id, node = result
        # Handle duplicate node_ids (e.g. 002_after_reading_the_archive.md
        # and 002_spark_and_handoff.md both map to thinking/002)
        if node_id in nodes:
            # Use filename as suffix to disambiguate
            node_id = f"thinking/{filepath.stem}"
        nodes[node_id] = node
        all_refs[node_id] = extract_body_refs(filepath)

    # Load chain history from state.json
    state_chains: list[dict] = []
    if STATE_JSON.exists():
        try:
            state = json.loads(STATE_JSON.read_text(encoding="utf-8"))
            ct = state.get("chain_tracking", {})
            state_chains = ct.get("chain_history", [])
        except Exception as exc:
            print(f"WARNING: could not read state.json: {exc}", file=sys.stderr)

    # Build edges
    edges = build_edges(nodes, all_refs)

    # Build chain summary
    chains = build_chain_summary(nodes, state_chains)

    # Compute stats
    stats = compute_stats(nodes, edges, chains)

    # Assemble output
    graph = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nodes": nodes,
        "edges": edges,
        "chains": chains,
        "stats": stats,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JSON}  ({stats['total_nodes']} nodes, {stats['total_edges']} edges)")

    # Write markdown summary
    write_summary(stats, chains, OUTPUT_MD)
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
