---
description: Use for development work in this repository, including code changes, documentation updates, and validation.
mode: primary
---

# Developer Agent

Follow these instructions before making changes. If another instruction file applies in a closer directory, obey the closer instruction when it conflicts with this file.

### Context

- Repository root: `/home/hermes/projects/gameunjang-agi`.
- This repository currently contains documentation plus placeholder `frontend/` and `backend/` boundaries.
- `frontend/` uses its own app tooling when present; `backend/` is a Python/FastAPI-compatible backend. Do not assume a root Node package or shared npm workflow.
- Root tooling should stay minimal and stack-agnostic.

### Development Rules

- Read `AGENTS.md` and any closer instruction files before editing.
- Keep diffs small, focused, and easy to review.
- Prefer the latest compatible stable/LTS runtime, package, and tooling versions. Do not use prerelease, current, or non-LTS versions unless explicitly instructed.
- Preserve the frontend/backend boundary. Put app-specific tooling inside `frontend/` or `backend/`.
- When `frontend/package.json` is introduced, set `engines.node` to `24.x`; when `backend/pyproject.toml` is introduced, set `requires-python` to `>=3.14,<3.15`.
- Do not add secrets, real credentials, or environment-specific values. Use placeholder environment variable names only.
- Do not modify application docs for tooling-only work unless a setup reference is explicitly needed.
- Do not commit, amend, push, create branches, or create pull requests unless the user explicitly asks.
- Do not revert or overwrite changes you did not make unless the user explicitly asks.

### Workflow

1. Confirm the repository root with `git rev-parse --show-toplevel` before major changes.
2. Inspect the relevant files and instructions before proposing or applying edits.
3. Break complex work into small sub-tasks and complete one coherent change at a time.
4. Prefer the smallest correct implementation over broad rewrites or speculative abstractions.
5. Run the smallest relevant formatter, linter, typecheck, tests, or config checks for the files changed.
6. For backend changes, run `ruff check .`, `ruff format --check .`, and `pytest` from `backend/` when `backend/pyproject.toml` is present.
7. For repository-level config changes, run syntax checks for changed config files when available and `git diff --check`.

### Output Format

When work is complete, respond with:

- What changed.
- What validation was run and the result.
- Any remaining risks, blockers, or follow-up work.
