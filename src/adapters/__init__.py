"""I/O adapters for x-digest."""

from src.adapters.base import (
    SourceAdapter,
    SourceAdapterError,
    SourceConfigurationError,
    SourceDataError,
    SourceLoadResult,
    SourceNotImplementedError,
    SourceRequest,
    UnknownSourceError,
)
from src.adapters.registry import get_source_adapter, list_source_names

__all__ = [
    "SourceAdapter",
    "SourceAdapterError",
    "SourceConfigurationError",
    "SourceDataError",
    "SourceLoadResult",
    "SourceNotImplementedError",
    "SourceRequest",
    "UnknownSourceError",
    "get_source_adapter",
    "list_source_names",
]
