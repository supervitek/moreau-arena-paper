"""API provider adapters for Round Table free-text responses.

Adapted from run_challenge.py but simplified for text-only output
(no structured JSON schema — we want natural language discussion).
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# Pricing per 1M tokens (USD) — as of March 2026
# ---------------------------------------------------------------------------

PRICING: dict[str, dict[str, float]] = {
    # Anthropic
    "claude-opus-4-6":             {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6":           {"input": 3.0,  "output": 15.0},
    "claude-haiku-4-5-20251001":   {"input": 0.80, "output": 4.0},
    # OpenAI
    "gpt-5.2":                     {"input": 2.50, "output": 10.0},
    "gpt-5.2-codex":               {"input": 2.50, "output": 10.0},
    "gpt-5.4":                     {"input": 2.50, "output": 10.0},
    "gpt-5.3-codex":               {"input": 2.50, "output": 10.0},
    # Google
    "gemini-3-flash-preview":      {"input": 0.15, "output": 0.60},
    "gemini-3.1-pro-preview":      {"input": 1.25, "output": 5.0},
    # xAI
    "grok-4-1-fast-reasoning":     {"input": 3.0,  "output": 15.0},
}

# Provider -> env var name
ENV_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
}

# Model -> provider mapping
MODEL_PROVIDERS: dict[str, str] = {
    "claude-opus-4-6": "anthropic",
    "claude-sonnet-4-6": "anthropic",
    "claude-haiku-4-5-20251001": "anthropic",
    "gpt-5.2": "openai",
    "gpt-5.2-codex": "openai",
    "gpt-5.4": "openai",
    "gpt-5.3-codex": "openai",
    "gemini-3-flash-preview": "google",
    "gemini-3.1-pro-preview": "google",
    "grok-4-1-fast-reasoning": "xai",
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given model call."""
    prices = PRICING.get(model, {"input": 5.0, "output": 15.0})
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


def get_api_key(provider: str) -> str:
    """Get API key from environment."""
    env_var = ENV_KEYS[provider]
    key = os.environ.get(env_var, "")
    if not key:
        raise ValueError(f"Missing {env_var} environment variable")
    return key


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _make_request(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout: int = 120,
) -> dict[str, Any]:
    """POST JSON and return parsed response."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for key, val in headers.items():
        req.add_header(key, val)
    req.add_header("Content-Type", "application/json")

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API {exc.code}: {error_body}") from exc


# ---------------------------------------------------------------------------
# Provider-specific callers (free-text, no structured output)
# ---------------------------------------------------------------------------

def call_anthropic(api_key: str, model: str, prompt: str) -> tuple[str, int, int]:
    """Call Anthropic Messages API. Returns (text, input_tokens, output_tokens)."""
    resp = _make_request(
        url="https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        body={
            "model": model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    text = ""
    for block in resp.get("content", []):
        if block.get("type") == "text":
            text += block.get("text", "")
    usage = resp.get("usage", {})
    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def call_openai(api_key: str, model: str, prompt: str) -> tuple[str, int, int]:
    """Call OpenAI Chat Completions API. Returns (text, input_tokens, output_tokens)."""
    resp = _make_request(
        url="https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        body={
            "model": model,
            "max_completion_tokens": 2048,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    choices = resp.get("choices", [])
    text = choices[0]["message"]["content"] if choices else ""
    usage = resp.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def call_google(api_key: str, model: str, prompt: str) -> tuple[str, int, int]:
    """Call Google Generative AI API. Returns (text, input_tokens, output_tokens)."""
    resp = _make_request(
        url=(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
            f":generateContent?key={api_key}"
        ),
        headers={},
        body={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 2048,
                "temperature": 0.7,
            },
        },
    )
    text = ""
    candidates = resp.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            text = parts[0].get("text", "")
    usage = resp.get("usageMetadata", {})
    return (
        text,
        usage.get("promptTokenCount", 0),
        usage.get("candidatesTokenCount", 0),
    )


def call_xai(api_key: str, model: str, prompt: str) -> tuple[str, int, int]:
    """Call xAI API (OpenAI-compatible). Returns (text, input_tokens, output_tokens).

    Note: reasoning models reject max_completion_tokens, so we omit it.
    """
    resp = _make_request(
        url="https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        body={
            "model": model,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    choices = resp.get("choices", [])
    text = choices[0]["message"]["content"] if choices else ""
    usage = resp.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

PROVIDER_CALLERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "google": call_google,
    "xai": call_xai,
}


def call_model(model: str, prompt: str) -> tuple[str, int, int]:
    """Call any supported model. Returns (text, input_tokens, output_tokens)."""
    provider = MODEL_PROVIDERS.get(model)
    if not provider:
        raise ValueError(f"Unknown model: {model}. Known: {list(MODEL_PROVIDERS)}")
    api_key = get_api_key(provider)
    caller = PROVIDER_CALLERS[provider]
    return caller(api_key, model, prompt)
