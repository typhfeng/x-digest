# Create an AI-agent style project scaffold for "x-digest" and zip it for download

import os, zipfile, textwrap, pathlib, json

base = "./x-digest-agent"
paths = [
    "agents",
    "prompts",
    "tools",
    "pipelines",
    "memory",
    "src/core",
    "src/models",
    "src/adapters",
    "tests",
    "data",
    "output",
    "scripts",
]

# Create directories
for p in paths:
    os.makedirs(os.path.join(base, p), exist_ok=True)

# Helper to write files
def write(path, content):
    path = os.path.join(base, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).strip() + "\n")

# Core files
write("README.md", """
# x-digest

AI-agent based research digest generator for X-like content.

Pipeline:
ingest → normalize → filter → cluster → summarize → export

This repository is structured for agent-driven development (Codex CLI, GPT, etc.).
""")

write("AGENTS.md", """
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
""")

# Prompt files
write("prompts/phase1_mvp.txt", """
Implement phase 1 for x-digest.

Goal:
Build a runnable Python MVP that reads posts from local JSON and exports a markdown digest.

Pipeline:
ingest -> normalize -> filter -> summarize -> export

Deliverables:
- runnable CLI
- sample data
- markdown output
- minimal tests
""")

write("prompts/phase2_llm_filter.txt", """
Implement LLM-based filtering and summarization.

Goals:
- pluggable provider interface
- rule-based fallback
- prompt templates stored in prompts/
""")

write("prompts/phase3_source_adapter.txt", """
Implement source adapter architecture.

Adapters:
- local json
- API adapter placeholder
- scraping adapter placeholder
""")

# Agent placeholder
write("agents/digest_agent.py", """
\"\"\"High-level orchestration agent.\"\"\"

def run():
    print("Digest agent placeholder. Implement orchestration here.")
""")

# Core pipeline
write("src/core/pipeline.py", """
\"\"\"Core pipeline implementation.\"\"\"

def run_pipeline(posts):
    return posts
""")

# Model
write("src/models/post.py", """
from dataclasses import dataclass

@dataclass
class Post:
    id: str
    author: str
    text: str
    url: str | None = None
    created_at: str | None = None
""")

# Adapter placeholder
write("src/adapters/json_source.py", """
import json

def load_posts(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
""")

# Tool placeholder
write("tools/markdown_export.py", """
from datetime import datetime
import os

def export(posts):
    os.makedirs("output", exist_ok=True)
    path = f"output/digest_{datetime.now().date()}.md"
    with open(path, "w") as f:
        f.write("# Digest\\n\\n")
        for p in posts:
            f.write(f"- {p['text']}\\n")
    return path
""")

# Script
write("scripts/run_codex_phase1.sh", """
#!/bin/bash
codex --model gpt-5.4 "$(cat prompts/phase1_mvp.txt)"
""")

# Sample data
sample_posts = [
    {
        "id": "1",
        "author": "elonmusk",
        "text": "Starship development update and flight testing progress.",
        "url": "https://x.com/example1",
        "created_at": "2026-03-10"
    },
    {
        "id": "2",
        "author": "naval",
        "text": "Read more books and think independently.",
        "url": "https://x.com/example2",
        "created_at": "2026-03-10"
    }
]

with open(os.path.join(base, "data/sample_posts.json"), "w", encoding="utf-8") as f:
    json.dump(sample_posts, f, indent=2)

# Zip the project
zip_path = "./x-digest-agent.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(base):
        for file in files:
            full = os.path.join(root, file)
            rel = os.path.relpath(full, base)
            z.write(full, rel)

zip_path