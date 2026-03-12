import tempfile
import unittest
from pathlib import Path

from src.adapters.base import SourceNotImplementedError, SourceRequest, UnknownSourceError
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

    def test_placeholder_adapters_fail_clearly(self) -> None:
        for source_name in ("archive", "x_api", "scraping"):
            with self.subTest(source_name=source_name):
                with self.assertRaises(SourceNotImplementedError):
                    get_source_adapter(source_name).load(
                        SourceRequest(input_path=Path("placeholder"))
                    )


if __name__ == "__main__":
    unittest.main()
