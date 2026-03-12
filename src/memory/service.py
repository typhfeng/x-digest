from __future__ import annotations

from dataclasses import replace

from src.memory.models import ResearchMemorySnapshot, TopicHistoryRecord
from src.models.digest import PipelineResult, TopicMemoryAnnotation


def annotate_result(
    result: PipelineResult,
    snapshot: ResearchMemorySnapshot | None,
) -> PipelineResult:
    """Attach memory-aware labels to the current digest result."""
    if snapshot is None:
        return result

    items = []
    topic_memory: dict[str, TopicMemoryAnnotation] = {}

    for item in result.items:
        if item.topic not in topic_memory:
            prior_digest_count = snapshot.topic_history.get(
                item.topic,
                TopicHistoryRecord(),
            ).digest_count
            topic_memory[item.topic] = TopicMemoryAnnotation(
                label="recurring topic" if prior_digest_count > 0 else "new topic",
                prior_digest_count=prior_digest_count,
            )

        memory_labels = ()
        if item.post.author.casefold() in snapshot.priority_authors:
            memory_labels = ("priority author",)

        items.append(replace(item, memory_labels=memory_labels))

    ordered_topic_memory = {
        topic: topic_memory[topic] for topic in sorted(topic_memory)
    }
    return replace(result, items=tuple(items), topic_memory=ordered_topic_memory)


def resolve_digest_date(result: PipelineResult) -> str:
    """Return the most recent known post date in a digest result."""
    dates = sorted(item.post.created_at for item in result.items if item.post.created_at)
    return dates[-1] if dates else "unknown"


def resolve_digest_topics(result: PipelineResult) -> tuple[str, ...]:
    """Return the sorted set of topics included in a digest result."""
    return tuple(sorted({item.topic for item in result.items}))
