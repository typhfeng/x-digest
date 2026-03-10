# AGENTS.md

## Project
x-digest is a research-oriented digest generator for filtering signal from social content.

## Pipeline
ingest -> normalize -> filter -> cluster -> summarize -> export

## Engineering Principles
- Keep architecture modular
- Prefer deterministic local inputs for testing
- Separate adapters from core pipeline
- Maintain a runnable local workflow
