from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.rank import DEFAULT_PRIORITY_AUTHORS
from src.memory.models import DigestMetadataRecord, ResearchMemorySnapshot, TopicHistoryRecord
from src.memory.service import resolve_digest_date, resolve_digest_topics
from src.models.digest import PipelineResult

MEMORY_FILENAME = "research_memory.json"
MEMORY_SCHEMA_VERSION = 1


class ResearchMemoryStore:
    """JSON-backed local storage for lightweight cross-run research memory."""

    def __init__(
        self,
        root_dir: str | Path,
        *,
        filename: str = MEMORY_FILENAME,
        recent_digest_limit: int = 10,
    ) -> None:
        self._root_dir = Path(root_dir)
        self._path = self._root_dir / filename
        self._recent_digest_limit = recent_digest_limit

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> ResearchMemorySnapshot:
        """Load memory from disk, initializing a default file when missing."""
        default_payload = self._default_payload()

        try:
            self._root_dir.mkdir(parents=True, exist_ok=True)
            if not self._path.exists():
                self._write_payload(default_payload)
                return self._snapshot_from_payload(default_payload)

            payload = json.loads(self._path.read_text(encoding="utf-8"))
            return self._snapshot_from_payload(payload)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._empty_snapshot(
                warnings=(
                    f"Research memory unavailable; using empty memory. {exc}",
                )
            )

    def record_digest(
        self,
        *,
        snapshot: ResearchMemorySnapshot,
        result: PipelineResult,
        source_path: str | Path,
        output_path: str | Path,
        total_posts: int,
    ) -> tuple[str, ...]:
        """Persist topic history and recent digest metadata after a successful export."""
        topic_history = dict(snapshot.topic_history)
        digest_date = resolve_digest_date(result)
        topics = resolve_digest_topics(result)

        for topic in topics:
            previous = topic_history.get(topic, TopicHistoryRecord())
            topic_history[topic] = TopicHistoryRecord(
                digest_count=previous.digest_count + 1,
                first_seen_digest_date=_resolve_first_seen(previous, digest_date),
                last_seen_digest_date=_resolve_last_seen(previous, digest_date),
            )

        recent_digest = DigestMetadataRecord(
            digest_date=digest_date,
            source_path=str(source_path),
            output_path=str(output_path),
            selected_count=len(result.items),
            total_posts=total_posts,
            topics=topics,
        )
        updated_snapshot = ResearchMemorySnapshot(
            priority_authors=snapshot.priority_authors,
            topic_history={topic: topic_history[topic] for topic in sorted(topic_history)},
            recent_digests=(recent_digest, *snapshot.recent_digests)[: self._recent_digest_limit],
        )

        try:
            self._root_dir.mkdir(parents=True, exist_ok=True)
            self._write_payload(self._payload_from_snapshot(updated_snapshot))
            return ()
        except OSError as exc:
            return (f"Research memory update failed: {exc}",)

    def _default_payload(self) -> dict[str, Any]:
        return self._payload_from_snapshot(self._empty_snapshot())

    def _empty_snapshot(
        self,
        *,
        warnings: tuple[str, ...] = (),
    ) -> ResearchMemorySnapshot:
        return ResearchMemorySnapshot(
            priority_authors=frozenset(sorted(DEFAULT_PRIORITY_AUTHORS)),
            topic_history={},
            recent_digests=(),
            warnings=warnings,
        )

    def _snapshot_from_payload(self, payload: Any) -> ResearchMemorySnapshot:
        if not isinstance(payload, dict):
            raise ValueError("Memory payload must be a JSON object.")

        version = payload.get("version", MEMORY_SCHEMA_VERSION)
        if version != MEMORY_SCHEMA_VERSION:
            raise ValueError(f"Unsupported memory schema version: {version}")

        priority_authors_raw = payload.get("priority_authors", [])
        if not isinstance(priority_authors_raw, list):
            raise ValueError("priority_authors must be a list.")

        priority_authors = set(DEFAULT_PRIORITY_AUTHORS)
        for author in priority_authors_raw:
            if not isinstance(author, str):
                raise ValueError("priority_authors entries must be strings.")
            normalized = _normalize_author(author)
            if normalized:
                priority_authors.add(normalized)

        topic_history_raw = payload.get("topic_history", {})
        if not isinstance(topic_history_raw, dict):
            raise ValueError("topic_history must be an object.")

        topic_history: dict[str, TopicHistoryRecord] = {}
        for topic, entry in sorted(topic_history_raw.items()):
            if not isinstance(topic, str) or not isinstance(entry, dict):
                raise ValueError("topic_history entries must be objects keyed by topic.")
            digest_count = entry.get("digest_count", 0)
            if not isinstance(digest_count, int) or digest_count < 0:
                raise ValueError("topic_history digest_count must be a non-negative integer.")
            topic_history[topic] = TopicHistoryRecord(
                digest_count=digest_count,
                first_seen_digest_date=_optional_string(
                    entry.get("first_seen_digest_date"),
                    field_name="first_seen_digest_date",
                ),
                last_seen_digest_date=_optional_string(
                    entry.get("last_seen_digest_date"),
                    field_name="last_seen_digest_date",
                ),
            )

        recent_digests_raw = payload.get("recent_digests", [])
        if not isinstance(recent_digests_raw, list):
            raise ValueError("recent_digests must be a list.")

        recent_digests = []
        for entry in recent_digests_raw[: self._recent_digest_limit]:
            if not isinstance(entry, dict):
                raise ValueError("recent_digests entries must be objects.")

            topics = entry.get("topics", [])
            if not isinstance(topics, list) or any(not isinstance(topic, str) for topic in topics):
                raise ValueError("recent_digests topics must be a list of strings.")

            selected_count = entry.get("selected_count", 0)
            total_posts = entry.get("total_posts", 0)
            if not isinstance(selected_count, int) or selected_count < 0:
                raise ValueError("selected_count must be a non-negative integer.")
            if not isinstance(total_posts, int) or total_posts < 0:
                raise ValueError("total_posts must be a non-negative integer.")

            recent_digests.append(
                DigestMetadataRecord(
                    digest_date=_required_string(entry.get("digest_date"), field_name="digest_date"),
                    source_path=_required_string(entry.get("source_path"), field_name="source_path"),
                    output_path=_required_string(entry.get("output_path"), field_name="output_path"),
                    selected_count=selected_count,
                    total_posts=total_posts,
                    topics=tuple(sorted(topics)),
                )
            )

        return ResearchMemorySnapshot(
            priority_authors=frozenset(sorted(priority_authors)),
            topic_history=topic_history,
            recent_digests=tuple(recent_digests),
        )

    def _payload_from_snapshot(self, snapshot: ResearchMemorySnapshot) -> dict[str, Any]:
        return {
            "version": MEMORY_SCHEMA_VERSION,
            "priority_authors": sorted(snapshot.priority_authors),
            "topic_history": {
                topic: {
                    "digest_count": record.digest_count,
                    "first_seen_digest_date": record.first_seen_digest_date,
                    "last_seen_digest_date": record.last_seen_digest_date,
                }
                for topic, record in sorted(snapshot.topic_history.items())
            },
            "recent_digests": [
                {
                    "digest_date": digest.digest_date,
                    "source_path": digest.source_path,
                    "output_path": digest.output_path,
                    "selected_count": digest.selected_count,
                    "total_posts": digest.total_posts,
                    "topics": list(digest.topics),
                }
                for digest in snapshot.recent_digests
            ],
        }

    def _write_payload(self, payload: dict[str, Any]) -> None:
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        temp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        temp_path.write_text(text, encoding="utf-8")
        temp_path.replace(self._path)


def _normalize_author(author: str) -> str:
    return author.strip().lstrip("@").casefold()


def _optional_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null.")
    return value


def _required_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    return value


def _resolve_first_seen(record: TopicHistoryRecord, digest_date: str) -> str | None:
    if record.first_seen_digest_date is not None:
        return record.first_seen_digest_date
    if digest_date == "unknown":
        return None
    return digest_date


def _resolve_last_seen(record: TopicHistoryRecord, digest_date: str) -> str | None:
    if digest_date == "unknown":
        return record.last_seen_digest_date
    return digest_date
