"""
AI API Gateway v4 — unified OpenAI-compatible proxy with smart triage.

Routing:
  1. Ping interceptor  → instant "OK" (zero cost)
  2. Triage classifier → GREEN (simple) → Ollama, RED (complex) → Claude CLI
  3. Fallback          → if primary fails → try the other backend

Features:
  - Smart triage: keyword classifier routes simple tasks to free Ollama models
  - SSE streaming for Claude CLI responses (OpenClaw TUI compatible)
  - Ping interceptor (zero-cost replies for trivial messages)
  - Dynamic backpressure (throttle after Claude generation)
  - Context window trimming for large message histories

Endpoints:
  POST /v1/chat/completions   — main proxy route
  GET  /v1/models             — list available models
  GET  /health                — health check
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

# ── Config ───────────────────────────────────────────────────────────
load_dotenv()

GATEWAY_HOST = os.getenv("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8080"))

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3-next:80b-cloud")

# Claude CLI
CLAUDE_BIN = os.getenv("CLAUDE_BIN", "/opt/homebrew/bin/claude")
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "300"))
CLAUDE_MAX_CONCURRENT = int(os.getenv("CLAUDE_MAX_CONCURRENT", "3"))
CLAUDE_FALLBACK_MODEL = os.getenv("CLAUDE_FALLBACK_MODEL", OLLAMA_DEFAULT_MODEL)
CLAUDE_MAX_MESSAGES = int(os.getenv("CLAUDE_MAX_MESSAGES", "20"))

# Triage
TRIAGE_ENABLED = os.getenv("TRIAGE_ENABLED", "false").lower() == "true"
TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", OLLAMA_DEFAULT_MODEL)

# Backpressure
BACKPRESSURE_FACTOR = float(os.getenv("BACKPRESSURE_FACTOR", "0.01"))
BACKPRESSURE_MAX = float(os.getenv("BACKPRESSURE_MAX", "15.0"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("gateway")

# ── Shared state ─────────────────────────────────────────────────────
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\x1b\[.*?[@-~]")
client: httpx.AsyncClient
claude_sem: asyncio.Semaphore
_claude_active: int = 0


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global client, claude_sem
    client = httpx.AsyncClient(timeout=httpx.Timeout(CLAUDE_TIMEOUT + 30, connect=10.0))
    claude_sem = asyncio.Semaphore(CLAUDE_MAX_CONCURRENT)
    log.info("Gateway v4 started on %s:%s", GATEWAY_HOST, GATEWAY_PORT)
    log.info("  Ollama     -> %s (default: %s)", OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL)
    log.info("  Claude CLI -> %s (max concurrent: %d, timeout: %ds)",
             CLAUDE_BIN, CLAUDE_MAX_CONCURRENT, CLAUDE_TIMEOUT)
    log.info("  Triage: %s (model: %s) | Ping: ON | Backpressure: %.2f * len, max %.1fs",
             "ON" if TRIAGE_ENABLED else "OFF", TRIAGE_MODEL,
             BACKPRESSURE_FACTOR, BACKPRESSURE_MAX)
    yield
    await client.aclose()


app = FastAPI(title="AI API Gateway", version="4.0.0", lifespan=lifespan)


# ======================================================================
#  PING INTERCEPTOR -- zero-cost replies for trivial messages
# ======================================================================

PING_PATTERNS = re.compile(
    r"^(say ok|hello|hi|hey|test|ping|ok)$",
    re.IGNORECASE,
)


def _is_ping(messages: list[dict]) -> bool:
    """Check if the last user message is a trivial ping."""
    if not messages:
        return False
    last = messages[-1]
    content = last.get("content", "")
    if isinstance(content, list):
        content = " ".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    content = content.strip()
    if len(content) < 15 and PING_PATTERNS.match(content):
        return True
    return False


def _ping_response(model: str) -> dict:
    return {
        "id": f"chatcmpl-ping-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "OK"},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 1, "total_tokens": 1},
    }


def _ping_stream_response(model: str) -> str:
    """Build SSE chunks for a ping response."""
    chunk_id = f"chatcmpl-ping-{uuid.uuid4().hex[:8]}"
    delta_chunk = {
        "id": chunk_id, "object": "chat.completion.chunk",
        "created": int(time.time()), "model": model,
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": "OK"}, "finish_reason": None}],
    }
    stop_chunk = {
        "id": chunk_id, "object": "chat.completion.chunk",
        "created": int(time.time()), "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    return (
        f"data: {json.dumps(delta_chunk)}\n\n"
        f"data: {json.dumps(stop_chunk)}\n\n"
        f"data: [DONE]\n\n"
    )


# ======================================================================
#  TRIAGE CLASSIFIER -- route by task complexity, not model name
# ======================================================================

# RED keywords -> must go to Claude (code, architecture, debugging, etc.)
_RED_KEYWORDS = re.compile(
    r"(?i)"
    # Code-related
    r"\b(write|rewrite|refactor|implement|create a|build a"
    r"|function|class |module|script|endpoint|middleware|decorator|generator"
    r"|def |async def|import |from .+ import|return |yield |lambda"
    r"|```)"
    r"|"
    # Russian code-related
    r"\b(napishi|sozdaj|realizuj|perepiши"
    r"|funkcij|klass|modul|skript|endpoint)"
    r"|"
    r"(напиши|создай|реализуй|перепиши|допиши|добавь функци"
    r"|функци[юяи]|класс[а-я]*|модул[ья]|скрипт|эндпоинт)"
    r"|"
    # Debugging
    r"\b(debug|fix|broken|crash|traceback|stack.?trace|exception|segfault"
    r"|почини|исправь|ошибк[аи]|баг|падает|не работает|сломал|крашит)\b"
    r"|"
    # Architecture & design
    r"\b(architect|design pattern|system.?design|tradeoff|refactor"
    r"|архитектур|проектир|паттерн|схем[аы]|миграци)\b"
    r"|"
    # Review & analysis
    r"\b(review|code.?review|analyze|audit|security|vulnerab|performance|optimize"
    r"|ревью|анализ|аудит|безопасност|уязвимост|производительност|оптимиз)\b"
    r"|"
    # DevOps & infrastructure
    r"\b(docker|dockerfile|kubernetes|k8s|ci.?cd|pipeline|deploy|nginx|terraform"
    r"|деплой|контейнер)\b"
    r"|"
    # Database
    r"\b(sql|query|database|postgres|mysql|redis|mongo|migration"
    r"|база.?данн|запрос.+к.+бд)\b"
    r"|"
    # Testing
    r"\b(pytest|unittest|test.?case|mock|assert|coverage"
    r"|тест[аыи]|покрыти)\b"
)

# GREEN patterns -> definitely simple, Ollama handles fine
_GREEN_PATTERNS = re.compile(
    r"(?i)"
    r"^("
    # Greetings & chat
    r"привет[!?.\s]*|hello[!?.\s]*|hi[!?.\s]*|hey[!?.\s]*"
    r"|как дела[!?.\s]*|what'?s up[!?.\s]*"
    r"|who are you[!?.\s]*|кто ты[!?.\s]*"
    r"|с какой.{0,15}модел[а-я]*[!?.\s]*|what model[!?.\s]*"
    r"|спасибо[!?.\s]*|thanks[!?.\s]*|thank you[!?.\s]*"
    r"|да[!?.\s]*|нет[!?.\s]*|yes[!?.\s]*|no[!?.\s]*"
    r"|ok[!?.\s]*|ок[!?.\s]*|хорошо[!?.\s]*|good[!?.\s]*|great[!?.\s]*|понятно[!?.\s]*"
    r"|расскажи о себе[!?.\s]*|tell me about yourself[!?.\s]*"
    r"|помощь[!?.\s]*|help[!?.\s]*"
    r"|что .{0,15}умеешь[!?.\s]*|what can you do[!?.\s]*"
    # Simple factual
    r"|что такое .{1,50}[?]?"
    r"|what is .{1,50}[?]?"
    r"|объясни .{1,50}"
    r"|explain .{1,50}"
    r"|переведи .{1,100}"
    r"|translate .{1,100}"
    r")$"
)


def _classify_complexity(messages: list[dict]) -> str:
    """Classify the last user message as 'green' or 'red'.

    Returns 'green' for simple tasks (-> Ollama) or 'red' for complex (-> Claude).
    """
    if not messages:
        return "green"

    # Get last user message
    last_content = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            last_content = content.strip()
            break

    if not last_content:
        return "green"

    # Explicit GREEN match (short, simple messages)
    if _GREEN_PATTERNS.match(last_content):
        return "green"

    # RED keyword scan
    if _RED_KEYWORDS.search(last_content):
        return "red"

    # Heuristic: long messages are likely complex tasks
    if len(last_content) > 300:
        return "red"

    # Default: short messages without code keywords -> green
    return "green"


def _route_for(model: str) -> str:
    """Determine backend: 'claude' or 'ollama'."""
    return "claude" if model.startswith("claude-") else "ollama"


# ======================================================================
#  BACKEND: OLLAMA
# ======================================================================

STREAM_PASSTHROUGH_HEADERS = {"content-type", "transfer-encoding", "x-request-id"}


async def _ollama_chat(body: dict, stream: bool, t0: float):
    """Forward request to Ollama's OpenAI-compatible endpoint."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    if stream:
        return await _ollama_stream(url, body, t0)
    resp = await client.post(url, json=body)
    elapsed = time.monotonic() - t0
    log.info("<- OLLAMA  | %d | %.1fs", resp.status_code, elapsed)
    if resp.status_code >= 400:
        raise RuntimeError(f"Ollama returned {resp.status_code}")
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


async def _ollama_stream(url: str, body: dict, t0: float):
    req = client.build_request("POST", url, json=body)
    resp = await client.send(req, stream=True)
    filtered_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() in STREAM_PASSTHROUGH_HEADERS
    }

    async def _gen():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        except Exception as e:
            log.error("OLLAMA stream error: %s", e)
        finally:
            await resp.aclose()
            log.info("<- OLLAMA  | stream done | %.1fs", time.monotonic() - t0)

    return StreamingResponse(
        _gen(),
        status_code=resp.status_code,
        media_type="text/event-stream",
        headers=filtered_headers,
    )


# ======================================================================
#  BACKEND: CLAUDE CLI
# ======================================================================

def _extract_prompt(messages: list[dict]) -> str:
    """Flatten message array into a single prompt for `claude -p`.
    Keeps system message + last CLAUDE_MAX_MESSAGES to avoid huge prompts."""
    system_parts = []
    conv_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            conv_parts.append(f"[Assistant]: {content}")
        else:
            conv_parts.append(content)

    # Trim conversation to last N messages
    if len(conv_parts) > CLAUDE_MAX_MESSAGES:
        trimmed = len(conv_parts) - CLAUDE_MAX_MESSAGES
        conv_parts = conv_parts[-CLAUDE_MAX_MESSAGES:]
        log.info("  trimmed %d old messages, keeping last %d", trimmed, CLAUDE_MAX_MESSAGES)

    parts = system_parts + conv_parts
    return "\n\n".join(parts)


def _make_oai_response(text: str, model: str) -> dict:
    """Build an OpenAI-compatible chat.completion object."""
    return {
        "id": f"chatcmpl-ghost-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def _make_sse_stream(text: str, model: str) -> str:
    """Convert a complete text into OpenAI-compatible SSE stream chunks."""
    chunk_id = f"chatcmpl-ghost-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    lines = []

    # Role chunk
    role_chunk = {
        "id": chunk_id, "object": "chat.completion.chunk",
        "created": created, "model": model,
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}],
    }
    lines.append(f"data: {json.dumps(role_chunk)}\n\n")

    # Content chunks -- split into ~80 char pieces for natural streaming feel
    chunk_size = 80
    for i in range(0, len(text), chunk_size):
        piece = text[i:i + chunk_size]
        content_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk",
            "created": created, "model": model,
            "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
        }
        lines.append(f"data: {json.dumps(content_chunk)}\n\n")

    # Stop chunk
    stop_chunk = {
        "id": chunk_id, "object": "chat.completion.chunk",
        "created": created, "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    lines.append(f"data: {json.dumps(stop_chunk)}\n\n")
    lines.append("data: [DONE]\n\n")

    return "".join(lines)


async def _claude_chat(body: dict, stream: bool, t0: float):
    """Run `claude -p` subprocess, return OpenAI-compatible JSON or SSE stream."""
    global _claude_active
    messages = body.get("messages", [])
    model = body.get("model", "claude-cli")
    prompt = _extract_prompt(messages)

    async with claude_sem:
        _claude_active += 1
        log.info(">> CLAUDE  | acquired slot (%d/%d active)",
                 _claude_active, CLAUDE_MAX_CONCURRENT)
        try:
            # Map model name to claude CLI model flag
            claude_model_flag = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
            if "opus" in model.lower():
                claude_model_flag = "claude-opus-4-6"
            elif "sonnet" in model.lower():
                claude_model_flag = "claude-sonnet-4-6"

            cmd_env = {**os.environ, "NO_COLOR": "1"}
            cmd_env.pop("ANTHROPIC_API_KEY", None)  # use Max subscription

            proc = await asyncio.create_subprocess_exec(
                CLAUDE_BIN, "-p", prompt, "--model", claude_model_flag,
                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=cmd_env,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=CLAUDE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            proc.kill()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                pass
            raise RuntimeError(f"claude CLI timed out after {CLAUDE_TIMEOUT}s")
        except FileNotFoundError:
            raise RuntimeError(f"claude binary not found: {CLAUDE_BIN}")
        finally:
            _claude_active -= 1

    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace").strip()[:500]
        raise RuntimeError(f"claude exit code {proc.returncode}: {err}")

    raw = stdout.decode("utf-8", errors="replace")
    clean = ANSI_RE.sub("", raw).strip()

    elapsed = time.monotonic() - t0
    log.info("<< CLAUDE  | %d chars | %.1fs", len(clean), elapsed)

    # -- Dynamic backpressure
    delay = min(len(clean) * BACKPRESSURE_FACTOR, BACKPRESSURE_MAX)
    if delay > 0.5:
        log.info(".. BACKPRESSURE | %.1fs delay (%d chars)", delay, len(clean))
        await asyncio.sleep(delay)

    # -- Return as SSE stream or JSON
    if stream:
        sse_payload = _make_sse_stream(clean, model)

        async def _sse_gen():
            yield sse_payload.encode("utf-8")

        return StreamingResponse(
            _sse_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return JSONResponse(content=_make_oai_response(clean, model))


# ======================================================================
#  MAIN ENDPOINT -- POST /v1/chat/completions
# ======================================================================

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    t0 = time.monotonic()
    body = await request.json()

    model = body.get("model", OLLAMA_DEFAULT_MODEL)
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    route = _route_for(model)

    # -- Ping interceptor
    if _is_ping(messages):
        log.info("** PING | model=%s | intercepted (zero-cost)", model)
        if stream:
            payload = _ping_stream_response(model)

            async def _ping_gen():
                yield payload.encode("utf-8")

            return StreamingResponse(
                _ping_gen(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        return JSONResponse(content=_ping_response(model))

    # -- Triage: smart routing for claude-* models
    actual_route = route
    triage_result = None
    if route == "claude" and TRIAGE_ENABLED:
        triage_result = _classify_complexity(messages)
        if triage_result == "green":
            actual_route = "ollama"
            log.info("GREEN TRIAGE | -> Ollama (free) | model=%s | msgs=%d | stream=%s",
                     model, len(messages), stream)
        else:
            log.info("RED TRIAGE | -> Claude (paid) | model=%s | msgs=%d | stream=%s",
                     model, len(messages), stream)
    else:
        log.info("-> %s | model=%s | msgs=%d | stream=%s",
                 actual_route.upper(), model, len(messages), stream)

    # -- Primary attempt
    try:
        if actual_route == "claude":
            return await _claude_chat(body, stream, t0)
        else:
            ollama_body = {**body, "model": TRIAGE_MODEL} if triage_result == "green" else body
            return await _ollama_chat(ollama_body, stream, t0)

    except Exception as primary_err:
        log.warning("XX %s failed: %s", actual_route.upper(), primary_err)

    # -- Fallback
    fallback = "ollama" if actual_route == "claude" else "claude"
    log.info("~~ FALLBACK | %s -> %s", actual_route.upper(), fallback.upper())

    try:
        if fallback == "claude":
            return await _claude_chat(body, stream, t0)
        else:
            fallback_body = {**body, "model": CLAUDE_FALLBACK_MODEL}
            return await _ollama_chat(fallback_body, stream, t0)

    except Exception as fallback_err:
        log.error("XX FALLBACK %s also failed: %s", fallback.upper(), fallback_err)
        raise HTTPException(
            502,
            f"Both backends failed. "
            f"{actual_route}: {primary_err} | {fallback}: {fallback_err}",
        )


# ======================================================================
#  GET /v1/models
# ======================================================================

@app.get("/v1/models")
async def list_models():
    models = []

    # Ollama models
    try:
        resp = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
        if resp.status_code == 200:
            for m in resp.json().get("models", []):
                models.append({"id": m["name"], "object": "model", "owned_by": "ollama"})
    except httpx.ConnectError:
        log.warning("Cannot reach Ollama at %s", OLLAMA_BASE_URL)

    # Claude CLI (virtual entry)
    try:
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_BIN, "--version",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        ver = stdout.decode().strip()
        models.append({"id": f"claude-cli ({ver})", "object": "model", "owned_by": "cli"})
    except Exception:
        pass

    return {"object": "list", "data": models}


# ======================================================================
#  GET /health
# ======================================================================

@app.get("/health")
async def health():
    ollama_ok = False
    try:
        resp = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
        ollama_ok = resp.status_code == 200
    except httpx.ConnectError:
        pass

    claude_ok = False
    claude_ver = None
    try:
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_BIN, "--version",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode == 0:
            claude_ok = True
            claude_ver = stdout.decode().strip()
    except Exception:
        pass

    both_up = ollama_ok and claude_ok
    return {
        "status": "ok" if both_up else ("degraded" if ollama_ok or claude_ok else "down"),
        "ollama": "up" if ollama_ok else "down",
        "claude": {
            "status": "up" if claude_ok else "down",
            "version": claude_ver,
            "binary": CLAUDE_BIN,
            "max_concurrent": CLAUDE_MAX_CONCURRENT,
            "timeout": CLAUDE_TIMEOUT,
        },
        "features": {
            "triage": "ON" if TRIAGE_ENABLED else "OFF",
            "triage_model": TRIAGE_MODEL,
            "ping_interceptor": True,
            "backpressure": f"{BACKPRESSURE_FACTOR} * len, max {BACKPRESSURE_MAX}s",
            "max_messages": CLAUDE_MAX_MESSAGES,
        },
    }


# ======================================================================
#  Entrypoint
# ======================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gateway:app", host=GATEWAY_HOST, port=GATEWAY_PORT, reload=True)
