#!/usr/bin/env python3
"""Round Table — Multi-model frontier AI council discussion.

Usage:
    # Ask a question to the default panel (Opus, GPT-5.2, Gemini Pro, Grok)
    python roundtable.py "Your question here"

    # Pick specific models
    python roundtable.py --models claude-opus-4-6,gpt-5.2 "Question"

    # Choose moderator
    python roundtable.py --moderator gpt-5.2 "Question"

    # Skip critique or voting phases
    python roundtable.py --no-critique "Question"
    python roundtable.py --no-vote "Question"

    # Load question from file
    python roundtable.py --file question.md

    # Save to specific directory
    python roundtable.py --output my_records/ "Question"

    # Dry run (no API calls)
    python roundtable.py --dry-run "Question"

Available models:
    anthropic:  claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5-20251001
    openai:     gpt-5.2, gpt-5.2-codex, gpt-5.4, gpt-5.3-codex
    google:     gemini-3-flash-preview, gemini-3.1-pro-preview
    xai:        grok-4-1-fast-reasoning

Environment variables (set before running):
    ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, XAI_API_KEY
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from roundtable.council import Council
from roundtable.output import save_session, to_markdown
from roundtable.providers import MODEL_PROVIDERS

DEFAULT_PANELISTS = [
    "claude-opus-4-6",
    "gpt-5.2",
    "gemini-3.1-pro-preview",
    "grok-4-1-fast-reasoning",
]
DEFAULT_MODERATOR = "claude-opus-4-6"
DEFAULT_OUTPUT = "council_records"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Round Table — Multi-model frontier AI council",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "question", nargs="?", default=None,
        help="The question to pose to the council",
    )
    parser.add_argument(
        "--file", "-f", type=str, default=None,
        help="Load question from a text file",
    )
    parser.add_argument(
        "--models", "-m", type=str, default=None,
        help="Comma-separated list of panelist models",
    )
    parser.add_argument(
        "--moderator", type=str, default=DEFAULT_MODERATOR,
        help=f"Moderator model (default: {DEFAULT_MODERATOR})",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--no-critique", action="store_true",
        help="Skip the critique phase",
    )
    parser.add_argument(
        "--no-vote", action="store_true",
        help="Skip the voting phase",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate without API calls",
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List all available models and exit",
    )
    args = parser.parse_args()

    if args.list_models:
        print("Available models:")
        for model, provider in sorted(MODEL_PROVIDERS.items()):
            print(f"  {model:<35s} ({provider})")
        return

    # Get question
    question: str | None = args.question
    if args.file:
        question = Path(args.file).read_text(encoding="utf-8").strip()
    if not question:
        parser.error("Provide a question as argument or via --file")

    # Get panelists
    if args.models:
        panelists = [m.strip() for m in args.models.split(",")]
    else:
        panelists = list(DEFAULT_PANELISTS)

    moderator = args.moderator

    # Print header
    mode = " [DRY RUN]" if args.dry_run else ""
    print(f"\nRound Table Council{mode}")
    print("=" * 60)
    print(f"Question: {question[:100]}{'...' if len(question) > 100 else ''}")
    print(f"Moderator: {moderator}")
    print(f"Panelists: {', '.join(panelists)}")
    phases = ["responses", "critique", "synthesis", "vote"]
    if args.no_critique:
        phases.remove("critique")
    if args.no_vote:
        phases.remove("vote")
    print(f"Phases: {' -> '.join(phases)}")
    print("=" * 60)
    print()

    # Run council
    council = Council(
        question=question,
        panelists=panelists,
        moderator=moderator,
        dry_run=args.dry_run,
        skip_critique=args.no_critique,
        skip_vote=args.no_vote,
    )

    session = council.run()

    # Save outputs
    md_path, json_path = save_session(session, args.output)

    # Print summary
    print()
    print("=" * 60)
    print("SESSION COMPLETE")
    print("=" * 60)
    print()

    # Print synthesis if available
    if session.synthesis:
        print("--- SYNTHESIS ---")
        print(session.synthesis.text)
        print()

    # Print vote tally if available
    if session.votes:
        print("--- VOTE TALLY ---")
        tally: dict[str, dict[str, int]] = {}
        for v in session.votes:
            for vote_item in v.votes:
                point = vote_item.get("point", "?")
                decision = vote_item.get("vote", "?").upper()
                if point not in tally:
                    tally[point] = {"AGREE": 0, "DISAGREE": 0, "ABSTAIN": 0}
                if decision in tally[point]:
                    tally[point][decision] += 1
        for point, counts in sorted(tally.items()):
            a, d, ab = counts["AGREE"], counts["DISAGREE"], counts["ABSTAIN"]
            print(f"  {point}: {a} agree, {d} disagree, {ab} abstain")
        print()

    # Cost summary
    print("--- COSTS ---")
    print(f"Total: ${session.total_cost_usd:.4f}")
    for model, cost in sorted(session.cost_by_model().items(), key=lambda x: -x[1]):
        print(f"  {model}: ${cost:.4f}")
    print()

    print(f"Saved: {md_path}")
    print(f"       {json_path}")


if __name__ == "__main__":
    main()
