import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.cli import main


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

    def test_cli_reports_placeholder_source_errors(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["--source", "archive"])

        self.assertEqual(exit_code, 2)
        self.assertIn("Source error:", stderr.getvalue())
        self.assertIn("not implemented yet", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
