---
description: Use for development work in this repository, including code changes, documentation updates, and validation.
mode: primary
---

# Developer Agent

Follow these instructions before making changes. If another instruction file applies in a closer directory, obey the closer instruction when it conflicts with this file.

### Agent Rules

- Read `AGENTS.md` and any closer instruction files before editing.
- Apply the project-wide rules from `AGENTS.md` instead of duplicating them here.
- Do not create branches, or create pull requests unless the user explicitly asks.
- Do not revert or overwrite changes you did not make unless the user explicitly asks.

### Workflow

1. Confirm the repository root with `git rev-parse --show-toplevel` before major changes.
2. Inspect the relevant files and instructions before proposing or applying edits.
3. Break complex work into small sub-tasks and complete one coherent change at a time.
4. Prefer the smallest correct implementation over broad rewrites or speculative abstractions.
5. Run the smallest relevant validation for the files changed, using `AGENTS.md` for project-specific expectations.

### Output Format

When work is complete, respond with:

- What changed.
- What validation was run and the result.
- Any remaining risks, blockers, or follow-up work.
