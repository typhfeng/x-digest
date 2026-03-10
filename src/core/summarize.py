from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from src.models.digest import DigestItem, RankedPost


def summarize_posts(posts: Sequence[RankedPost], *, max_words: int = 18) -> list[DigestItem]:
    """Create deterministic one-line summaries from ranked posts."""
    return [
        DigestItem(
            post=post.post,
            topic=post.topic,
            score=post.score,
            summary=_summarize_text(post.post.text, max_words),
            tags=post.tags,
            why_selected=post.why_selected,
        )
        for post in posts
    ]


def summarize_topics(items: Sequence[DigestItem], *, max_tags: int = 3) -> dict[str, str]:
    """Create deterministic topic summaries from selected digest items."""
    by_topic: dict[str, list[DigestItem]] = {}
    for item in items:
        by_topic.setdefault(item.topic, []).append(item)

    summaries: dict[str, str] = {}
    for topic, topic_items in by_topic.items():
        tag_counts = Counter(tag for item in topic_items for tag in item.tags)
        top_tags = [
            tag
            for tag, _count in sorted(tag_counts.items(), key=lambda pair: (-pair[1], pair[0]))
        ][:max_tags]
        coverage = ", ".join(top_tags) if top_tags else "broad market signal"
        top_score = max(item.score for item in topic_items)
        summaries[topic] = (
            f"{len(topic_items)} selected post"
            f"{'' if len(topic_items) == 1 else 's'} covering {coverage}. "
            f"Top score {top_score}."
        )

    return summaries


def _summarize_text(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        summary = text
    else:
        summary = " ".join(words[:max_words]).rstrip(".,;:!?") + "..."

    return f"Summary: {summary}"
