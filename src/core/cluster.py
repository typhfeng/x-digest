from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from src.models.digest import ClusteredPost
from src.models.post import Post

TOKEN_RE = re.compile(r"\b[a-z0-9][\w-]*\b")

DEFAULT_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ai": (
        "ai",
        "benchmark",
        "benchmarks",
        "embedding",
        "embeddings",
        "eval",
        "evaluation",
        "inference",
        "llm",
        "llms",
        "model",
        "models",
        "summarization",
    ),
    "semiconductor": (
        "chip",
        "chips",
        "fab",
        "foundry",
        "gpu",
        "gpus",
        "hbm",
        "semiconductor",
        "tsmc",
        "wafer",
    ),
    "macro": (
        "cpi",
        "fed",
        "gdp",
        "inflation",
        "macro",
        "rates",
        "tariff",
        "treasury",
        "yield",
    ),
    "space": (
        "launch",
        "nasa",
        "orbit",
        "payload",
        "rocket",
        "satellite",
        "space",
        "spacex",
    ),
    "software": (
        "adapter",
        "adapters",
        "api",
        "apis",
        "cache",
        "caching",
        "deploy",
        "deployment",
        "fixture",
        "fixtures",
        "pipeline",
        "pipelines",
        "queue",
        "queues",
        "scoring",
        "software",
        "test",
        "tests",
    ),
    "general": (),
}


def cluster_posts(
    posts: Sequence[Post],
    *,
    keyword_map: Mapping[str, Sequence[str]] | None = None,
) -> list[ClusteredPost]:
    """Assign each post to a heuristic topic using a simple keyword map."""
    topics = keyword_map or DEFAULT_TOPIC_KEYWORDS
    clustered: list[ClusteredPost] = []

    for post in posts:
        topic, tags, strength = assign_topic(post.text, keyword_map=topics)
        clustered.append(
            ClusteredPost(
                post=post,
                topic=topic,
                tags=tags,
                topic_match_strength=strength,
            )
        )

    return clustered


def assign_topic(
    text: str,
    *,
    keyword_map: Mapping[str, Sequence[str]] | None = None,
) -> tuple[str, tuple[str, ...], int]:
    """Return (topic, tags, strength) for the supplied text."""
    topics = keyword_map or DEFAULT_TOPIC_KEYWORDS
    lowered = text.casefold()
    tokens = set(TOKEN_RE.findall(lowered))
    best_topic = "general"
    best_tags: tuple[str, ...] = ()
    best_strength = 0

    for topic, keywords in topics.items():
        if topic == "general":
            continue

        matched = tuple(
            keyword
            for keyword in keywords
            if _keyword_matches(keyword.casefold(), lowered, tokens)
        )
        strength = len(matched)

        if strength > best_strength:
            best_topic = topic
            best_tags = matched
            best_strength = strength

    return best_topic, best_tags, best_strength


def _keyword_matches(keyword: str, lowered_text: str, tokens: set[str]) -> bool:
    if " " in keyword:
        return keyword in lowered_text

    return keyword in tokens
