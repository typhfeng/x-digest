from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.adapters import SourceAdapterError, SourceRequest, get_source_adapter, list_source_names
from src.adapters.markdown_export import export_digest
from src.core.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a markdown digest from supported X-like sources."
    )
    parser.add_argument(
        "--source",
        choices=list_source_names(),
        default="json",
        help="Source adapter to use. Defaults to the local JSON workflow.",
    )
    parser.add_argument(
        "--input",
        default="data/sample_posts.json",
        help="Path or source-specific input reference. Defaults to the sample local JSON fixture.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to the markdown file to write. Defaults to output/<input_stem>_digest.md.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=6,
        help="Minimum word count required for a post to be included.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else Path("output") / f"{input_path.stem}_digest.md"

    try:
        adapter = get_source_adapter(args.source)
        load_result = adapter.load(SourceRequest(input_path=input_path))
    except SourceAdapterError as exc:
        print(f"Source error: {exc}", file=sys.stderr)
        return 2

    raw_posts = load_result.posts
    result = run_pipeline(raw_posts, min_words=args.min_words)
    written_path = export_digest(
        result,
        output_path,
        source_path=load_result.source_label,
        total_posts=len(raw_posts),
    )

    print(f"Wrote digest to {written_path}")
    print(f"Selected {len(result.items)} of {len(raw_posts)} posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
