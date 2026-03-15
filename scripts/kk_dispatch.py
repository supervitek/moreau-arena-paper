#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COORD = ROOT / "coord"
INBOX = COORD / "inbox"
CLAIMS = COORD / "claims"
OUTBOX = COORD / "outbox"
ARCHIVE = COORD / "archive"
STATUS = COORD / "status"
SESSION_FILE = STATUS / "kk_sessions.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "task"


def ensure_layout() -> None:
    for path in (INBOX, CLAIMS, OUTBOX, ARCHIVE, STATUS):
        path.mkdir(parents=True, exist_ok=True)


def load_sessions() -> dict:
    if not SESSION_FILE.exists():
        return {"workers": {}}
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"workers": {}}


def save_sessions(data: dict) -> None:
    SESSION_FILE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_body(args: argparse.Namespace) -> str:
    if args.body:
        return args.body.strip()
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8").strip()
    raise SystemExit("submit requires --body or --body-file")


def write_task(args: argparse.Namespace) -> Path:
    ensure_layout()
    task_id = f"{now_stamp()}_{slugify(args.title)}"
    task_path = INBOX / f"{task_id}.md"
    content = (
        f"# {args.title}\n\n"
        f"- task_id: {task_id}\n"
        f"- assignee: {args.assignee}\n"
        f"- created_at: {now_iso()}\n"
        f"- cwd: {ROOT}\n\n"
        "## Objective\n\n"
        f"{read_body(args)}\n"
    )
    task_path.write_text(content, encoding="utf-8")
    return task_path


def find_task(task_ref: str | None) -> Path:
    ensure_layout()
    if task_ref:
        task_path = Path(task_ref)
        if task_path.exists():
            return task_path.resolve()
        by_name = INBOX / task_ref
        if by_name.exists():
            return by_name.resolve()
        if not task_ref.endswith(".md"):
            by_id = INBOX / f"{task_ref}.md"
            if by_id.exists():
                return by_id.resolve()
        raise SystemExit(f"task not found: {task_ref}")

    tasks = sorted(p for p in INBOX.glob("*.md") if p.is_file())
    if not tasks:
        raise SystemExit("no queued tasks in coord/inbox")
    return tasks[0].resolve()


def parse_task(task_path: Path) -> dict:
    text = task_path.read_text(encoding="utf-8")
    title = task_path.stem
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match:
        title = match.group(1).strip()

    meta = {}
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        meta[key.strip()] = value.strip()

    return {
        "title": title,
        "task_id": meta.get("task_id", task_path.stem),
        "assignee": meta.get("assignee", "kk"),
        "cwd": meta.get("cwd", str(ROOT)),
        "text": text,
    }


def save_claim(task: dict, worker: str, state: str, extra: dict | None = None) -> Path:
    claim_path = CLAIMS / f"{task['task_id']}.{worker}.json"
    payload = {
        "task_id": task["task_id"],
        "worker": worker,
        "state": state,
        "updated_at": now_iso(),
        "task_file": str(INBOX / f"{task['task_id']}.md"),
    }
    if extra:
        payload.update(extra)
    claim_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return claim_path


def build_prompt(task: dict, worker: str) -> str:
    return (
        f"You are Claude Code running as delegated worker '{worker}' for the repository at {ROOT}.\n"
        "Respect repo-local instructions such as CLAUDE.md and AGENTS.md.\n"
        "Execute the task directly if code changes are requested.\n"
        "At the end, reply concisely with:\n"
        "1. status\n"
        "2. what changed\n"
        "3. blockers or follow-ups\n\n"
        f"Task file: {task['task_id']}\n"
        f"Suggested cwd: {task['cwd']}\n\n"
        "Task contents:\n"
        "-----\n"
        f"{task['text']}\n"
        "-----"
    )


def run_claude(prompt: str, resume_session: str | None) -> dict:
    cmd = [
        "claude",
        "-p",
        "--dangerously-skip-permissions",
        "--permission-mode",
        "bypassPermissions",
        "--output-format",
        "json",
    ]
    if resume_session:
        cmd.extend(["--resume", resume_session])
    cmd.append(prompt)

    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"claude exited with {proc.returncode}")

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"failed to parse claude json output: {exc}") from exc


def archive_task(task_path: Path, suffix: str) -> Path:
    archive_path = ARCHIVE / f"{task_path.stem}.{suffix}.md"
    shutil.move(str(task_path), str(archive_path))
    return archive_path


def write_result_files(task: dict, worker: str, payload: dict) -> tuple[Path, Path]:
    stem = f"{task['task_id']}.{worker}"
    json_path = OUTBOX / f"{stem}.json"
    md_path = OUTBOX / f"{stem}.md"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result_text = payload.get("result", "").strip()
    md = [
        f"# Worker Result: {task['title']}",
        "",
        f"- task_id: {task['task_id']}",
        f"- worker: {worker}",
        f"- session_id: {payload.get('session_id', '')}",
        f"- captured_at: {now_iso()}",
        "",
        "## Response",
        "",
        result_text or "(empty)",
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")
    return json_path, md_path


def cmd_submit(args: argparse.Namespace) -> int:
    task_path = write_task(args)
    print(task_path)
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    ensure_layout()
    sessions = load_sessions().get("workers", {})
    queued = sorted(p.name for p in INBOX.glob("*.md"))

    print("Workers:")
    if not sessions:
        print("  (none)")
    for worker, info in sorted(sessions.items()):
        print(f"  {worker}: session={info.get('session_id', '-')}, updated_at={info.get('updated_at', '-')}")

    print("Queued tasks:")
    if not queued:
        print("  (none)")
    for name in queued:
        print(f"  {name}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    task_path = find_task(args.task)
    task = parse_task(task_path)
    worker = args.worker or task["assignee"] or "kk"
    sessions = load_sessions()
    resume_session = None
    if not args.fresh:
        resume_session = sessions.get("workers", {}).get(worker, {}).get("session_id")

    save_claim(task, worker, "running", {"session_id": resume_session or ""})

    try:
        payload = run_claude(build_prompt(task, worker), resume_session=resume_session)
    except Exception as exc:  # noqa: BLE001
        archive_path = archive_task(task_path, "failed")
        save_claim(task, worker, "failed", {"error": str(exc), "archived_task": str(archive_path)})
        raise

    session_id = payload.get("session_id", "")
    worker_state = {
        "session_id": session_id,
        "updated_at": now_iso(),
        "last_task_id": task["task_id"],
        "last_result_preview": str(payload.get("result", "")).strip()[:200],
    }
    sessions.setdefault("workers", {})[worker] = worker_state
    save_sessions(sessions)

    json_path, md_path = write_result_files(task, worker, payload)
    archive_path = archive_task(task_path, "done")
    save_claim(
        task,
        worker,
        "completed",
        {
            "session_id": session_id,
            "archived_task": str(archive_path),
            "result_json": str(json_path),
            "result_md": str(md_path),
        },
    )

    print(md_path)
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    ensure_layout()
    worker = args.worker
    sessions = load_sessions()
    resume_session = None if args.fresh else sessions.get("workers", {}).get(worker, {}).get("session_id")

    payload = run_claude(args.prompt, resume_session=resume_session)
    session_id = payload.get("session_id", "")
    sessions.setdefault("workers", {})[worker] = {
        "session_id": session_id,
        "updated_at": now_iso(),
        "last_task_id": None,
        "last_result_preview": str(payload.get("result", "")).strip()[:200],
    }
    save_sessions(sessions)

    stem = f"adhoc_{now_stamp()}.{worker}"
    json_path = OUTBOX / f"{stem}.json"
    md_path = OUTBOX / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                f"# Ad Hoc Worker Result ({worker})",
                "",
                f"- session_id: {session_id}",
                f"- captured_at: {now_iso()}",
                "",
                "## Prompt",
                "",
                args.prompt,
                "",
                "## Response",
                "",
                str(payload.get("result", "")).strip() or "(empty)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(md_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dispatch tasks to a local Claude Code worker.")
    sub = parser.add_subparsers(dest="command", required=True)

    submit = sub.add_parser("submit", help="Create a queued task in coord/inbox")
    submit.add_argument("--title", required=True)
    submit.add_argument("--body")
    submit.add_argument("--body-file")
    submit.add_argument("--assignee", default="kk")
    submit.set_defaults(func=cmd_submit)

    run = sub.add_parser("run", help="Run a queued task through the worker")
    run.add_argument("task", nargs="?")
    run.add_argument("--worker", default="kk")
    run.add_argument("--fresh", action="store_true", help="Do not resume the last worker session")
    run.set_defaults(func=cmd_run)

    ask = sub.add_parser("ask", help="Send an ad hoc prompt to the worker")
    ask.add_argument("--prompt", required=True)
    ask.add_argument("--worker", default="kk")
    ask.add_argument("--fresh", action="store_true", help="Do not resume the last worker session")
    ask.set_defaults(func=cmd_ask)

    status = sub.add_parser("status", help="Show worker sessions and queued tasks")
    status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    ensure_layout()
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
