"""Thin Vercel Python Function adapter.

Business logic and ASGI app creation stay in app.main so the backend remains
portable to ASGI servers or other hosting targets.
"""

from app.main import app

__all__ = ["app"]
