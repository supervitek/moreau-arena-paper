#!/usr/bin/env python3
"""Moreau Arena Ablation Study -- isolate the contribution of each T002 component.

Runs mini-tournaments, each enabling exactly ONE T002 enhancement while
keeping everything else at the T001 baseline:

    formulas-only         -- T001 prompt + exact stat formulas.
                             No meta context, no adaptation (blind series).
    meta-only             -- T001 prompt + top-5 meta builds from T001 data.
                             No formulas, no adaptation (blind series).
    adaptation-only       -- T001 prompt + adaptive series (loser sees winner, re-picks).
                             No formulas, no meta context.
    structured-output-only -- T001 prompt content but requiring JSON output
                             format (like T002). No formulas, no meta, no adaptation.
    formulas-no-meta      -- T002-style detailed formulas and descriptions but
                             WITHOUT the META CONTEXT section. No adaptation.
                             Isolates: formulas + detail without example builds.

Usage:
    # Dry-run all 5 variants (no API calls):
    python run_ablation.py --variant all --dry-run

    # Dry-run a single variant:
    python run_ablation.py --variant formulas-only --dry-run

    # Real run (requires API key):
    python run_ablation.py --variant meta-only --provider anthropic --model claude-sonnet-4-20250514
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.baselines import (
    BaseAgent,
    Build,
    ConservativeAgent,
    GreedyAgent,
    HighVarianceAgent,
    RandomAgent,
    SmartAgent,
)
from agents.llm_agent import LLMAgent, build_prompt, parse_response
from analysis.bt_ranking import compute_bt_scores, BTResult
from prompts.meta_extractor import extract_top_builds
from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine, CombatResult
from simulator.grid import Grid


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VARIANTS = (
    "formulas-only",
    "meta-only",
    "adaptation-only",
    "structured-output-only",
    "formulas-no-meta",
)

_ORIGINAL_ANIMALS = [
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
]

_BASELINES: list[tuple[str, type[BaseAgent]]] = [
    ("RandomAgent", RandomAgent),
    ("SmartAgent", SmartAgent),
]

_LLM_AGENT_NAMES = [
    "LLM-Ablation-1",
    "LLM-Ablation-2",
    "LLM-Ablation-3",
]


# ---------------------------------------------------------------------------
# Formulas text extracted from MECHANICS.md (for formulas-only variant)
# ---------------------------------------------------------------------------

_FORMULAS_BLOCK = """\

EXACT STAT FORMULAS (from game engine):
  max_hp = 50 + 10 * HP
    Example: HP=3 -> 80 hp, HP=8 -> 130 hp, HP=14 -> 190 hp
  base_dmg = floor(2 + 0.85 * ATK)
    Example: ATK=8 -> 8 dmg, ATK=14 -> 13 dmg
  dodge = max(0%, min(30%, 2.5% * (SPD - 1)))
    NOTE: SPD=1 gives 0% dodge, SPD=5 gives 10%, SPD=13 gives 30% (cap)
  ability_resist = min(60%, WIL * 3.3%)
    NOTE: Chance to resist OPPONENT's ability procs. WIL=1 gives 3.3%, WIL=10 gives 33%, cap 60%
  ability_proc_bonus = WIL * 0.08% (additive to YOUR proc rate)
    Example: WIL=8 adds +0.64% to all your proc rates
"""


# ---------------------------------------------------------------------------
# Meta context text builder
# ---------------------------------------------------------------------------

def _build_meta_text(meta_builds: list[dict]) -> str:
    """Build meta context section for injection into T001 prompt."""
    if not meta_builds:
        return ""
    lines = [
        "\nMETA CONTEXT (top builds from previous tournament, ranked by win rate):"
    ]
    for i, b in enumerate(meta_builds, 1):
        wr = b.get("win_rate", 0)
        games = b.get("games", 0)
        lines.append(
            f"  {i}. {b['animal']} {b['hp']}/{b['atk']}/{b['spd']}/{b['wil']} "
            f"-- {wr:.0%} win rate ({games} games)"
        )
    lines.append(
        "  Note: These builds were tested in blind pick (no adaptation). "
        "You can counter them or use them as a starting point."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Variant-specific prompt builders
# ---------------------------------------------------------------------------

def _build_formulas_only_prompt(
    opponent_animal: Animal | None,
    banned: list[Animal],
) -> str:
    """T001 prompt + exact formulas. No meta, no adaptation info."""
    base = build_prompt(opponent_animal, banned)
    # Insert formulas block before the final instruction line
    parts = base.rsplit("\nChoose an animal", 1)
    if len(parts) == 2:
        return parts[0] + _FORMULAS_BLOCK + "\nChoose an animal" + parts[1]
    return base + _FORMULAS_BLOCK


def _build_meta_only_prompt(
    opponent_animal: Animal | None,
    banned: list[Animal],
    meta_builds: list[dict],
) -> str:
    """T001 prompt + meta context. No formulas, no adaptation info."""
    base = build_prompt(opponent_animal, banned)
    meta_text = _build_meta_text(meta_builds)
    # Insert meta block before the final instruction line
    parts = base.rsplit("\nChoose an animal", 1)
    if len(parts) == 2:
        return parts[0] + meta_text + "\nChoose an animal" + parts[1]
    return base + meta_text


def _build_adaptation_only_prompt(
    opponent_animal: Animal | None,
    banned: list[Animal],
    opponent_reveal: Build | None = None,
) -> str:
    """T001 prompt + opponent reveal for adaptation. No formulas, no meta."""
    base = build_prompt(opponent_animal, banned)
    if opponent_reveal is None:
        return base
    reveal_text = (
        f"\nOPPONENT'S WINNING BUILD (you lost last game to this):\n"
        f"  {opponent_reveal.animal.value.upper()} "
        f"{opponent_reveal.hp}/{opponent_reveal.atk}/{opponent_reveal.spd}/{opponent_reveal.wil}\n"
        f"  Adapt your build to counter this specific opponent."
    )
    parts = base.rsplit("\nChoose an animal", 1)
    if len(parts) == 2:
        return parts[0] + reveal_text + "\nChoose an animal" + parts[1]
    return base + reveal_text


def _build_structured_output_only_prompt(
    opponent_animal: Animal | None,
    banned: list[Animal],
) -> str:
    """T001 prompt content but with JSON output format (like T002).

    No formulas beyond T001, no meta context, no adaptation.
    Isolates: does output format alone change strategy quality?
    """
    base = build_prompt(opponent_animal, banned)
    # Replace the text output instruction with JSON format
    base = base.replace(
        "Choose an animal and allocate 20 stat points.\n"
        "Respond ONLY in this exact format: ANIMAL HP ATK SPD WIL\n"
        "Example: BOAR 8 8 3 1",
        "Respond with a JSON object (no other text):\n"
        '{"animal": "ANIMAL_NAME", "hp": N, "atk": N, "spd": N, "wil": N}\n'
        "Stats must sum to 20, each >= 1. Animal must be one of the available animals.",
    )
    return base


def _build_formulas_no_meta_prompt(
    opponent_animal: Animal | None,
    banned: list[Animal],
) -> str:
    """T002-style detailed descriptions and formulas, but NO meta context.

    Same detailed animal descriptions, exact stat formulas, combat mechanics,
    and JSON output as T002 — minus the META CONTEXT section.
    Isolates: does full mechanical understanding suffice without example builds?
    """
    # Load T002 prompt template and strip the META CONTEXT section
    t002_path = Path(__file__).parent / "prompts" / "t002_prompt.txt"
    prompt = t002_path.read_text(encoding="utf-8")

    # Remove the META CONTEXT block (from "META CONTEXT" to the line before
    # "Respond with a JSON object")
    prompt = re.sub(
        r"\nMETA CONTEXT \(top builds.*?\n(?=Respond with a JSON object)",
        "\n",
        prompt,
        flags=re.DOTALL,
    )
    return prompt


# ---------------------------------------------------------------------------
# Ablation agents (LLMAgent subclasses with variant-specific prompts)
# ---------------------------------------------------------------------------

class FormulasOnlyAgent(BaseAgent):
    """LLM agent that receives T001 prompt + exact formulas. No meta, no adapt."""

    def __init__(self, name: str, api_call) -> None:
        self._name = name
        self._api_call = api_call

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        prompt = _build_formulas_only_prompt(opponent_animal, banned)
        response = self._api_call(prompt)
        build = parse_response(response, banned)
        if build is not None:
            return build
        return GreedyAgent().choose_build(opponent_animal, banned)


class MetaOnlyAgent(BaseAgent):
    """LLM agent that receives T001 prompt + meta context. No formulas, no adapt."""

    def __init__(self, name: str, api_call, meta_builds: list[dict]) -> None:
        self._name = name
        self._api_call = api_call
        self._meta_builds = meta_builds

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        prompt = _build_meta_only_prompt(opponent_animal, banned, self._meta_builds)
        response = self._api_call(prompt)
        build = parse_response(response, banned)
        if build is not None:
            return build
        return GreedyAgent().choose_build(opponent_animal, banned)


class AdaptationOnlyAgent(BaseAgent):
    """LLM agent that receives T001 prompt + opponent reveal. No formulas, no meta."""

    def __init__(self, name: str, api_call) -> None:
        self._name = name
        self._api_call = api_call

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        reveal_build = opponent_reveal if isinstance(opponent_reveal, Build) else None
        prompt = _build_adaptation_only_prompt(opponent_animal, banned, reveal_build)
        response = self._api_call(prompt)
        build = parse_response(response, banned)
        if build is not None:
            return build
        return GreedyAgent().choose_build(opponent_animal, banned)


class StructuredOutputOnlyAgent(BaseAgent):
    """LLM agent that receives T001 prompt but with JSON output format."""

    def __init__(self, name: str, api_call) -> None:
        self._name = name
        self._api_call = api_call

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        prompt = _build_structured_output_only_prompt(opponent_animal, banned)
        response = self._api_call(prompt)
        build = _parse_json_or_text(response, banned)
        if build is not None:
            return build
        return GreedyAgent().choose_build(opponent_animal, banned)


class FormulasNoMetaAgent(BaseAgent):
    """LLM agent with T002-style formulas/descriptions but no meta context."""

    def __init__(self, name: str, api_call) -> None:
        self._name = name
        self._api_call = api_call

    def choose_build(
        self,
        opponent_animal: Animal | None,
        banned: list[Animal],
        opponent_reveal: object | None = None,
    ) -> Build:
        prompt = _build_formulas_no_meta_prompt(opponent_animal, banned)
        response = self._api_call(prompt)
        build = _parse_json_or_text(response, banned)
        if build is not None:
            return build
        return GreedyAgent().choose_build(opponent_animal, banned)


def _parse_json_or_text(response: str, banned: list[Animal]) -> Build | None:
    """Try JSON parsing first, then fall back to text parsing."""
    _animal_map = {a.value.upper(): a for a in _ORIGINAL_ANIMALS}
    try:
        data = json.loads(response.strip())
        animal_str = data.get("animal", "").upper()
        animal = _animal_map.get(animal_str)
        if animal and animal not in banned:
            return Build(
                animal=animal,
                hp=int(data["hp"]),
                atk=int(data["atk"]),
                spd=int(data["spd"]),
                wil=int(data["wil"]),
            )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        pass
    return parse_response(response, banned)


# ---------------------------------------------------------------------------
# Creature creation (same as run_challenge.py)
# ---------------------------------------------------------------------------

def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
    """Create a Creature dataclass from a flat Build."""
    hp, atk, spd, wil = build.hp, build.atk, build.spd, build.wil
    animal = build.animal

    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)

    hp_atk = hp + atk
    if hp_atk <= 10:
        size = Size(1, 1)
    elif hp_atk <= 12:
        size = Size(2, 1)
    elif hp_atk <= 17:
        size = Size(2, 2)
    else:
        size = Size(3, 2)

    passive = ANIMAL_PASSIVE.get(animal)
    abilities = ANIMAL_ABILITIES.get(animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)

    return Creature(
        animal=animal,
        stats=StatBlock(hp=hp, atk=atk, spd=spd, wil=wil),
        passive=passive,
        current_hp=max_hp,
        max_hp=max_hp,
        base_dmg=base_dmg,
        armor_flat=0,
        size=size,
        position=position,
        dodge_chance=dodge,
        resist_chance=resist,
        movement_range=movement,
        abilities=abilities,
    )


# ---------------------------------------------------------------------------
# Combat helpers (same as run_challenge.py)
# ---------------------------------------------------------------------------

def _run_single_game(
    build_a: Build,
    build_b: Build,
    match_seed: int,
) -> CombatResult:
    """Run a single combat between two builds."""
    creature_a = _create_creature(build_a, "a", match_seed)
    creature_b = _create_creature(build_b, "b", match_seed)
    engine = CombatEngine()
    return engine.run_combat(creature_a, creature_b, match_seed)


def _build_to_dict(build: Build) -> dict[str, Any]:
    """Convert a Build to a serializable dict."""
    return {
        "animal": build.animal.value.upper(),
        "hp": build.hp,
        "atk": build.atk,
        "spd": build.spd,
        "wil": build.wil,
    }


# ---------------------------------------------------------------------------
# Series protocols
# ---------------------------------------------------------------------------

def _run_blind_series(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
) -> tuple[str, list[dict[str, Any]]]:
    """T001 blind-pick best-of-7. Each agent picks once, same build all games."""
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    build_a = agent_a.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )
    build_b = agent_b.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )

    wins_a, wins_b = 0, 0
    game_records: list[dict[str, Any]] = []

    for g in range(7):
        if wins_a >= 4 or wins_b >= 4:
            break

        match_seed = series_seed + g
        result = _run_single_game(build_a, build_b, match_seed)

        record = {
            "game": g + 1,
            "seed": match_seed,
            "build_a": _build_to_dict(build_a),
            "build_b": _build_to_dict(build_b),
            "winner_side": result.winner,
            "ticks": result.ticks,
            "end_condition": result.end_condition,
        }
        game_records.append(record)

        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1

    if wins_a > wins_b:
        return name_a, game_records
    elif wins_b > wins_a:
        return name_b, game_records
    return "draw", game_records


def _run_adaptive_series(
    agent_a: BaseAgent,
    agent_b: BaseAgent,
    series_seed: int,
) -> tuple[str, list[dict[str, Any]]]:
    """Adaptive best-of-7. Loser sees winner's build, can re-pick."""
    name_a = getattr(agent_a, "_name", agent_a.__class__.__name__)
    name_b = getattr(agent_b, "_name", agent_b.__class__.__name__)

    build_a = agent_a.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )
    build_b = agent_b.choose_build(
        opponent_animal=None, banned=[], opponent_reveal=None
    )

    wins_a, wins_b = 0, 0
    game_records: list[dict[str, Any]] = []

    for g in range(7):
        if wins_a >= 4 or wins_b >= 4:
            break

        match_seed = series_seed + g
        result = _run_single_game(build_a, build_b, match_seed)

        record = {
            "game": g + 1,
            "seed": match_seed,
            "build_a": _build_to_dict(build_a),
            "build_b": _build_to_dict(build_b),
            "winner_side": result.winner,
            "ticks": result.ticks,
            "end_condition": result.end_condition,
        }
        game_records.append(record)

        if result.winner == "a":
            wins_a += 1
            try:
                build_b = agent_b.choose_build(
                    opponent_animal=build_a.animal,
                    banned=[],
                    opponent_reveal=build_a,
                )
            except Exception:
                pass
        elif result.winner == "b":
            wins_b += 1
            try:
                build_a = agent_a.choose_build(
                    opponent_animal=build_b.animal,
                    banned=[],
                    opponent_reveal=build_b,
                )
            except Exception:
                pass

    if wins_a > wins_b:
        return name_a, game_records
    elif wins_b > wins_a:
        return name_b, game_records
    return "draw", game_records


# ---------------------------------------------------------------------------
# Dry-run random api_call (returns text for T001-style parsing)
# ---------------------------------------------------------------------------

def _random_build_dict() -> dict[str, Any]:
    """Generate a random valid build dict."""
    animal = random.choice(_ORIGINAL_ANIMALS)
    remaining = 16
    stats = [1, 1, 1, 1]
    for i in range(3):
        alloc = random.randint(0, remaining)
        stats[i] += alloc
        remaining -= alloc
    stats[3] += remaining
    return {
        "animal": animal.value.upper(),
        "hp": stats[0],
        "atk": stats[1],
        "spd": stats[2],
        "wil": stats[3],
    }


def _dry_run_api_call(prompt: str) -> str:
    """Return a random valid build as text or JSON depending on prompt format."""
    b = _random_build_dict()
    # If the prompt asks for JSON output, return JSON
    if '{"animal"' in prompt or "JSON object" in prompt:
        return json.dumps(b)
    return f"{b['animal']} {b['hp']} {b['atk']} {b['spd']} {b['wil']}"


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def _make_agents(
    variant: str,
    api_call,
    meta_builds: list[dict],
) -> list[tuple[str, BaseAgent]]:
    """Create the 5 agents for a given ablation variant: 3 LLM + 2 baseline."""
    agents: list[tuple[str, BaseAgent]] = []

    for name in _LLM_AGENT_NAMES:
        if variant == "formulas-only":
            agents.append((name, FormulasOnlyAgent(name, api_call)))
        elif variant == "meta-only":
            agents.append((name, MetaOnlyAgent(name, api_call, meta_builds)))
        elif variant == "adaptation-only":
            agents.append((name, AdaptationOnlyAgent(name, api_call)))
        elif variant == "structured-output-only":
            agents.append((name, StructuredOutputOnlyAgent(name, api_call)))
        elif variant == "formulas-no-meta":
            agents.append((name, FormulasNoMetaAgent(name, api_call)))

    for baseline_name, baseline_cls in _BASELINES:
        if baseline_cls in (RandomAgent, HighVarianceAgent):
            agents.append((baseline_name, baseline_cls(seed=42)))
        else:
            agents.append((baseline_name, baseline_cls()))

    return agents


# ---------------------------------------------------------------------------
# JSONL output
# ---------------------------------------------------------------------------

def _save_results_jsonl(
    output_dir: Path,
    variant: str,
    series_records: list[dict[str, Any]],
) -> Path:
    """Save all series results to a JSONL file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"ablation_{variant}_{timestamp}.jsonl"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        for record in series_records:
            f.write(json.dumps(record, default=str) + "\n")

    return output_path


# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

def _print_results(
    variant: str,
    pairwise: dict[tuple[str, str], dict[str, int]],
    bt_pairs: list[tuple[str, str]],
) -> None:
    """Print pairwise results and BT rankings for a variant."""
    print(f"\n{'=' * 65}")
    print(f"  ABLATION: {variant.upper()}")
    print(f"{'=' * 65}")

    # Aggregate per-agent stats
    agent_stats: dict[str, dict[str, int]] = {}
    for (a_name, b_name), counts in pairwise.items():
        if a_name not in agent_stats:
            agent_stats[a_name] = {"won": 0, "lost": 0, "draw": 0}
        if b_name not in agent_stats:
            agent_stats[b_name] = {"won": 0, "lost": 0, "draw": 0}
        agent_stats[a_name]["won"] += counts["won"]
        agent_stats[a_name]["lost"] += counts["lost"]
        agent_stats[a_name]["draw"] += counts["draw"]
        agent_stats[b_name]["won"] += counts["lost"]
        agent_stats[b_name]["lost"] += counts["won"]
        agent_stats[b_name]["draw"] += counts["draw"]

    print(f"\n  {'Agent':<25} {'Won':>6} {'Lost':>6} {'Draw':>6} {'WR':>8}")
    print("  " + "-" * 55)
    for name in sorted(agent_stats.keys()):
        s = agent_stats[name]
        total = s["won"] + s["lost"] + s["draw"]
        wr = s["won"] / total if total > 0 else 0.0
        print(f"  {name:<25} {s['won']:>6} {s['lost']:>6} {s['draw']:>6} {wr:>7.0%}")

    # BT rankings
    if bt_pairs:
        bt_results = compute_bt_scores(bt_pairs, n_bootstrap=1000, bootstrap_seed=42)
        print(f"\n  Bradley-Terry Rankings:")
        print(f"  {'Rank':<5} {'Agent':<25} {'BT Score':<10} {'95% CI':<22}")
        print("  " + "-" * 60)
        for i, r in enumerate(bt_results, 1):
            ci_str = f"[{r.ci_lower:.4f}, {r.ci_upper:.4f}]"
            print(f"  {i:<5} {r.name:<25} {r.score:<10.4f} {ci_str:<22}")

    print(f"{'=' * 65}\n")


# ---------------------------------------------------------------------------
# Run one ablation variant
# ---------------------------------------------------------------------------

def _run_variant(
    variant: str,
    api_call,
    meta_builds: list[dict],
    num_series: int,
    output_dir: Path,
) -> Path:
    """Run a single ablation variant mini-tournament."""
    agents = _make_agents(variant, api_call, meta_builds)
    series_fn = _run_adaptive_series if variant == "adaptation-only" else _run_blind_series

    # Build all pairs (round-robin)
    pairs: list[tuple[int, int]] = []
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            pairs.append((i, j))

    total_series = len(pairs) * num_series
    series_idx = 0
    base_seed = 200_000

    pairwise: dict[tuple[str, str], dict[str, int]] = {}
    bt_pairs: list[tuple[str, str]] = []
    all_records: list[dict[str, Any]] = []

    print(f"\n--- Ablation: {variant} ---")
    print(f"  Agents: {', '.join(n for n, _ in agents)}")
    print(f"  Protocol: {'adaptive' if variant == 'adaptation-only' else 'blind'}")
    print(f"  Series per pair: {num_series}")
    print(f"  Total series: {total_series}")
    print()

    for i, j in pairs:
        name_a, agent_cls_a = agents[i]
        name_b, agent_cls_b = agents[j]
        pair_key = (name_a, name_b)
        counts = {"won": 0, "lost": 0, "draw": 0}

        for s in range(num_series):
            series_idx += 1
            series_seed = base_seed + series_idx * 100

            # Reinstantiate agents for fresh state each series
            agent_a = _reinstantiate(agents[i], variant, api_call, meta_builds, series_seed)
            agent_b = _reinstantiate(agents[j], variant, api_call, meta_builds, series_seed)

            t_start = time.monotonic()
            winner, game_records = series_fn(agent_a, agent_b, series_seed)
            elapsed = time.monotonic() - t_start

            if winner == name_a:
                counts["won"] += 1
                bt_pairs.append((name_a, name_b))
            elif winner == name_b:
                counts["lost"] += 1
                bt_pairs.append((name_b, name_a))
            else:
                counts["draw"] += 1

            series_record = {
                "variant": variant,
                "agent_a": name_a,
                "agent_b": name_b,
                "winner": winner,
                "protocol": "adaptive" if variant == "adaptation-only" else "blind",
                "series_seed": series_seed,
                "games": game_records,
                "elapsed_s": round(elapsed, 2),
            }
            all_records.append(series_record)

            status = f"[{series_idx}/{total_series}]"
            print(
                f"  {status:>10}  {name_a:<22} vs {name_b:<22} "
                f"-> {winner:<25} ({len(game_records)} games, {elapsed:.1f}s)"
            )

        pairwise[pair_key] = counts

    _print_results(variant, pairwise, bt_pairs)
    output_path = _save_results_jsonl(output_dir, variant, all_records)
    print(f"  Results saved to: {output_path}")
    return output_path


def _reinstantiate(
    agent_tuple: tuple[str, BaseAgent],
    variant: str,
    api_call,
    meta_builds: list[dict],
    seed: int,
) -> BaseAgent:
    """Create a fresh agent instance for each series."""
    name, original = agent_tuple

    if isinstance(original, RandomAgent):
        return RandomAgent(seed=seed)
    if isinstance(original, HighVarianceAgent):
        return HighVarianceAgent(seed=seed)
    if isinstance(original, (GreedyAgent, SmartAgent, ConservativeAgent)):
        return original.__class__()

    # LLM agent -- reinstantiate with variant-specific class
    if variant == "formulas-only":
        return FormulasOnlyAgent(name, api_call)
    elif variant == "meta-only":
        return MetaOnlyAgent(name, api_call, meta_builds)
    elif variant == "adaptation-only":
        return AdaptationOnlyAgent(name, api_call)
    elif variant == "structured-output-only":
        return StructuredOutputOnlyAgent(name, api_call)
    elif variant == "formulas-no-meta":
        return FormulasNoMetaAgent(name, api_call)

    return original


# ---------------------------------------------------------------------------
# API call helpers (reused from run_challenge.py)
# ---------------------------------------------------------------------------

_ENV_KEY_MAP: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
}


def _build_api_callable(provider: str, model: str, api_key: str):
    """Build a real API callable. Imports from run_challenge to avoid duplication."""
    from run_challenge import _build_api_callable as _make_callable
    real_call = _make_callable(provider, model, api_key)

    # Wrap to return string (T001 format) since ablation agents use text parsing
    def api_call(prompt: str) -> str:
        result = real_call(prompt)
        if isinstance(result, dict):
            return f"{result.get('animal', 'BEAR')} {result.get('hp', 5)} {result.get('atk', 5)} {result.get('spd', 5)} {result.get('wil', 5)}"
        return str(result)

    return api_call


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_ablation(args: argparse.Namespace) -> None:
    """Execute the ablation study."""
    variants = list(VARIANTS) if args.variant == "all" else [args.variant]
    num_series = args.series
    output_dir = Path(args.output_dir)
    dry_run = args.dry_run

    # Resolve API call
    if dry_run:
        api_call = _dry_run_api_call
    else:
        provider = args.provider
        model = args.model
        api_key = args.api_key or os.environ.get(_ENV_KEY_MAP.get(provider, ""), "")
        if not api_key:
            env_var = _ENV_KEY_MAP.get(provider, "UNKNOWN")
            print(
                f"Error: No API key provided. Use --api-key or set {env_var}.",
                file=sys.stderr,
            )
            sys.exit(1)
        api_call = _build_api_callable(provider, model, api_key)

    # Load meta builds from T001 data
    t001_results_path = Path(__file__).parent / "data" / "tournament_001" / "results.jsonl"
    meta_builds: list[dict] = []
    if t001_results_path.exists():
        meta_builds = extract_top_builds(t001_results_path, top_n=5)

    # Print header
    print("=" * 65)
    print("  MOREAU ARENA ABLATION STUDY")
    print("=" * 65)
    print(f"  Variants:     {', '.join(variants)}")
    print(f"  Dry run:      {dry_run}")
    print(f"  Series/pair:  {num_series}")
    print(f"  Agents:       5 per variant (3 LLM + 2 baseline)")
    if meta_builds:
        print(f"  Meta builds:  {len(meta_builds)} loaded from T001")
    else:
        print("  Meta builds:  none (T001 results not found)")
    print(f"  Output dir:   {output_dir}")
    print("=" * 65)

    output_paths: list[Path] = []
    for variant in variants:
        path = _run_variant(variant, api_call, meta_builds, num_series, output_dir)
        output_paths.append(path)

    print("\n" + "=" * 65)
    print("  ABLATION COMPLETE")
    print("=" * 65)
    for p in output_paths:
        print(f"  {p}")
    print("=" * 65)


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        description="Moreau Arena Ablation Study -- isolate T002 component contributions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Variants:\n"
            "  formulas-only          T001 prompt + exact stat formulas. No meta, no adaptation.\n"
            "  meta-only              T001 prompt + top-5 meta builds. No formulas, no adaptation.\n"
            "  adaptation-only        T001 prompt + adaptive series. No formulas, no meta.\n"
            "  structured-output-only T001 prompt content but JSON output format. No formulas, no meta.\n"
            "  formulas-no-meta       T002-style formulas + detail but NO meta context. No adaptation.\n"
            "  all                    Run all 5 variants sequentially.\n"
            "\n"
            "Examples:\n"
            "  python run_ablation.py --variant all --dry-run\n"
            "  python run_ablation.py --variant formulas-only --dry-run --series 5\n"
            "  python run_ablation.py --variant meta-only --provider anthropic --model claude-sonnet-4-20250514\n"
        ),
    )

    parser.add_argument(
        "--variant",
        type=str,
        required=True,
        choices=[
            "formulas-only", "meta-only", "adaptation-only",
            "structured-output-only", "formulas-no-meta", "all",
        ],
        help="Which ablation variant to run (or 'all' for all 5)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "google", "xai"],
        help="API provider (default: openai, only needed for real runs)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="test",
        help="Model identifier (default: test)",
    )
    parser.add_argument(
        "--series",
        type=int,
        default=10,
        help="Number of best-of-7 series per pair (default: 10)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (or set env var: ANTHROPIC_API_KEY, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use random builds instead of real API calls (for testing)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Directory for output JSONL files (default: results/)",
    )

    return parser


def main() -> None:
    """Entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        run_ablation(args)
    except KeyboardInterrupt:
        print("\nAblation interrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
