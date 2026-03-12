from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RawPost = dict[str, Any]


class SourceAdapterError(RuntimeError):
    """Base exception for source adapter failures."""


class SourceConfigurationError(SourceAdapterError):
    """Raised when a selected source is missing required configuration."""


class SourceDataError(SourceAdapterError):
    """Raised when a source payload cannot be parsed into raw posts."""


class SourceNotImplementedError(SourceAdapterError):
    """Raised when a placeholder adapter is selected before implementation."""


class UnknownSourceError(SourceAdapterError):
    """Raised when a source name is not registered."""


@dataclass(frozen=True)
class SourceRequest:
    """Input parameters passed from the CLI to a source adapter."""

    input_path: Path | None = None


@dataclass(frozen=True)
class SourceLoadResult:
    """Raw posts plus a display label for downstream reporting."""

    posts: list[RawPost]
    source_label: str


class SourceAdapter(ABC):
    """Contract for all ingest adapters."""

    name: str
    description: str

    @abstractmethod
    def load(self, request: SourceRequest) -> SourceLoadResult:
        """Load raw post objects for the research pipeline."""
