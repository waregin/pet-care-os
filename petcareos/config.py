"""Configuration. External Brain OS convention: connection comes from DATABASE_URL.

Loads a sibling .env file if present (no third-party dependency — keep it boring).
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader: KEY=VALUE lines, '#' comments. Real env always wins."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def database_url() -> str:
    _load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Copy .env.example to .env and set it "
            "(or export DATABASE_URL)."
        )
    return url
