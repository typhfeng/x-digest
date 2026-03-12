from __future__ import annotations

from src.adapters.base import (
    SourceAdapter,
    SourceLoadResult,
    SourceNotImplementedError,
    SourceRequest,
)


class ArchiveSourceAdapter(SourceAdapter):
    """Placeholder adapter for imported archive ingestion."""

    name = "archive"
    description = "Load posts from an imported archive export."

    def load(self, request: SourceRequest) -> SourceLoadResult:
        raise SourceNotImplementedError(
            "Source 'archive' is not implemented yet. "
            "Use --source json with --input <local-json-file> for now."
        )


ADAPTER = ArchiveSourceAdapter()
