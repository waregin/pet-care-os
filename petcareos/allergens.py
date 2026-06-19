"""Per-pet allergy panel storage (allergen + score). Manual home for the data now;
automated food<->allergen matching to drive the safety gate is backlog issue #4."""

from __future__ import annotations

from typing import Optional


def _pet_id(conn, pet_name: str) -> int:
    row = conn.execute("SELECT id FROM pets WHERE name ILIKE %s", (pet_name,)).fetchone()
    if not row:
        raise SystemExit(f"No pet named {pet_name!r}.")
    return row["id"]


def upsert_allergen(conn, pet_id: int, allergen: str, score: Optional[str],
                    note: Optional[str] = None, source: str = "manual") -> None:
    conn.execute(
        """
        INSERT INTO pet_allergens (pet_id, allergen, score, note, source, updated_at)
        VALUES (%s, %s, %s, %s, %s, now())
        ON CONFLICT (pet_id, allergen) DO UPDATE SET
            score = EXCLUDED.score, note = EXCLUDED.note,
            source = EXCLUDED.source, updated_at = now()
        """,
        (pet_id, allergen, score, note, source),
    )


def list_allergens(conn, pet: Optional[str] = None) -> list[dict]:
    return conn.execute(
        """
        SELECT p.name AS pet, pa.allergen, pa.score, pa.note
        FROM pet_allergens pa
        JOIN pets p ON p.id = pa.pet_id
        WHERE (%(pet)s::text IS NULL OR p.name ILIKE %(pet)s)
        ORDER BY p.name, pa.allergen
        """,
        {"pet": pet},
    ).fetchall()
