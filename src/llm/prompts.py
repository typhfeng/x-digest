from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PromptTemplateSet:
    topic_summary_system: str
    topic_summary_user: str
    why_selected_system: str
    why_selected_user: str


def load_prompt_templates() -> PromptTemplateSet:
    """Load prompt templates from the repository template directory."""
    template_dir = Path(__file__).resolve().parents[2] / "prompts" / "templates"
    return PromptTemplateSet(
        topic_summary_system=_read_template(template_dir / "topic_summary_system.txt"),
        topic_summary_user=_read_template(template_dir / "topic_summary_user.txt"),
        why_selected_system=_read_template(template_dir / "why_selected_system.txt"),
        why_selected_user=_read_template(template_dir / "why_selected_user.txt"),
    )


def _read_template(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()
