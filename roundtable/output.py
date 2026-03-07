"""Output formatters for Round Table council sessions."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .models import CouncilSession


def _slugify(text: str, max_len: int = 50) -> str:
    """Turn text into a filename-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    slug = slug.strip("_")
    return slug[:max_len]


def session_filename(session: CouncilSession) -> str:
    """Generate a filename stem like 2026-03-06_1430_quality_gate."""
    dt = datetime.fromisoformat(session.timestamp)
    date_part = dt.strftime("%Y-%m-%d_%H%M")
    slug = _slugify(session.question)
    return f"{date_part}_{slug}"


def to_markdown(session: CouncilSession) -> str:
    """Render a council session as a human-readable markdown document."""
    session.compute_totals()
    lines: list[str] = []

    # Header
    lines.append(f"# Round Table Council — {session.timestamp[:10]}")
    lines.append("")
    lines.append(f"**Question:** {session.question}")
    lines.append("")
    lines.append(f"**Moderator:** {session.moderator}")
    lines.append(f"**Panelists:** {', '.join(session.panelists)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Phase 2: Responses
    lines.append("## Phase 1: Independent Responses")
    lines.append("")
    for r in session.responses:
        status = f" ({r.elapsed_s:.1f}s, ${r.cost_usd:.4f})"
        if r.error:
            status += f" **ERROR: {r.error}**"
        lines.append(f"### {r.model}{status}")
        lines.append("")
        lines.append(r.text)
        lines.append("")

    # Phase 3: Critiques
    if session.critiques:
        lines.append("---")
        lines.append("")
        lines.append("## Phase 2: Critique Round")
        lines.append("")
        for c in session.critiques:
            status = f" ({c.elapsed_s:.1f}s, ${c.cost_usd:.4f})"
            if c.error:
                status += f" **ERROR: {c.error}**"
            lines.append(f"### {c.model}'s Critique{status}")
            lines.append("")
            lines.append(c.text)
            lines.append("")

    # Phase 4: Synthesis
    if session.synthesis:
        lines.append("---")
        lines.append("")
        lines.append("## Phase 3: Moderator's Synthesis")
        lines.append("")
        lines.append(f"*Synthesized by {session.synthesis.model} "
                      f"({session.synthesis.elapsed_s:.1f}s, "
                      f"${session.synthesis.cost_usd:.4f})*")
        lines.append("")
        lines.append(session.synthesis.text)
        lines.append("")

    # Phase 5: Votes
    if session.votes:
        lines.append("---")
        lines.append("")
        lines.append("## Phase 4: Votes")
        lines.append("")
        for v in session.votes:
            status = f" ({v.elapsed_s:.1f}s, ${v.cost_usd:.4f})"
            if v.error:
                status += f" **ERROR: {v.error}**"
            lines.append(f"### {v.model}{status}")
            lines.append("")
            if v.votes:
                for vote_item in v.votes:
                    lines.append(f"- **{vote_item.get('point', '?')}**: "
                                 f"{vote_item.get('vote', '?')} — "
                                 f"{vote_item.get('reason', '')}")
            else:
                lines.append(v.provider)  # raw text fallback
            lines.append("")

    # Cost summary
    lines.append("---")
    lines.append("")
    lines.append("## Cost Summary")
    lines.append("")
    lines.append(f"**Total: ${session.total_cost_usd:.4f}**")
    lines.append("")
    lines.append("| Model | Cost |")
    lines.append("|-------|------|")
    for model, cost in sorted(session.cost_by_model().items(), key=lambda x: -x[1]):
        lines.append(f"| {model} | ${cost:.4f} |")
    lines.append("")

    return "\n".join(lines)


def save_session(session: CouncilSession, output_dir: str | Path) -> tuple[Path, Path]:
    """Save session as both markdown and JSON. Returns (md_path, json_path)."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = session_filename(session)
    md_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"

    md_path.write_text(to_markdown(session), encoding="utf-8")
    json_path.write_text(
        json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return md_path, json_path
