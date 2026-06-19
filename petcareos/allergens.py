"""Per-pet allergy panel storage (allergen + score + category). Manual home for the data now;
automated food<->allergen matching to drive the safety gate is backlog issue #4."""

from __future__ import annotations

from typing import Optional


def _pet_id(conn, pet_name: str) -> int:
    row = conn.execute("SELECT id FROM pets WHERE name ILIKE %s", (pet_name,)).fetchone()
    if not row:
        raise SystemExit(f"No pet named {pet_name!r}.")
    return row["id"]


def upsert_allergen(conn, pet_id: int, allergen: str, score: Optional[str],
                    category: Optional[str] = None, note: Optional[str] = None,
                    source: str = "manual") -> None:
    conn.execute(
        """
        INSERT INTO pet_allergens (pet_id, allergen, score, category, note, source, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (pet_id, allergen) DO UPDATE SET
            score = EXCLUDED.score, category = EXCLUDED.category,
            note = EXCLUDED.note, source = EXCLUDED.source, updated_at = now()
        """,
        (pet_id, allergen, score, category, note, source),
    )


def list_allergens(conn, pet: Optional[str] = None) -> list[dict]:
    return conn.execute(
        """
        SELECT p.name AS pet, pa.category, pa.allergen, pa.score, pa.note
        FROM pet_allergens pa
        JOIN pets p ON p.id = pa.pet_id
        WHERE (%(pet)s::text IS NULL OR p.name ILIKE %(pet)s)
        ORDER BY p.name, pa.category NULLS LAST, pa.allergen
        """,
        {"pet": pet},
    ).fetchall()


# Column aliases so panels exported from different tools/spreadsheets import without reshaping.
_ALIASES = {
    "allergen": ("allergen", "name"),
    "score": ("score", "num", "value", "ige"),
    "category": ("category", "type"),
    "note": ("note", "notes"),
}


def resolve_columns(fieldnames: list[str]) -> dict[str, Optional[str]]:
    """Map our logical fields to the CSV's actual column names (case-insensitive)."""
    lower = {c.lower().strip(): c for c in (fieldnames or [])}
    resolved: dict[str, Optional[str]] = {}
    for field, aliases in _ALIASES.items():
        resolved[field] = next((lower[a] for a in aliases if a in lower), None)
    return resolved
