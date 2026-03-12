from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Post:
    """Normalized post model used by the research pipeline."""

    id: str
    author: str
    text: str
    title: str | None = None
    url: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] | None = None
