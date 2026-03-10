from __future__ import annotations

import argparse
from pathlib import Path

from src.adapters.json_source import load_posts
from src.adapters.markdown_export import export_digest
from src.core.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a markdown digest from local JSON posts."
    )
    parser.add_argument(
        "--input",
        default="data/sample_posts.json",
        help="Path to a JSON file containing post objects.",
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

    raw_posts = load_posts(input_path)
    result = run_pipeline(raw_posts, min_words=args.min_words)
    written_path = export_digest(
        result,
        output_path,
        source_path=input_path,
        total_posts=len(raw_posts),
    )

    print(f"Wrote digest to {written_path}")
    print(f"Selected {len(result.items)} of {len(raw_posts)} posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
