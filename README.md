# x-digest

AI-agent based research digest generator for X-like content.

Pipeline:
ingest → normalize → filter → cluster → summarize → export

This repository is structured for agent-driven development (Codex CLI, GPT, etc.).

## Phase 1 MVP

The phase 1 MVP runs locally on deterministic JSON input and exports a markdown digest.

Run it from the repository root:

```bash
python3 -m src.cli --input data/sample_posts.json --output output/sample_digest.md
```

Run tests:

```bash
python3 -m unittest discover -s tests
```
