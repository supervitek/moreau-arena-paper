from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import parse, request

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_STATE_DIR = PROJECT_ROOT / "results" / "part_b_state_runtime"

RUN_CLASSES = {"manual", "operator-assisted", "agent-only"}
ACTOR_TYPES = {"manual", "operator", "agent", "system"}
ACTION_VERBS = {"HOLD", "CARE", "REST", "TRAIN", "ENTER_ARENA", "ENTER_CAVE", "EXTRACT", "MUTATE"}
CONFLICT_STATUSES = {"none", "stale_rejected", "operator_preempted", "manual_freeze"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_dir() -> Path:
    override = os.environ.get("MOREAU_PART_B_STATE_DIR", "").strip()
    return Path(override) if override else DEFAULT_STATE_DIR


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value)!r}")


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=_json_default) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                rows.append(data)
    return rows


def _coerce_run_class(value: str) -> str:
    run_class = (value or "").strip().lower()
    if run_class not in RUN_CLASSES:
        raise ValueError(f"Invalid run_class: {value}")
    return run_class


def _coerce_actor_type(value: str) -> str:
    actor_type = (value or "").strip().lower()
    if actor_type not in ACTOR_TYPES:
        raise ValueError(f"Invalid actor_type: {value}")
    return actor_type


def _coerce_action(action: str | None) -> str | None:
    if action is None:
        return None
    normalized = action.strip().upper()
    if normalized not in ACTION_VERBS:
        raise ValueError(f"Invalid action_verb: {action}")
    return normalized


def _sanitize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sanitize_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _base_run(payload: dict[str, Any], backend: str) -> dict[str, Any]:
    now = _utcnow()
    queue_state = _sanitize_list(payload.get("queue_state"))
    state_projection = _sanitize_dict(payload.get("state_projection"))
    return {
        "id": payload.get("id") or str(uuid.uuid4()),
        "season_id": (payload.get("season_id") or "part-b-proto").strip(),
        "run_class": _coerce_run_class(payload.get("run_class", "manual")),
        "status": (payload.get("status") or "active").strip(),
        "operator_id": payload.get("operator_id"),
        "subject_pet_id": payload.get("subject_pet_id"),
        "subject_pet_name": payload.get("subject_pet_name"),
        "subject_pet_animal": payload.get("subject_pet_animal"),
        "active_zone": (payload.get("active_zone") or "arena").strip(),
        "priority_profile": (payload.get("priority_profile") or "balanced").strip(),
        "risk_appetite": (payload.get("risk_appetite") or "measured").strip(),
        "care_threshold": int(payload.get("care_threshold", 60)),
        "combat_bias": int(payload.get("combat_bias", 50)),
        "expedition_bias": int(payload.get("expedition_bias", 50)),
        "world_tick": int(payload.get("world_tick", 0)),
        "state_revision": int(payload.get("state_revision", 0)),
        "inference_budget_remaining": int(payload.get("inference_budget_remaining", 4)),
        "observation_version": (payload.get("observation_version") or "B1").strip(),
        "action_version": (payload.get("action_version") or "B1").strip(),
        "scoring_version": (payload.get("scoring_version") or "B1").strip(),
        "conflict_policy": (payload.get("conflict_policy") or "operator_wins_before_execution").strip(),
        "queue_state": queue_state,
        "state_projection": state_projection,
        "metadata": _sanitize_dict(payload.get("metadata")),
        "last_event_at": None,
        "last_actor_type": None,
        "last_action_verb": None,
        "created_at": now,
        "updated_at": now,
        "backend": backend,
    }


def _report_from(run_record: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    by_actor: dict[str, int] = {}
    by_action: dict[str, int] = {}
    conflicts = 0
    accepted = 0
    for event in events:
        actor = event.get("actor_type", "unknown")
        by_actor[actor] = by_actor.get(actor, 0) + 1
        action = event.get("action_verb")
        if action:
            by_action[action] = by_action.get(action, 0) + 1
        if event.get("conflict_status") and event.get("conflict_status") != "none":
            conflicts += 1
        if event.get("accepted", False):
            accepted += 1
    return {
        "run_id": run_record["id"],
        "season_id": run_record["season_id"],
        "run_class": run_record["run_class"],
        "status": run_record["status"],
        "world_tick": run_record["world_tick"],
        "state_revision": run_record["state_revision"],
        "event_count": len(events),
        "accepted_event_count": accepted,
        "conflict_count": conflicts,
        "events_by_actor": by_actor,
        "actions_by_verb": by_action,
        "last_event_at": run_record.get("last_event_at"),
        "last_actor_type": run_record.get("last_actor_type"),
        "last_action_verb": run_record.get("last_action_verb"),
    }


class FilePartBStateStore:
    backend_name = "file"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or _state_dir()
        self.runs_dir = self.base_dir / "runs"
        self.events_dir = self.base_dir / "events"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)

    def storage_status(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "configured": True,
            "dev_fallback": True,
            "base_dir": str(self.base_dir),
        }

    def _run_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.json"

    def _events_path(self, run_id: str) -> Path:
        return self.events_dir / f"{run_id}.jsonl"

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_record = _base_run(payload, backend=self.backend_name)
        _write_json(self._run_path(run_record["id"]), run_record)
        return run_record

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        runs = []
        for path in sorted(self.runs_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            record = _read_json(path, None)
            if isinstance(record, dict):
                runs.append(record)
            if len(runs) >= limit:
                break
        return runs

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        path = self._run_path(run_id)
        if not path.exists():
            return None
        record = _read_json(path, None)
        return record if isinstance(record, dict) else None

    def update_run(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        for key in (
            "status",
            "active_zone",
            "priority_profile",
            "risk_appetite",
            "care_threshold",
            "combat_bias",
            "expedition_bias",
            "world_tick",
            "inference_budget_remaining",
            "conflict_policy",
            "subject_pet_id",
            "subject_pet_name",
            "subject_pet_animal",
        ):
            if key in payload and payload[key] is not None:
                run_record[key] = payload[key]
        if "queue_state" in payload and payload["queue_state"] is not None:
            run_record["queue_state"] = _sanitize_list(payload["queue_state"])
        if "state_projection" in payload and payload["state_projection"] is not None:
            run_record["state_projection"] = _sanitize_dict(payload["state_projection"])
        if "metadata" in payload and payload["metadata"] is not None:
            run_record["metadata"] = _sanitize_dict(payload["metadata"])
        run_record["state_revision"] = int(run_record.get("state_revision", 0)) + 1
        run_record["updated_at"] = _utcnow()
        _write_json(self._run_path(run_id), run_record)
        return run_record

    def append_event(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        events = _read_jsonl(self._events_path(run_id))
        expected_revision = payload.get("expected_state_revision")
        actor_type = _coerce_actor_type(payload.get("actor_type", "system"))
        action_verb = _coerce_action(payload.get("action_verb"))
        conflict_status = "none"
        accepted = True
        current_revision = int(run_record.get("state_revision", 0))

        if expected_revision is not None and actor_type in {"agent", "system"} and int(expected_revision) != current_revision:
            conflict_status = "stale_rejected"
            accepted = False

        event = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "sequence": len(events) + 1,
            "world_tick": int(payload.get("world_tick", run_record.get("world_tick", 0))),
            "actor_type": actor_type,
            "event_type": (payload.get("event_type") or "note").strip(),
            "action_verb": action_verb,
            "zone": payload.get("zone") or run_record.get("active_zone"),
            "expected_state_revision": expected_revision,
            "applied_state_revision": current_revision,
            "conflict_status": conflict_status,
            "accepted": accepted,
            "observation": _sanitize_dict(payload.get("observation")),
            "outcome": _sanitize_dict(payload.get("outcome")),
            "details": _sanitize_dict(payload.get("details")),
            "state_after": _sanitize_dict(payload.get("state_after")),
            "created_at": _utcnow(),
        }
        _append_jsonl(self._events_path(run_id), event)

        if accepted:
            run_record["world_tick"] = max(int(run_record.get("world_tick", 0)), int(event["world_tick"]))
            run_record["last_event_at"] = event["created_at"]
            run_record["last_actor_type"] = actor_type
            run_record["last_action_verb"] = action_verb
            if event["state_after"]:
                run_record["state_projection"] = event["state_after"]
                run_record["state_revision"] = current_revision + 1
            run_record["updated_at"] = _utcnow()
            _write_json(self._run_path(run_id), run_record)

        return event

    def replay(self, run_id: str, limit: int | None = None) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        events = _read_jsonl(self._events_path(run_id))
        if limit is not None:
            events = events[:limit]
        return {
            "run": run_record,
            "events": events,
            "report": _report_from(run_record, events),
        }


class SupabasePartBStateStore:
    backend_name = "supabase"

    def __init__(self, url: str, service_key: str, timeout: float = 10.0) -> None:
        self.url = url.rstrip("/")
        self.service_key = service_key
        self.timeout = timeout
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def storage_status(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "configured": True,
            "dev_fallback": False,
            "base_url": self.url,
        }

    def _request(self, method: str, table: str, *, params: dict[str, Any] | None = None, json_body: Any = None) -> list[dict[str, Any]]:
        endpoint = f"{self.url}/rest/v1/{table}"
        if params:
            endpoint = f"{endpoint}?{parse.urlencode(params)}"
        body = None
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
        req = request.Request(endpoint, data=body, headers=self.headers, method=method.upper())
        with request.urlopen(req, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        if not raw.strip():
            return []
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_record = _base_run(payload, backend=self.backend_name)
        row = {
            "id": run_record["id"],
            "season_id": run_record["season_id"],
            "run_class": run_record["run_class"],
            "status": run_record["status"],
            "operator_id": run_record["operator_id"],
            "subject_pet_id": run_record["subject_pet_id"],
            "subject_pet_name": run_record["subject_pet_name"],
            "subject_pet_animal": run_record["subject_pet_animal"],
            "active_zone": run_record["active_zone"],
            "priority_profile": run_record["priority_profile"],
            "risk_appetite": run_record["risk_appetite"],
            "care_threshold": run_record["care_threshold"],
            "combat_bias": run_record["combat_bias"],
            "expedition_bias": run_record["expedition_bias"],
            "world_tick": run_record["world_tick"],
            "state_revision": run_record["state_revision"],
            "inference_budget_remaining": run_record["inference_budget_remaining"],
            "observation_version": run_record["observation_version"],
            "action_version": run_record["action_version"],
            "scoring_version": run_record["scoring_version"],
            "conflict_policy": run_record["conflict_policy"],
            "queue_state": run_record["queue_state"],
            "state_projection": run_record["state_projection"],
            "metadata": run_record["metadata"],
            "last_event_at": run_record["last_event_at"],
            "last_actor_type": run_record["last_actor_type"],
            "last_action_verb": run_record["last_action_verb"],
        }
        rows = self._request("POST", "part_b_runs", json_body=row)
        return rows[0] if rows else run_record

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        params = {"select": "*", "order": "updated_at.desc", "limit": str(limit)}
        return self._request("GET", "part_b_runs", params=params)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        params = {"select": "*", "id": f"eq.{run_id}", "limit": "1"}
        rows = self._request("GET", "part_b_runs", params=params)
        return rows[0] if rows else None

    def update_run(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        row = dict(run_record)
        for key in (
            "status",
            "active_zone",
            "priority_profile",
            "risk_appetite",
            "care_threshold",
            "combat_bias",
            "expedition_bias",
            "world_tick",
            "inference_budget_remaining",
            "conflict_policy",
            "subject_pet_id",
            "subject_pet_name",
            "subject_pet_animal",
        ):
            if key in payload and payload[key] is not None:
                row[key] = payload[key]
        if "queue_state" in payload and payload["queue_state"] is not None:
            row["queue_state"] = _sanitize_list(payload["queue_state"])
        if "state_projection" in payload and payload["state_projection"] is not None:
            row["state_projection"] = _sanitize_dict(payload["state_projection"])
        if "metadata" in payload and payload["metadata"] is not None:
            row["metadata"] = _sanitize_dict(payload["metadata"])
        row["state_revision"] = int(row.get("state_revision", 0)) + 1
        row["updated_at"] = _utcnow()
        rows = self._request("PATCH", "part_b_runs", params={"id": f"eq.{run_id}", "select": "*"}, json_body=row)
        return rows[0] if rows else row

    def append_event(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        existing_events = self._request("GET", "part_b_events", params={"select": "id", "run_id": f"eq.{run_id}"})
        expected_revision = payload.get("expected_state_revision")
        actor_type = _coerce_actor_type(payload.get("actor_type", "system"))
        action_verb = _coerce_action(payload.get("action_verb"))
        conflict_status = "none"
        accepted = True
        current_revision = int(run_record.get("state_revision", 0))

        if expected_revision is not None and actor_type in {"agent", "system"} and int(expected_revision) != current_revision:
            conflict_status = "stale_rejected"
            accepted = False

        event = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "sequence": len(existing_events) + 1,
            "world_tick": int(payload.get("world_tick", run_record.get("world_tick", 0))),
            "actor_type": actor_type,
            "event_type": (payload.get("event_type") or "note").strip(),
            "action_verb": action_verb,
            "zone": payload.get("zone") or run_record.get("active_zone"),
            "expected_state_revision": expected_revision,
            "applied_state_revision": current_revision,
            "conflict_status": conflict_status,
            "accepted": accepted,
            "observation": _sanitize_dict(payload.get("observation")),
            "outcome": _sanitize_dict(payload.get("outcome")),
            "details": _sanitize_dict(payload.get("details")),
            "state_after": _sanitize_dict(payload.get("state_after")),
        }
        rows = self._request("POST", "part_b_events", json_body=event)
        event = rows[0] if rows else event

        if accepted:
            update_payload: dict[str, Any] = {
                "world_tick": max(int(run_record.get("world_tick", 0)), int(event["world_tick"])),
                "metadata": run_record.get("metadata") or {},
            }
            run_record["last_event_at"] = _utcnow()
            run_record["last_actor_type"] = actor_type
            run_record["last_action_verb"] = action_verb
            if event.get("state_after"):
                update_payload["state_projection"] = event["state_after"]
            self.update_run(run_id, update_payload)
        return event

    def replay(self, run_id: str, limit: int | None = None) -> dict[str, Any] | None:
        run_record = self.get_run(run_id)
        if not run_record:
            return None
        params = {"select": "*", "run_id": f"eq.{run_id}", "order": "sequence.asc"}
        if limit is not None:
            params["limit"] = str(limit)
        events = self._request("GET", "part_b_events", params=params)
        return {
            "run": run_record,
            "events": events,
            "report": _report_from(run_record, events),
        }


def get_part_b_store() -> FilePartBStateStore | SupabasePartBStateStore:
    if os.environ.get("MOREAU_PART_B_FORCE_FILE", "").strip() == "1":
        return FilePartBStateStore()
    url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if url and service_key:
        return SupabasePartBStateStore(url, service_key)
    return FilePartBStateStore()


def part_b_storage_status() -> dict[str, Any]:
    store = get_part_b_store()
    status = store.storage_status()
    status["public_contract_ready"] = True
    status["replay_supported"] = True
    return status


def create_part_b_run(payload: dict[str, Any]) -> dict[str, Any]:
    return get_part_b_store().create_run(payload)


def list_part_b_runs(limit: int = 50) -> list[dict[str, Any]]:
    return get_part_b_store().list_runs(limit)


def get_part_b_run(run_id: str) -> dict[str, Any] | None:
    return get_part_b_store().get_run(run_id)


def update_part_b_run(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return get_part_b_store().update_run(run_id, payload)


def append_part_b_event(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    return get_part_b_store().append_event(run_id, payload)


def replay_part_b_run(run_id: str, limit: int | None = None) -> dict[str, Any] | None:
    return get_part_b_store().replay(run_id, limit)


def part_b_run_report(run_id: str) -> dict[str, Any] | None:
    replay = replay_part_b_run(run_id)
    if not replay:
        return None
    return replay["report"]
