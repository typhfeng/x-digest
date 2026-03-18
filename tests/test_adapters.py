import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.adapters.base import (
    SourceConfigurationError,
    SourceDataError,
    SourceNotImplementedError,
    SourceRequest,
    UnknownSourceError,
)
from src.adapters.json_source import load_posts
from src.adapters.registry import get_source_adapter, list_source_names
from src.core.normalize import normalize_posts


class _FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class AdapterTests(unittest.TestCase):
    def test_adapter_registry_uses_explicit_stable_names(self) -> None:
        self.assertEqual(
            list_source_names(),
            ("json", "archive", "x_api", "scraping"),
        )
        self.assertEqual(get_source_adapter("json").name, "json")
        self.assertEqual(get_source_adapter("archive").name, "archive")
        self.assertEqual(get_source_adapter("x_api").name, "x_api")
        self.assertEqual(get_source_adapter("scraping").name, "scraping")

    def test_unknown_source_raises_helpful_error(self) -> None:
        with self.assertRaisesRegex(
            UnknownSourceError,
            "Supported sources: json, archive, x_api, scraping",
        ):
            get_source_adapter("rss")

    def test_json_source_loads_local_posts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "posts.json"
            input_path.write_text(
                '[{"id":"1","author":"alpha","text":"A local fixture with enough words to be valid."}]',
                encoding="utf-8",
            )

            result = get_source_adapter("json").load(SourceRequest(input_path=input_path))
            loaded = load_posts(input_path)

            self.assertEqual(len(result.posts), 1)
            self.assertEqual(result.posts[0]["author"], "alpha")
            self.assertEqual(result.source_label, str(input_path))
            self.assertEqual(loaded, result.posts)

    def test_archive_source_loads_realistic_wrapped_archive_records(self) -> None:
        archive_payload = {
            "account": {"username": "archiveowner"},
            "tweets": [
                {
                    "tweet": {
                        "id": "101",
                        "full_text": "Evaluation fixtures made inference debugging cheaper for teams shipping local benchmarks.",
                        "created_at": "Wed Mar 11 09:15:00 +0000 2026",
                        "conversation_id": "conv-101",
                        "metrics": {"likes": 4},
                    }
                },
                {
                    "tweet": {
                        "tweet_id": "102",
                        "screen_name": "@signalboost",
                        "text": "Local replay tests help adapter changes land without breaking downstream ranking.",
                        "created_at": "2026-03-10T18:45:00Z",
                        "reply_to": "101",
                        "quoted_post_id": "88",
                        "thread_id": "thread-102",
                        "url": "https://x.com/signalboost/status/102",
                        "metrics": {"likes": 9, "reposts": 2},
                        "client": "web",
                    },
                    "archived_at": "2026-03-11T09:16:00Z",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "archive.json"
            input_path.write_text(json.dumps(archive_payload), encoding="utf-8")

            result = get_source_adapter("archive").load(SourceRequest(input_path=input_path))
            normalized = normalize_posts(result.posts)

            self.assertEqual(len(result.posts), 2)
            self.assertEqual(result.source_label, str(input_path))

            self.assertEqual(result.posts[0]["id"], "101")
            self.assertEqual(result.posts[0]["author"], "archiveowner")
            self.assertEqual(
                result.posts[0]["created_at"],
                "2026-03-11T09:15:00+00:00",
            )
            self.assertEqual(
                result.posts[0]["metadata"],
                {
                    "original_created_at": "Wed Mar 11 09:15:00 +0000 2026",
                    "conversation_id": "conv-101",
                    "metrics": {"likes": 4},
                },
            )

            self.assertEqual(result.posts[1]["id"], "102")
            self.assertEqual(result.posts[1]["author"], "signalboost")
            self.assertEqual(
                result.posts[1]["metadata"]["archive_wrapper"],
                {"archived_at": "2026-03-11T09:16:00Z"},
            )
            self.assertEqual(
                result.posts[1]["metadata"]["extra_fields"],
                {"client": "web"},
            )
            self.assertEqual(normalized[1].metadata, result.posts[1]["metadata"])

    def test_archive_source_fails_clearly_on_invalid_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "invalid_archive.json"
            input_path.write_text('{"tweets": "not-a-list"}', encoding="utf-8")

            with self.assertRaisesRegex(
                SourceDataError,
                "expected 'tweets' to be a list",
            ):
                get_source_adapter("archive").load(SourceRequest(input_path=input_path))

    def test_archive_source_fails_clearly_on_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "missing_fields.json"
            input_path.write_text(
                '{"tweets": [{"tweet": {"id": "101", "created_at": "2026-03-10"}}]}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                SourceDataError,
                "missing 'author', 'username', or 'screen_name'",
            ):
                get_source_adapter("archive").load(SourceRequest(input_path=input_path))

    def test_x_api_source_requires_bearer_token(self) -> None:
        request_config = {
            "mode": "recent_search",
            "query": "from:researchops -is:retweet",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "x_request.json"
            input_path.write_text(json.dumps(request_config), encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(
                    SourceConfigurationError,
                    "X_DIGEST_X_API_BEARER_TOKEN",
                ):
                    get_source_adapter("x_api").load(SourceRequest(input_path=input_path))

    def test_x_api_source_loads_recent_search_and_handles_pagination(self) -> None:
        request_config = {
            "mode": "recent_search",
            "query": "from:researchops -is:retweet",
            "max_results": 2,
            "max_pages": 2,
        }
        page_1 = {
            "data": [
                {
                    "id": "11",
                    "text": "Deterministic inference evaluation lowered regression debugging time for local benchmark loops.",
                    "author_id": "u1",
                    "created_at": "2026-03-17T10:00:00Z",
                    "conversation_id": "11",
                    "lang": "en",
                    "public_metrics": {"like_count": 10},
                },
                {
                    "id": "12",
                    "text": "Teams moved summarization jobs into batched windows to stabilize queue latency.",
                    "author_id": "u2",
                    "created_at": "2026-03-17T11:00:00Z",
                },
            ],
            "includes": {
                "users": [
                    {"id": "u1", "username": "researchops"},
                    {"id": "u2", "username": "signalboost"},
                ]
            },
            "meta": {"next_token": "next-page-token"},
        }
        page_2 = {
            "data": [
                {
                    "id": "12",
                    "text": "Teams moved summarization jobs into batched windows to stabilize queue latency.",
                    "author_id": "u2",
                    "created_at": "2026-03-17T11:00:00Z",
                },
                {
                    "id": "13",
                    "text": "Adapter boundaries let ranking and filtering evolve without API coupling.",
                    "author_id": "u1",
                    "created_at": "2026-03-17T12:00:00Z",
                    "referenced_tweets": [{"type": "replied_to", "id": "11"}],
                },
            ],
            "includes": {
                "users": [
                    {"id": "u1", "username": "researchops"},
                    {"id": "u2", "username": "signalboost"},
                ]
            },
            "meta": {},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "x_request.json"
            input_path.write_text(json.dumps(request_config), encoding="utf-8")

            with patch.dict(
                os.environ,
                {"X_DIGEST_X_API_BEARER_TOKEN": "token-value"},
                clear=True,
            ):
                with patch(
                    "src.adapters.x_api_source.urllib_request.urlopen",
                    side_effect=[_FakeHttpResponse(page_1), _FakeHttpResponse(page_2)],
                ) as mock_urlopen:
                    result = get_source_adapter("x_api").load(
                        SourceRequest(input_path=input_path)
                    )

            self.assertEqual(len(result.posts), 3)
            self.assertEqual(
                [post["id"] for post in result.posts],
                ["11", "12", "13"],
            )
            self.assertEqual(result.posts[0]["author"], "researchops")
            self.assertEqual(
                result.posts[0]["url"],
                "https://x.com/researchops/status/11",
            )
            self.assertEqual(
                result.posts[0]["metadata"]["public_metrics"],
                {"like_count": 10},
            )
            self.assertEqual(result.source_label, "x_api:recent_search:from:researchops -is:retweet")
            self.assertEqual(mock_urlopen.call_count, 2)

            first_url = mock_urlopen.call_args_list[0].args[0].full_url
            second_url = mock_urlopen.call_args_list[1].args[0].full_url
            self.assertIn("/tweets/search/recent", first_url)
            self.assertIn("query=from%3Aresearchops+-is%3Aretweet", first_url)
            self.assertIn("next_token=next-page-token", second_url)

    def test_placeholder_scraping_adapter_fails_clearly(self) -> None:
        with self.assertRaises(SourceNotImplementedError):
            get_source_adapter("scraping").load(SourceRequest(input_path=Path("placeholder")))


if __name__ == "__main__":
    unittest.main()
