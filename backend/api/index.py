"""Vercel serverless entrypoint.

Exposes the FastAPI ASGI app so Vercel's Python runtime can serve it. All routes
are rewritten to this function via ``backend/vercel.json``. This is a free-tier,
stateless deployment: SQLite lives in ``/tmp`` (ephemeral) and the LLM runs in
keyless ``stub`` mode — see ``docs/DEPLOYMENT.md``.
"""

from __future__ import annotations

import os

# matplotlib needs a writable cache dir; only /tmp is writable on Vercel.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")

from app.main import app  # noqa: E402  (import after env setup)

__all__ = ["app"]
