from __future__ import annotations

from dataclasses import dataclass, field

from src.models.post import Post


@dataclass(frozen=True, slots=True)
class ClusteredPost:
    """A normalized post paired with a deterministic topic assignment."""

    post: Post
    topic: str
    tags: tuple[str, ...] = ()
    topic_match_strength: int = 0


@dataclass(frozen=True, slots=True)
class RankedPost:
    """A clustered post paired with a deterministic importance score."""

    post: Post
    topic: str
    score: int
    tags: tuple[str, ...] = ()
    topic_match_strength: int = 0
    why_selected: str | None = None


@dataclass(frozen=True, slots=True)
class DigestItem:
    """A ranked post paired with its deterministic summary."""

    post: Post
    topic: str
    score: int
    summary: str
    tags: tuple[str, ...] = ()
    why_selected: str | None = None
    memory_labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TopicMemoryAnnotation:
    """Memory-derived metadata for a topic in the current digest."""

    label: str
    prior_digest_count: int = 0


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Pipeline output used by adapters such as markdown export."""

    items: tuple[DigestItem, ...]
    topic_summaries: dict[str, str]
    topic_memory: dict[str, TopicMemoryAnnotation] = field(default_factory=dict)
