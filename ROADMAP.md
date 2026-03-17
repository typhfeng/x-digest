# x-digest Roadmap

## Phase 1 – Local MVP
Goal:
Generate a markdown digest from local JSON posts.

Features:
- CLI interface
- local JSON adapter
- normalize posts
- filter short/duplicate posts
- deterministic summaries
- markdown export
- basic tests

Status: COMPLETE

---

## Phase 2A – Research Pipeline Refactor
Goal:
Refactor the MVP into a modular research pipeline.

Planned modules:
- normalize
- filter
- cluster
- rank
- summarize
- export

Features:
- thin CLI
- separated core modules
- structured digest items
- improved markdown export

Status: COMPLETE

---

## Phase 2B – Topic Clustering and Ranking
Goal:
Make the digest topic-centric and priority-aware.

Features:
- keyword-based topic clustering
- deterministic importance scoring
- topic-grouped markdown output
- per-post why_selected

Status: COMPLETE

---

## Phase 3 – LLM Summarization
Goal:
Add optional LLM intelligence.

Features:
- provider abstraction
- rule-based fallback
- topic summaries
- why selected explanations
- concise signal extraction

Status: COMPLETE

---

## Phase 4 – Source Adapters
Goal:
Support real source ingestion.

Adapters:
- local JSON
- imported archive
- X API placeholder
- scraping placeholder

Status: COMPLETE

---

## Phase 5 – Lightweight Research Memory
Goal:
Carry research context across local digest runs without adding external services.

Features:
- topic memory
- priority account tracking
- recent digest metadata
- memory-aware digest annotations
- recurring digest workflow

Status: COMPLETE

---

## Phase 6A – Realistic Archive Import Source
Goal:
Turn archive ingestion into a real local adapter without changing the core research pipeline.

Features:
- working `archive` CLI source
- realistic archive JSON support with wrapped records and alternate field names
- preserved archive metadata on normalized posts
- local sample archive fixture
- adapter, CLI, and pipeline coverage for archive input

Status: COMPLETE

---

## Phase 6B – Deterministic Time-Window Filtering
Goal:
Support repeatable research slices by selecting posts within an explicit ISO time window.

Features:
- CLI flags `--since` and `--until` for inclusive ISO boundaries
- pipeline-level date filtering across all supported sources
- deterministic handling for date-only and datetime boundaries
- clear validation errors for invalid windows
- test and README coverage

Status: COMPLETE
