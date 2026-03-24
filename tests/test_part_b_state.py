from __future__ import annotations

import json
import pytest

from part_b_state import (
    ACTION_VERBS,
    PUBLIC_OBSERVATION_KEYS,
    _derive_scores,
    _fallback_house_plan,
    _leaderboard_entry,
    _observation_from,
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
    sync_part_b_run,
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
    assert "return_report" in report
    assert "watch" in report


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
    assert preview["action_verb"] in ACTION_VERBS
    assert set(preview["observation"]) == set(PUBLIC_OBSERVATION_KEYS)
    assert preview["memory_input"]["mode"] == "public_observation_only"
    assert set(preview["memory_input"]["observation"]) == set(PUBLIC_OBSERVATION_KEYS)
    assert preview["memory_input"]["memory_notes"] == []

    tick_one = process_part_b_ticks(run_record["id"], count=1)
    assert tick_one is not None
    assert tick_one["processed"][0]["source"] == "house-agent"

    stored = get_part_b_run(run_record["id"])
    assert stored is not None
    assert stored["inference_budget_remaining"] == 0
    assert stored["house_agent_last_plan"]["action_verb"]
    assert stored["house_agent_last_plan"]["action_verb"] in ACTION_VERBS
    assert set(stored["house_agent_last_plan"]["memory_input"]["observation"]) == set(PUBLIC_OBSERVATION_KEYS)

    tick_two = process_part_b_ticks(run_record["id"], count=1)
    assert tick_two is not None
    assert tick_two["processed"][0]["source"] == "house-agent-autopause"

    paused = get_part_b_run(run_record["id"])
    assert paused is not None
    assert paused["status"] == "paused"
    assert paused["autopause_reason"] == "inference_budget_exhausted"


def test_part_b_watch_sync_catches_up_due_ticks(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    departure = "2026-03-20T00:00:00Z"
    last_sync = "2026-03-20T00:00:00Z"
    expires = "2026-03-21T00:00:00Z"
    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "inference_budget_remaining": 4,
            "inference_budget_daily": 4,
            "state_projection": {"health_pct": 90, "happiness_pct": 78, "morale_pct": 82, "energy_pct": 86},
            "metadata": {
                "watch_mode": True,
                "watch_label": "Watch Over Them",
                "watch_window_hours": 24,
                "watch_started_at": departure,
                "watch_last_sync_at": "2026-03-19T12:00:00Z",
                "watch_expires_at": expires,
                "watch_departure_seen_at": departure,
                "watch_departure_tick": 0,
                "watch_departure_state": {"health_pct": 90, "happiness_pct": 78, "morale_pct": 82, "energy_pct": 86},
            },
        }
    )

    synced = sync_part_b_run(run_record["id"], max_ticks=24)
    assert synced is not None
    assert "synced_ticks" in synced
    assert "watch_status" in synced
    assert synced["report"]["watch"]["enabled"] is True
    assert synced["report"]["watch"]["tick_cadence_hours"] == 6
    assert "next_due_at" in synced["report"]["watch"]
    assert "estimated_ticks_remaining" in synced["report"]["watch"]
    assert "headline" in synced["report"]["return_report"]
    assert "summary" in synced["report"]["return_report"]
    assert "status_line" in synced["report"]["return_report"]
    assert "primary_lane" in synced["report"]["return_report"]
    assert "action_digest" in synced["report"]["return_report"]


def test_part_b_watch_sync_completes_expired_watch(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "metadata": {
                "watch_mode": True,
                "watch_started_at": "2026-03-19T00:00:00Z",
                "watch_last_sync_at": "2026-03-19T18:00:00Z",
                "watch_expires_at": "2026-03-20T00:00:00Z",
                "watch_window_hours": 24,
                "watch_status": "running",
            },
        }
    )
    synced = sync_part_b_run(run_record["id"], max_ticks=2)
    assert synced is not None
    assert synced["run"]["status"] == "completed"
    assert synced["run"]["house_agent_enabled"] is False
    assert synced["run"]["autopause_reason"] == "watch_window_complete"
    assert synced["report"]["watch"]["next_due_at"] is None
    assert synced["report"]["watch"]["estimated_ticks_remaining"] == 0
    assert "finished" in synced["report"]["return_report"]["recommendation"].lower()


def test_part_b_fallback_house_agent_samples_cave_when_expedition_untouched(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "priority_profile": "keep-moving",
            "state_projection": {
                "health_pct": 88,
                "morale_pct": 80,
                "happiness_pct": 81,
                "energy_pct": 84,
                "cave_depth_last_run": 0,
                "current_cave_depth": 0,
                "current_cave_value": 0,
            },
        }
    )
    plan = _fallback_house_plan(run_record)
    assert plan["action_verb"] == "ENTER_CAVE"
    assert plan["zone"] == "cave"


def test_part_b_watch_sync_noop_for_non_watch_run(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run({"run_class": "manual"})
    synced = sync_part_b_run(run_record["id"], max_ticks=24)
    assert synced is not None
    assert synced["synced_ticks"] == 0


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
    assert archive["trace_summary"]["total_runs"] >= 1
    assert "manual" in archive["trace_summary"]["by_run_class"]
    assert archive["review_cadence"]["daily"]


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
    assert "balanced" in calibration["priority_summary"]
    assert "measured" in calibration["risk_summary"]
    assert "house-agent" in calibration["agent_summary"]


def test_part_b_invalid_queue_action_is_dropped(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run({"run_class": "operator-assisted"})
    update_part_b_run(
        run_record["id"],
        {
            "queue_state": [
                {"action_verb": "EXTRACT", "actor_type": "operator", "zone": "cave"},
                {"action_verb": "CARE", "actor_type": "operator", "zone": "arena"},
            ]
        },
    )
    result = process_part_b_ticks(run_record["id"], count=2)
    assert result is not None
    assert result["processed"][0]["event_type"] == "tick_skipped"
    assert result["processed"][1]["action_verb"] == "CARE"


def test_part_b_leaderboards_include_run_class_depth(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    for run_class in ("manual", "operator-assisted", "agent-only"):
        run_record = create_part_b_run({"run_class": run_class, "subject_pet_name": run_class})
        append_part_b_event(
            run_record["id"],
            {
                "actor_type": "manual" if run_class == "manual" else "agent",
                "event_type": "action_applied",
                "action_verb": "CARE",
                "world_tick": 1,
                "expected_state_revision": 0,
                "outcome": {"welfare_delta": 10},
                "state_after": {"health_pct": 95, "morale_pct": 85, "happiness_pct": 88, "energy_pct": 80},
            },
        )

    boards = part_b_leaderboards(limit=5)
    assert set(boards["by_run_class_top"]) == {"manual", "operator-assisted", "agent-only"}


def test_part_b_house_agent_observation_contract_is_public_only(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "state_projection": {"health_pct": 76, "morale_pct": 74, "happiness_pct": 72, "energy_pct": 64},
            "metadata": {"private_debug": "should_not_leak"},
        }
    )

    observation = _observation_from(run_record)
    assert set(observation) == set(PUBLIC_OBSERVATION_KEYS)
    assert "metadata" not in observation
    assert "subject_pet_name" not in observation

    preview = preview_part_b_house_agent(run_record["id"])
    assert preview is not None
    assert set(preview["memory_input"]["observation_keys"]) == set(PUBLIC_OBSERVATION_KEYS)
    assert set(preview["memory_input"]["observation"]) == set(PUBLIC_OBSERVATION_KEYS)


def test_part_b_scoring_independent_of_house_agent_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    base_run = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": False,
            "state_projection": {"health_pct": 91, "morale_pct": 83, "happiness_pct": 86, "energy_pct": 72},
        }
    )
    events = [
        {
            "actor_type": "agent",
            "event_type": "action_applied",
            "action_verb": "ENTER_ARENA",
            "world_tick": 1,
            "expected_state_revision": 0,
            "outcome": {"result": "win", "reward": 12, "xp_gain": 20},
        },
        {
            "actor_type": "agent",
            "event_type": "action_applied",
            "action_verb": "ENTER_CAVE",
            "world_tick": 2,
            "expected_state_revision": 1,
            "outcome": {"depth": 2, "extract_value": 16, "injury": 3},
        },
    ]
    for payload in events:
        append_part_b_event(base_run["id"], payload)

    report = part_b_run_report(base_run["id"])
    assert report is not None
    compare_run = dict(base_run)
    compare_run["house_agent_enabled"] = True
    assert _derive_scores(base_run, replay_part_b_run(base_run["id"])["events"]) == _derive_scores(compare_run, replay_part_b_run(base_run["id"])["events"])


def test_part_b_leaderboard_entries_expose_labels_and_compliance(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "subject_pet_name": "Signal",
            "state_projection": {"health_pct": 92, "morale_pct": 85, "happiness_pct": 84, "energy_pct": 79},
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
            "outcome": {"welfare_delta": 8},
            "state_after": {"health_pct": 96, "morale_pct": 88, "happiness_pct": 89, "energy_pct": 77},
        },
    )
    report = part_b_run_report(run_record["id"])
    assert report is not None
    entry = _leaderboard_entry(get_part_b_run(run_record["id"]), report)
    assert entry["run_class"] == "agent-only"
    assert entry["agent_type"] == "house-agent"
    assert entry["public_contract_compliant"] is True
    assert entry["benchmark_eligible"] is True


def test_part_b_gemini_house_agent_uses_model_path(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    class _FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return json.dumps(self._payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        assert "generativelanguage.googleapis.com" in req.full_url
        body = json.loads(req.data.decode("utf-8"))
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        return _FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {
                                            "action_verb": "ENTER_CAVE",
                                            "zone": "cave",
                                            "rationale": "Cave pressure slightly outweighs arena pull.",
                                        }
                                    )
                                }
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("part_b_state.request.urlopen", fake_urlopen)

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "house_agent_provider": "gemini",
            "house_agent_model": "gemini-2.0-flash-lite",
        }
    )
    preview = preview_part_b_house_agent(run_record["id"])
    assert preview is not None
    assert preview["mode"] == "model"
    assert preview["provider"] == "gemini"
    assert preview["model"] == "gemini-2.5-flash-lite"
    assert preview["action_verb"] == "ENTER_CAVE"


def test_part_b_gemini_house_agent_falls_back_without_key(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "house_agent_provider": "gemini",
            "house_agent_model": "gemini-2.0-flash-lite",
            "state_projection": {"health_pct": 44, "happiness_pct": 39, "morale_pct": 60, "energy_pct": 32},
        }
    )
    preview = preview_part_b_house_agent(run_record["id"])
    assert preview is not None
    assert preview["mode"] == "fallback"
    assert preview["provider"] == "fallback"
    assert preview["action_verb"] in ACTION_VERBS


def test_part_b_gemini_house_agent_malformed_output_falls_back(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    class _BadResponse:
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": '{"action_verb":"FLY"}'}]}}]}).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("part_b_state.request.urlopen", lambda req, timeout=0: _BadResponse())  # noqa: ARG005

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "house_agent_provider": "gemini",
            "house_agent_model": "gemini-2.0-flash-lite",
        }
    )
    preview = preview_part_b_house_agent(run_record["id"])
    assert preview is not None
    assert preview["mode"] == "fallback"
    assert preview["provider"] == "fallback"


def test_part_b_gemini_house_agent_alias_normalized_on_create(monkeypatch, tmp_path):
    monkeypatch.setenv("MOREAU_PART_B_FORCE_FILE", "1")
    monkeypatch.setenv("MOREAU_PART_B_STATE_DIR", str(tmp_path))

    run_record = create_part_b_run(
        {
            "run_class": "agent-only",
            "house_agent_enabled": True,
            "house_agent_provider": "gemini",
            "house_agent_model": "gemini-2.0-flash-lite",
        }
    )
    assert run_record["house_agent_model"] == "gemini-2.5-flash-lite"
