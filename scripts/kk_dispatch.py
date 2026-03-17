#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


ROOT = Path(__file__).resolve().parent.parent
COORD = ROOT / "coord"
INBOX = COORD / "inbox"
CLAIMS = COORD / "claims"
OUTBOX = COORD / "outbox"
ARCHIVE = COORD / "archive"
STATUS = COORD / "status"
SESSION_FILE = STATUS / "kk_sessions.json"
SESSION_LOCK_FILE = STATUS / "kk_sessions.lock"
SESSION_LOCK = Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "task"


def normalize_worker(worker: str | None) -> str:
    name = (worker or "kk").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise SystemExit(f"invalid worker name: {worker!r}")
    return name


def parse_worker_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    workers: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        worker = normalize_worker(part)
        if worker in seen:
            continue
        seen.add(worker)
        workers.append(worker)
    return workers


def ensure_layout() -> None:
    for path in (INBOX, CLAIMS, OUTBOX, ARCHIVE, STATUS):
        path.mkdir(parents=True, exist_ok=True)


def claude_env() -> dict[str, str]:
    env = os.environ.copy()
    if env.get("MOREAU_KK_USE_API_KEY", "").strip() not in {"1", "true", "TRUE", "yes", "YES"}:
        env.pop("ANTHROPIC_API_KEY", None)
    return env


@contextmanager
def session_guard():
    ensure_layout()
    SESSION_LOCK_FILE.touch(exist_ok=True)
    with SESSION_LOCK:
        with SESSION_LOCK_FILE.open("r+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_sessions() -> dict:
    if not SESSION_FILE.exists():
        return {"workers": {}}
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"workers": {}}


def save_sessions(data: dict) -> None:
    SESSION_FILE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_resume_session(worker: str, fresh: bool) -> str | None:
    if fresh:
        return None
    with session_guard():
        return load_sessions().get("workers", {}).get(worker, {}).get("session_id")


def update_worker_session(worker: str, session_id: str, task_id: str | None, result_text: str) -> None:
    with session_guard():
        sessions = load_sessions()
        sessions.setdefault("workers", {})[worker] = {
            "session_id": session_id,
            "updated_at": now_iso(),
            "last_task_id": task_id,
            "last_result_preview": result_text.strip()[:200],
        }
        save_sessions(sessions)


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
    assignee = normalize_worker(args.assignee)
    content = (
        f"# {args.title}\n\n"
        f"- task_id: {task_id}\n"
        f"- assignee: {assignee}\n"
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


def list_task_paths() -> list[Path]:
    ensure_layout()
    return sorted(p.resolve() for p in INBOX.glob("*.md") if p.is_file())


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
        "assignee": normalize_worker(meta.get("assignee", "kk")),
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
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--disable-slash-commands",
        "--no-chrome",
        "--output-format",
        "json",
    ]
    if resume_session:
        cmd.extend(["--resume", resume_session])
    cmd.append(prompt)

    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=claude_env(),
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


def execute_task(task_path: Path, worker_override: str | None, fresh: bool) -> Path:
    task = parse_task(task_path)
    worker = normalize_worker(worker_override or task["assignee"] or "kk")
    resume_session = read_resume_session(worker, fresh=fresh)

    save_claim(task, worker, "running", {"session_id": resume_session or ""})

    try:
        payload = run_claude(build_prompt(task, worker), resume_session=resume_session)
    except Exception as exc:  # noqa: BLE001
        archive_path = archive_task(task_path, "failed")
        save_claim(task, worker, "failed", {"error": str(exc), "archived_task": str(archive_path)})
        raise

    session_id = payload.get("session_id", "")
    update_worker_session(worker, session_id, task["task_id"], str(payload.get("result", "")))

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
    return md_path


def execute_ask(worker: str, prompt: str, fresh: bool) -> Path:
    ensure_layout()
    worker = normalize_worker(worker)
    resume_session = read_resume_session(worker, fresh=fresh)

    payload = run_claude(prompt, resume_session=resume_session)
    session_id = payload.get("session_id", "")
    update_worker_session(worker, session_id, None, str(payload.get("result", "")))

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
                prompt,
                "",
                "## Response",
                "",
                str(payload.get("result", "")).strip() or "(empty)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return md_path


def cmd_submit(args: argparse.Namespace) -> int:
    task_path = write_task(args)
    print(task_path)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ensure_layout()
    with session_guard():
        sessions = load_sessions().get("workers", {})
    filter_workers = set(parse_worker_list(args.workers))
    queued_tasks = [parse_task(path) for path in list_task_paths()]
    if filter_workers:
        queued_tasks = [task for task in queued_tasks if task["assignee"] in filter_workers]

    if args.json:
        payload = {
            "workers": {k: v for k, v in sorted(sessions.items()) if not filter_workers or k in filter_workers},
            "queued_tasks": queued_tasks,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print("Workers:")
    visible_workers = [(worker, info) for worker, info in sorted(sessions.items()) if not filter_workers or worker in filter_workers]
    if not visible_workers:
        print("  (none)")
    for worker, info in visible_workers:
        print(f"  {worker}: session={info.get('session_id', '-')}, updated_at={info.get('updated_at', '-')}")

    print("Queued tasks:")
    if not queued_tasks:
        print("  (none)")
    for task in queued_tasks:
        print(f"  {task['task_id']}.md [{task['assignee']}]")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    task_path = find_task(args.task)
    md_path = execute_task(task_path, worker_override=args.worker, fresh=args.fresh)
    print(md_path)
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    requested_workers = set(parse_worker_list(args.workers))
    selected: list[tuple[Path, str]] = []
    claimed_workers: set[str] = set()
    for task_path in list_task_paths():
        task = parse_task(task_path)
        worker = task["assignee"]
        if requested_workers and worker not in requested_workers:
            continue
        if worker in claimed_workers:
            continue
        selected.append((task_path, worker))
        claimed_workers.add(worker)
        if args.limit and len(selected) >= args.limit:
            break

    if not selected:
        raise SystemExit("no runnable queued tasks matched the current worker filter")

    max_parallel = max(1, min(args.parallel, len(selected)))
    errors: list[tuple[str, str]] = []
    results: list[Path] = []

    def run_one(item: tuple[Path, str]) -> Path:
        task_path, worker = item
        cmd = [sys.executable, str(Path(__file__).resolve()), "run", str(task_path), "--worker", worker]
        if args.fresh:
            cmd.append("--fresh")
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            message = proc.stderr.strip() or proc.stdout.strip() or f"kk_dispatch run exited with {proc.returncode}"
            raise RuntimeError(message)
        output = proc.stdout.strip().splitlines()
        if not output:
            raise RuntimeError("kk_dispatch run returned no result path")
        return Path(output[-1]).resolve()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as pool:
        future_map = {pool.submit(run_one, item): item for item in selected}
        for future in concurrent.futures.as_completed(future_map):
            task_path, worker = future_map[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                errors.append((f"{task_path.name} [{worker}]", str(exc)))
                if args.stop_on_error:
                    break

    for path in sorted(results):
        print(path)

    if errors:
        for label, error in errors:
            print(f"error: {label}: {error}", file=sys.stderr)
        return 1
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    md_path = execute_ask(args.worker, args.prompt, fresh=args.fresh)
    print(md_path)
    return 0


def cmd_ask_many(args: argparse.Namespace) -> int:
    workers = parse_worker_list(args.workers)
    if not workers:
        raise SystemExit("ask-many requires at least one worker")

    max_parallel = max(1, min(args.parallel, len(workers)))
    errors: list[tuple[str, str]] = []
    results: list[Path] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as pool:
        future_map = {
            pool.submit(execute_ask, worker, args.prompt, args.fresh): worker
            for worker in workers
        }
        for future in concurrent.futures.as_completed(future_map):
            worker = future_map[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                errors.append((worker, str(exc)))

    for path in sorted(results):
        print(path)

    if errors:
        for worker, error in errors:
            print(f"error: {worker}: {error}", file=sys.stderr)
        return 1
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
    run.add_argument("--worker")
    run.add_argument("--fresh", action="store_true", help="Do not resume the last worker session")
    run.set_defaults(func=cmd_run)

    run_all = sub.add_parser("run-all", help="Run one queued task per worker lane")
    run_all.add_argument("--workers", help="Comma-separated worker list filter")
    run_all.add_argument("--parallel", type=int, default=4, help="Maximum concurrent workers")
    run_all.add_argument("--limit", type=int, help="Maximum tasks to dispatch")
    run_all.add_argument("--fresh", action="store_true", help="Do not resume the last worker session")
    run_all.add_argument("--stop-on-error", action="store_true", help="Return early after the first worker failure")
    run_all.set_defaults(func=cmd_run_all)

    ask = sub.add_parser("ask", help="Send an ad hoc prompt to the worker")
    ask.add_argument("--prompt", required=True)
    ask.add_argument("--worker", default="kk")
    ask.add_argument("--fresh", action="store_true", help="Do not resume the last worker session")
    ask.set_defaults(func=cmd_ask)

    ask_many = sub.add_parser("ask-many", help="Send the same ad hoc prompt to multiple workers")
    ask_many.add_argument("--prompt", required=True)
    ask_many.add_argument("--workers", required=True, help="Comma-separated worker list")
    ask_many.add_argument("--parallel", type=int, default=4, help="Maximum concurrent workers")
    ask_many.add_argument("--fresh", action="store_true", help="Do not resume the last worker session")
    ask_many.set_defaults(func=cmd_ask_many)

    status = sub.add_parser("status", help="Show worker sessions and queued tasks")
    status.add_argument("--workers", help="Comma-separated worker list filter")
    status.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
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
