from __future__ import annotations

import re

from src.models.post import Post

WORD_RE = re.compile(r"\b[\w'-]+\b")


def filter_posts(posts: list[Post], *, min_words: int = 6) -> list[Post]:
    """Keep substantive, unique posts."""
    selected: list[Post] = []
    seen_texts: set[str] = set()

    for post in posts:
        normalized_text = post.text.casefold()
        word_count = count_words(post.text)

        if word_count < min_words:
            continue
        if normalized_text in seen_texts:
            continue

        selected.append(post)
        seen_texts.add(normalized_text)

    return selected


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))
