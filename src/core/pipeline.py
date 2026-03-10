"""Core pipeline implementation for the phase-1 local MVP."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from src.models.post import Post

WORD_RE = re.compile(r"\b[\w'-]+\b")


@dataclass(frozen=True, slots=True)
class DigestItem:
    """A filtered post paired with its deterministic summary."""

    post: Post
    summary: str


def normalize_posts(raw_posts: list[dict[str, Any]]) -> list[Post]:
    """Convert loose JSON records into normalized Post objects."""
    normalized: list[Post] = []

    for index, raw_post in enumerate(raw_posts):
        if not isinstance(raw_post, dict):
            raise ValueError(f"Post at index {index} must be an object")

        post_id = str(raw_post.get("id", "")).strip()
        author = str(raw_post.get("author", "")).strip().lstrip("@")
        text = _collapse_whitespace(str(raw_post.get("text", "")))
        url = _normalize_optional(raw_post.get("url"))
        created_at = _normalize_optional(raw_post.get("created_at"))

        if not post_id:
            raise ValueError(f"Post at index {index} is missing an id")
        if not author:
            raise ValueError(f"Post {post_id} is missing an author")
        if not text:
            raise ValueError(f"Post {post_id} is missing text")

        normalized.append(
            Post(
                id=post_id,
                author=author,
                text=text,
                url=url,
                created_at=created_at,
            )
        )

    return normalized


def filter_posts(posts: list[Post], *, min_words: int = 6) -> list[Post]:
    """Keep substantive, unique posts."""
    selected: list[Post] = []
    seen_texts: set[str] = set()

    for post in posts:
        normalized_text = post.text.casefold()
        word_count = len(WORD_RE.findall(post.text))

        if word_count < min_words:
            continue
        if normalized_text in seen_texts:
            continue

        selected.append(post)
        seen_texts.add(normalized_text)

    return selected


def summarize_posts(posts: list[Post], *, max_words: int = 18) -> list[DigestItem]:
    """Create deterministic one-line summaries from filtered posts."""
    return [DigestItem(post=post, summary=_summarize_text(post.text, max_words)) for post in posts]


def run_pipeline(raw_posts: list[dict[str, Any]], *, min_words: int = 6) -> list[DigestItem]:
    """Run ingest -> normalize -> filter -> summarize for local JSON input."""
    normalized = normalize_posts(raw_posts)
    filtered = filter_posts(normalized, min_words=min_words)
    return summarize_posts(filtered)


def _summarize_text(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        summary = text
    else:
        summary = " ".join(words[:max_words]).rstrip(".,;:!?") + "..."

    return f"Summary: {summary}"


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalize_optional(value: Any) -> str | None:
    if value is None:
        return None

    normalized = _collapse_whitespace(str(value))
    return normalized or None
