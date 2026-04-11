from __future__ import annotations

import json
import math
import random
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Protocol


MAX_VITALITY = 20
START_VITALITY = 10
DEFAULT_MAX_CYCLES = 50
DEFAULT_CARRY_LIMIT = 1200
WEATHER_SEQUENCE = ("clear", "wind", "storm", "scarcity")


BASE_GRAPH: dict[str, tuple[str, ...]] = {
    "shore": ("grove",),
    "grove": ("shore", "marsh", "ridge", "shelter"),
    "shelter": ("grove", "spring", "scrap"),
    "marsh": ("grove", "quarry"),
    "ridge": ("grove", "quarry", "watch"),
    "spring": ("shelter", "watch"),
    "scrap": ("shelter", "watch"),
    "quarry": ("marsh", "ridge"),
    "watch": ("ridge", "spring", "scrap"),
}

EDGE_COLLAPSE_ORDER = (
    ("grove", "marsh"),
    ("ridge", "quarry"),
    ("scrap", "watch"),
)

BLOOM_TARGET_SEQUENCE = ("scrap", "watch", "ridge", "grove")


@dataclass
class NodeState:
    node_id: str
    kind: str
    resource: int = 0
    hazard: int = 0
    shelter: bool = False


@dataclass
class WorldState:
    cycle: int
    weather: str
    nodes: dict[str, NodeState]
    blocked_edges: set[tuple[str, str]] = field(default_factory=set)
    last_event: str = "habitat initialized"


@dataclass
class AgentRuntimeState:
    location: str = "shore"
    vitality: int = START_VITALITY
    carry_forward: str = ""
    death_reason: str | None = None


@dataclass
class AgentDecision:
    action: str
    carry_forward: str = ""
    rationale: str = ""


@dataclass
class EpisodeSummary:
    agent_name: str
    seed: int
    cycles_completed: int
    died: bool
    death_reason: str | None
    ending_location: str
    ending_vitality: int
    action_counts: dict[str, int]
    action_diversity: float
    carry_forward_bytes_last: int
    carry_forward_bytes_mean: float
    resources_gathered: int
    world_events_seen: list[str]


class HabitatAgent(Protocol):
    name: str

    def decide(self, observation: dict, runtime: AgentRuntimeState) -> AgentDecision:
        ...


def initial_world() -> WorldState:
    nodes = {
        "shore": NodeState("shore", "empty"),
        "grove": NodeState("grove", "resource", resource=3),
        "shelter": NodeState("shelter", "shelter", shelter=True),
        "marsh": NodeState("marsh", "hazard", hazard=2),
        "ridge": NodeState("ridge", "resource", resource=1),
        "spring": NodeState("spring", "shelter", shelter=True),
        "scrap": NodeState("scrap", "resource", resource=1),
        "quarry": NodeState("quarry", "hazard", hazard=2),
        "watch": NodeState("watch", "resource", resource=1),
    }
    return WorldState(cycle=0, weather="clear", nodes=nodes)


def _canonical_edge(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def _neighbors(world: WorldState, node_id: str) -> list[str]:
    neighbors: list[str] = []
    for candidate in BASE_GRAPH[node_id]:
        if _canonical_edge(node_id, candidate) not in world.blocked_edges:
            neighbors.append(candidate)
    return neighbors


def observe(world: WorldState, runtime: AgentRuntimeState) -> dict:
    current = world.nodes[runtime.location]
    visible_nodes = [runtime.location, *_neighbors(world, runtime.location)]
    visible = {}
    for node_id in visible_nodes:
        node = world.nodes[node_id]
        visible[node_id] = {
            "kind": node.kind,
            "resource": node.resource,
            "hazard": node.hazard,
            "shelter": node.shelter,
            "neighbors": _neighbors(world, node_id),
        }
    legal_actions = ["REST", *[f"MOVE:{node_id}" for node_id in _neighbors(world, runtime.location)]]
    if current.resource > 0:
        legal_actions.append("GATHER")
    return {
        "cycle": world.cycle,
        "weather": world.weather,
        "weather_next": WEATHER_SEQUENCE[(world.cycle + 1) % len(WEATHER_SEQUENCE)],
        "location": runtime.location,
        "vitality": runtime.vitality,
        "carry_forward": runtime.carry_forward,
        "visible": visible,
        "legal_actions": legal_actions,
        "last_event": world.last_event,
    }


def _clip_carry_forward(text: str, limit: int) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def _json_loads_safely(text: str) -> dict:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 4)


def _distance(world: WorldState, start: str, goal: str) -> int | None:
    if start == goal:
        return 0
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        node, dist = queue.popleft()
        for nxt in _neighbors(world, node):
            if nxt == goal:
                return dist + 1
            if nxt in seen:
                continue
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None


def _next_step_toward(world: WorldState, start: str, goal: str) -> str | None:
    if start == goal:
        return None
    best_neighbor: str | None = None
    best_distance: int | None = None
    for neighbor in _neighbors(world, start):
        dist = _distance(world, neighbor, goal)
        if dist is None:
            continue
        if best_distance is None or dist < best_distance or (dist == best_distance and neighbor < (best_neighbor or neighbor)):
            best_distance = dist
            best_neighbor = neighbor
    return best_neighbor


def _hazard_penalty(world: WorldState, location: str) -> int:
    node = world.nodes[location]
    penalty = node.hazard
    if world.weather == "storm":
        penalty += 3 if not node.shelter else 1
    if world.weather == "scarcity" and node.kind == "hazard":
        penalty += 1
    return penalty


def resolve_decision(
    world: WorldState,
    runtime: AgentRuntimeState,
    decision: AgentDecision,
    *,
    carry_limit: int,
) -> tuple[dict, AgentRuntimeState]:
    before_location = runtime.location
    current = world.nodes[runtime.location]
    action = decision.action.strip().upper()
    event_parts = [f"action={action}"]
    gathered = 0
    vitality_delta = -2

    if action.startswith("MOVE:"):
        target = action.split(":", 1)[1].strip().lower()
        if target in _neighbors(world, runtime.location):
            runtime.location = target
            event_parts.append(f"moved={target}")
        else:
            event_parts.append("invalid_move")
    elif action == "GATHER":
        if current.resource > 0:
            current.resource -= 1
            gain = 6 if world.weather != "scarcity" else 4
            vitality_delta += gain
            gathered = 1
            event_parts.append(f"gathered={gain}")
        else:
            event_parts.append("dry_gather")
    elif action == "REST":
        rest_gain = 2 if current.shelter else 0
        if world.weather == "storm" and not current.shelter:
            rest_gain = 0
        vitality_delta += rest_gain
        event_parts.append(f"rested={rest_gain}")
    else:
        event_parts.append("invalid_action")

    hazard_penalty = _hazard_penalty(world, runtime.location)
    vitality_delta -= hazard_penalty
    if hazard_penalty:
        event_parts.append(f"hazard={hazard_penalty}")

    runtime.vitality = max(0, min(MAX_VITALITY, runtime.vitality + vitality_delta))
    runtime.carry_forward = _clip_carry_forward(decision.carry_forward, carry_limit)
    if runtime.vitality <= 0:
        runtime.death_reason = "vitality_depleted"

    return {
        "cycle": world.cycle,
        "before_location": before_location,
        "after_location": runtime.location,
        "action": action,
        "rationale": decision.rationale,
        "gathered": gathered,
        "vitality_after": runtime.vitality,
        "carry_forward": runtime.carry_forward,
        "resolution": ", ".join(event_parts),
    }, runtime


def world_tick(world: WorldState, rng: random.Random) -> str:
    next_cycle = world.cycle + 1
    events: list[str] = []

    world.weather = WEATHER_SEQUENCE[next_cycle % len(WEATHER_SEQUENCE)]
    events.append(f"weather={world.weather}")

    resource_nodes = [node for node in world.nodes.values() if node.kind == "resource"]

    if next_cycle % 3 == 0:
        source = max(resource_nodes, key=lambda item: (item.resource, item.node_id))
        preferred = BLOOM_TARGET_SEQUENCE[((next_cycle // 3) - 1) % len(BLOOM_TARGET_SEQUENCE)]
        if preferred == source.node_id:
            target_candidates = [node for node in resource_nodes if node.node_id != source.node_id]
            target = target_candidates[0]
        else:
            target = world.nodes[preferred]
        if source.resource > 0:
            source.resource = max(0, source.resource - 1)
        target.resource = min(4, target.resource + 3)
        events.append(f"bloom_shift={source.node_id}->{target.node_id}")

    if next_cycle % 4 == 0:
        hazard_nodes = ["marsh", "quarry", "ridge", "watch"]
        for node_id in hazard_nodes:
            world.nodes[node_id].hazard = max(0, world.nodes[node_id].hazard - 1)
        chosen = hazard_nodes[rng.randrange(len(hazard_nodes))]
        world.nodes[chosen].hazard = min(3, world.nodes[chosen].hazard + 2)
        events.append(f"hazard_shift={chosen}")

    if next_cycle % 6 == 0:
        edge = EDGE_COLLAPSE_ORDER[((next_cycle // 6) - 1) % len(EDGE_COLLAPSE_ORDER)]
        canonical = _canonical_edge(*edge)
        if canonical not in world.blocked_edges:
            world.blocked_edges.add(canonical)
            events.append(f"landslide={canonical[0]}-{canonical[1]}")

    world.cycle = next_cycle
    world.last_event = "; ".join(events)
    return world.last_event


class RandomAgent:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def decide(self, observation: dict, runtime: AgentRuntimeState) -> AgentDecision:
        choice = self._rng.choice(observation["legal_actions"])
        return AgentDecision(action=choice, carry_forward="", rationale="random choice")


class FreshHeuristicAgent:
    name = "fresh-heuristic"

    def decide(self, observation: dict, runtime: AgentRuntimeState) -> AgentDecision:
        visible = observation["visible"]
        current = visible[observation["location"]]
        vitality = observation["vitality"]

        if "GATHER" in observation["legal_actions"] and current["resource"] > 0 and vitality <= 17:
            return AgentDecision(action="GATHER", rationale="gather visible resource")
        if vitality <= 6:
            if current["shelter"]:
                return AgentDecision(action="REST", rationale="recover at visible shelter")
            shelter_moves = [action for action in observation["legal_actions"] if action.startswith("MOVE:") and visible[action.split(":", 1)[1]]["shelter"]]
            if shelter_moves:
                return AgentDecision(action=sorted(shelter_moves)[0], rationale="move toward visible shelter")
        resource_moves = [
            action
            for action in observation["legal_actions"]
            if action.startswith("MOVE:") and visible[action.split(":", 1)[1]]["resource"] > 0
        ]
        if resource_moves:
            best = max(resource_moves, key=lambda action: (visible[action.split(":", 1)[1]]["resource"], action))
            return AgentDecision(action=best, rationale="move toward visible resource")
        if "REST" in observation["legal_actions"] and vitality < 5:
            return AgentDecision(action="REST", rationale="stabilize")
        moves = sorted(action for action in observation["legal_actions"] if action.startswith("MOVE:"))
        if moves:
            return AgentDecision(action=moves[0], rationale="default exploration")
        return AgentDecision(action="REST", rationale="no move available")


def _extract_bloom_target(last_event: str) -> str | None:
    marker = "bloom_shift="
    if marker not in last_event:
        return None
    try:
        pair = last_event.split(marker, 1)[1].split(";", 1)[0]
        _, target = pair.split("->", 1)
        target = target.strip()
        return target if target in BASE_GRAPH else None
    except ValueError:
        return None


def _scout_decision(
    observation: dict,
    runtime: AgentRuntimeState,
    *,
    use_memory: bool,
    allow_offscreen_routing: bool,
) -> AgentDecision:
    memory = _json_loads_safely(runtime.carry_forward) if use_memory else {}
    visible = observation["visible"]
    current_location = observation["location"]
    vitality = observation["vitality"]
    legal_actions = observation["legal_actions"]
    current = visible[current_location]

    known_resources = memory.get("known_resources", {})
    visited = set(memory.get("visited", []))
    known_shelters = set(memory.get("known_shelters", []))
    blocked = set(tuple(edge) for edge in memory.get("blocked_edges", []))
    last_weather = memory.get("last_weather")
    bloom_target = memory.get("bloom_target")

    for node_id, node in visible.items():
        visited.add(node_id)
        if node["resource"] > 0:
            known_resources[node_id] = node["resource"]
        else:
            known_resources.pop(node_id, None)
        if node["shelter"]:
            known_shelters.add(node_id)
    for node_id in BASE_GRAPH:
        for neighbor in BASE_GRAPH[node_id]:
            if neighbor not in visible.get(node_id, {}).get("neighbors", BASE_GRAPH[node_id]):
                blocked.add(_canonical_edge(node_id, neighbor))

    observed_bloom_target = _extract_bloom_target(observation["last_event"]) if use_memory else None
    if observed_bloom_target:
        bloom_target = observed_bloom_target
        known_resources[bloom_target] = max(known_resources.get(bloom_target, 0), 3)

    weather_next = observation.get("weather_next")

    if observation["weather"] == "storm" and not current["shelter"]:
        best_shelter = _best_target(observation, known_shelters, extra_blocked=blocked)
        step = _step_from_observation(observation, best_shelter, extra_blocked=blocked) if allow_offscreen_routing else None
        if not step:
            visible_shelter_moves = [
                action
                for action in legal_actions
                if action.startswith("MOVE:") and visible[action.split(":", 1)[1]]["shelter"]
            ]
            step = sorted(visible_shelter_moves)[0] if visible_shelter_moves else None
        action = step or "REST"
        rationale = "storm cover now" if step else "storm emergency rest"
    elif "GATHER" in legal_actions and current["resource"] > 0 and vitality <= 18:
        action = "GATHER"
        rationale = "bank visible resource"
    elif vitality <= 6:
        if current["shelter"]:
            bloom_is_visible = isinstance(bloom_target, str) and bloom_target in visible
            step = None
            if bloom_is_visible and observation["weather"] in {"clear", "wind"} and vitality >= 7:
                step = _step_from_observation(observation, bloom_target, extra_blocked=blocked)
            elif use_memory and allow_offscreen_routing and observation["weather"] == "clear" and weather_next != "storm" and vitality >= 8:
                step = _step_from_observation(observation, bloom_target, extra_blocked=blocked)
            if step:
                action = step
                rationale = "leave shelter toward remembered bloom"
            else:
                action = "REST"
                rationale = "recover at shelter"
        else:
            best_shelter = _best_target(observation, known_shelters, extra_blocked=blocked)
            step = _step_from_observation(observation, best_shelter, extra_blocked=blocked) if allow_offscreen_routing else None
            if not step:
                visible_shelter_moves = [
                    action
                    for action in legal_actions
                    if action.startswith("MOVE:") and visible[action.split(":", 1)[1]]["shelter"]
                ]
                step = sorted(visible_shelter_moves)[0] if visible_shelter_moves else None
            action = step or "REST"
            rationale = "move toward remembered shelter" if step else "forced rest"
    else:
        visible_resource_moves = [
            act for act in legal_actions if act.startswith("MOVE:") and visible[act.split(":", 1)[1]]["resource"] > 0
        ]
        if visible_resource_moves:
            action = max(visible_resource_moves, key=lambda item: (visible[item.split(":", 1)[1]]["resource"], item))
            rationale = "move toward visible resource"
        else:
            remembered_target = bloom_target if bloom_target in BASE_GRAPH else _best_target(
                observation,
                set(known_resources),
                extra_blocked=blocked,
            )
            step = _step_from_observation(observation, remembered_target, extra_blocked=blocked) if allow_offscreen_routing else None
            if step and remembered_target not in visible:
                action = step
                rationale = "move toward remembered bloom" if remembered_target == bloom_target else "move toward remembered resource"
            else:
                unseen = [node_id for node_id in BASE_GRAPH if node_id not in visited]
                target = unseen[0] if unseen else "watch"
                step = _step_from_observation(observation, target, extra_blocked=blocked) if allow_offscreen_routing else None
                if not step:
                    visible_moves = sorted(action for action in legal_actions if action.startswith("MOVE:"))
                    step = visible_moves[0] if visible_moves else None
                action = step or "REST"
                rationale = "explore unseen node" if step else "no better move"

    next_memory = {
        "known_resources": dict(sorted(known_resources.items())),
        "known_shelters": sorted(known_shelters),
        "visited": sorted(visited),
        "blocked_edges": [list(edge) for edge in sorted(blocked)],
        "last_event": observation["last_event"],
        "last_weather": observation["weather"],
        "bloom_target": bloom_target,
        "last_action_intent": rationale,
    }
    carry_forward = json.dumps(next_memory, sort_keys=True) if use_memory else ""
    return AgentDecision(action=action, carry_forward=carry_forward, rationale=rationale)


class FreshScoutControlAgent:
    name = "fresh-scout-control"

    def decide(self, observation: dict, runtime: AgentRuntimeState) -> AgentDecision:
        fresh_runtime = AgentRuntimeState(location=runtime.location, vitality=runtime.vitality, carry_forward="")
        return _scout_decision(observation, fresh_runtime, use_memory=False, allow_offscreen_routing=False)


class PersistentScoutAgent:
    name = "persistent-scout"

    def decide(self, observation: dict, runtime: AgentRuntimeState) -> AgentDecision:
        return _scout_decision(observation, runtime, use_memory=True, allow_offscreen_routing=True)


def build_llm_observation_prompt(observation: dict, carry_limit: int = DEFAULT_CARRY_LIMIT) -> str:
    return (
        "You are an Island Habitat agent.\n"
        "Your job is to survive, adapt, and maintain useful carry-forward state across cycles.\n"
        "Return strict JSON with keys: action, carry_forward, rationale.\n"
        f"carry_forward must fit within {carry_limit} bytes when UTF-8 encoded.\n"
        "Use only legal actions.\n\n"
        f"OBSERVATION:\n{json.dumps(observation, ensure_ascii=True, indent=2)}\n"
    )


def parse_llm_decision(raw_text: str) -> AgentDecision:
    data = _json_loads_safely(raw_text)
    action = str(data.get("action", "REST")).strip().upper() or "REST"
    carry_forward = str(data.get("carry_forward", "")).strip()
    rationale = str(data.get("rationale", "llm fallback")).strip()
    return AgentDecision(action=action, carry_forward=carry_forward, rationale=rationale)


class LLMAdapterAgent:
    name = "llm-adapter"

    def __init__(self, completion_fn: Callable[[str, dict, AgentRuntimeState], str], *, carry_limit: int = DEFAULT_CARRY_LIMIT, name: str = "llm-adapter") -> None:
        self._completion_fn = completion_fn
        self._carry_limit = carry_limit
        self.name = name

    def decide(self, observation: dict, runtime: AgentRuntimeState) -> AgentDecision:
        prompt = build_llm_observation_prompt(observation, carry_limit=self._carry_limit)
        raw = self._completion_fn(prompt, observation, runtime)
        decision = parse_llm_decision(raw)
        if decision.action not in observation["legal_actions"]:
            decision = AgentDecision(action="REST", carry_forward=decision.carry_forward, rationale="invalid llm action fallback")
        decision.carry_forward = _clip_carry_forward(decision.carry_forward, self._carry_limit)
        return decision


def _best_target(
    observation: dict,
    candidates: set[str],
    *,
    extra_blocked: set[tuple[str, str]] | None = None,
) -> str | None:
    if not candidates:
        return None
    current_location = observation["location"]
    best_target: str | None = None
    best_distance: int | None = None
    world = _world_from_observation(observation, extra_blocked=extra_blocked)
    for target in sorted(candidates):
        distance = _distance(world, current_location, target)
        if distance is None:
            continue
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_target = target
    return best_target


def _world_from_observation(
    observation: dict,
    *,
    extra_blocked: set[tuple[str, str]] | None = None,
) -> WorldState:
    # Build a lightweight world shell from static graph and visible hints so pathfinding works.
    nodes = {
        node_id: NodeState(node_id=node_id, kind="unknown")
        for node_id in BASE_GRAPH
    }
    for node_id, details in observation["visible"].items():
        nodes[node_id] = NodeState(
            node_id=node_id,
            kind=details["kind"],
            resource=details["resource"],
            hazard=details["hazard"],
            shelter=details["shelter"],
        )
    world = WorldState(cycle=observation["cycle"], weather=observation["weather"], nodes=nodes)
    if extra_blocked:
        world.blocked_edges = set(extra_blocked)
    return world


def _step_from_observation(
    observation: dict,
    target: str | None,
    *,
    extra_blocked: set[tuple[str, str]] | None = None,
) -> str | None:
    if not target:
        return None
    world = _world_from_observation(observation, extra_blocked=extra_blocked)
    next_step = _next_step_toward(world, observation["location"], target)
    if not next_step:
        return None
    candidate_lower = f"move:{next_step}".lower()
    for action in observation["legal_actions"]:
        if action.lower() == candidate_lower:
            return action
    return None


def run_episode(
    agent: HabitatAgent,
    *,
    seed: int,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    carry_limit: int = DEFAULT_CARRY_LIMIT,
    output_path: Path | None = None,
) -> tuple[EpisodeSummary, list[dict]]:
    rng = random.Random(seed)
    world = initial_world()
    runtime = AgentRuntimeState()
    records: list[dict] = []
    action_counter: Counter[str] = Counter()
    carry_sizes: list[int] = []
    resources_gathered = 0
    world_events_seen: list[str] = [world.last_event]

    for _ in range(max_cycles):
        observation = observe(world, runtime)
        decision = agent.decide(observation, runtime)
        resolved, runtime = resolve_decision(world, runtime, decision, carry_limit=carry_limit)
        action_counter[resolved["action"]] += 1
        carry_sizes.append(len(runtime.carry_forward.encode("utf-8")))
        resources_gathered += resolved["gathered"]
        pre_tick_event = world_tick(world, rng)
        world_events_seen.append(pre_tick_event)
        record = {
            "cycle": resolved["cycle"],
            "agent": agent.name,
            "seed": seed,
            "observation": observation,
            "decision": asdict(decision),
            "resolved": resolved,
            "world_after_tick": serialize_world(world),
        }
        records.append(record)
        if runtime.death_reason:
            break

    summary = EpisodeSummary(
        agent_name=agent.name,
        seed=seed,
        cycles_completed=len(records),
        died=runtime.death_reason is not None,
        death_reason=runtime.death_reason,
        ending_location=runtime.location,
        ending_vitality=runtime.vitality,
        action_counts=dict(action_counter),
        action_diversity=_entropy(action_counter),
        carry_forward_bytes_last=carry_sizes[-1] if carry_sizes else 0,
        carry_forward_bytes_mean=round(sum(carry_sizes) / len(carry_sizes), 2) if carry_sizes else 0.0,
        resources_gathered=resources_gathered,
        world_events_seen=world_events_seen[-5:],
    )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    return summary, records


def serialize_world(world: WorldState) -> dict:
    return {
        "cycle": world.cycle,
        "weather": world.weather,
        "blocked_edges": [list(edge) for edge in sorted(world.blocked_edges)],
        "last_event": world.last_event,
        "nodes": {
            node_id: {
                "kind": node.kind,
                "resource": node.resource,
                "hazard": node.hazard,
                "shelter": node.shelter,
            }
            for node_id, node in sorted(world.nodes.items())
        },
    }


def evaluate_agents(
    agents: list[HabitatAgent],
    *,
    seeds: list[int],
    max_cycles: int = DEFAULT_MAX_CYCLES,
    carry_limit: int = DEFAULT_CARRY_LIMIT,
    output_dir: Path | None = None,
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for agent in agents:
        summaries: list[EpisodeSummary] = []
        for seed in seeds:
            output_path = None
            if output_dir is not None:
                output_path = output_dir / f"{agent.name}_seed{seed}.jsonl"
            summary, _ = run_episode(
                agent,
                seed=seed,
                max_cycles=max_cycles,
                carry_limit=carry_limit,
                output_path=output_path,
            )
            summaries.append(summary)
        results[agent.name] = aggregate_summaries(summaries)
    return results


def aggregate_summaries(summaries: list[EpisodeSummary]) -> dict:
    return {
        "runs": len(summaries),
        "mean_cycles": round(sum(item.cycles_completed for item in summaries) / len(summaries), 2),
        "mean_vitality_end": round(sum(item.ending_vitality for item in summaries) / len(summaries), 2),
        "death_rate": round(sum(1 for item in summaries if item.died) / len(summaries), 2),
        "mean_action_diversity": round(sum(item.action_diversity for item in summaries) / len(summaries), 4),
        "mean_resources_gathered": round(sum(item.resources_gathered for item in summaries) / len(summaries), 2),
        "mean_carry_bytes": round(sum(item.carry_forward_bytes_mean for item in summaries) / len(summaries), 2),
    }
