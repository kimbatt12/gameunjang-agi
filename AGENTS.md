# OpenCode Project Rules

## Repository Scope

- Work only inside `/home/hermes/projects/gameunjang-agi`.
- Before major changes, verify `git rev-parse --show-toplevel` returns `/home/hermes/projects/gameunjang-agi`.
- This repository currently has documentation plus placeholder `frontend/` and `backend/` boundaries.
- Keep `backend/` and `frontend/` strictly separated, including non-code docs and ignore files. They should remain independently split-able into separate repositories without shared root runtime, package-manager, or tooling assumptions.
- `frontend/` uses its own app tooling when present; `backend/` is a Python/FastAPI-compatible backend. Do not assume a root Node package or shared npm contract.
- Do not add secrets or real credentials. Use placeholder environment variable names only in examples.

## Development Workflow

- Prefer small, focused changes that preserve existing documentation structure.
- Prefer the latest compatible stable/LTS runtime, package, and tooling versions. Do not use prerelease, current, or non-LTS versions unless explicitly instructed.
- Keep root tooling minimal and stack-agnostic. Put app-specific tooling inside `frontend/` or `backend/`.
- Do not add root npm orchestration unless both apps explicitly need a shared Node-based workflow.
- Application docs should not be modified for tooling-only work unless a setup reference is explicitly needed.

## OpenCode Agent Workflow

- Use `@developer` or the `developer` primary agent for development work in this repository.
- Address `@code-reviewer` findings, then rerun the smallest relevant validation before push or merge.
- Do not commit, push, create branches, or create pull requests unless explicitly instructed.

## Git Hooks

- Enable tracked hooks with `git config core.hooksPath .githooks` after cloning.
- The tracked `pre-push` hook first runs local validation aligned with CI policy, then runs a read-only `opencode` `code-reviewer` review against the current branch diff before allowing push.

## Validation Expectations

- Run the smallest relevant formatter, linter, typecheck, and tests for the files or app you changed.
- If `frontend/package.json` exists, use that package's own scripts when available.
- For backend changes, validate the Python backend with `ruff check .`, `ruff format --check .`, and `pytest` from `backend/` when `backend/pyproject.toml` is present.
- For repository-level config changes, at minimum run syntax checks for changed config files and `git diff --check`.
- Commit messages must follow Conventional Commits, for example `chore: configure development tooling`.

## App Tooling Guidelines

- `frontend/` may use Node-based tooling and should keep its dependencies and scripts inside `frontend/`. When `frontend/package.json` is introduced, set `engines.node` to `24.x`.
- `backend/` is a Python/FastAPI-compatible backend; keep Python backend tooling inside `backend/`. When `backend/pyproject.toml` is introduced, set `requires-python` to `>=3.14,<3.15`.
- CI may optionally run frontend `lint`, `typecheck`, `test`, and `build` scripts when `frontend/package.json` exists, but missing scripts should not create an artificial frontend contract before the app exists.
