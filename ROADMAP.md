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

Status: NOT STARTED

---

## Phase 5 – Research Agent
Goal:
Turn the pipeline into a reusable research assistant.

Features:
- topic memory
- priority account tracking
- trend detection
- recurring digest workflow

Status: NOT STARTED
