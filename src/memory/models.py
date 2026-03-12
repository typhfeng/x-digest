from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TopicHistoryRecord:
    """Stored history for a topic across successful digest runs."""

    digest_count: int = 0
    first_seen_digest_date: str | None = None
    last_seen_digest_date: str | None = None


@dataclass(frozen=True, slots=True)
class DigestMetadataRecord:
    """Compact metadata for a recent digest generation."""

    digest_date: str
    source_path: str
    output_path: str
    selected_count: int
    total_posts: int
    topics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResearchMemorySnapshot:
    """In-memory representation of the local research memory store."""

    priority_authors: frozenset[str]
    topic_history: dict[str, TopicHistoryRecord]
    recent_digests: tuple[DigestMetadataRecord, ...]
    warnings: tuple[str, ...] = ()
