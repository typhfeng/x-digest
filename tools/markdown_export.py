"""Compatibility wrapper for the markdown exporter used in phase 1."""

from pathlib import Path

from src.adapters.markdown_export import export_digest
from src.models.digest import PipelineResult


def export(
    result: PipelineResult,
    *,
    output_path: str | Path,
    source_path: str | Path,
    total_posts: int,
) -> Path:
    return export_digest(
        result,
        output_path=output_path,
        source_path=source_path,
        total_posts=total_posts,
    )
