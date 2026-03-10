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
    items = sorted(
        result.items,
        key=lambda item: (item.topic, -item.score, item.post.author.casefold(), item.post.id),
    )
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
        f"Source: `{Path(source_path)}`",
        f"Selected: {len(result.items)} / {total_posts}",
        f"Key Topics: {key_topics}",
        "",
        "## Topics",
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
            topic_items = grouped[topic]
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
                lines.extend(
                    [
                        f"### {index}. @{post.author} ({item.score})",
                        item.summary,
                        "",
                        f"- Why selected: {item.why_selected or 'n/a'}",
                        f"- Tags: {', '.join(item.tags) if item.tags else 'n/a'}",
                        f"- Date: {post.created_at or 'unknown'}",
                        f"- URL: {post.url or 'n/a'}",
                        f"- Original: {post.text}",
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
