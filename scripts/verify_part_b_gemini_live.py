from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import request


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        base_url.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with request.urlopen(req, timeout=60.0) as response:
        return json.loads(response.read().decode("utf-8"))


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Part B Gemini Live Verification",
        "",
        f"- Base URL: `{payload['base_url']}`",
        f"- Run ID: `{payload['run_id']}`",
        f"- Priority profile: `{payload['priority_profile']}`",
        f"- Risk appetite: `{payload['risk_appetite']}`",
        f"- Combat bias: `{payload['combat_bias']}`",
        f"- Expedition bias: `{payload['expedition_bias']}`",
        f"- Stored model: `{payload['stored_model']}`",
        f"- Preview mode: `{payload['preview']['mode']}`",
        f"- Preview provider: `{payload['preview']['provider']}`",
        f"- Preview model: `{payload['preview']['model']}`",
        f"- Preview action: `{payload['preview']['action_verb']}`",
        f"- Watch mode: `{payload['watch_mode']}`",
        "",
        "## Tick Results",
        "",
    ]
    for index, item in enumerate(payload["processed"], start=1):
        lines.extend(
            [
                f"### Tick {index}",
                "",
                f"- Source: `{item.get('source')}`",
                f"- Action: `{item.get('action_verb')}`",
                f"- Zone: `{item.get('zone')}`",
                f"- Accepted: `{item.get('accepted')}`",
                f"- World tick: `{item.get('world_tick')}`",
                "",
            ]
        )
    report = payload["report"]
    scores = report["scores"]
    lines.extend(
        [
            "## Report",
            "",
            f"- Welfare: `{scores['welfare']}`",
            f"- Combat: `{scores['combat']}`",
            f"- Expedition: `{scores['expedition']}`",
            f"- Queue pending: `{report['queue']['pending_count']}`",
            f"- Event count: `{report['event_count']}`",
            "",
        ]
    )
    if payload["preview"]["provider"] == "gemini" and payload["preview"]["mode"] == "model":
        lines.extend(
            [
                "## Verdict",
                "",
                "- Live Gemini path is active.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Verdict",
                "",
                "- Live Gemini path is not active yet; preview stayed on fallback.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify live Gemini house-agent behavior for Part B.")
    parser.add_argument("--base-url", default="https://moreauarena.com")
    parser.add_argument("--ticks", type=int, default=3)
    parser.add_argument("--model", default="gemini-2.5-flash-lite")
    parser.add_argument("--priority-profile", default="balanced")
    parser.add_argument("--risk-appetite", default="measured")
    parser.add_argument("--combat-bias", type=int, default=50)
    parser.add_argument("--expedition-bias", type=int, default=50)
    parser.add_argument("--pet-name", default="GeminiLive")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--watch-mode", action="store_true")
    parser.add_argument("--backdate-hours", type=int, default=0)
    args = parser.parse_args()

    now = datetime.now(timezone.utc).replace(microsecond=0)
    metadata = {"source": "verify-part-b-gemini-live"}
    if args.watch_mode:
        started_at = now - timedelta(hours=max(0, args.backdate_hours))
        expires_at = started_at + timedelta(hours=24)
        metadata.update(
            {
                "watch_mode": True,
                "watch_label": "Watch Over Them",
                "watch_window_hours": 24,
                "watch_started_at": started_at.isoformat().replace("+00:00", "Z"),
                "watch_last_sync_at": started_at.isoformat().replace("+00:00", "Z"),
                "watch_expires_at": expires_at.isoformat().replace("+00:00", "Z"),
                "watch_departure_seen_at": started_at.isoformat().replace("+00:00", "Z"),
                "watch_departure_tick": 0,
            }
        )

    create = request_json(
        args.base_url,
        "POST",
        "/api/v1/island/part-b/runs",
        {
            "run_class": "agent-only",
            "subject_pet_name": args.pet_name,
            "subject_pet_animal": "fox",
            "priority_profile": args.priority_profile,
            "risk_appetite": args.risk_appetite,
            "combat_bias": args.combat_bias,
            "expedition_bias": args.expedition_bias,
            "house_agent_enabled": True,
            "house_agent_provider": "gemini",
            "house_agent_model": args.model,
            "inference_budget_remaining": max(args.ticks, 1),
            "inference_budget_daily": max(args.ticks, 1),
            "billing_mode": "hybrid",
            "world_access_active": True,
            "metadata": metadata,
        },
    )
    run_id = create["id"]
    run = request_json(args.base_url, "GET", f"/api/v1/island/part-b/runs/{run_id}")
    preview = request_json(args.base_url, "GET", f"/api/v1/island/part-b/runs/{run_id}/house-agent/preview")
    if args.watch_mode:
        tick = request_json(args.base_url, "POST", f"/api/v1/island/part-b/runs/{run_id}/sync", {"max_ticks": args.ticks})
    else:
        tick = request_json(args.base_url, "POST", f"/api/v1/island/part-b/runs/{run_id}/tick", {"count": args.ticks})
    report = request_json(args.base_url, "GET", f"/api/v1/island/part-b/runs/{run_id}/report")

    payload = {
        "base_url": args.base_url,
        "run_id": run_id,
        "watch_mode": args.watch_mode,
        "priority_profile": run.get("priority_profile"),
        "risk_appetite": run.get("risk_appetite"),
        "combat_bias": run.get("combat_bias"),
        "expedition_bias": run.get("expedition_bias"),
        "stored_model": run.get("house_agent_model"),
        "preview": {
            "mode": preview.get("mode"),
            "provider": preview.get("provider"),
            "model": preview.get("model"),
            "action_verb": preview.get("action_verb"),
        },
        "processed": tick.get("processed") or [],
        "report": report,
    }

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    text = build_report(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
