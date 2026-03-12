from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


class LlmProviderError(RuntimeError):
    """Raised when an LLM provider request fails."""


@dataclass(frozen=True, slots=True)
class OpenAICompatibleProvider:
    """Small OpenAI-compatible chat completions client using the standard library."""

    model: str
    api_key: str
    base_url: str
    timeout_seconds: float

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        endpoint = self._resolve_endpoint()
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode("utf-8")
        req = request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise LlmProviderError(str(exc)) from exc

        try:
            parsed = json.loads(body)
            message = parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LlmProviderError("Invalid response payload from OpenAI-compatible provider") from exc

        text = _coerce_content_to_text(message).strip()
        if not text:
            raise LlmProviderError("Received empty response from OpenAI-compatible provider")

        return text

    def _resolve_endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url

        return f"{self.base_url}/chat/completions"


def _coerce_content_to_text(message: Any) -> str:
    if isinstance(message, str):
        return message

    if isinstance(message, list):
        parts: list[str] = []
        for part in message:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
        return "\n".join(part for part in parts if part)

    return ""
