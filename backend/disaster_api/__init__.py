"""`backend.disaster_api` package

This package provides a lightweight namespace for the API surface while
we incrementally refactor the codebase into a more structured layout.

Exports:
- `create_app()` - returns the Flask app object
- `app` - the Flask app instance (if available)
"""

from typing import Optional

try:
    # Prefer top-level import when running app.py directly (app is main module)
    from app import app as app  # type: ignore
except Exception:
    try:
        # Fall back to package import
        from backend.app import app as app  # type: ignore
    except Exception:
        app = None


def create_app() -> Optional[object]:
    """Return the Flask app instance (or None if available)."""
    return app

__all__ = ["app", "create_app"]
