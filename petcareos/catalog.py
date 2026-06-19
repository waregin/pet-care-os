"""Food catalog operations: add and list cat foods."""

from __future__ import annotations

from typing import Optional


def add_food(
    conn,
    name: str,
    brand: Optional[str] = None,
    form: Optional[str] = None,
    can_size_oz: Optional[float] = None,
    calories_per_can: Optional[int] = None,
    source: str = "manual",
    source_url: Optional[str] = None,
) -> dict:
    """Insert a food. Returns the row. Raises on duplicate (brand, name)."""
    return conn.execute(
        """
        INSERT INTO foods (name, brand, form, can_size_oz, calories_per_can, source, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, brand, name, form, can_size_oz, calories_per_can, source
        """,
        (name, brand, form, can_size_oz, calories_per_can, source, source_url),
    ).fetchone()


def find_food(conn, name: str, brand: Optional[str] = None) -> list[dict]:
    """Find foods by case-insensitive name, optionally narrowed by brand."""
    if brand:
        return conn.execute(
            "SELECT id, brand, name FROM foods WHERE name ILIKE %s AND brand ILIKE %s",
            (name, brand),
        ).fetchall()
    return conn.execute(
        "SELECT id, brand, name FROM foods WHERE name ILIKE %s", (name,)
    ).fetchall()


def list_foods(conn) -> list[dict]:
    return conn.execute(
        """
        SELECT id, brand, name, form, can_size_oz, calories_per_can, source, discontinued
        FROM foods
        ORDER BY discontinued, brand NULLS FIRST, name
        """
    ).fetchall()
