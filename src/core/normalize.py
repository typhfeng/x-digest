from __future__ import annotations

from typing import Any

from src.models.post import Post


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


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalize_optional(value: Any) -> str | None:
    if value is None:
        return None

    normalized = _collapse_whitespace(str(value))
    return normalized or None
