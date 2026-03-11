# x-digest

AI-agent based research digest generator for X-like content.

Pipeline:
ingest → normalize → filter → cluster → rank → summarize → export

This repository is structured for agent-driven development (Codex CLI, GPT, etc.).

## Architecture

The current local research pipeline is deterministic and modular:

- `src/adapters/json_source.py` loads local JSON fixtures.
- `src/core/normalize.py` converts loose JSON objects into normalized `Post` records.
- `src/core/filter.py` removes short or duplicate posts.
- `src/core/cluster.py` assigns heuristic topics with a simple keyword map.
- `src/core/rank.py` applies explainable local scoring from topic strength, word count, URL presence, and priority authors.
- `src/core/summarize.py` generates deterministic one-line summaries and topic summaries.
- `src/core/pipeline.py` orchestrates the stage sequence and returns a `PipelineResult`.
- `src/adapters/markdown_export.py` writes grouped markdown output by topic and score.

No external APIs or LLM calls are used yet. The local JSON workflow remains the reference path for testing and iteration.

## Run Locally

Generate a digest from the sample fixture:

```bash
python3 -m src.cli --input data/sample_posts.json --output output/sample_digest.md
```

The output markdown includes:

- digest date and source path
- selected versus total post counts
- key topics
- per-topic summaries
- selected posts grouped by topic and sorted by score
- per-post title/date, score, author, URL, why-selected metadata, tags, and short summary

Run tests:

```bash
python3 -m unittest discover -s tests
```

## Next Gaps Before LLM Integration

- Topic clustering is still a keyword heuristic and will miss nuanced themes.
- Ranking is intentionally local and explainable, not learned.
- Topic summaries are template-based rather than abstractive.
