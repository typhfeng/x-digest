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
- `src/adapters/archive_source.py` ingests realistic archive exports and maps alternate field names into the existing raw-post contract while preserving archive metadata.
- `src/adapters/x_api_source.py` loads real posts from the X API using a local request config plus bearer-token authentication.
- `src/adapters/scraping_source.py` remains a placeholder that fails clearly until implemented.
- `src/core/normalize.py` converts loose JSON objects into normalized `Post` records.
- `src/core/filter.py` removes short or duplicate posts and optionally applies deterministic ISO time-window filtering.
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

Archive imports use the same pipeline and output format:

```bash
python3 -m src.cli --source archive --input data/sample_archive.json --output output/sample_archive_digest.md --memory-dir state/memory
```

X API ingestion uses a local request JSON plus a bearer token:

```bash
export X_DIGEST_X_API_BEARER_TOKEN=your_token_here
python3 -m src.cli --source x_api --input data/sample_x_api_request.json --output output/sample_x_api_digest.md --memory-dir state/memory
```

Sample request config (`data/sample_x_api_request.json`):

```json
{
  "mode": "recent_search",
  "query": "(inference OR evaluation OR benchmark) lang:en -is:retweet",
  "max_results": 25,
  "max_pages": 1,
  "start_time": "2026-03-10T00:00:00Z"
}
```

Supported request modes:

- `recent_search` with required `query`
- `user_tweets` with required `user_id`

Optional request fields:

- `max_results` (1-100)
- `max_pages` (1-20)
- `start_time`, `end_time`, `since_id`, `until_id`
- `exclude` (`replies`, `retweets`) for `user_tweets`
- `base_url` and `timeout_seconds` for custom environments

Additional environment variables:

- `X_DIGEST_X_API_TIMEOUT` (default `20`)
- `X_DIGEST_X_API_BASE_URL` (default `https://api.x.com/2`)

Time-window filtering is optional and works across supported sources:

```bash
python3 -m src.cli --source archive --input data/sample_archive.json --output output/sample_archive_digest.md --since 2026-03-10 --until 2026-03-11
```

`--since` and `--until` are inclusive ISO-8601 boundaries (`YYYY-MM-DD` or full datetime).
When a time window is provided, posts with missing or non-ISO `created_at` values are excluded.

The checked-in archive fixture demonstrates a realistic wrapped archive shape:

- top-level `account.username` fallback for author data
- `tweets` list containing nested `tweet` objects
- alternate field names such as `tweet_id`, `screen_name`, and `full_text`
- preserved archive metadata such as `reply_to`, `quoted_post_id`, `thread_id`, `conversation_id`, `metrics`, and extra archive-only fields

Available source names:

- `json` for the current local JSON workflow
- `archive` for imported archive JSON with realistic alternate field names
- `x_api` for real X API ingestion via request config JSON
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
- Scraping remains a deliberate placeholder due brittleness and maintenance overhead.
- Research memory is still a single local JSON file; there is no database, concurrency control, or cross-machine sync yet.
