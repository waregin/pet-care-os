"""Tiny forward-only migration runner. Applies migrations/*.sql in filename order, once each.

Boring on purpose: no rollbacks, no DSL. Tracks applied files in schema_migrations.
"""

from __future__ import annotations

from pathlib import Path

from .db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _ensure_tracking_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename   TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def applied_set(conn) -> set[str]:
    rows = conn.execute("SELECT filename FROM schema_migrations").fetchall()
    return {r["filename"] for r in rows}


def run() -> list[str]:
    """Apply any pending migrations. Returns the filenames applied this run."""
    files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))
    newly_applied: list[str] = []
    with connect() as conn:
        _ensure_tracking_table(conn)
        done = applied_set(conn)
        for path in files:
            if path.name in done:
                continue
            conn.execute(path.read_text())
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
            )
            newly_applied.append(path.name)
    return newly_applied
