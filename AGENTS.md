# AGENTS.md

## Project
x-digest is a research-oriented digest generator focused on extracting signal from X-like social content.

## Product intent
This is not a generic feed reader.
It is a research pipeline that should prioritize:
- signal over noise
- topic organization over raw post listing
- deterministic local workflows before external integrations
- extensibility for future LLM and source adapters

## Current architecture goal
Pipeline:

ingest -> normalize -> filter -> cluster -> rank -> summarize -> export

## Engineering principles
- Keep the codebase modular and incremental
- Preserve a runnable local workflow at all times
- Prefer simple, deterministic implementations first
- Use local JSON input before adding real external sources
- Avoid unnecessary dependencies
- Keep CLI entrypoints thin
- Separate adapters from core pipeline logic
- Keep tests deterministic and focused

## Coding rules
- Python 3.11+
- Use type hints
- Prefer standard library unless a dependency is clearly justified
- Keep functions short and explicit
- Avoid hidden global state
- Avoid large rewrites unless necessary
- Preserve backward compatibility for the current CLI where practical
- Use English comments/docstrings in code

## Required development workflow
Before making changes:
1. Read this file
2. Read ROADMAP.md
3. Read PROJECT_STATE.md
4. Read TASK_QUEUE.md
5. Inspect current repository structure

After completing a task:
1. Run the relevant CLI command
2. Run tests
3. Update PROJECT_STATE.md
4. Update TASK_QUEUE.md
5. If a phase is completed, update ROADMAP.md
6. Commit the changes
7. Create a tag if the task completes a phase or milestone
8. Do not push automatically

## Git rules
After successful implementation:
- Stage all relevant changes
- Create a commit with a clear message
- Create an annotated tag for phase or milestone completion
- Do not rewrite history
- Do not push automatically
- Show the exact git push commands for the user

### Commit message format
Examples:
- Phase2A: refactor pipeline into modular research stages
- Phase2B: add topic clustering and deterministic ranking
- Phase3: add optional LLM summarization

### Tag format
Examples:
- v0.2-phase2a
- v0.3-phase2b
- v0.4-phase3

## Output expectations
When finished, report:
1. Architecture summary
2. Files changed
3. Commands run
4. Validation results
5. Suggested git push commands