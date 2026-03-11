# x-digest Project State

Last updated: 2026-03-11

## Current Phase
Phase 3 – LLM Intelligence

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

Validation

python3 -m src.cli --input data/sample_posts.json --output output/sample_digest.md
python3 -m unittest discover -s tests

Result: SUCCESS

---

## Remaining Work

1 Phase 3 LLM-assisted summaries and richer selection rationale
2 Phase 4 source adapters beyond local JSON
3 Phase 5 research-agent automation

---

## Future Phases

Phase 3 – LLM summary  
Phase 4 – X data ingestion  
Phase 5 – research agent
