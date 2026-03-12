from __future__ import annotations

from dataclasses import replace

from src.llm.prompts import PromptTemplateSet, load_prompt_templates
from src.llm.provider import LlmProvider
from src.models.digest import DigestItem, PipelineResult


class LlmDigestEnhancer:
    """Apply optional LLM improvements to topic summaries and why-selected explanations."""

    def __init__(
        self,
        provider: LlmProvider,
        *,
        prompts: PromptTemplateSet | None = None,
    ) -> None:
        self._provider = provider
        self._prompts = prompts or load_prompt_templates()

    def enhance(self, result: PipelineResult) -> PipelineResult:
        """Return a new result with per-topic and per-item LLM enhancements when available."""
        items = tuple(self._enhance_item(item) for item in result.items)
        topic_summaries = dict(result.topic_summaries)

        for topic in sorted({item.topic for item in items}):
            topic_items = [item for item in items if item.topic == topic]
            if not topic_items:
                continue

            topic_summaries[topic] = self._enhance_topic_summary(
                topic,
                topic_items,
                fallback_summary=topic_summaries.get(topic, "No topic summary available."),
            )

        return replace(result, items=items, topic_summaries=topic_summaries)

    def _enhance_item(self, item: DigestItem) -> DigestItem:
        fallback_reason = item.why_selected or "Selected by the deterministic ranking rules."
        tags = ", ".join(item.tags) if item.tags else "none"
        prompt = self._prompts.why_selected_user.format(
            topic=item.topic,
            score=item.score,
            tags=tags,
            fallback_reason=fallback_reason,
            post_text=item.post.text,
        )
        improved = self._safe_complete(
            system_prompt=self._prompts.why_selected_system,
            user_prompt=prompt,
            fallback=fallback_reason,
        )
        return replace(item, why_selected=_normalize_single_line(improved))

    def _enhance_topic_summary(
        self,
        topic: str,
        topic_items: list[DigestItem],
        *,
        fallback_summary: str,
    ) -> str:
        posts = "\n".join(
            f"- score={item.score}; author=@{item.post.author}; tags={', '.join(item.tags) if item.tags else 'none'}; text={item.post.text}"
            for item in topic_items
        )
        prompt = self._prompts.topic_summary_user.format(topic=topic, posts=posts)
        improved = self._safe_complete(
            system_prompt=self._prompts.topic_summary_system,
            user_prompt=prompt,
            fallback=fallback_summary,
        )
        return _normalize_single_line(improved)

    def _safe_complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        fallback: str,
    ) -> str:
        try:
            return self._provider.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception:
            return fallback


def _normalize_single_line(text: str) -> str:
    return " ".join(text.split())
