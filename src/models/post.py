from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Post:
    """Normalized post model used by the local MVP pipeline."""

    id: str
    author: str
    text: str
    title: str | None = None
    url: str | None = None
    created_at: str | None = None
