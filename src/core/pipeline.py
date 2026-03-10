"""Core pipeline orchestration for x-digest."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from src.core.cluster import DEFAULT_TOPIC_KEYWORDS, assign_topic, cluster_posts
from src.core.filter import count_words, filter_posts
from src.core.normalize import normalize_posts
from src.core.rank import DEFAULT_PRIORITY_AUTHORS, rank_posts, score_post
from src.core.summarize import summarize_posts, summarize_topics
from src.models.digest import ClusteredPost, DigestItem, PipelineResult, RankedPost
from src.models.post import Post


def run_pipeline(
    raw_posts: list[dict[str, Any]],
    *,
    min_words: int = 6,
    keyword_map: Mapping[str, Sequence[str]] | None = None,
    priority_authors: Iterable[str] | None = None,
    max_summary_words: int = 18,
) -> PipelineResult:
    """Run normalize -> filter -> cluster -> rank -> summarize for local JSON input."""
    normalized = normalize_posts(raw_posts)
    filtered = filter_posts(normalized, min_words=min_words)
    clustered = cluster_posts(filtered, keyword_map=keyword_map)
    ranked = rank_posts(clustered, priority_authors=priority_authors)
    items = summarize_posts(ranked, max_words=max_summary_words)
    return PipelineResult(
        items=tuple(items),
        topic_summaries=summarize_topics(items),
    )


__all__ = [
    "ClusteredPost",
    "DEFAULT_PRIORITY_AUTHORS",
    "DEFAULT_TOPIC_KEYWORDS",
    "DigestItem",
    "PipelineResult",
    "Post",
    "RankedPost",
    "assign_topic",
    "cluster_posts",
    "count_words",
    "filter_posts",
    "normalize_posts",
    "rank_posts",
    "run_pipeline",
    "score_post",
    "summarize_posts",
]
