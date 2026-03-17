from __future__ import annotations

from part_b_state import (
    append_part_b_event,
    create_part_b_run,
    get_part_b_run,
    list_part_b_runs,
    part_b_run_report,
    part_b_storage_status,
    replay_part_b_run,
    update_part_b_run,
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
