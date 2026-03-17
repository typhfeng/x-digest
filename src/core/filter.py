from __future__ import annotations

import re
from datetime import datetime, timezone

from src.models.post import Post

WORD_RE = re.compile(r"\b[\w'-]+\b")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def filter_posts(
    posts: list[Post],
    *,
    min_words: int = 6,
    since: str | None = None,
    until: str | None = None,
) -> list[Post]:
    """Keep substantive, unique posts."""
    since_dt = _parse_datetime_boundary(since, is_until=False) if since else None
    until_dt = _parse_datetime_boundary(until, is_until=True) if until else None
    if since_dt and until_dt and since_dt > until_dt:
        raise ValueError("--since must be earlier than or equal to --until")

    selected: list[Post] = []
    seen_texts: set[str] = set()

    for post in posts:
        normalized_text = post.text.casefold()
        word_count = count_words(post.text)
        created_at = _parse_post_created_at(post.created_at)

        if word_count < min_words:
            continue
        if since_dt and (created_at is None or created_at < since_dt):
            continue
        if until_dt and (created_at is None or created_at > until_dt):
            continue
        if normalized_text in seen_texts:
            continue

        selected.append(post)
        seen_texts.add(normalized_text)

    return selected


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def _parse_post_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return _to_utc_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _parse_datetime_boundary(value: str, *, is_until: bool) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError("Date boundary cannot be empty")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            "Date boundary must be ISO-8601 (for example: 2026-03-10 or 2026-03-10T12:00:00+00:00)"
        ) from exc

    if is_until and DATE_ONLY_RE.fullmatch(text):
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    return _to_utc_datetime(parsed)


def _to_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
