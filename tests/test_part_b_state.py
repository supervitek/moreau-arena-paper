from __future__ import annotations

import pytest

from part_b_state import (
    append_part_b_event,
    clear_part_b_queue,
    create_part_b_run,
    enqueue_part_b_action,
    export_part_b_season_archive,
    get_part_b_run,
    list_part_b_runs,
    part_b_calibration_report,
    part_b_leaderboards,
    part_b_run_report,
    part_b_season_status,
    part_b_storage_status,
    preview_part_b_baseline,
    preview_part_b_house_agent,
    process_part_b_ticks,
    remove_part_b_queued_action,
    replay_part_b_run,
    run_part_b_baseline,
    update_part_b_run,
    update_part_b_house_agent,
)


def test_part_b_run_roundtrip_with_file_store(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "season_id": "b5-proto",
            "run_class": "agent-only",
            "subject_pet_name": "Shkodik",
            "subject_pet_animal": "fox",
            "state_projection": {"health_pct": 92, "queue": []},
        }
    )
    assert run_record["state_revision"] == 0

    updated = update_part_b_run(
        run_record["id"],
        {
            "priority_profile": "welfare-first",
            "queue_state": [{"verb": "CARE"}],
            "state_projection": {"health_pct": 92, "queue": [{"verb": "CARE"}]},
        },
    )
    assert updated is not None
    assert updated["state_revision"] == 1
    assert updated["priority_profile"] == "welfare-first"

    event = append_part_b_event(
        run_record["id"],
        {
            "actor_type": "agent",
            "event_type": "action_applied",
            "action_verb": "CARE",
            "world_tick": 1,
            "expected_state_revision": 1,
            "state_after": {"health_pct": 97, "queue": []},
            "outcome": {"welfare_delta": 5},
        },
    )
    assert event is not None
    assert event["accepted"] is True

    stored = get_part_b_run(run_record["id"])
    assert stored is not None
    assert stored["world_tick"] == 1
    assert stored["state_revision"] == 2
    assert stored["state_projection"]["health_pct"] == 97


def test_part_b_stale_agent_event_is_logged_but_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run({"run_class": "agent-only"})
    update_part_b_run(run_record["id"], {"queue_state": [{"verb": "ENTER_CAVE"}]})

    event = append_part_b_event(
        run_record["id"],
        {
            "actor_type": "agent",
            "event_type": "action_applied",
            "action_verb": "ENTER_CAVE",
            "world_tick": 1,
            "expected_state_revision": 0,
            "state_after": {"depth": 1},
        },
    )
    assert event is not None
    assert event["accepted"] is False
    assert event["conflict_status"] == "stale_rejected"

    report = part_b_run_report(run_record["id"])
    assert report is not None
    assert report["conflict_count"] == 1
    replay = replay_part_b_run(run_record["id"])
    assert replay is not None
    assert replay["events"][0]["conflict_status"] == "stale_rejected"


def test_part_b_report_includes_family_scores(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "manual",
            "state_projection": {
                "health_pct": 88,
                "morale_pct": 76,
                "happiness_pct": 82,
                "neglect_ticks": 1,
                "cave_depth_last_run": 0,
                "cave_extract_value_last_run": 0,
                "cave_injury_last_run": 0,
            },
        }
    )
    append_part_b_event(
        run_record["id"],
        {
            "actor_type": "manual",
            "event_type": "action_applied",
            "action_verb": "ENTER_ARENA",
            "world_tick": 1,
            "expected_state_revision": 0,
            "outcome": {"result": "win", "reward": 12, "xp_gain": 20},
        },
    )
    append_part_b_event(
        run_record["id"],
        {
            "actor_type": "manual",
            "event_type": "action_applied",
            "action_verb": "ENTER_CAVE",
            "world_tick": 2,
            "expected_state_revision": 0,
            "outcome": {"depth": 2, "extract_value": 18, "injury": 4},
        },
    )

    report = part_b_run_report(run_record["id"])
    assert report is not None
    assert set(report["scores"]) == {"welfare", "combat", "expedition"}
    assert report["scores"]["welfare"] > 0
    assert report["scores"]["combat"] > 0
    assert report["scores"]["expedition"] > 0


def test_part_b_storage_status_and_listing(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    status = part_b_storage_status()
    assert status["backend"] == "file"
    assert status["replay_supported"] is True

    first = create_part_b_run(
        {
            "run_class": "operator-assisted",
            "subject_pet_name": "Echo",
            "subject_pet_animal": "monkey",
        }
    )
    second = create_part_b_run(
        {
            "run_class": "manual",
            "subject_pet_name": "Ash",
            "subject_pet_animal": "wolf",
        }
    )

    runs = list_part_b_runs(limit=10)
    assert len(runs) == 2
    assert {run["id"] for run in runs} == {first["id"], second["id"]}


def test_part_b_queue_fifo_and_tick_processing(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "operator-assisted",
            "state_projection": {"health_pct": 80, "morale_pct": 72, "happiness_pct": 70, "energy_pct": 76},
        }
    )
    enqueue_part_b_action(run_record["id"], {"action_verb": "CARE", "actor_type": "operator"})
    enqueue_part_b_action(run_record["id"], {"action_verb": "REST", "actor_type": "operator"})

    result = process_part_b_ticks(run_record["id"], count=2)
    assert result is not None
    assert len(result["processed"]) == 2
    assert [item["action_verb"] for item in result["processed"]] == ["CARE", "REST"]

    stored = get_part_b_run(run_record["id"])
    assert stored is not None
    assert stored["world_tick"] == 2
    assert stored["queue_state"] == []
    assert stored["state_projection"]["care_like_ticks"] >= 2


def test_part_b_queue_capacity_remove_and_clear(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run({"run_class": "manual", "queue_capacity": 2})
    first = enqueue_part_b_action(run_record["id"], {"action_verb": "CARE", "actor_type": "manual"})
    second = enqueue_part_b_action(run_record["id"], {"action_verb": "REST", "actor_type": "manual"})
    assert first is not None
    assert second is not None

    with pytest.raises(ValueError):
        enqueue_part_b_action(run_record["id"], {"action_verb": "HOLD", "actor_type": "manual"})

    removed = remove_part_b_queued_action(run_record["id"], first["queued_item"]["id"])
    assert removed is not None
    assert removed["removed"] is True
    assert len(removed["queue_state"]) == 1

    cleared = clear_part_b_queue(run_record["id"])
    assert cleared is not None
    assert cleared["queue_state"] == []


def test_part_b_house_agent_preview_and_autopause(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "inference_budget_remaining": 1,
            "inference_budget_daily": 1,
            "state_projection": {"health_pct": 41, "happiness_pct": 40, "morale_pct": 58, "energy_pct": 30},
        }
    )
    preview = preview_part_b_house_agent(run_record["id"])
    assert preview is not None
    assert preview["action_verb"] in {"CARE", "REST", "HOLD", "ENTER_ARENA", "ENTER_CAVE", "EXTRACT"}

    tick_one = process_part_b_ticks(run_record["id"], count=1)
    assert tick_one is not None
    assert tick_one["processed"][0]["source"] == "house-agent"

    stored = get_part_b_run(run_record["id"])
    assert stored is not None
    assert stored["inference_budget_remaining"] == 0
    assert stored["house_agent_last_plan"]["action_verb"]

    tick_two = process_part_b_ticks(run_record["id"], count=1)
    assert tick_two is not None
    assert tick_two["processed"][0]["source"] == "house-agent-autopause"

    paused = get_part_b_run(run_record["id"])
    assert paused is not None
    assert paused["status"] == "paused"
    assert paused["autopause_reason"] == "inference_budget_exhausted"


def test_part_b_house_agent_requires_agent_only(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run({"run_class": "manual"})
    with pytest.raises(ValueError):
        update_part_b_house_agent(run_record["id"], {"house_agent_enabled": True})


def test_part_b_season_status_and_leaderboards(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    season = part_b_season_status()
    assert season["season_id"].startswith("part-b-s1")
    assert season["composite_headline_enabled"] is False

    manual = create_part_b_run(
        {
            "run_class": "manual",
            "subject_pet_name": "Iris",
            "subject_pet_animal": "fox",
            "world_tick": 4,
            "state_projection": {
                "health_pct": 92,
                "morale_pct": 88,
                "happiness_pct": 90,
                "energy_pct": 74,
                "care_like_ticks": 3,
                "total_ticks": 4,
            },
        }
    )
    append_part_b_event(
        manual["id"],
        {
            "actor_type": "manual",
            "event_type": "action_applied",
            "action_verb": "ENTER_ARENA",
            "world_tick": 1,
            "expected_state_revision": 0,
            "outcome": {"result": "win", "reward": 12, "xp_gain": 20},
        },
    )

    boards = part_b_leaderboards(run_class="manual", limit=5)
    assert boards["selected_run_class"] == "manual"
    assert boards["counts"]["eligible_runs"] >= 1
    assert boards["families"]["welfare"][0]["run_id"] == manual["id"]


def test_part_b_baseline_preview_and_run(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "state_projection": {"health_pct": 38, "happiness_pct": 42, "morale_pct": 51, "energy_pct": 28},
        }
    )
    preview = preview_part_b_baseline(run_record["id"], "conservative")
    assert preview is not None
    assert preview["action_verb"] in {"CARE", "REST", "HOLD", "EXTRACT"}

    result = run_part_b_baseline(run_record["id"], "conservative", ticks=2)
    assert result is not None
    assert result["processed"]
    stored = get_part_b_run(run_record["id"])
    assert stored is not None
    assert stored["metadata"]["baseline_policy"] == "conservative"

    for policy in ("caremax", "arena-spam", "expedition-max"):
        preview = preview_part_b_baseline(run_record["id"], policy)
        assert preview is not None
        assert preview["action_verb"] in {"CARE", "REST", "HOLD", "ENTER_ARENA", "ENTER_CAVE", "EXTRACT"}


def test_part_b_fatal_run_is_completed(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "operator-assisted",
            "state_projection": {
                "health_pct": 2,
                "morale_pct": 20,
                "happiness_pct": 20,
                "energy_pct": 60,
            },
        }
    )
    enqueue_part_b_action(run_record["id"], {"action_verb": "ENTER_ARENA", "actor_type": "operator"})
    enqueue_part_b_action(run_record["id"], {"action_verb": "CARE", "actor_type": "operator"})
    result = process_part_b_ticks(run_record["id"], count=1)
    assert result is not None
    stored = get_part_b_run(run_record["id"])
    assert stored is not None
    assert stored["status"] == "completed"
    assert stored["autopause_reason"] == "subject_not_alive"
    assert stored["queue_state"] == []
    assert stored["house_agent_enabled"] is False


def test_part_b_season_archive_includes_leaderboards(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run({"run_class": "manual", "subject_pet_name": "Moss"})
    append_part_b_event(
        run_record["id"],
        {
            "actor_type": "manual",
            "event_type": "action_applied",
            "action_verb": "CARE",
            "world_tick": 1,
            "expected_state_revision": 0,
            "outcome": {"welfare_delta": 10},
            "state_after": {"health_pct": 96, "morale_pct": 84, "happiness_pct": 88, "energy_pct": 84},
        },
    )

    archive = export_part_b_season_archive(limit=25)
    assert archive["season"]["season_id"].startswith("part-b-s1")
    assert archive["leaderboards"]["headline_note"]
    assert archive["runs"]


def test_part_b_calibration_report_flags_flatlined_family(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    for policy in ("conservative", "greedy", "random"):
        run_record = create_part_b_run(
            {
                "run_class": "agent-only",
                "metadata": {"baseline_policy": policy},
                "state_projection": {"health_pct": 50, "morale_pct": 50, "happiness_pct": 50, "energy_pct": 50},
            }
        )
        append_part_b_event(
            run_record["id"],
            {
                "actor_type": "agent",
                "event_type": "action_applied",
                "action_verb": "CARE",
                "world_tick": 1,
                "expected_state_revision": 0,
                "outcome": {"welfare_delta": 10},
                "state_after": {"health_pct": 60, "morale_pct": 60, "happiness_pct": 60, "energy_pct": 50},
            },
        )

    calibration = part_b_calibration_report()
    assert calibration["total_runs"] == 3
    assert "combat_flatlined" in calibration["warnings"]
    assert calibration["policy_summary"]["conservative"]["runs"] == 1
