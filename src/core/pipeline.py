"""Core pipeline orchestration for x-digest."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from src.core.cluster import DEFAULT_TOPIC_KEYWORDS, assign_topic, cluster_posts
from src.core.filter import count_words, filter_posts
from src.core.normalize import normalize_posts
from src.core.rank import DEFAULT_PRIORITY_AUTHORS, rank_posts, score_post
from src.core.summarize import summarize_posts, summarize_topics
from src.llm.config import LlmSettings, load_llm_settings
from src.llm.provider import LlmProvider, build_provider
from src.llm.service import LlmDigestEnhancer
from src.memory.models import ResearchMemorySnapshot
from src.memory.service import annotate_result
from src.models.digest import (
    ClusteredPost,
    DigestItem,
    PipelineResult,
    RankedPost,
    TopicMemoryAnnotation,
)
from src.models.post import Post


def run_pipeline(
    raw_posts: list[dict[str, Any]],
    *,
    min_words: int = 6,
    keyword_map: Mapping[str, Sequence[str]] | None = None,
    priority_authors: Iterable[str] | None = None,
    max_summary_words: int = 18,
    llm_settings: LlmSettings | None = None,
    llm_provider: LlmProvider | None = None,
    memory_snapshot: ResearchMemorySnapshot | None = None,
) -> PipelineResult:
    """Run normalize -> filter -> cluster -> rank -> summarize for local JSON input."""
    normalized = normalize_posts(raw_posts)
    filtered = filter_posts(normalized, min_words=min_words)
    clustered = cluster_posts(filtered, keyword_map=keyword_map)
    ranked = rank_posts(clustered, priority_authors=priority_authors)
    items = summarize_posts(ranked, max_words=max_summary_words)
    result = PipelineResult(
        items=tuple(items),
        topic_summaries=summarize_topics(items),
    )
    settings = llm_settings or load_llm_settings()
    provider = llm_provider or build_provider(settings)
    if provider is None:
        return annotate_result(result, memory_snapshot)

    enhanced = LlmDigestEnhancer(provider).enhance(result)
    return annotate_result(enhanced, memory_snapshot)


__all__ = [
    "ClusteredPost",
    "DEFAULT_PRIORITY_AUTHORS",
    "DEFAULT_TOPIC_KEYWORDS",
    "DigestItem",
    "LlmSettings",
    "PipelineResult",
    "Post",
    "RankedPost",
    "TopicMemoryAnnotation",
    "assign_topic",
    "build_provider",
    "cluster_posts",
    "count_words",
    "filter_posts",
    "load_llm_settings",
    "normalize_posts",
    "rank_posts",
    "run_pipeline",
    "score_post",
    "summarize_posts",
]
