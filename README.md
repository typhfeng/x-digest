# x-digest

Research-oriented digest generator for X-like social content.

Pipeline:
ingest → normalize → filter → cluster → rank → summarize → export

The local JSON workflow remains the reference path. Optional LLM enhancement is available for topic summaries and `why_selected` text, but the app still runs without any API key.

## Architecture

The pipeline is modular and keeps deterministic behavior as the default:

- `src/adapters/base.py` defines the source adapter contract and shared adapter errors.
- `src/adapters/registry.py` resolves explicit source names to adapters.
- `src/adapters/json_source.py` keeps local JSON as the working default source.
- `src/adapters/archive_source.py`, `src/adapters/x_api_source.py`, and `src/adapters/scraping_source.py` are placeholders that fail clearly until implemented.
- `src/core/normalize.py` converts loose JSON objects into normalized `Post` records.
- `src/core/filter.py` removes short or duplicate posts.
- `src/core/cluster.py` assigns heuristic topics with a simple keyword map.
- `src/core/rank.py` applies explainable local scoring from topic strength, word count, URL presence, and priority authors.
- `src/core/summarize.py` generates deterministic post summaries and fallback topic summaries.
- `src/memory/` stores lightweight cross-run research memory in local JSON, including topic history, priority authors, and recent digest metadata.
- `src/llm/config.py`, `src/llm/provider.py`, `src/llm/openai_compatible.py`, and `src/llm/service.py` add an optional provider-driven enhancement layer.
- `prompts/templates/` stores the prompt templates used for topic summaries and improved `why_selected` explanations.
- `src/core/pipeline.py` orchestrates the stage sequence and applies LLM enhancement only when configuration is complete.
- `src/adapters/markdown_export.py` writes grouped markdown output by topic and score, with simple memory-aware annotations.

If no LLM credentials are configured, or if a provider request fails, the pipeline falls back to deterministic summaries and rationale text.

## Run Locally

Generate a digest from the sample fixture:

```bash
python3 -m src.cli --input data/sample_posts.json --output output/sample_digest.md --memory-dir state/memory
```

The source can also be selected explicitly:

```bash
python3 -m src.cli --source json --input data/sample_posts.json --output output/sample_digest.md --memory-dir state/memory
```

Available source names:

- `json` for the current local JSON workflow
- `archive` placeholder for imported archive ingestion
- `x_api` placeholder for future API ingestion
- `scraping` placeholder for future browser-assisted ingestion

Selecting a placeholder source currently returns a clear error and exits without changing the pipeline.

The markdown output includes:

- digest date and source path
- selected versus total post counts
- key topics
- per-topic summaries
- per-topic memory labels for new versus recurring topics
- selected posts grouped by topic and sorted by score
- per-post title/date, score, author, URL, `why_selected`, tags, optional priority-author memory labels, and short summary

Run tests:

```bash
python3 -m unittest discover -s tests
```

## Local Research Memory

Phase 5 adds a lightweight JSON-backed memory layer. It stays local and deterministic:

- default storage path is `state/memory/research_memory.json`
- missing memory files are initialized automatically
- invalid or unavailable memory falls back to an empty in-memory snapshot and still produces the digest
- topic history tracks whether a topic is new or recurring across successful runs
- priority authors are stored in the same JSON file and merged with the built-in defaults
- recent digest metadata stores the latest digest date, source path, output path, counts, and selected topics

On the first successful run a topic section is labeled `Memory: new topic`. On later runs with the same topic, the digest shows `Memory: recurring topic` with the prior digest count. Posts from tracked priority authors get a `- Memory: priority author` line.

## Optional LLM Mode

Configuration can come from environment variables, plus an optional JSON config file referenced by `X_DIGEST_CONFIG`.

Supported environment variables:

- `X_DIGEST_LLM_ENABLED=true`
- `X_DIGEST_LLM_PROVIDER=openai_compatible`
- `X_DIGEST_LLM_MODEL=gpt-4.1-mini`
- `X_DIGEST_LLM_BASE_URL=https://api.openai.com/v1`
- `X_DIGEST_LLM_TIMEOUT=20`
- `X_DIGEST_LLM_API_KEY=...`

`OPENAI_API_KEY` is also accepted as the API key source.

Optional config file example:

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai_compatible",
    "model": "gpt-4.1-mini",
    "base_url": "https://api.openai.com/v1",
    "timeout_seconds": 20
  }
}
```

Usage example:

```bash
export X_DIGEST_CONFIG=config/llm.json
export OPENAI_API_KEY=your_api_key_here
python3 -m src.cli --source json --input data/sample_posts.json --output output/sample_digest.md
```

When enabled and configured, the provider is used to:

- generate a concise per-topic summary
- improve per-post `why_selected` text

The deterministic local pipeline still handles ingestion, normalization, filtering, clustering, ranking, and post summaries. If provider setup is incomplete or a request fails, the digest is still produced in fallback mode.

## Current Limits

- Topic clustering is still keyword-based and intentionally simple.
- Ranking remains local and explainable rather than learned.
- Only an OpenAI-compatible provider is implemented in Phase 3.
- Non-JSON source adapters are placeholders in Phase 4 and intentionally do not perform real API or scraping work yet.
- Research memory is still a single local JSON file; there is no database, concurrency control, or cross-machine sync yet.
