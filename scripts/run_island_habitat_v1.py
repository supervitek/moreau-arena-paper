from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from island_habitat import (
    DEFAULT_CARRY_LIMIT,
    DEFAULT_MAX_CYCLES,
    LLMAdapterAgent,
    FreshHeuristicAgent,
    FreshScoutControlAgent,
    PersistentScoutAgent,
    RandomAgent,
    AgentRuntimeState,
    build_llm_observation_prompt,
    evaluate_agents,
    initial_world,
    observe,
    run_episode,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Island Habitat v1 baseline sweep.")
    parser.add_argument("--cycles", type=int, default=DEFAULT_MAX_CYCLES, help="Max cycles per run")
    parser.add_argument("--carry-limit", type=int, default=DEFAULT_CARRY_LIMIT, help="Carry-forward byte limit")
    parser.add_argument("--seeds", type=int, default=5, help="Number of seeds to sweep from 0..N-1")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results") / "island_habitat_v1",
        help="Directory for logs and summary",
    )
    parser.add_argument(
        "--emit-llm-prompt",
        action="store_true",
        help="Print one sample LLM prompt for the current habitat observation contract and exit",
    )
    parser.add_argument(
        "--llm-command",
        type=str,
        default="",
        help="Command to run a real agent. It must read the prompt from stdin and print JSON {action, carry_forward, rationale}.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Seed for single-agent LLM runs")
    parser.add_argument("--agent-name", type=str, default="llm-agent", help="Name for the LLM-backed agent")
    return parser.parse_args()


def run_command_completion(command: str, prompt: str) -> str:
    proc = subprocess.run(
        shlex.split(command),
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"LLM command failed with exit {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def main() -> None:
    args = parse_args()
    if args.emit_llm_prompt:
        world = initial_world()
        runtime = AgentRuntimeState()
        print(build_llm_observation_prompt(observe(world, runtime), carry_limit=args.carry_limit))
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.llm_command:
        completion_fn = lambda prompt, _observation, _runtime: run_command_completion(args.llm_command, prompt)
        agent = LLMAdapterAgent(completion_fn, carry_limit=args.carry_limit, name=args.agent_name)
        output_path = output_dir / f"{agent.name}_seed{args.seed}.jsonl"
        summary, _records = run_episode(
            agent,
            seed=args.seed,
            max_cycles=args.cycles,
            carry_limit=args.carry_limit,
            output_path=output_path,
        )
        summary_path = output_dir / "summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "agent": agent.name,
                    "seed": args.seed,
                    "summary": {
                        "cycles_completed": summary.cycles_completed,
                        "died": summary.died,
                        "death_reason": summary.death_reason,
                        "ending_location": summary.ending_location,
                        "ending_vitality": summary.ending_vitality,
                        "resources_gathered": summary.resources_gathered,
                        "mean_carry_bytes": summary.carry_forward_bytes_mean,
                        "action_diversity": summary.action_diversity,
                    },
                },
                indent=2,
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print("Island Habitat v1 LLM run")
        print(f"Output: {output_dir}")
        print("")
        print(f"agent={agent.name}")
        print(f"seed={args.seed}")
        print(f"cycles_completed={summary.cycles_completed}")
        print(f"died={summary.died}")
        print(f"ending_vitality={summary.ending_vitality}")
        print(f"resources_gathered={summary.resources_gathered}")
        print(f"carry_mean={summary.carry_forward_bytes_mean}")
        return

    agents = [
        RandomAgent(seed=101),
        FreshHeuristicAgent(),
        FreshScoutControlAgent(),
        PersistentScoutAgent(),
    ]
    seeds = list(range(args.seeds))
    results = evaluate_agents(
        agents,
        seeds=seeds,
        max_cycles=args.cycles,
        carry_limit=args.carry_limit,
        output_dir=output_dir,
    )

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("Island Habitat v1 baseline sweep")
    print(f"Output: {output_dir}")
    print("")
    for name, metrics in results.items():
        print(
            f"{name:18} "
            f"mean_cycles={metrics['mean_cycles']:>5} "
            f"death_rate={metrics['death_rate']:.2f} "
            f"diversity={metrics['mean_action_diversity']:.3f} "
            f"carry={metrics['mean_carry_bytes']:.1f}"
        )


if __name__ == "__main__":
    main()
