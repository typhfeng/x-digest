from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.adapters.base import (
    RawPost,
    SourceAdapter,
    SourceConfigurationError,
    SourceDataError,
    SourceLoadResult,
    SourceRequest,
)


class ArchiveSourceAdapter(SourceAdapter):
    """Load posts from realistic archive exports into the raw post contract."""

    name = "archive"
    description = "Load posts from an imported archive export."

    def load(self, request: SourceRequest) -> SourceLoadResult:
        if request.input_path is None:
            raise SourceConfigurationError(
                "Source 'archive' requires --input <path-to-archive-json>."
            )

        input_path = Path(request.input_path)
        payload = self._load_payload(input_path)
        records, default_author = self._extract_records(payload, input_path)

        return SourceLoadResult(
            posts=[
                self._normalize_record(record, index=index, default_author=default_author)
                for index, record in enumerate(records)
            ],
            source_label=str(input_path),
        )

    def _load_payload(self, input_path: Path) -> Any:
        try:
            with input_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            raise SourceConfigurationError(
                f"Source 'archive' could not find input file: {input_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SourceDataError(
                f"Source 'archive' could not parse JSON from {input_path}: {exc.msg}"
            ) from exc

    def _extract_records(
        self,
        payload: Any,
        input_path: Path,
    ) -> tuple[list[Any], str | None]:
        if isinstance(payload, list):
            return payload, None

        if not isinstance(payload, dict):
            raise SourceDataError(
                f"Source 'archive' expected a JSON list or object in {input_path}"
            )

        default_author = _extract_default_author(payload)
        for key in ("tweets", "posts", "items", "entries"):
            records = payload.get(key)
            if records is None:
                continue
            if not isinstance(records, list):
                raise SourceDataError(
                    f"Source 'archive' expected '{key}' to be a list in {input_path}"
                )
            return records, default_author

        raise SourceDataError(
            "Source 'archive' expected a list of records or an object containing "
            "'tweets', 'posts', 'items', or 'entries'."
        )

    def _normalize_record(
        self,
        record: Any,
        *,
        index: int,
        default_author: str | None,
    ) -> RawPost:
        payload = _unwrap_archive_record(record, index)
        post_id = _coerce_string(payload.get("id") or payload.get("tweet_id"))
        author = (
            _coerce_string(
                payload.get("author")
                or payload.get("username")
                or payload.get("screen_name")
            )
            or default_author
        )
        text = _coerce_string(payload.get("text") or payload.get("full_text"))

        if not post_id:
            raise SourceDataError(
                f"Archive record at index {index} is missing 'id' or 'tweet_id'."
            )
        if not author:
            raise SourceDataError(
                "Archive record at index "
                f"{index} is missing 'author', 'username', or 'screen_name'."
            )
        if not text:
            raise SourceDataError(
                f"Archive record at index {index} is missing 'text' or 'full_text'."
            )

        created_at = _normalize_created_at(payload.get("created_at"))
        normalized: RawPost = {
            "id": post_id,
            "author": author.lstrip("@"),
            "text": text,
        }
        title = _coerce_string(payload.get("title"))
        url = _coerce_string(payload.get("url"))
        if title:
            normalized["title"] = title
        if url:
            normalized["url"] = url
        if created_at:
            normalized["created_at"] = created_at

        metadata = _build_metadata(payload, created_at=created_at)
        if metadata:
            normalized["metadata"] = metadata

        return normalized


def _unwrap_archive_record(record: Any, index: int) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise SourceDataError(f"Archive record at index {index} must be an object.")

    for key in ("tweet", "post", "status"):
        nested = record.get(key)
        if nested is None:
            continue
        if not isinstance(nested, dict):
            raise SourceDataError(
                f"Archive record at index {index} has a non-object '{key}' field."
            )
        payload = dict(nested)
        wrapper_metadata = {
            wrapper_key: wrapper_value
            for wrapper_key, wrapper_value in record.items()
            if wrapper_key != key
        }
        if wrapper_metadata:
            payload["_archive_wrapper"] = wrapper_metadata
        return payload

    return dict(record)


def _extract_default_author(payload: dict[str, Any]) -> str | None:
    for key in ("author", "username", "screen_name"):
        value = _coerce_string(payload.get(key))
        if value:
            return value.lstrip("@")

    for key in ("account", "profile", "user"):
        nested = payload.get(key)
        if not isinstance(nested, dict):
            continue
        for nested_key in ("author", "username", "screen_name"):
            value = _coerce_string(nested.get(nested_key))
            if value:
                return value.lstrip("@")

    return None


def _normalize_created_at(value: Any) -> str | None:
    created_at = _coerce_string(value)
    if not created_at:
        return None

    for parser in (_parse_iso_datetime, _parse_x_datetime):
        parsed = parser(created_at)
        if parsed is not None:
            return parsed

    return created_at


def _parse_iso_datetime(value: str) -> str | None:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.isoformat()


def _parse_x_datetime(value: str) -> str | None:
    try:
        parsed = datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return None
    return parsed.astimezone(UTC).isoformat()


def _build_metadata(
    payload: dict[str, Any],
    *,
    created_at: str | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if created_at and payload.get("created_at") not in (None, created_at):
        metadata["original_created_at"] = payload.get("created_at")

    for key in (
        "reply_to",
        "quoted_post_id",
        "thread_id",
        "conversation_id",
        "metrics",
    ):
        value = payload.get(key)
        if value is not None:
            metadata[key] = value

    wrapper = payload.get("_archive_wrapper")
    if isinstance(wrapper, dict) and wrapper:
        metadata["archive_wrapper"] = wrapper

    extra_fields = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "id",
            "tweet_id",
            "author",
            "username",
            "screen_name",
            "text",
            "full_text",
            "title",
            "url",
            "created_at",
            "reply_to",
            "quoted_post_id",
            "thread_id",
            "conversation_id",
            "metrics",
            "_archive_wrapper",
        }
        and value is not None
    }
    if extra_fields:
        metadata["extra_fields"] = extra_fields

    return metadata


def _coerce_string(value: Any) -> str | None:
    if value is None:
        return None

    normalized = " ".join(str(value).split())
    return normalized or None


ADAPTER = ArchiveSourceAdapter()
