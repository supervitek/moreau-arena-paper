#!/usr/bin/env python3
"""Build a lightweight INDEX.md for self/thinking/.

Supports two generations of files:
- legacy files without YAML frontmatter
- new files with a simple frontmatter block delimited by ---
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
QUESTION_RE = re.compile(r"\bQ\d+\b")
TITLE_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end() :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def summarize(path: Path) -> tuple[str, str, str, str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = parse_frontmatter(text)

    title_match = TITLE_RE.search(body)
    title = title_match.group(1).strip() if title_match else path.stem
    title = title.replace("|", "\\|")

    question = frontmatter.get("question", "")
    if not question:
        q_match = QUESTION_RE.search(title)
        if q_match:
            question = q_match.group(0)

    chain_root = frontmatter.get("chain_root", "")
    classification = frontmatter.get("classification", "legacy")

    snippet = ""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            snippet = stripped
            break
    if not snippet:
        snippet = "(empty)"
    snippet = snippet.replace("|", "\\|")
    if len(snippet) > 140:
        snippet = snippet[:137] + "..."

    return path.name, question or "-", chain_root or "-", classification, f"{title} — {snippet}"


def build_index(thinking_dir: Path, output: Path) -> None:
    rows = []
    for path in sorted(thinking_dir.glob("*.md")):
        if path.name == output.name:
            continue
        rows.append(summarize(path))

    lines = [
        "# Thinking Index",
        "",
        "| File | Question | Chain Root | Classification | Summary |",
        "|---|---|---|---|---|",
    ]
    for file_name, question, chain_root, classification, summary in rows:
        lines.append(
            f"| [{file_name}]({file_name}) | {question} | {chain_root} | {classification} | {summary} |"
        )
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        default="/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/thinking",
        help="Directory containing thinking files.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file. Defaults to <dir>/INDEX.md",
    )
    args = parser.parse_args()

    thinking_dir = Path(args.dir)
    output = Path(args.output) if args.output else thinking_dir / "INDEX.md"
    build_index(thinking_dir, output)
    print(output)


if __name__ == "__main__":
    main()
