from __future__ import annotations

import json
from pathlib import Path

from src.adapters.base import (
    RawPost,
    SourceAdapter,
    SourceConfigurationError,
    SourceDataError,
    SourceLoadResult,
    SourceRequest,
)


class JsonSourceAdapter(SourceAdapter):
    """Load raw posts from a local JSON file."""

    name = "json"
    description = "Load post objects from a local JSON file."

    def load(self, request: SourceRequest) -> SourceLoadResult:
        if request.input_path is None:
            raise SourceConfigurationError(
                "Source 'json' requires --input <path-to-json-file>."
            )

        input_path = Path(request.input_path)
        try:
            with input_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError as exc:
            raise SourceConfigurationError(
                f"Source 'json' could not find input file: {input_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SourceDataError(
                f"Source 'json' could not parse JSON from {input_path}: {exc.msg}"
            ) from exc

        if not isinstance(payload, list):
            raise SourceDataError(f"Expected a list of posts in {input_path}")

        return SourceLoadResult(
            posts=payload,
            source_label=str(input_path),
        )


def load_posts(path: str | Path) -> list[RawPost]:
    """Backward-compatible helper for local JSON loading."""
    return JsonSourceAdapter().load(SourceRequest(input_path=Path(path))).posts


ADAPTER = JsonSourceAdapter()
