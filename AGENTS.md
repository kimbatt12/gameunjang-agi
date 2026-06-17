# OpenCode Project Rules

## Repository Scope

- Work only inside `/home/hermes/projects/gameunjang-agi`.
- Before major changes, verify `git rev-parse --show-toplevel` returns `/home/hermes/projects/gameunjang-agi`.
- This repository currently has documentation plus placeholder `frontend/` and `backend/` boundaries.
- Frontend and backend stacks may differ; do not assume a root Node package or shared npm contract.
- Do not add secrets or real credentials. Use placeholder environment variable names only in examples.

## Development Workflow

- Prefer small, focused changes that preserve existing documentation structure.
- Keep root tooling minimal and stack-agnostic. Put app-specific tooling inside `frontend/` or `backend/`.
- Do not add root npm orchestration unless both apps explicitly need a shared Node-based workflow.
- Application docs should not be modified for tooling-only work unless a setup reference is explicitly needed.

## OpenCode Agent Workflow

- Use `@developer` or the `developer` primary agent for development work in this repository.
- Before pushing or asking someone else to merge changes, run a read-only review with `@code-reviewer` against the current git diff.
- Address `@code-reviewer` findings, then rerun the smallest relevant validation before push or merge.
- Do not commit, amend, push, create branches, or create pull requests unless explicitly instructed.

## Validation Expectations

- Run the smallest relevant formatter, linter, typecheck, and tests for the files or app you changed.
- If `frontend/package.json` or `backend/package.json` exists, use that package's own scripts when available.
- For repository-level config changes, at minimum run syntax checks for changed config files and `git diff --check`.
- Commit messages must follow Conventional Commits, for example `chore: configure development tooling`.

## App Tooling Guidelines

- `frontend/` may use Node-based tooling and should keep its dependencies and scripts inside `frontend/`.
- `backend/` may use Python, Node, Java, or another stack; add stack-specific tooling inside `backend/` when selected.
- CI may optionally run `lint`, `typecheck`, `test`, and `build` for a directory that contains `package.json`, but missing scripts should not create an artificial contract before the app exists.
