from island_habitat import (
    FreshHeuristicAgent,
    PersistentScoutAgent,
    RandomAgent,
    evaluate_agents,
    initial_world,
    observe,
    world_tick,
)


def test_world_tick_changes_world_without_agent() -> None:
    world = initial_world()
    before_weather = world.weather
    before_resources = {node_id: node.resource for node_id, node in world.nodes.items()}

    rng = __import__("random").Random(7)
    event = ""
    for _ in range(3):
        event = world_tick(world, rng)

    after_resources = {node_id: node.resource for node_id, node in world.nodes.items()}
    assert world.cycle == 3
    assert world.weather != before_weather
    assert event
    assert after_resources != before_resources


def test_observation_is_partial_not_global() -> None:
    world = initial_world()
    runtime = type("Runtime", (), {"location": "shore", "vitality": 12, "carry_forward": ""})()
    obs = observe(world, runtime)
    assert "shore" in obs["visible"]
    assert "grove" in obs["visible"]
    assert "quarry" not in obs["visible"]


def test_baseline_sweep_shows_memory_signal() -> None:
    results = evaluate_agents(
        [RandomAgent(seed=9), FreshHeuristicAgent(), PersistentScoutAgent()],
        seeds=[0, 1, 2, 3, 4],
        max_cycles=25,
        carry_limit=800,
    )

    assert results["persistent-scout"]["mean_cycles"] >= results["fresh-heuristic"]["mean_cycles"]
    assert results["fresh-heuristic"]["mean_cycles"] >= results["random"]["mean_cycles"]
    assert results["persistent-scout"]["mean_carry_bytes"] > 0
