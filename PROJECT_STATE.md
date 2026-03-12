# x-digest Project State

Last updated: 2026-03-12

## Current Phase
Phase 4 – Source Adapters

---

## Completed

### Phase 1 – Local MVP
- CLI interface implemented
- JSON input adapter
- normalize posts
- filter duplicates and short posts
- deterministic summaries
- markdown export
- tests passing

Validation

python3 -m src.cli --input data/sample_posts.json --output output/sample_digest.md  
python3 -m unittest discover -s tests

Result: SUCCESS

---

## Completed This Phase

### Phase 2A – Pipeline Refactor
- split pipeline into `src/core/normalize.py`, `filter.py`, `cluster.py`, `rank.py`, `summarize.py`, and `pipeline.py`
- kept adapters isolated under `src/adapters/`
- preserved the local JSON workflow and thin CLI entrypoint

### Phase 2B – Clustering and Ranking
- added heuristic topic clustering with deterministic fallback to `general`
- added deterministic importance scoring from topic strength, word count, URL presence, and priority-author bonus
- extended digest items with topic, score, tags, and optional why-selected metadata
- updated markdown export to group by topic and sort posts by score
- expanded deterministic test coverage for clustering, ranking, pipeline output shape, and CLI execution

### Phase 3 – LLM Summarization
- added optional `src/llm/` provider abstraction with an OpenAI-compatible implementation
- added config-driven LLM selection using environment variables and optional JSON config file via `X_DIGEST_CONFIG`
- kept rule-based summaries and rationale text as the default fallback when no credentials are present
- added prompt templates under `prompts/templates/` for topic summaries and improved `why_selected` output
- made provider failures degrade gracefully back to deterministic markdown output
- updated README and tests to document and validate fallback mode, provider selection, and LLM enhancement hooks

Validation

python3 -m src.cli --input data/sample_posts.json --output output/sample_digest.md
python3 -m unittest discover -s tests

Result: SUCCESS

---

## Remaining Work

1 Phase 4 source adapters beyond local JSON
2 Phase 5 research-agent automation

---

## Future Phases

Phase 4 – X data ingestion  
Phase 5 – research agent
