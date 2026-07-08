"""LLM provider interfaces for optional extraction adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import request


class LLMProvider(Protocol):
    """Minimal provider contract used by LLM-backed memory extractors."""

    def generate_json(self, *, system: str, user: str) -> dict[str, Any]:
        """Return one JSON object for the supplied system and user prompts."""
        ...


class LLMProviderError(RuntimeError):
    """Raised when a provider response cannot be converted into JSON."""


@dataclass(slots=True)
class OpenAICompatibleProvider:
    """Small OpenAI-compatible chat/completions adapter using only stdlib HTTP."""

    api_key: str | None
    model: str
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 30.0
    temperature: float = 0.2
    max_tokens: int | None = None
    extra_body: dict[str, Any] | None = None

    def generate_json(self, *, system: str, user: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        if self.extra_body:
            payload.update(self.extra_body)

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            self._chat_completions_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except OSError as exc:
            raise LLMProviderError("LLM provider request failed") from exc

        try:
            response_data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LLM provider returned non-JSON response") from exc

        content = _message_content(response_data)
        if isinstance(content, dict):
            return content
        return extract_json_object(content)

    def _chat_completions_url(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response."""

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise LLMProviderError("LLM provider response did not contain a JSON object")


def _message_content(response_data: dict[str, Any]) -> str | dict[str, Any]:
    choices = response_data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMProviderError("LLM provider response is missing choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise LLMProviderError("LLM provider response has invalid choices")
    message = first.get("message")
    if not isinstance(message, dict):
        raise LLMProviderError("LLM provider response is missing a message")

    content = message.get("content")
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
        if chunks:
            return "\n".join(chunks)
    raise LLMProviderError("LLM provider response is missing text content")
