# x-digest Project State

Last updated: 2026-03-12

## Current Phase
Phase 5 – Lightweight Research Memory

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

### Phase 5 – Lightweight Research Memory
- added `src/memory/` with a JSON-backed local memory store and typed snapshot models
- initialized missing memory files automatically and kept invalid memory files on a graceful fallback path
- tracked topic history across successful runs and labeled topics as `new topic` or `recurring topic`
- tracked priority authors through local memory and threaded them into ranking plus digest annotations
- stored recent digest metadata with digest date, source path, output path, counts, and selected topics
- updated the CLI to load memory before pipeline execution and persist memory only after the markdown export succeeds
- updated markdown export to include simple memory-aware annotations without changing the overall digest structure
- expanded tests to cover memory initialization, recurring topics, priority authors, and invalid-memory fallback

Validation

python3 -m src.cli --source json --input data/sample_posts.json --output output/sample_digest.md --memory-dir state/memory
python3 -m unittest discover -s tests

Result: SUCCESS

---

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

### Phase 4 – Source Adapters
- added a typed source adapter contract in `src/adapters/base.py`
- kept `src/adapters/json_source.py` as the working default adapter and preserved `load_posts()` for backward compatibility
- added explicit adapter selection through `src/adapters/registry.py` and `--source` in the CLI
- added placeholder adapters for imported archives, the X API, and browser-assisted scraping with clear failure messages
- kept `src/core/pipeline.py` unchanged so ingest selection stays separate from normalization, filtering, clustering, ranking, summarization, and export
- expanded tests to cover adapter selection, JSON adapter behavior, placeholder failures, and CLI compatibility

Validation

python3 -m src.cli --source json --input data/sample_posts.json --output output/sample_digest.md
python3 -m unittest discover -s tests

Result: SUCCESS

---

## Remaining Work

- define the next roadmap phase beyond lightweight local research memory

---

## Future Phases

TBD
