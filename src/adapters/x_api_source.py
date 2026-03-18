from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from src.adapters.base import (
    RawPost,
    SourceAdapter,
    SourceConfigurationError,
    SourceDataError,
    SourceLoadResult,
    SourceRequest,
)

DEFAULT_BASE_URL = "https://api.x.com/2"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_RESULTS = 25
DEFAULT_MAX_PAGES = 1
MAX_PAGE_SIZE = 100
MAX_PAGES = 20
DEFAULT_TWEET_FIELDS = (
    "id",
    "text",
    "author_id",
    "created_at",
    "conversation_id",
    "lang",
    "public_metrics",
    "referenced_tweets",
)
DEFAULT_EXPANSIONS = ("author_id",)
DEFAULT_USER_FIELDS = ("id", "username", "name")


@dataclass(frozen=True)
class XApiRequestConfig:
    mode: str
    query: str | None
    user_id: str | None
    max_results: int
    max_pages: int
    start_time: str | None
    end_time: str | None
    since_id: str | None
    until_id: str | None
    exclude: tuple[str, ...]
    base_url: str
    timeout_seconds: int


class XApiSourceAdapter(SourceAdapter):
    """Load posts from the X API v2 with a local JSON request configuration."""

    name = "x_api"
    description = "Load posts from the X API."

    def load(self, request: SourceRequest) -> SourceLoadResult:
        if request.input_path is None:
            raise SourceConfigurationError(
                "Source 'x_api' requires --input <path-to-request-json>."
            )

        input_path = Path(request.input_path)
        payload = self._load_config_payload(input_path)
        config = self._parse_request_config(payload, input_path)
        bearer_token = self._load_bearer_token()

        posts = self._load_posts_from_api(config, bearer_token)
        if not posts:
            raise SourceDataError(
                "Source 'x_api' returned no posts for the provided request."
            )

        source_label = self._build_source_label(config)
        return SourceLoadResult(posts=posts, source_label=source_label)

    def _load_config_payload(self, input_path: Path) -> Any:
        try:
            with input_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            raise SourceConfigurationError(
                f"Source 'x_api' could not find input file: {input_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SourceDataError(
                f"Source 'x_api' could not parse JSON from {input_path}: {exc.msg}"
            ) from exc

    def _parse_request_config(self, payload: Any, input_path: Path) -> XApiRequestConfig:
        if not isinstance(payload, dict):
            raise SourceDataError(
                f"Source 'x_api' expected a JSON object in {input_path}"
            )

        mode = _coerce_string(payload.get("mode"))
        if mode is None:
            raise SourceConfigurationError(
                "Source 'x_api' request config must define 'mode' "
                "as 'recent_search' or 'user_tweets'."
            )
        mode = mode.casefold()
        if mode not in {"recent_search", "user_tweets"}:
            raise SourceConfigurationError(
                "Source 'x_api' request config has unsupported mode "
                f"'{mode}'. Use 'recent_search' or 'user_tweets'."
            )

        query = _coerce_string(payload.get("query"))
        user_id = _coerce_string(payload.get("user_id"))
        if mode == "recent_search" and not query:
            raise SourceConfigurationError(
                "Source 'x_api' mode 'recent_search' requires 'query'."
            )
        if mode == "user_tweets" and not user_id:
            raise SourceConfigurationError(
                "Source 'x_api' mode 'user_tweets' requires 'user_id'."
            )

        max_results = _parse_bounded_int(
            payload.get("max_results"),
            field_name="max_results",
            default=DEFAULT_MAX_RESULTS,
            minimum=1,
            maximum=MAX_PAGE_SIZE,
        )
        max_pages = _parse_bounded_int(
            payload.get("max_pages"),
            field_name="max_pages",
            default=DEFAULT_MAX_PAGES,
            minimum=1,
            maximum=MAX_PAGES,
        )
        timeout_seconds = _parse_bounded_int(
            payload.get("timeout_seconds"),
            field_name="timeout_seconds",
            default=self._load_timeout_from_env(),
            minimum=1,
            maximum=120,
        )
        exclude = _parse_exclude_values(payload.get("exclude"))

        base_url = _coerce_string(payload.get("base_url")) or _coerce_string(
            os.getenv("X_DIGEST_X_API_BASE_URL")
        )
        if not base_url:
            base_url = DEFAULT_BASE_URL

        return XApiRequestConfig(
            mode=mode,
            query=query,
            user_id=user_id,
            max_results=max_results,
            max_pages=max_pages,
            start_time=_coerce_string(payload.get("start_time")),
            end_time=_coerce_string(payload.get("end_time")),
            since_id=_coerce_string(payload.get("since_id")),
            until_id=_coerce_string(payload.get("until_id")),
            exclude=exclude,
            base_url=base_url.rstrip("/"),
            timeout_seconds=timeout_seconds,
        )

    def _load_bearer_token(self) -> str:
        token = _coerce_string(os.getenv("X_DIGEST_X_API_BEARER_TOKEN")) or _coerce_string(
            os.getenv("X_API_BEARER_TOKEN")
        )
        if not token:
            raise SourceConfigurationError(
                "Source 'x_api' requires environment variable "
                "X_DIGEST_X_API_BEARER_TOKEN."
            )
        return token

    def _load_timeout_from_env(self) -> int:
        raw_value = _coerce_string(os.getenv("X_DIGEST_X_API_TIMEOUT"))
        if raw_value is None:
            return DEFAULT_TIMEOUT_SECONDS
        return _parse_bounded_int(
            raw_value,
            field_name="X_DIGEST_X_API_TIMEOUT",
            default=DEFAULT_TIMEOUT_SECONDS,
            minimum=1,
            maximum=120,
        )

    def _load_posts_from_api(
        self,
        config: XApiRequestConfig,
        bearer_token: str,
    ) -> list[RawPost]:
        endpoint_path, pagination_param, params = _build_endpoint_request(config)
        seen_ids: set[str] = set()
        posts: list[RawPost] = []
        next_token: str | None = None

        for _ in range(config.max_pages):
            page_params = dict(params)
            if next_token:
                page_params[pagination_param] = next_token
            response = _request_json(
                base_url=config.base_url,
                endpoint_path=endpoint_path,
                params=page_params,
                bearer_token=bearer_token,
                timeout_seconds=config.timeout_seconds,
            )

            users_by_id = _build_user_lookup(response.get("includes"))
            page_data = response.get("data")
            if page_data is None:
                break
            if not isinstance(page_data, list):
                raise SourceDataError(
                    "Source 'x_api' expected response field 'data' to be a list."
                )

            for index, tweet in enumerate(page_data):
                normalized = _normalize_tweet(tweet, users_by_id=users_by_id, index=index)
                post_id = str(normalized["id"])
                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                posts.append(normalized)

            next_token = _extract_next_token(response.get("meta"))
            if not next_token:
                break

        return posts

    def _build_source_label(self, config: XApiRequestConfig) -> str:
        if config.mode == "recent_search":
            assert config.query is not None
            return f"x_api:recent_search:{_summarize_label_value(config.query)}"
        assert config.user_id is not None
        return f"x_api:user_tweets:{config.user_id}"


ADAPTER = XApiSourceAdapter()


def _build_endpoint_request(
    config: XApiRequestConfig,
) -> tuple[str, str, dict[str, str]]:
    params: dict[str, str] = {
        "max_results": str(config.max_results),
        "tweet.fields": ",".join(DEFAULT_TWEET_FIELDS),
        "expansions": ",".join(DEFAULT_EXPANSIONS),
        "user.fields": ",".join(DEFAULT_USER_FIELDS),
    }
    if config.start_time:
        params["start_time"] = config.start_time
    if config.end_time:
        params["end_time"] = config.end_time
    if config.since_id:
        params["since_id"] = config.since_id
    if config.until_id:
        params["until_id"] = config.until_id

    if config.mode == "recent_search":
        assert config.query is not None
        params["query"] = config.query
        return "/tweets/search/recent", "next_token", params

    assert config.user_id is not None
    if config.exclude:
        params["exclude"] = ",".join(config.exclude)
    return f"/users/{config.user_id}/tweets", "pagination_token", params


def _request_json(
    *,
    base_url: str,
    endpoint_path: str,
    params: dict[str, str],
    bearer_token: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    query = urllib_parse.urlencode(params)
    request_url = f"{base_url}{endpoint_path}"
    if query:
        request_url = f"{request_url}?{query}"
    request = urllib_request.Request(
        request_url,
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "User-Agent": "x-digest/phase7a",
        },
        method="GET",
    )

    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        raise SourceDataError(
            "Source 'x_api' request failed "
            f"(HTTP {exc.code}): {_read_http_error_detail(exc)}"
        ) from exc
    except urllib_error.URLError as exc:
        raise SourceConfigurationError(
            f"Source 'x_api' request failed: {exc.reason}"
        ) from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise SourceDataError(
            f"Source 'x_api' returned invalid JSON: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise SourceDataError("Source 'x_api' expected a JSON object response.")
    return payload


def _build_user_lookup(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    users = value.get("users")
    if not isinstance(users, list):
        return {}

    users_by_id: dict[str, str] = {}
    for user in users:
        if not isinstance(user, dict):
            continue
        user_id = _coerce_string(user.get("id"))
        username = _coerce_string(user.get("username"))
        if user_id and username:
            users_by_id[user_id] = username.lstrip("@")
    return users_by_id


def _normalize_tweet(
    value: Any,
    *,
    users_by_id: dict[str, str],
    index: int,
) -> RawPost:
    if not isinstance(value, dict):
        raise SourceDataError(
            f"Source 'x_api' expected tweet at index {index} to be an object."
        )

    post_id = _coerce_string(value.get("id"))
    text = _coerce_string(value.get("text"))
    author_id = _coerce_string(value.get("author_id"))
    author = (
        _coerce_string(value.get("author"))
        or _coerce_string(value.get("username"))
        or (users_by_id.get(author_id) if author_id else None)
        or author_id
    )
    created_at = _coerce_string(value.get("created_at"))

    if not post_id:
        raise SourceDataError(f"Source 'x_api' tweet at index {index} is missing 'id'.")
    if not author:
        raise SourceDataError(
            f"Source 'x_api' tweet {post_id} is missing author data."
        )
    if not text:
        raise SourceDataError(f"Source 'x_api' tweet {post_id} is missing 'text'.")

    author_handle = author.lstrip("@")
    normalized: RawPost = {
        "id": post_id,
        "author": author_handle,
        "text": text,
    }
    if created_at:
        normalized["created_at"] = created_at

    if author_id and author_handle != author_id:
        normalized["url"] = f"https://x.com/{author_handle}/status/{post_id}"

    metadata: dict[str, Any] = {}
    for key in (
        "author_id",
        "conversation_id",
        "lang",
        "public_metrics",
        "referenced_tweets",
        "entities",
        "possibly_sensitive",
    ):
        field_value = value.get(key)
        if field_value is not None:
            metadata[key] = field_value
    if metadata:
        normalized["metadata"] = metadata

    return normalized


def _extract_next_token(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    return _coerce_string(value.get("next_token"))


def _read_http_error_detail(error: urllib_error.HTTPError) -> str:
    try:
        body = error.read().decode("utf-8", errors="replace")
    except OSError:
        body = str(error.reason)
    if not body:
        body = str(error.reason)
    return " ".join(body.split())[:300]


def _parse_bounded_int(
    value: Any,
    *,
    field_name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    if value is None:
        return default
    try:
        parsed = int(str(value))
    except ValueError as exc:
        raise SourceConfigurationError(
            f"Source 'x_api' field '{field_name}' must be an integer."
        ) from exc
    if parsed < minimum or parsed > maximum:
        raise SourceConfigurationError(
            "Source 'x_api' field "
            f"'{field_name}' must be between {minimum} and {maximum}."
        )
    return parsed


def _parse_exclude_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise SourceConfigurationError(
            "Source 'x_api' field 'exclude' must be a list of strings."
        )
    parsed = tuple(
        item.casefold()
        for item in (_coerce_string(item) for item in value)
        if item is not None
    )
    allowed = {"replies", "retweets"}
    invalid = sorted(set(parsed) - allowed)
    if invalid:
        raise SourceConfigurationError(
            "Source 'x_api' field 'exclude' supports only "
            f"{', '.join(sorted(allowed))}; got {', '.join(invalid)}."
        )
    return parsed


def _summarize_label_value(value: str) -> str:
    compact = " ".join(value.split())
    if len(compact) <= 60:
        return compact
    return f"{compact[:57]}..."


def _coerce_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    return normalized or None
