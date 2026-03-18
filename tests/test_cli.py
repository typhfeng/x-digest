import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.cli import main


class _FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class CliTests(unittest.TestCase):
    def test_cli_writes_markdown_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "digest.md"
            memory_dir = Path(tmp_dir) / "memory"
            stdout = io.StringIO()

            with patch.dict(os.environ, {}, clear=True):
                with redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "--input",
                            "data/sample_posts.json",
                            "--output",
                            str(output_path),
                            "--memory-dir",
                            str(memory_dir),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# X Digest", content)
            self.assertIn("Digest Date: 2026-03-10", content)
            self.assertIn("Source Path: `data/sample_posts.json`", content)
            self.assertIn("Selected vs Total: 3 / 5", content)
            self.assertIn("Key Topics:", content)
            self.assertIn("## ai", content)
            self.assertIn("## software", content)
            self.assertIn("Memory: new topic", content)
            self.assertIn("- Score:", content)
            self.assertIn("- Summary:", content)
            self.assertNotIn("- Summary: Summary:", content)
            self.assertIn("Why selected:", content)
            self.assertIn("- Memory: priority author", content)
            self.assertIn("@researchops", content)
            self.assertNotIn("gm", content)
            self.assertIn("Wrote digest to", stdout.getvalue())

    def test_cli_accepts_explicit_json_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "digest.md"
            memory_dir = Path(tmp_dir) / "memory"

            with patch.dict(os.environ, {}, clear=True):
                exit_code = main(
                    [
                        "--source",
                        "json",
                        "--input",
                        "data/sample_posts.json",
                        "--output",
                        str(output_path),
                        "--memory-dir",
                        str(memory_dir),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())

    def test_cli_accepts_archive_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "archive_digest.md"
            memory_dir = Path(tmp_dir) / "memory"
            stdout = io.StringIO()

            with patch.dict(os.environ, {}, clear=True):
                with redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "--source",
                            "archive",
                            "--input",
                            "data/sample_archive.json",
                            "--output",
                            str(output_path),
                            "--memory-dir",
                            str(memory_dir),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("Source Path: `data/sample_archive.json`", content)
            self.assertIn("Selected vs Total: 3 / 5", content)
            self.assertIn("## ai", content)
            self.assertIn("## software", content)
            self.assertIn("@researchops", content)
            self.assertIn("@signalboost", content)
            self.assertIn("Wrote digest to", stdout.getvalue())

    def test_cli_accepts_x_api_source_with_mocked_http(self) -> None:
        request_payload = {
            "mode": "recent_search",
            "query": "from:researchops -is:retweet",
            "max_results": 10,
            "max_pages": 1,
        }
        api_payload = {
            "data": [
                {
                    "id": "101",
                    "text": "Deterministic adapter boundaries help keep ranking changes isolated from external data loading paths.",
                    "author_id": "u1",
                    "created_at": "2026-03-17T10:00:00Z",
                    "public_metrics": {"like_count": 4},
                }
            ],
            "includes": {
                "users": [{"id": "u1", "username": "researchops"}],
            },
            "meta": {},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            request_path = Path(tmp_dir) / "x_request.json"
            output_path = Path(tmp_dir) / "x_digest.md"
            memory_dir = Path(tmp_dir) / "memory"
            request_path.write_text(json.dumps(request_payload), encoding="utf-8")

            with patch.dict(
                os.environ,
                {"X_DIGEST_X_API_BEARER_TOKEN": "token-value"},
                clear=True,
            ):
                with patch(
                    "src.adapters.x_api_source.urllib_request.urlopen",
                    return_value=_FakeHttpResponse(api_payload),
                ):
                    exit_code = main(
                        [
                            "--source",
                            "x_api",
                            "--input",
                            str(request_path),
                            "--output",
                            str(output_path),
                            "--memory-dir",
                            str(memory_dir),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("Source Path: `x_api:recent_search:from:researchops -is:retweet`", content)
            self.assertIn("@researchops", content)

    def test_cli_applies_time_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "digest.md"
            memory_dir = Path(tmp_dir) / "memory"

            with patch.dict(os.environ, {}, clear=True):
                exit_code = main(
                    [
                        "--source",
                        "json",
                        "--input",
                        "data/sample_posts.json",
                        "--output",
                        str(output_path),
                        "--memory-dir",
                        str(memory_dir),
                        "--since",
                        "2026-03-10",
                    ]
                )

            self.assertEqual(exit_code, 0)
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("Selected vs Total: 1 / 5", content)
            self.assertIn("@researchops", content)
            self.assertNotIn("@infrawatch", content)
            self.assertNotIn("@signalboost", content)

    def test_cli_reports_invalid_time_window(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(
                [
                    "--source",
                    "json",
                    "--input",
                    "data/sample_posts.json",
                    "--since",
                    "2026-03-11",
                    "--until",
                    "2026-03-10",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("Pipeline error:", stderr.getvalue())
        self.assertIn("--since must be earlier than or equal to --until", stderr.getvalue())

    def test_cli_reports_placeholder_source_errors(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["--source", "scraping"])

        self.assertEqual(exit_code, 2)
        self.assertIn("Source error:", stderr.getvalue())
        self.assertIn("not implemented yet", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
