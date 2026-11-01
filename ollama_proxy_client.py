"""Secure server-side client for an authenticated Ollama proxy.

Required environment variables:
  OLLAMA_PROXY_URL=https://your-proxy.example.com
  OLLAMA_PROXY_TOKEN=replace-with-a-long-random-token
  OLLAMA_MODEL=qwen2.5:14b
"""

from __future__ import annotations

import os
from typing import Any

import requests


PROXY_URL = os.environ.get("OLLAMA_PROXY_URL", "").rstrip("/")
PROXY_TOKEN = os.environ.get("OLLAMA_PROXY_TOKEN", "")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:14b")
CONNECT_TIMEOUT = float(os.environ.get("OLLAMA_CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = float(os.environ.get("OLLAMA_READ_TIMEOUT", "300"))
MAX_PROMPT_CHARS = int(os.environ.get("OLLAMA_MAX_PROMPT_CHARS", "12000"))


class OllamaProxyError(RuntimeError):
    """Raised when the proxy cannot be called successfully."""


def ask_ollama(prompt: str, *, model: str | None = None) -> dict[str, Any]:
    """Send one prompt to the proxy and return its JSON response.

    The token is added only on the server side. Never call this function from
    browser JavaScript or expose PROXY_TOKEN to the client.
    """
    if not PROXY_URL:
        raise OllamaProxyError("OLLAMA_PROXY_URL is not configured")
    if not PROXY_TOKEN:
        raise OllamaProxyError("OLLAMA_PROXY_TOKEN is not configured")
    if not isinstance(prompt, str) or not prompt.strip():
        raise OllamaProxyError("prompt is required")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise OllamaProxyError(
            f"prompt is too long; maximum is {MAX_PROMPT_CHARS} characters"
        )

    payload = {
        "prompt": prompt.strip(),
        "model": model or MODEL,
    }
    headers = {
        "Authorization": f"Bearer {PROXY_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/api/ai",
            json=payload,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
    except requests.Timeout as exc:
        raise OllamaProxyError("proxy request timed out") from exc
    except requests.RequestException as exc:
        raise OllamaProxyError(f"proxy connection failed: {exc}") from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise OllamaProxyError(
            f"proxy returned non-JSON response (HTTP {response.status_code})"
        ) from exc

    if not response.ok:
        detail = body.get("error", "proxy request failed") if isinstance(body, dict) else "proxy request failed"
        raise OllamaProxyError(f"HTTP {response.status_code}: {detail}")

    return body


def extract_text(response_body: dict[str, Any]) -> str:
    """Extract common response shapes without logging secrets."""
    if isinstance(response_body.get("response"), str):
        return response_body["response"]

    message = response_body.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]

    return ""


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Call an authenticated Ollama proxy")
    parser.add_argument("prompt", help="Prompt to send")
    args = parser.parse_args()

    result = ask_ollama(args.prompt)
    print(extract_text(result))
