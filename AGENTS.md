# OpenCode Project Rules

## Repository Scope

- Work only inside `/home/hermes/projects/gameunjang-agi`.
- Before major changes, verify `git rev-parse --show-toplevel` returns `/home/hermes/projects/gameunjang-agi`.
- This repository is currently documentation-only. The planned monorepo layout is `frontend/` and `backend/`.
- Do not add secrets or real credentials. Use placeholder environment variable names only in examples.

## Development Workflow

- Prefer small, focused changes that preserve existing documentation structure.
- Keep root tooling generic and make it activate automatically when `frontend/` and `backend/` are added.
- Root scripts must not fail solely because `frontend/` or `backend/` is missing.
- Application docs should not be modified for tooling-only work unless a setup reference is explicitly needed.

## Validation Expectations

- On save: run formatting and auto-fixable linting with `npm run fix`.
- Before commit: run `npm run precommit`.
- Before push: run `npm run prepush`.
- Commit messages must follow Conventional Commits, for example `chore: configure development tooling`.

## Planned Project Scripts

- `frontend/` packages should expose `lint`, `typecheck`, `test`, optional `test:fast`, and `build` scripts.
- `backend/` packages should expose `lint`, `typecheck`, `test`, optional `test:fast`, and `build` scripts.
- The root package will skip unavailable directories and scripts until those packages exist.
