from __future__ import annotations

from src.adapters.base import (
    SourceAdapter,
    SourceLoadResult,
    SourceNotImplementedError,
    SourceRequest,
)


class XApiSourceAdapter(SourceAdapter):
    """Placeholder adapter for future X API ingestion."""

    name = "x_api"
    description = "Load posts from the X API."

    def load(self, request: SourceRequest) -> SourceLoadResult:
        raise SourceNotImplementedError(
            "Source 'x_api' is not implemented yet. "
            "Use --source json with --input <local-json-file> for now."
        )


ADAPTER = XApiSourceAdapter()
