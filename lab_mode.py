"""Laboratory Mode v2: iteration efficiency curve experiment.

Gives an LLM unlimited local simulation access and measures how its
proposed builds improve over successive rounds of feedback.

v2 additions (Task 3.1):
- Brute-force known optimum from simulator
- Distance-to-optimum metric per round
- iteration_curve.json output
- Plot output (rounds x best_wr with optimum reference line)
- Convergence tracking (round where improvement < 1pp)

Usage:
    # Dry run (no API key needed)
    python lab_mode.py --dry-run --provider openai --model test --rounds 5 \\
        --builds-per-round 5 --games-per-pair 10

    # Real run with an LLM
    python lab_mode.py --provider anthropic --model claude-sonnet-4-5 --rounds 10
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from simulator.animals import (
    ANIMAL_ABILITIES,
    ANIMAL_PASSIVE,
    Animal,
    Creature,
    Size,
    StatBlock,
)
from simulator.engine import CombatEngine
from simulator.grid import Grid
from simulator.seed import seeded_random

from agents.baselines import Build, SmartAgent
from agents.llm_agent_v2 import _STATIC_RULES


# ---------------------------------------------------------------------------
# Available animals for lab mode (original 6 only)
# ---------------------------------------------------------------------------

_LAB_ANIMALS = (
    Animal.BEAR,
    Animal.BUFFALO,
    Animal.BOAR,
    Animal.TIGER,
    Animal.WOLF,
    Animal.MONKEY,
)
_ANIMAL_NAMES = frozenset(a.value.upper() for a in _LAB_ANIMALS)
_ANIMAL_LOOKUP: dict[str, Animal] = {a.value.upper(): a for a in _LAB_ANIMALS}


# ---------------------------------------------------------------------------
# Creature creation (from a Build)
# ---------------------------------------------------------------------------

def _compute_derived(hp: int, atk: int, spd: int, wil: int) -> dict[str, Any]:
    """Compute derived combat stats from raw stat allocation."""
    max_hp = 50 + 10 * hp
    base_dmg = math.floor(2 + 0.85 * atk)
    dodge = max(0.0, min(0.30, 0.025 * (spd - 1)))
    resist = min(0.60, wil * 0.033)
    return {
        "max_hp": max_hp,
        "base_dmg": base_dmg,
        "dodge": dodge,
        "resist": resist,
    }


def _compute_size(hp: int, atk: int) -> Size:
    """Compute creature size from HP + ATK sum."""
    total = hp + atk
    if total <= 10:
        return Size(1, 1)
    elif total <= 12:
        return Size(2, 1)
    elif total <= 17:
        return Size(2, 2)
    else:
        return Size(3, 2)


def _create_creature(build: Build, side: str, match_seed: int) -> Creature:
    """Create a Creature instance from a Build for one side of the arena."""
    hp, atk, spd, wil = build.hp, build.atk, build.spd, build.wil
    derived = _compute_derived(hp, atk, spd, wil)
    size = _compute_size(hp, atk)
    passive = ANIMAL_PASSIVE.get(build.animal)
    abilities = ANIMAL_ABILITIES.get(build.animal, ())
    grid = Grid()
    position = grid.generate_starting_position(side, size, match_seed)
    movement = 1 if spd <= 3 else (2 if spd <= 6 else 3)

    return Creature(
        animal=build.animal,
        stats=StatBlock(hp=hp, atk=atk, spd=spd, wil=wil),
        passive=passive,
        current_hp=derived["max_hp"],
        max_hp=derived["max_hp"],
        base_dmg=derived["base_dmg"],
        armor_flat=0,
        size=size,
        position=position,
        dodge_chance=derived["dodge"],
        resist_chance=derived["resist"],
        movement_range=movement,
        abilities=abilities,
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _run_games(build_a: Build, build_b: Build, num_games: int,
               base_seed: int) -> dict[str, int]:
    """Run N games between two builds and return win/loss/draw counts."""
    engine = CombatEngine()
    wins_a = 0
    wins_b = 0
    draws = 0

    for i in range(num_games):
        match_seed = base_seed + i
        creature_a = _create_creature(build_a, "a", match_seed)
        creature_b = _create_creature(build_b, "b", match_seed)
        result = engine.run_combat(creature_a, creature_b, match_seed)

        if result.winner == "a":
            wins_a += 1
        elif result.winner == "b":
            wins_b += 1
        else:
            draws += 1

    return {"wins_a": wins_a, "wins_b": wins_b, "draws": draws}


def _run_round_robin(
    builds: list[Build],
    games_per_pair: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    """Run a full round-robin among builds, returning per-build results.

    Returns a list of dicts (one per build), each containing:
        build, total_wins, total_games, win_rate, pairwise (dict of opponent -> wr)
    """
    n = len(builds)
    total_wins = [0] * n
    total_games = [0] * n
    pairwise: list[dict[int, float]] = [{} for _ in range(n)]
    seed_offset = base_seed

    for i in range(n):
        for j in range(i + 1, n):
            res = _run_games(builds[i], builds[j], games_per_pair, seed_offset)
            seed_offset += games_per_pair

            total_wins[i] += res["wins_a"]
            total_wins[j] += res["wins_b"]
            total_games[i] += games_per_pair
            total_games[j] += games_per_pair

            wr_i = res["wins_a"] / games_per_pair if games_per_pair > 0 else 0.0
            wr_j = res["wins_b"] / games_per_pair if games_per_pair > 0 else 0.0
            pairwise[i][j] = wr_i
            pairwise[j][i] = wr_j

    results = []
    for i in range(n):
        wr = total_wins[i] / total_games[i] if total_games[i] > 0 else 0.0
        results.append({
            "build": builds[i],
            "total_wins": total_wins[i],
            "total_games": total_games[i],
            "win_rate": wr,
            "pairwise": pairwise[i],
        })
    return results


# ---------------------------------------------------------------------------
# Build formatting
# ---------------------------------------------------------------------------

def _format_build(build: Build) -> str:
    """Format a Build as 'animal hp/atk/spd/wil'."""
    return f"{build.animal.value} {build.hp}/{build.atk}/{build.spd}/{build.wil}"


def _build_to_dict(build: Build) -> dict[str, Any]:
    """Serialize a Build to a JSON-friendly dict."""
    return {
        "animal": build.animal.value.upper(),
        "hp": build.hp,
        "atk": build.atk,
        "spd": build.spd,
        "wil": build.wil,
    }


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_round1_prompt(builds_per_round: int) -> str:
    """Build the prompt for round 1 (no previous results)."""
    return (
        f"{_STATIC_RULES}\n\n"
        f"LABORATORY MODE\n"
        f"You have access to unlimited local simulation. "
        f"Your task: propose {builds_per_round} different builds to test.\n"
        f"Each build is an animal + stat allocation (HP+ATK+SPD+WIL=20, each >= 1).\n"
        f"Animals: BEAR, BUFFALO, BOAR, TIGER, WOLF, MONKEY\n\n"
        f"Try to explore diverse strategies. You want to find the strongest possible build.\n\n"
        f'Respond with ONLY a JSON array of {builds_per_round} builds (no other text):\n'
        f'[{{"animal":"BEAR","hp":3,"atk":14,"spd":2,"wil":1}}, ...]\n'
    )


def _build_round_n_prompt(
    round_num: int,
    prev_rankings: list[dict[str, Any]],
    pairwise_summary: str,
    builds_per_round: int,
) -> str:
    """Build the prompt for round 2+ with previous results."""
    ranking_lines = []
    for i, entry in enumerate(prev_rankings, 1):
        b = entry["build"]
        wr = entry["win_rate"]
        ranking_lines.append(
            f"  {i}. {b.animal.value.upper()} "
            f"{b.hp}/{b.atk}/{b.spd}/{b.wil} "
            f"-- {wr:.1%} win rate"
        )
    ranking_text = "\n".join(ranking_lines)

    return (
        f"{_STATIC_RULES}\n\n"
        f"LABORATORY MODE — Round {round_num}\n\n"
        f"Results from round {round_num - 1}:\n\n"
        f"Build Rankings (by avg win rate vs field):\n"
        f"{ranking_text}\n\n"
        f"Pairwise matrix (selected matchups):\n"
        f"{pairwise_summary}\n\n"
        f"Now propose {builds_per_round} new builds for the next round.\n"
        f"You may keep good builds from before and replace weak ones.\n"
        f"Your goal: find the single strongest build possible.\n\n"
        f'Respond with ONLY a JSON array of {builds_per_round} builds (no other text):\n'
        f'[{{"animal":"BEAR","hp":3,"atk":14,"spd":2,"wil":1}}, ...]\n'
    )


def _build_pairwise_summary(
    builds: list[Build],
    round_results: list[dict[str, Any]],
    max_rows: int = 10,
) -> str:
    """Build a compact text representation of the pairwise win-rate matrix."""
    n = min(len(builds), max_rows)
    sorted_results = sorted(round_results, key=lambda r: r["win_rate"], reverse=True)
    top_indices = []
    build_to_idx: dict[int, int] = {}
    for entry in sorted_results[:n]:
        idx = round_results.index(entry)
        top_indices.append(idx)
        build_to_idx[idx] = len(top_indices) - 1

    labels = []
    for idx in top_indices:
        b = builds[idx]
        labels.append(f"{b.animal.value[:3].upper()}{b.hp}/{b.atk}")

    header = f"{'':>12}" + "".join(f"{lbl:>10}" for lbl in labels)
    lines = [header]

    for row_idx in top_indices:
        row_pw = round_results[row_idx]["pairwise"]
        row_label = labels[build_to_idx[row_idx]]
        row = f"{row_label:>12}"
        for col_idx in top_indices:
            if row_idx == col_idx:
                row += f"{'--':>10}"
            else:
                wr = row_pw.get(col_idx, 0.0)
                row += f"{wr:.0%}".rjust(10)

        lines.append(row)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Brute-force optimum finder (sampled, vs SmartAgent)
# ---------------------------------------------------------------------------

# Known strong builds to always include in the optimum search
_KNOWN_STRONG_BUILDS: list[tuple[Animal, int, int, int, int]] = [
    (Animal.BEAR, 8, 8, 3, 1),
    (Animal.BEAR, 3, 14, 2, 1),
    (Animal.BEAR, 5, 11, 3, 1),
    (Animal.BEAR, 5, 5, 5, 5),
    (Animal.BEAR, 4, 13, 2, 1),
    (Animal.BEAR, 7, 9, 3, 1),
    (Animal.BOAR, 8, 8, 3, 1),
    (Animal.BOAR, 7, 9, 3, 1),
    (Animal.BOAR, 9, 8, 2, 1),
    (Animal.BOAR, 4, 13, 2, 1),
    (Animal.BUFFALO, 8, 6, 4, 2),
    (Animal.BUFFALO, 7, 7, 4, 2),
    (Animal.TIGER, 2, 8, 7, 3),
    (Animal.TIGER, 1, 3, 15, 1),
    (Animal.WOLF, 5, 10, 3, 2),
    (Animal.WOLF, 7, 5, 4, 4),
    (Animal.MONKEY, 4, 4, 4, 8),
    (Animal.MONKEY, 6, 6, 5, 3),
]


def _sample_random_builds(
    samples_per_animal: int = 50,
    rng_seed: int = 12345,
) -> list[Build]:
    """Generate random valid builds for each of the 6 lab animals.

    Produces *samples_per_animal* random stat allocations per animal
    plus all *_KNOWN_STRONG_BUILDS*, de-duplicated.
    """
    rng = random.Random(rng_seed)
    builds: list[Build] = []
    seen: set[tuple] = set()

    # Add known strong builds first
    for animal, hp, atk, spd, wil in _KNOWN_STRONG_BUILDS:
        key = (animal, hp, atk, spd, wil)
        if key not in seen:
            seen.add(key)
            builds.append(Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil))

    # Random samples per animal
    for animal in _LAB_ANIMALS:
        count = 0
        attempts = 0
        while count < samples_per_animal and attempts < samples_per_animal * 5:
            attempts += 1
            # Random partition of 16 extra points among 4 stats (each starts at 1)
            cuts = sorted(rng.sample(range(1, 17), 3))  # 3 cuts in 1..16
            parts = [
                cuts[0],
                cuts[1] - cuts[0],
                cuts[2] - cuts[1],
                16 - cuts[2],
            ]
            hp = 1 + parts[0]
            atk = 1 + parts[1]
            spd = 1 + parts[2]
            wil = 1 + parts[3]
            key = (animal, hp, atk, spd, wil)
            if key not in seen:
                seen.add(key)
                builds.append(Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil))
                count += 1

    return builds


def _eval_build_vs_smart(
    build: Build,
    num_games: int,
    base_seed: int,
) -> float:
    """Evaluate a build against SmartAgent's counter-pick over *num_games* seeds.

    SmartAgent sees the candidate's animal and picks its best counter.
    Returns the candidate's win rate.
    """
    smart = SmartAgent()
    counter = smart.choose_build(
        opponent_animal=build.animal,
        banned=[],
    )
    res = _run_games(build, counter, num_games, base_seed)
    return res["wins_a"] / num_games if num_games > 0 else 0.0


# Module-level cache for the optimum result
_OPTIMUM_CACHE: dict[str, Any] = {}


def _find_optimum(
    num_games: int = 50,
    samples_per_animal: int = 50,
    base_seed: int = 7777,
) -> tuple[Build, float]:
    """Find the approximate optimum by sampling builds and testing vs SmartAgent.

    Uses *samples_per_animal* random allocations per animal (~300 total)
    plus known strong builds. Each candidate is tested over *num_games*
    seeds against SmartAgent's counter-pick.

    Results are cached so the search runs only once per process.

    Returns:
        (best_build, best_win_rate) tuple.
    """
    cache_key = f"{num_games}_{samples_per_animal}_{base_seed}"
    if cache_key in _OPTIMUM_CACHE:
        cached = _OPTIMUM_CACHE[cache_key]
        return cached["build"], cached["wr"]

    candidates = _sample_random_builds(
        samples_per_animal=samples_per_animal,
        rng_seed=base_seed,
    )

    best_build = candidates[0]
    best_wr = 0.0
    seed_offset = base_seed

    total = len(candidates)
    for idx, candidate in enumerate(candidates):
        wr = _eval_build_vs_smart(candidate, num_games, seed_offset)
        seed_offset += num_games

        if wr > best_wr:
            best_wr = wr
            best_build = candidate

        if (idx + 1) % 100 == 0:
            print(f"  Optimum search: {idx + 1}/{total} builds tested...")

    _OPTIMUM_CACHE[cache_key] = {"build": best_build, "wr": best_wr}
    return best_build, best_wr


def _eval_model_build_vs_smart(
    model_build: Build,
    num_games: int = 50,
    base_seed: int = 8888,
) -> float:
    """Evaluate a model's build against SmartAgent, returning win rate."""
    return _eval_build_vs_smart(model_build, num_games, base_seed)


# ---------------------------------------------------------------------------
# Plot generation
# ---------------------------------------------------------------------------

def _generate_plot(
    curve: list[dict[str, Any]],
    optimum_wr: float | None,
    convergence_round: int,
    model: str,
    output_path: str,
) -> str | None:
    """Generate iteration curve plot (rounds x best_wr).

    Returns the path to the saved PNG, or None if matplotlib unavailable.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  Warning: matplotlib not available, skipping plot generation.")
        return None

    rounds = [entry["round"] for entry in curve]
    best_wrs = [entry["best_wr"] for entry in curve]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rounds, best_wrs, "b-o", linewidth=2, markersize=6, label="Best WR per round")

    if optimum_wr is not None:
        ax.axhline(y=optimum_wr, color="r", linestyle="--", linewidth=1.5,
                    label=f"Known optimum ({optimum_wr:.1%})")

    if convergence_round < len(curve):
        ax.axvline(x=convergence_round, color="g", linestyle=":", linewidth=1.5,
                    label=f"Convergence (round {convergence_round})")

    ax.set_xlabel("Round", fontsize=12)
    ax.set_ylabel("Best Win Rate (vs field)", fontsize=12)
    ax.set_title(f"Moreau Arena Lab Mode — Iteration Curve\n{model}", fontsize=13)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(rounds)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

_JSON_ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")
_JSON_OBJECT_PATTERN = re.compile(r"\{[^}]+\}")


def _parse_builds_response(
    response_text: str,
    expected_count: int,
) -> list[Build]:
    """Parse an LLM response into a list of Build objects.

    Tries JSON array first, then falls back to extracting individual
    JSON objects from the text.
    """
    builds: list[Build] = []

    array_match = _JSON_ARRAY_PATTERN.search(response_text)
    if array_match:
        try:
            items = json.loads(array_match.group(0))
            if isinstance(items, list):
                for item in items:
                    build = _validate_build_dict(item)
                    if build is not None:
                        builds.append(build)
                if builds:
                    return builds[:expected_count]
        except (json.JSONDecodeError, TypeError):
            pass

    for obj_match in _JSON_OBJECT_PATTERN.finditer(response_text):
        try:
            data = json.loads(obj_match.group(0))
            build = _validate_build_dict(data)
            if build is not None:
                builds.append(build)
        except (json.JSONDecodeError, TypeError):
            continue

    return builds[:expected_count]


def _validate_build_dict(data: dict) -> Build | None:
    """Validate a parsed dict into a Build, returning None on failure."""
    try:
        animal_str = str(data.get("animal", "")).upper()
        animal = _ANIMAL_LOOKUP.get(animal_str)
        if animal is None:
            return None

        hp = int(data["hp"])
        atk = int(data["atk"])
        spd = int(data["spd"])
        wil = int(data["wil"])

        if hp < 1 or atk < 1 or spd < 1 or wil < 1:
            return None
        if hp + atk + spd + wil != 20:
            return None

        return Build(animal=animal, hp=hp, atk=atk, spd=spd, wil=wil)
    except (ValueError, TypeError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Dry-run build generator
# ---------------------------------------------------------------------------

def _generate_dry_run_builds(
    count: int,
    round_num: int,
    seed: int,
) -> list[Build]:
    """Generate deterministic pseudo-random builds for --dry-run mode."""
    animals = list(_LAB_ANIMALS)
    builds: list[Build] = []

    for i in range(count):
        build_seed = seed + round_num * 1000 + i
        animal_idx = int(seeded_random(build_seed, 0, len(animals) - 0.001))
        animal = animals[animal_idx]

        remaining = 16  # 20 - 4 (min 1 each)
        values = [1, 1, 1, 1]
        for s in range(4):
            sub_seed_val = build_seed * 31 + s * 7919
            sub_seed_val = sub_seed_val & 0xFFFFFFFF
            if s == 3:
                values[s] += remaining
            else:
                max_alloc = min(remaining, 14)
                if max_alloc > 0:
                    alloc = int(seeded_random(sub_seed_val, 0, max_alloc + 0.999))
                    alloc = max(0, min(alloc, remaining))
                    values[s] += alloc
                    remaining -= alloc

        try:
            builds.append(Build(
                animal=animal,
                hp=values[0],
                atk=values[1],
                spd=values[2],
                wil=values[3],
            ))
        except ValueError:
            builds.append(Build(animal=animal, hp=5, atk=5, spd=5, wil=5))

    return builds


# ---------------------------------------------------------------------------
# API call helpers (urllib only)
# ---------------------------------------------------------------------------

def _get_api_key(provider: str, cli_key: str | None) -> str:
    """Resolve the API key from CLI arg or environment variable."""
    if cli_key:
        return cli_key

    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "xai": "XAI_API_KEY",
    }

    keys = env_map.get(provider, provider.upper() + "_API_KEY")
    if isinstance(keys, list):
        for k in keys:
            val = os.environ.get(k)
            if val:
                return val
        raise ValueError(
            f"No API key found. Set one of: {', '.join(keys)} "
            f"or pass --api-key"
        )

    val = os.environ.get(keys)
    if not val:
        raise ValueError(
            f"No API key found. Set {keys} or pass --api-key"
        )
    return val


def _create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context for HTTPS requests."""
    ctx = ssl.create_default_context()
    return ctx


def _call_anthropic(
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Call Anthropic Messages API and return the text response."""
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = _create_ssl_context()

    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    for block in body.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""


def _call_openai(
    api_key: str,
    model: str,
    prompt: str,
    base_url: str = "https://api.openai.com/v1/chat/completions",
) -> str:
    """Call OpenAI-compatible chat completions API and return the text response."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.7,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    ctx = _create_ssl_context()

    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    choices = body.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _call_google(
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Call Google Generative Language API and return the text response."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 4096,
            "temperature": 0.7,
        },
    }
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = _create_ssl_context()

    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    candidates = body.get("candidates", [])
    if candidates:
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if parts:
            return parts[0].get("text", "")
    return ""


def _call_xai(
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Call xAI API (OpenAI-compatible) and return the text response."""
    return _call_openai(
        api_key, model, prompt,
        base_url="https://api.x.ai/v1/chat/completions",
    )


_PROVIDER_CALLERS = {
    "anthropic": _call_anthropic,
    "openai": _call_openai,
    "google": _call_google,
    "xai": _call_xai,
}


def _call_llm(
    provider: str,
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    """Route an LLM call to the appropriate provider."""
    caller = _PROVIDER_CALLERS.get(provider)
    if caller is None:
        raise ValueError(f"Unknown provider: {provider}")
    return caller(api_key, model, prompt)


# ---------------------------------------------------------------------------
# Main lab loop
# ---------------------------------------------------------------------------

def run_lab(
    provider: str,
    model: str,
    api_key: str,
    builds_per_round: int,
    games_per_pair: int,
    rounds: int,
    seed: int,
    dry_run: bool,
    output_dir: str,
    skip_optimum: bool = False,
    optimum_games: int = 0,
) -> dict[str, Any]:
    """Execute the laboratory mode experiment and return full results.

    Returns a dict with model info, iteration curve, distance-to-optimum,
    and totals. Saves iteration_curve.json and iteration_curve.png.
    """
    curve: list[dict[str, Any]] = []
    total_simulations = 0
    total_api_calls = 0
    round_seed = seed

    # Resolve optimum games: default to games_per_pair (min 5 for speed)
    if optimum_games <= 0:
        optimum_games = max(5, games_per_pair)

    print(f"\n{'=' * 60}")
    print("MOREAU ARENA -- LABORATORY MODE v2")
    print(f"{'=' * 60}")
    print(f"Model: {model} ({provider})")
    print(f"Rounds: {rounds} | Builds/round: {builds_per_round} | Games/pair: {games_per_pair}")
    if dry_run:
        print("Mode: DRY RUN (random builds, no API calls)")
    if not skip_optimum:
        print(f"Optimum search: enabled ({optimum_games} games/pair)")
    print()

    sims_per_round = builds_per_round * (builds_per_round - 1) // 2 * games_per_pair
    est_total = sims_per_round * rounds
    print(f"Estimated simulations per round: {sims_per_round:,}")
    print(f"Estimated total simulations: {est_total:,}")
    print()

    # Compute optimum upfront so per-round distance can be tracked
    optimum_build: Build | None = None
    optimum_wr: float | None = None
    if not skip_optimum:
        print("--- Finding brute-force optimum (sampled, vs SmartAgent) ---")
        opt_start = time.time()
        optimum_build, optimum_wr = _find_optimum(
            num_games=optimum_games,
            samples_per_animal=50,
            base_seed=seed + 5_000_000,
        )
        opt_elapsed = time.time() - opt_start
        print(
            f"  Optimum: {_format_build(optimum_build)} "
            f"({optimum_wr:.1%}) found in {opt_elapsed:.1f}s"
        )
        print()

    prev_rankings: list[dict[str, Any]] | None = None
    prev_builds: list[Build] | None = None

    for r in range(1, rounds + 1):
        round_start = time.time()
        print(f"--- Round {r}/{rounds} ---")

        # 1. Get builds from LLM (or dry-run generator)
        if dry_run:
            builds = _generate_dry_run_builds(builds_per_round, r, seed)
        else:
            if r == 1:
                prompt = _build_round1_prompt(builds_per_round)
            else:
                pairwise_summary = _build_pairwise_summary(
                    prev_builds, prev_rankings,
                )
                sorted_prev = sorted(
                    prev_rankings, key=lambda x: x["win_rate"], reverse=True,
                )
                prompt = _build_round_n_prompt(
                    r, sorted_prev, pairwise_summary, builds_per_round,
                )

            try:
                response_text = _call_llm(provider, api_key, model, prompt)
                total_api_calls += 1
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                print(f"  API error: {exc}")
                print("  Falling back to dry-run builds for this round.")
                builds = _generate_dry_run_builds(builds_per_round, r, seed)
                response_text = None

            if not dry_run and response_text is not None:
                builds = _parse_builds_response(response_text, builds_per_round)
                if not builds:
                    print(f"  Warning: could not parse any builds from LLM response.")
                    print(f"  Response preview: {response_text[:200]}")
                    builds = _generate_dry_run_builds(builds_per_round, r, seed)

        # Deduplicate builds (keep first occurrence)
        seen: set[tuple] = set()
        unique_builds: list[Build] = []
        for b in builds:
            key = (b.animal, b.hp, b.atk, b.spd, b.wil)
            if key not in seen:
                seen.add(key)
                unique_builds.append(b)
        builds = unique_builds

        if len(builds) < 2:
            print(f"  Warning: only {len(builds)} unique build(s), adding fallback.")
            fallback = Build(animal=Animal.BEAR, hp=5, atk=5, spd=5, wil=5)
            if len(builds) == 0:
                builds = [
                    fallback,
                    Build(animal=Animal.BOAR, hp=8, atk=8, spd=3, wil=1),
                ]
            else:
                builds.append(fallback)

        print(f"  Builds submitted: {len(builds)}")

        # 2. Run round-robin simulation
        actual_sims = len(builds) * (len(builds) - 1) // 2 * games_per_pair
        total_simulations += actual_sims

        round_results = _run_round_robin(builds, games_per_pair, round_seed)
        round_seed += actual_sims

        # 3. Sort by win rate
        sorted_results = sorted(
            round_results, key=lambda x: x["win_rate"], reverse=True,
        )

        best_entry = sorted_results[0]
        best_build = best_entry["build"]
        best_wr = best_entry["win_rate"]

        print(f"  Best: {_format_build(best_build)} ({best_wr:.1%})")
        elapsed = time.time() - round_start
        print(f"  Simulations: {actual_sims:,} | Time: {elapsed:.1f}s")
        print()

        # Record curve entry
        all_builds_data = []
        for entry in sorted_results:
            b = entry["build"]
            all_builds_data.append({
                "animal": b.animal.value.upper(),
                "hp": b.hp,
                "atk": b.atk,
                "spd": b.spd,
                "wil": b.wil,
                "win_rate": round(entry["win_rate"], 4),
            })

        # Compute per-round improvement
        if len(curve) == 0:
            improvement_pp: float | None = None
        else:
            prev_best = curve[-1]["best_wr"]
            improvement_pp = round((best_wr - prev_best) * 100, 2)

        # Compute per-round distance-to-optimum (vs SmartAgent)
        round_distance: float | None = None
        if optimum_wr is not None:
            model_wr_vs_smart = _eval_model_build_vs_smart(
                best_build,
                num_games=optimum_games,
                base_seed=seed + 6_000_000 + r * 10000,
            )
            round_distance = round(optimum_wr - model_wr_vs_smart, 4)

        curve.append({
            "round": r,
            "best_build": _build_to_dict(best_build),
            "best_wr": round(best_wr, 4),
            "improvement_pp": improvement_pp,
            "distance_to_optimum": round_distance,
            "builds_tried": all_builds_data,
        })

        prev_rankings = round_results
        prev_builds = builds

    # -----------------------------------------------------------------------
    # Final analysis
    # -----------------------------------------------------------------------

    # Find overall best build across all rounds
    overall_best_wr = 0.0
    overall_best_build: Build | None = None
    overall_best_round = 0

    for entry in curve:
        if entry["best_wr"] > overall_best_wr:
            overall_best_wr = entry["best_wr"]
            overall_best_build = _find_build_from_curve_entry(entry)
            overall_best_round = entry["round"]

    if overall_best_build is None:
        overall_best_build = Build(animal=Animal.BEAR, hp=5, atk=5, spd=5, wil=5)

    # Convergence: first round where improvement < 1pp
    convergence_round = rounds
    for i in range(1, len(curve)):
        imp = curve[i]["improvement_pp"]
        if imp is not None and imp < 1.0:
            convergence_round = curve[i]["round"]
            break

    # SmartAgent comparison: run 100 games vs bear 3/14/2/1
    smart_build = Build(animal=Animal.BEAR, hp=3, atk=14, spd=2, wil=1)
    comparison_res = _run_games(overall_best_build, smart_build, 100, seed + 999999)
    vs_smart_wr = comparison_res["wins_a"] / 100.0

    # Print final results
    derived = _compute_derived(
        overall_best_build.hp, overall_best_build.atk,
        overall_best_build.spd, overall_best_build.wil,
    )

    first_wr = curve[0]["best_wr"]
    last_wr = curve[-1]["best_wr"]
    total_improvement_pp = (last_wr - first_wr) * 100

    print(f"\n{'=' * 60}")
    print("=== LABORATORY MODE v2 RESULTS ===")
    print(f"{'=' * 60}")
    print()
    print(f"Model: {model}")
    print(
        f"Rounds: {rounds} | Builds/round: {builds_per_round} | "
        f"Games/pair: {games_per_pair}"
    )
    print(f"Total simulations: {total_simulations:,}")
    print(f"Total API calls: {total_api_calls}")
    print()
    print("Iteration Curve:")
    for entry in curve:
        bb = entry["best_build"]
        build_str = f"{bb['animal']} {bb['hp']}/{bb['atk']}/{bb['spd']}/{bb['wil']}"
        marker = ""
        if entry["round"] == overall_best_round:
            marker = "  [peak]"
        if entry["round"] == convergence_round and entry["round"] > 1:
            marker = "  [converged]"
        dist_str = ""
        if entry.get("distance_to_optimum") is not None:
            dist_str = f"  d2o={entry['distance_to_optimum']:.2f}"
        print(
            f"  Round {entry['round']:2d}: best = {build_str}  "
            f"({entry['best_wr']:.1%}){dist_str}{marker}"
        )

    print()
    print(
        f"Improvement: {first_wr:.1%} -> {last_wr:.1%} "
        f"({'+' if total_improvement_pp >= 0 else ''}{total_improvement_pp:.1f}pp "
        f"over {rounds} rounds)"
    )
    print(
        f"Convergence: round {convergence_round} "
        f"(first round with <1pp improvement)"
    )
    print()
    print(f"Best build found: {_format_build(overall_best_build)}")
    print(
        f"  max_hp={derived['max_hp']}, base_dmg={derived['base_dmg']}, "
        f"dodge={derived['dodge']:.1%}, resist={derived['resist']:.1%}"
    )
    print(
        f"  Win rate vs SmartAgent's bear 3/14/2/1: {vs_smart_wr:.1%}"
    )

    if optimum_build is not None and optimum_wr is not None:
        print()
        print(
            f"Known optimum: {_format_build(optimum_build)} "
            f"({optimum_wr:.1%} vs SmartAgent)"
        )
        final_dist = curve[-1].get("distance_to_optimum")
        if final_dist is not None:
            print(f"Final distance-to-optimum: {final_dist:.4f}")

    # Build output dict (full results)
    ts_iso = datetime.now(timezone.utc).isoformat()
    output: dict[str, Any] = {
        "version": 2,
        "model": model,
        "provider": provider,
        "rounds": rounds,
        "builds_per_round": builds_per_round,
        "games_per_pair": games_per_pair,
        "seed": seed,
        "dry_run": dry_run,
        "curve": curve,
        "total_simulations": total_simulations,
        "total_api_calls": total_api_calls,
        "best_build": _build_to_dict(overall_best_build),
        "best_build_wr": round(overall_best_wr, 4),
        "best_build_round": overall_best_round,
        "convergence_round": convergence_round,
        "vs_smart_agent_wr": round(vs_smart_wr, 4),
        "improvement_pp": round(total_improvement_pp, 1),
        "timestamp": ts_iso,
    }

    if optimum_build is not None and optimum_wr is not None:
        output["optimum"] = {
            "build": _build_to_dict(optimum_build),
            "win_rate": round(optimum_wr, 4),
        }

    # Save results
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_model = re.sub(r"[^a-zA-Z0-9_.-]", "_", model)

    # Save full results JSON
    filename = f"lab_{safe_model}_{ts}.json"
    filepath = out_path / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {filepath}")

    # Save iteration_curve_TIMESTAMP.json (spec format from Task 3.1)
    optimum_section: dict[str, Any] | None = None
    if optimum_build is not None and optimum_wr is not None:
        optimum_section = {
            "animal": optimum_build.animal.value.upper(),
            "stats": [optimum_build.hp, optimum_build.atk,
                      optimum_build.spd, optimum_build.wil],
            "win_rate": round(optimum_wr, 4),
        }

    curve_output: dict[str, Any] = {
        "metadata": {
            "provider": provider,
            "model": model,
            "rounds": rounds,
            "builds_per_round": builds_per_round,
            "games_per_pair": games_per_pair,
            "dry_run": dry_run,
            "timestamp": ts_iso,
        },
        "optimum": optimum_section,
        "convergence_round": convergence_round,
        "rounds": [
            {
                "round": entry["round"],
                "best_build": entry["best_build"],
                "best_wr": entry["best_wr"],
                "distance_to_optimum": entry.get("distance_to_optimum"),
                "improvement_pp": entry.get("improvement_pp"),
                "builds_tried": entry.get("builds_tried", []),
            }
            for entry in curve
        ],
    }

    curve_filename = f"iteration_curve_{ts}.json"
    curve_filepath = out_path / curve_filename
    with open(curve_filepath, "w", encoding="utf-8") as f:
        json.dump(curve_output, f, indent=2, ensure_ascii=False)
    print(f"Iteration curve saved to: {curve_filepath}")

    # Generate plot
    plot_filename = f"iteration_curve_{safe_model}_{ts}.png"
    plot_filepath = str(out_path / plot_filename)
    plot_result = _generate_plot(
        curve=curve,
        optimum_wr=optimum_wr,
        convergence_round=convergence_round,
        model=model,
        output_path=plot_filepath,
    )
    if plot_result:
        print(f"Plot saved to: {plot_result}")

    return output


def _find_build_from_curve_entry(entry: dict[str, Any]) -> Build | None:
    """Extract the best Build from a curve entry's best_build dict."""
    best = entry.get("best_build")
    if best is None or not isinstance(best, dict):
        return None
    animal = _ANIMAL_LOOKUP.get(str(best.get("animal", "")).upper())
    if animal is None:
        return None
    try:
        return Build(
            animal=animal,
            hp=best["hp"],
            atk=best["atk"],
            spd=best["spd"],
            wil=best["wil"],
        )
    except (ValueError, KeyError):
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Moreau Arena -- Laboratory Mode v2 (iteration efficiency curve)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Dry run (no API key needed)\n"
            '  python lab_mode.py --dry-run --provider openai --model test '
            "--rounds 5 --builds-per-round 5 --games-per-pair 10\n\n"
            "  # Real run\n"
            "  python lab_mode.py --provider anthropic "
            "--model claude-sonnet-4-5 --rounds 10\n\n"
            "  # Skip optimum search (faster)\n"
            "  python lab_mode.py --dry-run --provider openai --model test "
            "--rounds 5 --skip-optimum\n"
        ),
    )

    parser.add_argument(
        "--provider",
        type=str,
        required=True,
        choices=["openai", "anthropic", "google", "xai"],
        help="LLM provider (openai, anthropic, google, xai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model identifier (e.g. claude-sonnet-4-5, gpt-4o)",
    )
    parser.add_argument(
        "--builds-per-round",
        type=int,
        default=20,
        help="Number of builds the LLM proposes each round (default: 20)",
    )
    parser.add_argument(
        "--games-per-pair",
        type=int,
        default=50,
        help="Number of simulation games per build pair (default: 50)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="Number of iteration rounds (default: 10)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (or set via env: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate random builds instead of calling LLM API",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Directory for output files (default: results/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--skip-optimum",
        action="store_true",
        help="Skip brute-force optimum search (faster, no distance-to-optimum)",
    )
    parser.add_argument(
        "--optimum-games",
        type=int,
        default=0,
        help="Games per pair for optimum search (default: games_per_pair / 5)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for laboratory mode."""
    args = _parse_args(argv)

    if not args.dry_run:
        try:
            api_key = _get_api_key(args.provider, args.api_key)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        api_key = "dry-run"

    try:
        run_lab(
            provider=args.provider,
            model=args.model,
            api_key=api_key,
            builds_per_round=args.builds_per_round,
            games_per_pair=args.games_per_pair,
            rounds=args.rounds,
            seed=args.seed,
            dry_run=args.dry_run,
            output_dir=args.output_dir,
            skip_optimum=args.skip_optimum,
            optimum_games=args.optimum_games,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
