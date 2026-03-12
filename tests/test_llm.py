import json
import tempfile
import unittest
from pathlib import Path

from src.core.pipeline import LlmSettings, run_pipeline
from src.llm.config import load_llm_settings
from src.llm.openai_compatible import OpenAICompatibleProvider
from src.llm.provider import build_provider


class _FakeProvider:
    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        if "topic summaries" in system_prompt:
            return "LLM topic summary for selected signal."
        return "LLM explanation for why the post was selected."


class _FailingProvider:
    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("provider failure")


class LlmTests(unittest.TestCase):
    def test_fallback_behavior_without_api_key(self) -> None:
        settings = LlmSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-4.1-mini",
            base_url="https://api.openai.com/v1",
            api_key=None,
        )

        result = run_pipeline(
            [
                {
                    "id": "1",
                    "author": "researchops",
                    "text": "Deterministic pipeline fixtures help teams debug ranking changes without touching external APIs.",
                    "url": "https://example.com/post/1",
                }
            ],
            llm_settings=settings,
        )

        self.assertIn("selected post covering", result.topic_summaries["software"])
        self.assertIn("topic=software", result.items[0].why_selected or "")

    def test_provider_selection_logic_uses_optional_config_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "x_digest.json"
            config_path.write_text(
                json.dumps(
                    {
                        "llm": {
                            "enabled": True,
                            "provider": "openai_compatible",
                            "model": "gpt-4.1-mini",
                            "base_url": "https://api.openai.com/v1",
                            "timeout_seconds": 12,
                        }
                    }
                ),
                encoding="utf-8",
            )

            settings = load_llm_settings(
                env={
                    "X_DIGEST_CONFIG": str(config_path),
                    "OPENAI_API_KEY": "test-key",
                }
            )

        provider = build_provider(settings)

        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertTrue(settings.is_configured)
        self.assertEqual(settings.timeout_seconds, 12.0)

    def test_pipeline_still_works_in_rule_based_mode(self) -> None:
        result = run_pipeline(
            [
                {
                    "id": "1",
                    "author": "researchops",
                    "text": "Evaluation teams cache embeddings so deterministic benchmark fixtures can run faster across repeated inference jobs.",
                    "url": "https://example.com/post/1",
                    "created_at": "2026-03-11",
                },
                {
                    "id": "2",
                    "author": "signalboost",
                    "text": "Local replay tests protect queue and adapter changes without depending on external APIs during digest development.",
                    "url": "https://example.com/post/2",
                    "created_at": "2026-03-10",
                },
            ],
            llm_settings=LlmSettings(enabled=False),
        )

        self.assertEqual(len(result.items), 2)
        self.assertIn("ai", result.topic_summaries)
        self.assertIn("software", result.topic_summaries)
        self.assertGreaterEqual(result.items[0].score, result.items[1].score)
        self.assertTrue(all(item.summary.startswith("Summary: ") for item in result.items))

    def test_pipeline_uses_provider_when_available(self) -> None:
        result = run_pipeline(
            [
                {
                    "id": "1",
                    "author": "researchops",
                    "text": "Evaluation teams cache embeddings so deterministic benchmark fixtures can run faster across repeated inference jobs.",
                    "url": "https://example.com/post/1",
                }
            ],
            llm_provider=_FakeProvider(),
            llm_settings=LlmSettings(enabled=True),
        )

        self.assertEqual(result.topic_summaries["ai"], "LLM topic summary for selected signal.")
        self.assertEqual(
            result.items[0].why_selected,
            "LLM explanation for why the post was selected.",
        )

    def test_pipeline_gracefully_falls_back_when_provider_fails(self) -> None:
        result = run_pipeline(
            [
                {
                    "id": "1",
                    "author": "researchops",
                    "text": "Evaluation teams cache embeddings so deterministic benchmark fixtures can run faster across repeated inference jobs.",
                    "url": "https://example.com/post/1",
                }
            ],
            llm_provider=_FailingProvider(),
            llm_settings=LlmSettings(enabled=True),
        )

        self.assertIn("selected post covering", result.topic_summaries["ai"])
        self.assertIn("topic=ai", result.items[0].why_selected or "")


if __name__ == "__main__":
    unittest.main()
