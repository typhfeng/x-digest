# x-digest Project State

Last updated: 2026-03-18

## Current Phase
Phase 7A – Real X API Adapter

---

## Completed

### Phase 7A – Real X API Adapter
- replaced `src/adapters/x_api_source.py` placeholder with a working X API adapter that loads request settings from local JSON
- added support for `recent_search` and `user_tweets` request modes, including deterministic pagination controls (`max_pages`) and duplicate suppression by post id
- mapped X API responses into the existing raw-post contract (`id`, `author`, `text`, optional `created_at`, `url`, and metadata)
- added bearer-token authentication via `X_DIGEST_X_API_BEARER_TOKEN` and configurable base URL/timeout via config or environment variables
- added a checked-in request fixture `data/sample_x_api_request.json` for repeatable local workflows
- expanded adapter and CLI tests to cover X API config validation, pagination behavior, response mapping, and end-to-end digest generation with mocked HTTP responses
- updated `README.md`, `ROADMAP.md`, and `TASK_QUEUE.md` to document Phase 7A usage and next steps

Validation

python3 -m src.cli --source x_api --input data/sample_x_api_request.json --output output/sample_x_api_digest.md --memory-dir state/memory  
python3 -m unittest discover -s tests

Result: SUCCESS

---

### Phase 6B – Deterministic Time-Window Filtering
- added inclusive `--since` and `--until` CLI options for ISO-8601 boundaries in `src/cli.py`
- extended `src/core/pipeline.py` to thread optional time-window controls into filtering without changing the ingest/cluster/rank/summarize flow
- updated `src/core/filter.py` to apply deterministic time filtering after normalization, with support for date-only boundaries and explicit validation errors for invalid windows
- kept backward compatibility when no time window is provided
- added deterministic tests for date-window filtering and invalid range handling in pipeline and CLI suites
- updated `README.md` and `ROADMAP.md` to document the new phase and usage

Validation

python3 -m src.cli --source archive --input data/sample_archive.json --output output/sample_archive_window_digest.md --memory-dir state/memory --since 2026-03-10 --until 2026-03-11  
python3 -m unittest discover -s tests

Result: SUCCESS

---

### Phase 6A – Realistic Archive Import Source
- replaced the `archive` placeholder with a working local archive adapter in `src/adapters/archive_source.py`
- supported realistic archive containers such as top-level `tweets` lists with nested `tweet` objects
- normalized alternate archive field names including `tweet_id`, `screen_name`, and `full_text` into the existing raw-post contract
- preserved richer archive fields such as `reply_to`, `quoted_post_id`, `thread_id`, `conversation_id`, `metrics`, wrapper metadata, and extra archive-only fields under `Post.metadata`
- normalized common archive timestamp formats into ISO-style strings while preserving the original timestamp in metadata when transformed
- kept `src/adapters/json_source.py` as the simple baseline adapter and left ranking, memory, export, and optional LLM summarization unchanged
- added `data/sample_archive.json` plus deterministic tests for archive adapter success and failure, CLI archive mode, and pipeline execution with archive-sourced posts

Validation

python3 -m src.cli --source archive --input data/sample_archive.json --output output/sample_archive_digest.md --memory-dir state/memory  
python3 -m unittest discover -s tests

Result: SUCCESS

---

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

- Phase 7B: add a deterministic browser-assisted scraping fallback adapter
- harden operational X API workflows (request presets, retry policy tuning, and schedule automation)

---

## Future Phases

- Phase 7 and beyond: TBD
