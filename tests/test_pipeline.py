import unittest

from src.core.pipeline import filter_posts, normalize_posts, run_pipeline


class PipelineTests(unittest.TestCase):
    def test_normalize_posts_strips_whitespace_and_author_prefix(self) -> None:
        normalized = normalize_posts(
            [
                {
                    "id": " 42 ",
                    "author": " @example ",
                    "text": "  spaced   text here  ",
                    "url": " https://example.com/post ",
                    "created_at": " 2026-03-10 ",
                }
            ]
        )

        self.assertEqual(normalized[0].id, "42")
        self.assertEqual(normalized[0].author, "example")
        self.assertEqual(normalized[0].text, "spaced text here")
        self.assertEqual(normalized[0].url, "https://example.com/post")
        self.assertEqual(normalized[0].created_at, "2026-03-10")

    def test_filter_posts_removes_short_and_duplicate_posts(self) -> None:
        normalized = normalize_posts(
            [
                {"id": "1", "author": "alpha", "text": "very short"},
                {
                    "id": "2",
                    "author": "beta",
                    "text": "This post has enough words to survive the initial filter pass.",
                },
                {
                    "id": "3",
                    "author": "gamma",
                    "text": "This post has enough words to survive the initial filter pass.",
                },
            ]
        )

        filtered = filter_posts(normalized, min_words=6)

        self.assertEqual([post.id for post in filtered], ["2"])

    def test_run_pipeline_produces_deterministic_summaries(self) -> None:
        items = run_pipeline(
            [
                {
                    "id": "1",
                    "author": "alpha",
                    "text": "Deterministic local fixtures make pipeline tests cheaper to run and easier to debug.",
                }
            ]
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0].summary,
            "Summary: Deterministic local fixtures make pipeline tests cheaper to run and easier to debug.",
        )


if __name__ == "__main__":
    unittest.main()
