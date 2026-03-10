from __future__ import annotations

from collections.abc import Iterable, Sequence

from src.core.filter import count_words
from src.models.digest import ClusteredPost, RankedPost

DEFAULT_PRIORITY_AUTHORS = frozenset(
    {
        "anduril",
        "infrawatch",
        "nasa",
        "researchops",
        "semianalysis",
        "signalboost",
    }
)


def rank_posts(
    posts: Sequence[ClusteredPost],
    *,
    priority_authors: Iterable[str] | None = None,
) -> list[RankedPost]:
    """Assign a deterministic importance score to each clustered post."""
    priority_set = {
        author.strip().lstrip("@").casefold()
        for author in (priority_authors or DEFAULT_PRIORITY_AUTHORS)
    }
    ranked: list[RankedPost] = []

    for entry in posts:
        word_count = count_words(entry.post.text)
        has_url = bool(entry.post.url)
        priority_author = entry.post.author.casefold() in priority_set
        score = score_post(
            topic_match_strength=entry.topic_match_strength,
            word_count=word_count,
            has_url=has_url,
            priority_author=priority_author,
        )

        reasons = [
            f"topic={entry.topic}",
            f"keyword_hits={entry.topic_match_strength}",
            f"words={word_count}",
            f"has_url={'yes' if has_url else 'no'}",
        ]
        if priority_author:
            reasons.append("priority_author=yes")

        ranked.append(
            RankedPost(
                post=entry.post,
                topic=entry.topic,
                score=score,
                tags=entry.tags,
                topic_match_strength=entry.topic_match_strength,
                why_selected="; ".join(reasons),
            )
        )

    return sorted(
        ranked,
        key=lambda item: (-item.score, item.topic, item.post.author.casefold(), item.post.id),
    )


def score_post(
    *,
    topic_match_strength: int,
    word_count: int,
    has_url: bool,
    priority_author: bool,
) -> int:
    """Simple explainable scoring formula for local ranking."""
    bounded_word_count = min(word_count, 30)
    return (
        topic_match_strength * 10
        + bounded_word_count
        + (5 if has_url else 0)
        + (10 if priority_author else 0)
    )
