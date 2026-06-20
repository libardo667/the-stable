# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class InferenceError(Exception):
    pass


# Substrings of model ids known to accept image content blocks. Best-effort and conservative:
# the default for an unrecognised model is text-only (a familiar with vision it lacks would send
# image blocks into a void). A familiar can override either way with "vision": true/false in its
# familiar.json — this is only the fallback when the config is silent.
_VISION_MODEL_HINTS = (
    "claude-3", "claude-sonnet-4", "claude-opus-4", "claude-haiku-4",  # Claude 3+ and 4.x are multimodal
    "gemini",                                                          # Gemini flash/pro
    "gpt-5", "gpt-4o", "gpt-4.1", "gpt-4-vision", "gpt-4-turbo", "o1", "o3", "o4",
    "pixtral", "mistral-small-3", "mistral-medium-3",                 # Mistral's vision line (NOT mistral-large)
    "-vl", "qwen2.5-vl", "qwen-vl",                                   # Qwen vision variants (NOT plain -instruct)
    "llama-3.2", "llama-4",                                           # Llama vision-capable
    "grok-2-vision", "grok-4",
)
# Substrings that are explicitly text-only even though a looser match might suggest otherwise.
_TEXT_ONLY_OVERRIDES = ("mistral-large", "deepseek-chat", "deepseek-v3", "deepseek-r1")


def model_accepts_images(model: str) -> bool:
    """Best-effort: does this model id accept image content blocks? Conservative — unknown
    models are treated as text-only. Override per-familiar with ``"vision"`` in familiar.json."""
    m = (model or "").lower()
    if any(t in m for t in _TEXT_ONLY_OVERRIDES):
        return False
    return any(t in m for t in _VISION_MODEL_HINTS)


class InferenceClient:
    """
    Thin async wrapper around an OpenRouter-compatible chat completions API.
    Shared by all residents and all loops. Stateless — context comes from caller.

    The agent never knows this exists. All prompt construction happens in the
    loop layer; this client just sends text and returns text.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        default_model: str = "google/gemini-flash-1.5",
        timeout: float = 60.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        # Lightweight usage accounting — lets callers measure real token cost
        # (e.g. the cost-curve harness, Minor 63's per-pulse metabolic mass) without
        # re-plumbing every call site. ``last_usage``/``last_model`` reflect the most
        # recent call; the totals are the running sum.
        self.last_usage: dict[str, Any] = {}
        self.last_model: str = ""
        self.total_calls = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    @property
    def is_local(self) -> bool:
        """Best-effort: is the pen a locally-hosted model (Ollama / localhost) rather than a cloud
        provider? Derived from the inference base URL so later analysis can split local-pen pulses
        from cloud-pen pulses (Minor 63's ``pen_local``) without re-deriving it from config."""
        u = self._base_url.lower()
        return any(h in u for h in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]", "host.docker.internal", "ollama")) or ":11434" in u

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
        images: list[str] | None = None,
    ) -> str:
        """
        Send a chat completion. Returns the assistant message text.
        Retries on transient errors (429, 500, 502, 503).

        ``max_tokens=None`` (the default) omits the cap entirely, so the model finishes its thought
        rather than being truncated mid-output — a being is not cut off mid-sentence in its own home.
        Pass an int only where a hard ceiling is genuinely wanted.

        ``response_format`` is passed through to the API when set — e.g.
        ``{"type": "json_object"}`` to constrain the model to a single JSON
        object (portable across OpenAI-compatible backends, including Ollama).

        ``images`` is an optional list of ``data:`` URLs (base64 image blocks). When present and
        non-empty the user turn becomes a multimodal content array; when absent the user content
        stays a plain string, so every existing text-only call is byte-for-byte unchanged. Only
        send images to a vision-capable model (see ``model_accepts_images``) — a text-only backend
        will error or ignore them.
        """
        if images:
            user_content: Any = [{"type": "text", "text": user_prompt}]
            user_content += [{"type": "image_url", "image_url": {"url": url}} for url in images]
        else:
            user_content = user_prompt
        payload = {
            "model": model or self._default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format

        response = await self._post_with_retry("/chat/completions", payload)
        content = response["choices"][0]["message"]["content"]

        usage = response.get("usage", {}) or {}
        self.last_usage = dict(usage)
        self.last_model = str(payload["model"])
        self.total_calls += 1
        self.total_prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.total_completion_tokens += int(usage.get("completion_tokens") or 0)
        logger.debug(
            "inference: model=%s tokens=%s+%s",
            payload["model"],
            usage.get("prompt_tokens", "?"),
            usage.get("completion_tokens", "?"),
        )

        return content

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> dict:
        """
        Like complete(), but parses the response as JSON.
        Strips markdown fences if present. Raises InferenceError on parse failure.

        Use sparingly — "respond with JSON" is the most visible seam.
        Prefer complete() + lightweight parsing where possible.
        """
        text = await self.complete(system_prompt, user_prompt, **kwargs)
        # Some models/providers (esp. small ones with response_format) return no
        # content at all. Fail closed with InferenceError (callers catch it and skip
        # the pulse) rather than crashing the daemon on None.strip().
        if not text or not str(text).strip():
            raise InferenceError("Model returned an empty response (no content).")
        text = str(text).strip()

        # Strip markdown fences if the model wrapped the JSON
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise InferenceError(f"Response was not valid JSON: {e}\n\nResponse was:\n{text}") from e

    async def _post_with_retry(
        self,
        path: str,
        payload: dict,
        *,
        max_retries: int = 2,
    ) -> dict:
        retryable = {429, 500, 502, 503}
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                resp = await self._client.post(path, json=payload)

                if resp.status_code in retryable:
                    delay = 2**attempt
                    logger.warning(
                        "inference: HTTP %s, retrying in %ss (attempt %s/%s)",
                        resp.status_code,
                        delay,
                        attempt + 1,
                        max_retries + 1,
                    )
                    await asyncio.sleep(delay)
                    last_error = httpx.HTTPStatusError(f"HTTP {resp.status_code}", request=resp.request, response=resp)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)
                    continue
                raise InferenceError("Inference request timed out") from e

        raise InferenceError(f"Inference failed after {max_retries + 1} attempts") from last_error

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> InferenceClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
