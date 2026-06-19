"""Database access. Thin wrapper over psycopg3 — one short-lived connection per command."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .config import database_url


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Yield a connection that commits on success and rolls back on error."""
    conn = psycopg.connect(database_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
