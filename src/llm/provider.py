from __future__ import annotations

from typing import Protocol

from src.llm.config import LlmSettings
from src.llm.openai_compatible import OpenAICompatibleProvider


class LlmProvider(Protocol):
    """Minimal provider interface used by the digest summarization layer."""

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return a text completion for the supplied prompts."""


def build_provider(settings: LlmSettings) -> LlmProvider | None:
    """Instantiate a configured provider or return None for fallback mode."""
    if not settings.is_configured:
        return None

    provider_name = settings.provider.casefold()
    if provider_name in {"openai", "openai_compatible"}:
        return OpenAICompatibleProvider(
            model=settings.model or "",
            api_key=settings.api_key or "",
            base_url=settings.base_url,
            timeout_seconds=settings.timeout_seconds,
        )

    return None
