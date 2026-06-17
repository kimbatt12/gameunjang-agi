# Backend Rules

- `backend/` is a Python/FastAPI-compatible backend boundary.
- Keep Python backend tooling and dependencies inside `backend/`.
- Prefer the latest compatible stable/LTS Python runtime, packages, and tooling. Do not use prerelease, current, or non-LTS versions unless explicitly instructed.
- When `pyproject.toml` is introduced, set `requires-python` to `>=3.14,<3.15`.
- When `pyproject.toml` is present, validate backend changes from this directory with `ruff check .`, `ruff format --check .`, and `pytest`.
