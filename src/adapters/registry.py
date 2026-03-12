from __future__ import annotations

from src.adapters.archive_source import ADAPTER as ARCHIVE_SOURCE_ADAPTER
from src.adapters.base import SourceAdapter, UnknownSourceError
from src.adapters.json_source import ADAPTER as JSON_SOURCE_ADAPTER
from src.adapters.scraping_source import ADAPTER as SCRAPING_SOURCE_ADAPTER
from src.adapters.x_api_source import ADAPTER as X_API_SOURCE_ADAPTER

SOURCE_ADAPTERS: dict[str, SourceAdapter] = {
    JSON_SOURCE_ADAPTER.name: JSON_SOURCE_ADAPTER,
    ARCHIVE_SOURCE_ADAPTER.name: ARCHIVE_SOURCE_ADAPTER,
    X_API_SOURCE_ADAPTER.name: X_API_SOURCE_ADAPTER,
    SCRAPING_SOURCE_ADAPTER.name: SCRAPING_SOURCE_ADAPTER,
}


def get_source_adapter(name: str) -> SourceAdapter:
    """Resolve a source adapter by its stable CLI name."""
    adapter = SOURCE_ADAPTERS.get(name.casefold())
    if adapter is None:
        supported = ", ".join(list_source_names())
        raise UnknownSourceError(
            f"Unknown source '{name}'. Supported sources: {supported}."
        )
    return adapter


def list_source_names() -> tuple[str, ...]:
    """Return the registered source names in a stable order."""
    return tuple(SOURCE_ADAPTERS)
