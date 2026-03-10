import unittest

from src.core.pipeline import (
    assign_topic,
    cluster_posts,
    filter_posts,
    normalize_posts,
    rank_posts,
    run_pipeline,
)


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

    def test_assign_topic_uses_keyword_map_and_falls_back_to_general(self) -> None:
        ai_topic, ai_tags, ai_strength = assign_topic(
            "Evaluation teams improved inference latency with better embeddings."
        )
        general_topic, general_tags, general_strength = assign_topic(
            "A quiet day with broad observations and no obvious domain terms."
        )

        self.assertEqual(ai_topic, "ai")
        self.assertEqual(ai_tags, ("embeddings", "evaluation", "inference"))
        self.assertGreaterEqual(ai_strength, 2)
        self.assertEqual(general_topic, "general")
        self.assertEqual(general_tags, ())
        self.assertEqual(general_strength, 0)

    def test_rank_posts_scores_priority_authors_and_urls_deterministically(self) -> None:
        normalized = normalize_posts(
            [
                {
                    "id": "1",
                    "author": "researchops",
                    "text": "Evaluation pipelines improved inference with cached embeddings and deterministic fixtures.",
                    "url": "https://example.com/1",
                },
                {
                    "id": "2",
                    "author": "observer",
                    "text": "Evaluation pipelines improved inference with cached embeddings and deterministic fixtures.",
                },
            ]
        )

        clustered = cluster_posts(normalized)
        ranked = rank_posts(clustered)

        self.assertGreater(ranked[0].score, ranked[1].score)
        self.assertIn("priority_author=yes", ranked[0].why_selected or "")
        self.assertIn("has_url=yes", ranked[0].why_selected or "")
        self.assertIn("has_url=no", ranked[1].why_selected or "")

    def test_run_pipeline_produces_topics_scores_and_summaries(self) -> None:
        result = run_pipeline(
            [
                {
                    "id": "1",
                    "author": "alpha",
                    "text": "Deterministic local fixtures make pipeline tests cheaper to run and easier to debug.",
                }
            ]
        )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(
            result.items[0].summary,
            "Summary: Deterministic local fixtures make pipeline tests cheaper to run and easier to debug.",
        )
        self.assertEqual(result.items[0].topic, "software")
        self.assertGreater(result.items[0].score, 0)
        self.assertEqual(result.items[0].tags, ("fixtures", "pipeline", "tests"))
        self.assertIn("software", result.topic_summaries)


if __name__ == "__main__":
    unittest.main()
