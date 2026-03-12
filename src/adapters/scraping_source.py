from __future__ import annotations

from src.adapters.base import (
    SourceAdapter,
    SourceLoadResult,
    SourceNotImplementedError,
    SourceRequest,
)


class ScrapingSourceAdapter(SourceAdapter):
    """Placeholder adapter for future browser or scraping ingestion."""

    name = "scraping"
    description = "Load posts from a browser-assisted or scraping source."

    def load(self, request: SourceRequest) -> SourceLoadResult:
        raise SourceNotImplementedError(
            "Source 'scraping' is not implemented yet. "
            "Brittle scraping is intentionally deferred; use --source json for now."
        )


ADAPTER = ScrapingSourceAdapter()
