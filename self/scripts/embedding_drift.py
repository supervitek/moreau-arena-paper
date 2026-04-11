#!/usr/bin/env python3
"""
Embedding Drift Detection — measures semantic drift between early and recent thinking files.

Uses a LOCAL embedding model via Ollama (NOT Claude) to break the self-referential loop.
Run: python3 self/scripts/embedding_drift.py
"""

import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
THINKING_DIR = PROJECT_ROOT / "self" / "thinking"
DOCS_DIR = PROJECT_ROOT / "self" / "docs"
EMBEDDINGS_DIR = PROJECT_ROOT / "self" / "embeddings"
HISTORY_FILE = EMBEDDINGS_DIR / "history.jsonl"
REPORT_FILE = DOCS_DIR / "drift_report.md"

OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODELS = ["nomic-embed-text", "all-minilm", "mxbai-embed-large"]

EARLY_COUNT = 5
RECENT_COUNT = 5
FIRST_N_FOR_VOCAB = 30

# ---------------------------------------------------------------------------
# Math helpers (stdlib only — no numpy)
# ---------------------------------------------------------------------------


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def centroid(vectors: list[list[float]]) -> list[float]:
    n = len(vectors)
    dim = len(vectors[0])
    return [sum(v[i] for v in vectors) / n for i in range(dim)]


def avg_pairwise_similarity(vectors: list[list[float]]) -> float:
    pairs = list(combinations(range(len(vectors)), 2))
    if not pairs:
        return 1.0
    total = sum(cosine_similarity(vectors[i], vectors[j]) for i, j in pairs)
    return total / len(pairs)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (--- delimited) if present."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text.strip()


def get_thinking_files() -> list[Path]:
    """Return all .md files in the thinking directory, sorted by name."""
    if not THINKING_DIR.is_dir():
        return []
    return sorted(THINKING_DIR.glob("*.md"))


def extract_number(path: Path) -> int:
    """Extract leading number from filename for sorting earliest files."""
    match = re.match(r"^(\d+)", path.name)
    return int(match.group(1)) if match else 9999


def select_early_files(all_files: list[Path], count: int) -> list[Path]:
    """Select the earliest files by filename number."""
    by_number = sorted(all_files, key=extract_number)
    return by_number[:count]


def select_recent_files(all_files: list[Path], count: int) -> list[Path]:
    """Select the most recent files by modification time."""
    by_mtime = sorted(all_files, key=lambda p: p.stat().st_mtime, reverse=True)
    return by_mtime[:count]


def extract_words(text: str, min_length: int = 5) -> set[str]:
    """Extract unique lowercased words longer than min_length chars."""
    return {w.lower() for w in re.findall(r"[a-zA-Z\u0400-\u04ff]+", text) if len(w) > min_length - 1}


# ---------------------------------------------------------------------------
# Ollama embedding
# ---------------------------------------------------------------------------


def try_embed(text: str, model: str) -> list[float] | None:
    """Attempt to get an embedding from Ollama. Returns None on failure."""
    payload = json.dumps({"model": model, "input": text}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            embeddings = data.get("embeddings")
            if embeddings and len(embeddings) > 0:
                return embeddings[0]
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError):
        pass
    return None


def find_working_model() -> str | None:
    """Try each candidate model, return the first that works."""
    test_text = "hello world"
    for model in EMBED_MODELS:
        result = try_embed(test_text, model)
        if result is not None:
            return model
    return None


def embed_files(files: list[Path], model: str) -> list[list[float]] | None:
    """Embed a list of files. Returns None if any embedding fails."""
    vectors = []
    for f in files:
        text = strip_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        # Truncate very long files to ~8000 chars to stay within model context
        if len(text) > 8000:
            text = text[:8000]
        vec = try_embed(text, model)
        if vec is None:
            return None
        vectors.append(vec)
    return vectors


# ---------------------------------------------------------------------------
# Vocabulary novelty
# ---------------------------------------------------------------------------


def compute_vocabulary_novelty(
    all_files: list[Path], recent_files: list[Path], baseline_count: int
) -> float:
    """Fraction of unique words in recent files not found in the first N files."""
    baseline_files = sorted(all_files, key=extract_number)[:baseline_count]

    baseline_words: set[str] = set()
    for f in baseline_files:
        text = strip_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        baseline_words |= extract_words(text)

    recent_words: set[str] = set()
    for f in recent_files:
        text = strip_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        recent_words |= extract_words(text)

    if not recent_words:
        return 0.0

    novel = recent_words - baseline_words
    return len(novel) / len(recent_words)


# ---------------------------------------------------------------------------
# Cycle detection (from history.jsonl)
# ---------------------------------------------------------------------------


def get_next_cycle() -> int:
    """Read history.jsonl to determine next cycle number."""
    if not HISTORY_FILE.exists():
        return 1
    last_cycle = 0
    for line in HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines():
        try:
            entry = json.loads(line)
            last_cycle = max(last_cycle, entry.get("cycle", 0))
        except json.JSONDecodeError:
            continue
    return last_cycle + 1


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def write_error_report(reason: str) -> None:
    """Write a minimal report when embedding is unavailable."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"""# Embedding Drift Report
**Generated:** {now}
**Status:** ERROR

## Error
{reason}
"""
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Error report written to {REPORT_FILE}")


def write_report(
    model: str,
    early_files: list[Path],
    recent_files: list[Path],
    intra_recent: float,
    intra_early: float,
    inter_drift: float,
    vocabulary_novelty: float,
) -> None:
    """Write the full drift report."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    early_names = ", ".join(f.name for f in early_files)
    recent_names = ", ".join(f.name for f in recent_files)

    # Interpretation
    if intra_recent > 0.92 and inter_drift < 0.1:
        interpretation = "SEMANTIC STAGNATION WARNING"
    elif inter_drift > 0.3:
        interpretation = "SIGNIFICANT EVOLUTION detected"
    else:
        interpretation = "Normal drift within expected range"

    report = f"""# Embedding Drift Report
**Generated:** {now}
**Model:** {model} (Ollama, local)
**Early files:** {early_names}
**Recent files:** {recent_names}

## Metrics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| intra_recent | {intra_recent:.4f} | How similar recent files are to each other |
| intra_early | {intra_early:.4f} | How similar early files were to each other |
| inter_drift | {inter_drift:.4f} | Distance between early and recent centroids |
| vocabulary_novelty | {vocabulary_novelty:.4f} | Fraction of new substantive words |

## Interpretation
{interpretation}
"""
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Report written to {REPORT_FILE}")


def append_history(
    cycle: int,
    intra_recent: float,
    intra_early: float,
    inter_drift: float,
    vocabulary_novelty: float,
) -> None:
    """Append one-line JSON to history.jsonl."""
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "cycle": cycle,
        "intra_recent": round(intra_recent, 4),
        "intra_early": round(intra_early, 4),
        "inter_drift": round(inter_drift, 4),
        "vocabulary_novelty": round(vocabulary_novelty, 4),
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"History appended to {HISTORY_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=== Embedding Drift Detection ===\n")

    # 1. Gather thinking files
    all_files = get_thinking_files()
    if len(all_files) < EARLY_COUNT + RECENT_COUNT:
        write_error_report(
            f"Not enough thinking files: found {len(all_files)}, "
            f"need at least {EARLY_COUNT + RECENT_COUNT}."
        )
        return

    early_files = select_early_files(all_files, EARLY_COUNT)
    recent_files = select_recent_files(all_files, RECENT_COUNT)

    print(f"Early files:  {[f.name for f in early_files]}")
    print(f"Recent files: {[f.name for f in recent_files]}")

    # 2. Find a working embedding model
    print("\nProbing Ollama for embedding models...")
    model = find_working_model()
    if model is None:
        write_error_report(
            "Ollama unavailable or no embedding model found. "
            f"Tried: {', '.join(EMBED_MODELS)}. "
            "Ensure Ollama is running and at least one embedding model is pulled."
        )
        return

    print(f"Using model: {model}")

    # 3. Compute embeddings
    print("Embedding early files...")
    early_vectors = embed_files(early_files, model)
    if early_vectors is None:
        write_error_report(f"Failed to embed early files with model {model}.")
        return

    print("Embedding recent files...")
    recent_vectors = embed_files(recent_files, model)
    if recent_vectors is None:
        write_error_report(f"Failed to embed recent files with model {model}.")
        return

    # 4. Calculate metrics
    print("Computing metrics...")
    intra_recent = avg_pairwise_similarity(recent_vectors)
    intra_early = avg_pairwise_similarity(early_vectors)

    early_centroid = centroid(early_vectors)
    recent_centroid = centroid(recent_vectors)
    inter_drift = 1.0 - cosine_similarity(early_centroid, recent_centroid)

    # 5. Vocabulary novelty
    vocabulary_novelty = compute_vocabulary_novelty(all_files, recent_files, FIRST_N_FOR_VOCAB)

    # 6. Report
    print(f"\n--- Results ---")
    print(f"  intra_recent:       {intra_recent:.4f}")
    print(f"  intra_early:        {intra_early:.4f}")
    print(f"  inter_drift:        {inter_drift:.4f}")
    print(f"  vocabulary_novelty: {vocabulary_novelty:.4f}")
    print()

    write_report(
        model=model,
        early_files=early_files,
        recent_files=recent_files,
        intra_recent=intra_recent,
        intra_early=intra_early,
        inter_drift=inter_drift,
        vocabulary_novelty=vocabulary_novelty,
    )

    # 7. Append to history
    cycle = get_next_cycle()
    append_history(cycle, intra_recent, intra_early, inter_drift, vocabulary_novelty)

    print("\nDone.")


if __name__ == "__main__":
    main()
