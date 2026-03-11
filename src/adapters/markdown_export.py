from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from src.models.digest import DigestItem, PipelineResult


def export_digest(
    result: PipelineResult,
    output_path: str | Path,
    *,
    source_path: str | Path,
    total_posts: int,
) -> Path:
    """Write a deterministic markdown digest to disk."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    items = tuple(result.items)
    grouped = _group_by_topic(items)
    digest_date = _resolve_digest_date(items)
    ordered_topics = sorted(
        grouped,
        key=lambda topic: (
            -max(item.score for item in grouped[topic]),
            -len(grouped[topic]),
            topic,
        ),
    )
    key_topics = ", ".join(ordered_topics) if ordered_topics else "none"

    lines = [
        "# X Digest",
        "",
        f"Digest Date: {digest_date}",
        f"Source Path: `{Path(source_path)}`",
        f"Selected vs Total: {len(result.items)} / {total_posts}",
        f"Key Topics: {key_topics}",
        "",
    ]

    if not result.items:
        lines.extend(
            [
                "No posts matched the current filter settings.",
                "",
            ]
        )
    else:
        for topic in ordered_topics:
            topic_items = sorted(
                grouped[topic],
                key=lambda item: (-item.score, item.post.author.casefold(), item.post.id),
            )
            lines.extend(
                [
                    f"## {topic}",
                    "",
                    result.topic_summaries.get(topic, "No topic summary available."),
                    "",
                ]
            )
            for index, item in enumerate(topic_items, start=1):
                post = item.post
                title = _resolve_post_title(post.title, post.text)
                summary = item.summary.removeprefix("Summary: ").strip()
                lines.extend(
                    [
                        f"### {index}. {title}",
                        f"Date: {post.created_at or 'unknown'}",
                        "",
                        f"- Score: {item.score}",
                        f"- Author: @{post.author}",
                        f"- URL: {post.url or 'n/a'}",
                        f"- Why selected: {item.why_selected or 'n/a'}",
                        f"- Tags: {', '.join(item.tags) if item.tags else 'n/a'}",
                        f"- Summary: {summary}",
                        "",
                    ]
                )

    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination


def _group_by_topic(items: Sequence[DigestItem]) -> dict[str, list[DigestItem]]:
    grouped: dict[str, list[DigestItem]] = {}
    for item in items:
        grouped.setdefault(item.topic, []).append(item)
    return grouped


def _resolve_digest_date(items: Sequence[DigestItem]) -> str:
    dates = sorted(item.post.created_at for item in items if item.post.created_at)
    return dates[-1] if dates else "unknown"


def _resolve_post_title(title: str | None, text: str, *, max_words: int = 10) -> str:
    if title:
        return title

    words = text.split()
    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]).rstrip(".,;:!?") + "..."
