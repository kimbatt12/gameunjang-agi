"""Vercel-only ASGI entrypoint for the repo-root deployment.

The FastAPI app and backend code remain under backend/. This shim only makes
that app visible to Vercel Python Functions when deploying from the repository
root alongside the frontend Vite build.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

__all__ = ["app"]
