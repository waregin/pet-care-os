"""Per-cat assessments and the v1 deliverable: the safe-and-accepted reorder list."""

from __future__ import annotations

from typing import Optional

ACCEPTANCE_VALUES = ("loves", "eats", "tolerates", "rejects", "never_tried")
SAFETY_VALUES = ("safe", "unsafe", "unknown")


def _pet_id(conn, pet_name: str) -> int:
    row = conn.execute("SELECT id FROM pets WHERE name ILIKE %s", (pet_name,)).fetchone()
    if not row:
        raise SystemExit(f"No pet named {pet_name!r}. Known pets: " + _pet_names(conn))
    return row["id"]


def _pet_names(conn) -> str:
    rows = conn.execute("SELECT name FROM pets ORDER BY name").fetchall()
    return ", ".join(r["name"] for r in rows) or "(none)"


def _food_id(conn, food_name: str, brand: Optional[str]) -> int:
    from .catalog import find_food

    matches = find_food(conn, food_name, brand)
    if not matches:
        raise SystemExit(f"No food matching name={food_name!r} brand={brand!r}.")
    if len(matches) > 1:
        opts = "; ".join(f"[{m['brand']}] {m['name']}" for m in matches)
        raise SystemExit(f"Ambiguous food {food_name!r}; narrow with --brand. Matches: {opts}")
    return matches[0]["id"]


def assess(
    conn,
    pet_name: str,
    food_name: str,
    acceptance: Optional[str] = None,
    safety: Optional[str] = None,
    note: Optional[str] = None,
    brand: Optional[str] = None,
) -> dict:
    """Upsert one cat's assessment of one food. Only provided axes are changed."""
    if acceptance and acceptance not in ACCEPTANCE_VALUES:
        raise SystemExit(f"acceptance must be one of {ACCEPTANCE_VALUES}")
    if safety and safety not in SAFETY_VALUES:
        raise SystemExit(f"safety must be one of {SAFETY_VALUES}")

    pid = _pet_id(conn, pet_name)
    fid = _food_id(conn, food_name, brand)

    # COALESCE keeps the existing value for any axis the caller left out.
    return conn.execute(
        """
        INSERT INTO assessments (pet_id, food_id, acceptance, safety, note, updated_at)
        VALUES (%(pid)s, %(fid)s,
                COALESCE(%(acc)s::acceptance_status, 'never_tried'),
                COALESCE(%(saf)s::safety_status, 'unknown'),
                %(note)s, now())
        ON CONFLICT (pet_id, food_id) DO UPDATE SET
            acceptance = COALESCE(%(acc)s::acceptance_status, assessments.acceptance),
            safety     = COALESCE(%(saf)s::safety_status, assessments.safety),
            note       = COALESCE(%(note)s, assessments.note),
            updated_at = now()
        RETURNING pet_id, food_id, acceptance, safety, note
        """,
        {"pid": pid, "fid": fid, "acc": acceptance, "saf": safety, "note": note},
    ).fetchone()


def reorder_list(conn) -> list[dict]:
    """Foods that are safe (no safety-gate cat says unsafe) and accepted (no acceptance-gate
    cat rejects). Surfaces gate statuses so unknowns/risks are visible."""
    return conn.execute(
        """
        SELECT brand, name, form, safety_gate_status, acceptance_gate_status
        FROM reorderable_foods
        ORDER BY brand NULLS FIRST, name
        """
    ).fetchall()
