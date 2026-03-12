import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.cli import main
from src.core.pipeline import LlmSettings, run_pipeline
from src.memory.store import ResearchMemoryStore


class MemoryTests(unittest.TestCase):
    def test_memory_initialization_creates_default_json_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = ResearchMemoryStore(Path(tmp_dir) / "memory")

            snapshot = store.load()

            self.assertEqual(snapshot.warnings, ())
            self.assertTrue(store.path.exists())

            payload = json.loads(store.path.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], 1)
            self.assertIn("researchops", payload["priority_authors"])
            self.assertEqual(payload["topic_history"], {})
            self.assertEqual(payload["recent_digests"], [])

    def test_recurring_topic_detection_uses_prior_successful_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = ResearchMemoryStore(Path(tmp_dir) / "memory")
            first_snapshot = store.load()
            first_result = run_pipeline(
                [
                    {
                        "id": "1",
                        "author": "observer",
                        "text": "Evaluation teams improved inference latency with cached embeddings and better benchmark fixtures.",
                        "created_at": "2026-03-10",
                    }
                ],
                llm_settings=LlmSettings(enabled=False),
                priority_authors=first_snapshot.priority_authors,
                memory_snapshot=first_snapshot,
            )

            self.assertEqual(first_result.topic_memory["ai"].label, "new topic")
            self.assertEqual(
                store.record_digest(
                    snapshot=first_snapshot,
                    result=first_result,
                    source_path="data/sample_posts.json",
                    output_path="output/first.md",
                    total_posts=1,
                ),
                (),
            )

            second_snapshot = store.load()
            second_result = run_pipeline(
                [
                    {
                        "id": "2",
                        "author": "observer",
                        "text": "Inference teams expanded model evaluation coverage with fresh embeddings and deterministic benchmarks.",
                        "created_at": "2026-03-11",
                    }
                ],
                llm_settings=LlmSettings(enabled=False),
                priority_authors=second_snapshot.priority_authors,
                memory_snapshot=second_snapshot,
            )

            self.assertEqual(second_result.topic_memory["ai"].label, "recurring topic")
            self.assertEqual(second_result.topic_memory["ai"].prior_digest_count, 1)

    def test_priority_author_detection_uses_memory_authors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = ResearchMemoryStore(Path(tmp_dir) / "memory")
            snapshot = store.load()
            payload = json.loads(store.path.read_text(encoding="utf-8"))
            payload["priority_authors"].append("alpha")
            store.path.write_text(json.dumps(payload), encoding="utf-8")

            snapshot = store.load()
            result = run_pipeline(
                [
                    {
                        "id": "1",
                        "author": "@Alpha",
                        "text": "Local pipeline tests validate adapter changes without touching external APIs during digest work.",
                        "created_at": "2026-03-10",
                    }
                ],
                llm_settings=LlmSettings(enabled=False),
                priority_authors=snapshot.priority_authors,
                memory_snapshot=snapshot,
            )

            self.assertEqual(result.items[0].memory_labels, ("priority author",))
            self.assertIn("priority_author=yes", result.items[0].why_selected or "")

    def test_cli_gracefully_handles_invalid_memory_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "digest.md"
            memory_dir = Path(tmp_dir) / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            memory_path = memory_dir / "research_memory.json"
            memory_path.write_text("{invalid json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.dict(os.environ, {}, clear=True):
                with redirect_stdout(stdout), redirect_stderr(stderr):
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
            self.assertIn("Memory warning:", stderr.getvalue())

            payload = json.loads(memory_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], 1)
            self.assertIn("topic_history", payload)


if __name__ == "__main__":
    unittest.main()
