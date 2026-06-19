"""Pet management. Phase 1 seeds the three cats; this adds future pets (e.g. the dogs)."""

from __future__ import annotations

from typing import Optional


def add_pet(
    conn,
    name: str,
    species: str = "cat",
    calories_per_meal: Optional[int] = None,
    can_cap: bool = False,
    is_safety_gate: bool = False,
    is_acceptance_gate: bool = False,
    notes: Optional[str] = None,
) -> dict:
    return conn.execute(
        """
        INSERT INTO pets (name, species, calories_per_meal, can_cap,
                          is_safety_gate, is_acceptance_gate, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, name, species, is_safety_gate, is_acceptance_gate
        """,
        (name, species, calories_per_meal, can_cap, is_safety_gate, is_acceptance_gate, notes),
    ).fetchone()


def list_pets(conn) -> list[dict]:
    return conn.execute(
        """
        SELECT id, name, species, calories_per_meal, can_cap,
               is_safety_gate, is_acceptance_gate, notes
        FROM pets ORDER BY species, name
        """
    ).fetchall()
