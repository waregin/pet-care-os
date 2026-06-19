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


def _upsert(conn, pid: int, fid: int, acceptance, safety, note) -> dict:
    """Upsert one (pet, food) assessment. None on an axis leaves it unchanged."""
    if acceptance and acceptance not in ACCEPTANCE_VALUES:
        raise ValueError(f"acceptance must be one of {ACCEPTANCE_VALUES}")
    if safety and safety not in SAFETY_VALUES:
        raise ValueError(f"safety must be one of {SAFETY_VALUES}")
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


def assess(
    conn,
    pet_name: str,
    food_name: str,
    acceptance: Optional[str] = None,
    safety: Optional[str] = None,
    note: Optional[str] = None,
    brand: Optional[str] = None,
) -> dict:
    """Upsert one cat's assessment of one food by name. Only provided axes change."""
    pid = _pet_id(conn, pet_name)
    fid = _food_id(conn, food_name, brand)
    try:
        return _upsert(conn, pid, fid, acceptance, safety, note)
    except ValueError as e:
        raise SystemExit(str(e))


def list_assessments(conn, pet: Optional[str] = None, food: Optional[str] = None) -> list[dict]:
    """Current assessments as a readable table. Optional pet/food filters."""
    return conn.execute(
        """
        SELECT p.name AS pet, f.brand, f.name AS food, a.acceptance, a.safety, a.note
        FROM assessments a
        JOIN pets p ON p.id = a.pet_id
        JOIN foods f ON f.id = a.food_id
        WHERE (%(pet)s::text IS NULL OR p.name ILIKE %(pet)s)
          AND (%(food)s::text IS NULL OR f.name ILIKE %(food)s)
        ORDER BY f.brand NULLS FIRST, f.name, p.name
        """,
        {"pet": pet, "food": food},
    ).fetchall()


TEMPLATE_COLUMNS = ["brand", "name", "pet", "acceptance", "safety", "note"]


def template_rows(conn) -> list[dict]:
    """Full food x pet grid pre-filled with current values — the CSV capture form.
    Empty acceptance/safety cells = not yet assessed (fill them in, blanks are left unchanged)."""
    return conn.execute(
        """
        SELECT f.brand,
               f.name,
               p.name AS pet,
               COALESCE(a.acceptance::text, '') AS acceptance,
               COALESCE(a.safety::text, '')     AS safety,
               COALESCE(a.note, '')             AS note
        FROM foods f
        CROSS JOIN pets p
        LEFT JOIN assessments a ON a.food_id = f.id AND a.pet_id = p.id
        WHERE f.discontinued = FALSE
        ORDER BY f.brand NULLS FIRST, f.name, p.name
        """
    ).fetchall()


def import_row(conn, brand, name, pet, acceptance, safety, note) -> bool:
    """Apply one template row; returns True if it changed anything. A fully blank row
    (no acceptance/safety/note) is a no-op so the grid's empty cells don't create
    placeholder rows. Raises ValueError with a clear message on bad pet/food/value."""
    brand = (brand or "").strip() or None
    name = (name or "").strip()
    pet = (pet or "").strip()
    acceptance = (acceptance or "").strip() or None
    safety = (safety or "").strip() or None
    note = (note or "").strip() or None

    if acceptance is None and safety is None and note is None:
        return False

    prow = conn.execute("SELECT id FROM pets WHERE name ILIKE %s", (pet,)).fetchone()
    if not prow:
        raise ValueError(f"unknown pet {pet!r}")
    if brand:
        matches = conn.execute(
            "SELECT id FROM foods WHERE name ILIKE %s AND brand ILIKE %s", (name, brand)
        ).fetchall()
    else:
        matches = conn.execute(
            "SELECT id FROM foods WHERE name ILIKE %s AND brand IS NULL", (name,)
        ).fetchall()
    if not matches:
        raise ValueError(f"no food matching brand={brand!r} name={name!r}")
    if len(matches) > 1:
        raise ValueError(f"ambiguous food brand={brand!r} name={name!r}")
    _upsert(conn, prow["id"], matches[0]["id"], acceptance, safety, note)
    return True


def reorder_list(conn, tier: Optional[str] = None) -> list[dict]:
    """Foods that are safe (no safety-gate cat says unsafe), not rejected by the acceptance
    gate, and not flagged do_not_buy. Each row is tiered:
      * 'proven'    — the acceptance-gate cat has actually eaten it (loves/eats/tolerates)
      * 'candidate' — safe but never tried by the gate cat yet
    Optional tier filter ('proven' / 'candidate'). Proven sort first."""
    rows = conn.execute(
        """
        SELECT brand, name, form, safety_gate_status, acceptance_gate_status,
               CASE WHEN acceptance_gate_status IN ('loves', 'eats', 'tolerates')
                    THEN 'proven' ELSE 'candidate' END AS tier
        FROM reorderable_foods
        ORDER BY (acceptance_gate_status IN ('loves', 'eats', 'tolerates')) DESC,
                 brand NULLS FIRST, name
        """
    ).fetchall()
    if tier:
        rows = [r for r in rows if r["tier"] == tier]
    return rows
