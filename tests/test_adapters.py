import json
import tempfile
import unittest
from pathlib import Path

from src.adapters.base import (
    SourceDataError,
    SourceNotImplementedError,
    SourceRequest,
    UnknownSourceError,
)
from src.core.normalize import normalize_posts
from src.adapters.json_source import load_posts
from src.adapters.registry import get_source_adapter, list_source_names


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

    def test_placeholder_adapters_fail_clearly(self) -> None:
        for source_name in ("x_api", "scraping"):
            with self.subTest(source_name=source_name):
                with self.assertRaises(SourceNotImplementedError):
                    get_source_adapter(source_name).load(
                        SourceRequest(input_path=Path("placeholder"))
                    )


if __name__ == "__main__":
    unittest.main()
