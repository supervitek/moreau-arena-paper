#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "tournament_002" / "results.jsonl"
DEFAULT_OUTPUT = ROOT / "reports" / "t002_adaptation_metrics.md"
LLM_ORDER = [
    "gpt-5.2-codex",
    "gemini-3-flash-preview",
    "grok-4-1-fast-reasoning",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "gpt-5.2",
    "claude-haiku-4-5-20251001",
    "gemini-3.1-pro-preview",
]


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "--"
    return f"{(numerator / denominator) * 100:.2f}%"


def compute_metrics(path: Path) -> dict[str, dict]:
    losses = defaultdict(int)
    adapted = defaultdict(int)
    adapted_wins = defaultdict(int)
    adapted_total = defaultdict(int)
    stuck_wins = defaultdict(int)
    stuck_total = defaultdict(int)
    unique_builds: dict[str, set[tuple]] = defaultdict(set)

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            agent_a = record["agent_a"]
            agent_b = record["agent_b"]
            games = record.get("games", [])

            for game in games:
                build_a = game.get("build_a", {})
                build_b = game.get("build_b", {})
                unique_builds[agent_a].add(
                    (build_a.get("animal"), build_a.get("hp"), build_a.get("atk"), build_a.get("spd"), build_a.get("wil"))
                )
                unique_builds[agent_b].add(
                    (build_b.get("animal"), build_b.get("hp"), build_b.get("atk"), build_b.get("spd"), build_b.get("wil"))
                )

            for idx, game in enumerate(games[:-1]):
                next_game = games[idx + 1]
                winner = game.get("winner")
                if winner == agent_a:
                    loser = agent_b
                    previous_build = game.get("build_b", {})
                    next_build = next_game.get("build_b", {})
                elif winner == agent_b:
                    loser = agent_a
                    previous_build = game.get("build_a", {})
                    next_build = next_game.get("build_a", {})
                else:
                    continue

                losses[loser] += 1
                changed = any(previous_build.get(key) != next_build.get(key) for key in ("animal", "hp", "atk", "spd", "wil"))
                if changed:
                    adapted[loser] += 1
                    adapted_total[loser] += 1
                    if next_game.get("winner") == loser:
                        adapted_wins[loser] += 1
                else:
                    stuck_total[loser] += 1
                    if next_game.get("winner") == loser:
                        stuck_wins[loser] += 1

    metrics = {}
    for agent, build_set in unique_builds.items():
        metrics[agent] = {
            "losses_with_next_game": losses[agent],
            "adapted": adapted[agent],
            "rate_pct": pct(adapted[agent], losses[agent]),
            "unique_builds": len(build_set),
            "adapt_wr": pct(adapted_wins[agent], adapted_total[agent]),
            "stick_wr": pct(stuck_wins[agent], stuck_total[agent]),
            "adapted_wins": adapted_wins[agent],
            "adapted_total": adapted_total[agent],
            "stuck_wins": stuck_wins[agent],
            "stuck_total": stuck_total[agent],
        }
    return metrics


def build_markdown(metrics: dict[str, dict]) -> str:
    llm_losses = sum(metrics.get(agent, {}).get("losses_with_next_game", 0) for agent in LLM_ORDER)
    llm_adapted = sum(metrics.get(agent, {}).get("adapted", 0) for agent in LLM_ORDER)
    llm_adapted_wins = sum(metrics.get(agent, {}).get("adapted_wins", 0) for agent in LLM_ORDER)
    llm_adapted_total = sum(metrics.get(agent, {}).get("adapted_total", 0) for agent in LLM_ORDER)
    llm_stuck_wins = sum(metrics.get(agent, {}).get("stuck_wins", 0) for agent in LLM_ORDER)
    llm_stuck_total = sum(metrics.get(agent, {}).get("stuck_total", 0) for agent in LLM_ORDER)

    lines = [
        "# T002 Adaptation Metrics",
        "",
        "Computed from `data/tournament_002/results.jsonl` by comparing the loser's build between consecutive games.",
        "",
        "## Aggregate LLM Summary",
        f"- Losses with a next game: `{llm_losses}`",
        f"- Adaptations: `{llm_adapted}`",
        f"- Adapt rate: `{pct(llm_adapted, llm_losses)}`",
        f"- Adapt win rate: `{pct(llm_adapted_wins, llm_adapted_total)}`",
        f"- Stick win rate: `{pct(llm_stuck_wins, llm_stuck_total)}`",
        "",
        "## Per-Agent Table",
        "",
        "| Agent | Blds | Lost | Adpt | Rate | Adpt WR | Stick WR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for agent in LLM_ORDER:
        item = metrics.get(agent, {})
        lines.append(
            f"| {agent} | {item.get('unique_builds', 0)} | {item.get('losses_with_next_game', 0)} | "
            f"{item.get('adapted', 0)} | {item.get('rate_pct', '--')} | {item.get('adapt_wr', '--')} | {item.get('stick_wr', '--')} |"
        )

    lines.extend(
        [
            "",
            "## Note",
            "This derivation is fully reproducible from committed JSONL. If these values disagree with the paper or older derived artifacts, the direct JSONL-derived output should be treated as canonical.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute reproducible T002 adaptation metrics from canonical JSONL.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = compute_metrics(input_path)
    output_path.write_text(build_markdown(metrics), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
