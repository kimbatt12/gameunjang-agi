#!/usr/bin/env bash

run_validation() {
  validation_path=$1
  diff_base=$2

  printf 'pre-push: running git diff --check...\n' >&2
  (cd "$validation_path" && git diff --check "$diff_base" HEAD) || abort "git diff --check failed; push blocked."

  if [ -f "$validation_path/frontend/package.json" ]; then
    if ! command -v npm >/dev/null 2>&1; then
      abort "frontend/package.json exists but npm is not installed or not on PATH."
    fi

    if ! command -v node >/dev/null 2>&1; then
      abort "frontend/package.json exists but node is not installed or not on PATH."
    fi

    if ! node -e "process.exit(process.versions.node.split('.')[0] === '24' ? 0 : 1);"; then
      abort "frontend validation requires Node 24.x to match CI."
    fi

    printf 'pre-push: frontend/package.json found; installing frontend dependencies...\n' >&2
    npm ci --prefix "$validation_path/frontend" || abort "npm ci --prefix frontend failed; push blocked."

    for script in lint typecheck test build; do
      if (cd "$validation_path" && node -e "const scripts = require('./frontend/package.json').scripts || {}; process.exit(Object.prototype.hasOwnProperty.call(scripts, process.argv[1]) ? 0 : 1);" "$script"); then
        printf 'pre-push: running frontend %s script...\n' "$script" >&2
        npm run --prefix "$validation_path/frontend" "$script" || abort "frontend $script script failed; push blocked."
      else
        printf 'pre-push: skipping frontend %s script; not defined in frontend/package.json.\n' "$script" >&2
      fi
    done
  else
    printf 'pre-push: skipping frontend validation; frontend/package.json not found.\n' >&2
  fi

  if [ -f "$validation_path/backend/pyproject.toml" ]; then
    if ! command -v python >/dev/null 2>&1; then
      abort "backend/pyproject.toml exists but python is not installed or not on PATH."
    fi

    if ! python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 14) else 1)"; then
      abort "backend validation requires Python 3.14 to match CI."
    fi

    printf 'pre-push: backend/pyproject.toml found; installing backend dependencies...\n' >&2
    python -m venv "$validation_path/backend/.pre-push-venv" || abort "backend virtual environment creation failed; push blocked."
    backend_python="$validation_path/backend/.pre-push-venv/bin/python"
    (cd "$validation_path/backend" && "$backend_python" -m pip install --upgrade pip) || abort "backend pip upgrade failed; push blocked."
    if ! (cd "$validation_path/backend" && "$backend_python" -m pip install -e '.[dev]'); then
      printf "pre-push: backend dev install failed; falling back to base editable install...\n" >&2
      (cd "$validation_path/backend" && "$backend_python" -m pip install -e .) || abort "backend editable install failed; push blocked."
    fi
    (cd "$validation_path/backend" && "$backend_python" -m pip install ruff pytest) || abort "backend validation dependency install failed; push blocked."

    printf 'pre-push: running backend ruff check...\n' >&2
    (cd "$validation_path/backend" && "$backend_python" -m ruff check .) || abort "backend ruff check failed; push blocked."
    printf 'pre-push: running backend ruff format --check...\n' >&2
    (cd "$validation_path/backend" && "$backend_python" -m ruff format --check .) || abort "backend ruff format --check failed; push blocked."
    printf 'pre-push: running backend pytest...\n' >&2
    (cd "$validation_path/backend" && "$backend_python" -m pytest) || abort "backend pytest failed; push blocked."
  else
    printf 'pre-push: skipping backend validation; backend/pyproject.toml not found.\n' >&2
  fi
}

prepare_validation_worktree() {
  validation_sha=$1

  validation_root=$(mktemp -d "${TMPDIR:-/tmp}/pre-push-validation.XXXXXX") || abort "failed to create temporary validation worktree path."
  git worktree add --detach --quiet "$validation_root" "$validation_sha" || abort "failed to create temporary validation worktree for $validation_sha."
}

remove_validation_worktree() {
  git worktree remove --force "$validation_root" >/dev/null 2>&1 || abort "failed to remove temporary validation worktree."
  validation_root=""
}
