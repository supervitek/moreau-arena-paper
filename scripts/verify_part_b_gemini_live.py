from __future__ import annotations

import argparse
import json
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
        f"- Stored model: `{payload['stored_model']}`",
        f"- Preview mode: `{payload['preview']['mode']}`",
        f"- Preview provider: `{payload['preview']['provider']}`",
        f"- Preview model: `{payload['preview']['model']}`",
        f"- Preview action: `{payload['preview']['action_verb']}`",
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
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    create = request_json(
        args.base_url,
        "POST",
        "/api/v1/island/part-b/runs",
        {
            "run_class": "agent-only",
            "subject_pet_name": "GeminiLive",
            "subject_pet_animal": "fox",
            "house_agent_enabled": True,
            "house_agent_provider": "gemini",
            "house_agent_model": args.model,
            "inference_budget_remaining": max(args.ticks, 1),
            "inference_budget_daily": max(args.ticks, 1),
            "billing_mode": "hybrid",
            "world_access_active": True,
        },
    )
    run_id = create["id"]
    run = request_json(args.base_url, "GET", f"/api/v1/island/part-b/runs/{run_id}")
    preview = request_json(args.base_url, "GET", f"/api/v1/island/part-b/runs/{run_id}/house-agent/preview")
    tick = request_json(args.base_url, "POST", f"/api/v1/island/part-b/runs/{run_id}/tick", {"count": args.ticks})
    report = request_json(args.base_url, "GET", f"/api/v1/island/part-b/runs/{run_id}/report")

    payload = {
        "base_url": args.base_url,
        "run_id": run_id,
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
