from pathlib import Path

from src.core.pipeline import DigestItem


def export_digest(
    items: list[DigestItem],
    output_path: str | Path,
    *,
    source_path: str | Path,
    total_posts: int,
) -> Path:
    """Write a deterministic markdown digest to disk."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# X Digest",
        "",
        f"Source: `{Path(source_path)}`",
        f"Posts read: {total_posts}",
        f"Posts selected: {len(items)}",
        "",
        "## Highlights",
        "",
    ]

    if not items:
        lines.extend(
            [
                "No posts matched the current filter settings.",
                "",
            ]
        )
    else:
        for index, item in enumerate(items, start=1):
            post = item.post
            lines.extend(
                [
                    f"### {index}. @{post.author}",
                    item.summary,
                    "",
                    f"- Date: {post.created_at or 'unknown'}",
                    f"- URL: {post.url or 'n/a'}",
                    f"- Original: {post.text}",
                    "",
                ]
            )

    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination
