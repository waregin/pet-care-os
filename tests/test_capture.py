"""Tests for the CSV capture path and allergen import.

Needs a throwaway PostgreSQL (set TEST_DATABASE_URL or DATABASE_URL); skips otherwise.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", ""))

if not os.environ.get("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set; skipping DB-backed tests", allow_module_level=True)

from petcareos import allergens, migrate, preferences  # noqa: E402
from petcareos.db import connect  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _migrated():
    migrate.run()


def test_template_covers_every_food_pet_pair():
    with connect() as conn:
        # default template skips do_not_buy foods
        n_foods = conn.execute(
            "SELECT count(*) c FROM foods WHERE NOT discontinued AND NOT do_not_buy").fetchone()["c"]
        n_pets = conn.execute("SELECT count(*) c FROM pets").fetchone()["c"]
        rows = preferences.template_rows(conn)
    assert len(rows) == n_foods * n_pets
    assert set(preferences.TEMPLATE_COLUMNS).issubset(rows[0].keys())


def test_template_current_is_rotation_only():
    with connect() as conn:
        rows = preferences.template_rows(conn, current=True)
        n_manual = conn.execute("SELECT count(*) c FROM foods WHERE source='manual'").fetchone()["c"]
        n_pets = conn.execute("SELECT count(*) c FROM pets").fetchone()["c"]
    assert len(rows) == n_manual * n_pets


def test_blank_row_is_noop():
    with connect() as conn:
        before = conn.execute("SELECT count(*) c FROM assessments").fetchone()["c"]
        result = preferences.import_row(conn, "", "Mack & Jack", "Gwen", "", "", "")
        after = conn.execute("SELECT count(*) c FROM assessments").fetchone()["c"]
    assert result == "noop"
    assert before == after


def test_filled_row_upserts_and_drives_gate():
    with connect() as conn:
        # Troy rejects a previously-fine food -> it leaves the reorder list
        result = preferences.import_row(conn, "", "catalina catch", "Troy", "rejects", "", "")
        names = {r["name"] for r in preferences.reorder_list(conn)}
    assert result == "updated"
    assert "catalina catch" not in names


def test_create_missing_adds_food():
    with connect() as conn:
        # A food "in my head" not in the catalog: rejected without the flag...
        with pytest.raises(ValueError):
            preferences.import_row(conn, "Tiki Cat", "Ahi Tuna", "Troy", "loves", "", "")
        # ...created with it
        result = preferences.import_row(conn, "Tiki Cat", "Ahi Tuna", "Troy", "loves", "", "",
                                        create_missing=True)
        exists = conn.execute(
            "SELECT 1 FROM foods WHERE brand='Tiki Cat' AND name='Ahi Tuna'").fetchone()
    assert result == "created"
    assert exists is not None


def test_bad_value_raises_valueerror():
    with connect() as conn:
        with pytest.raises(ValueError):
            preferences.import_row(conn, "", "Mack & Jack", "Gwen", "adores", "", "")


def test_allergen_upsert_is_idempotent():
    with connect() as conn:
        pid = allergens._pet_id(conn, "Samson")
        allergens.upsert_allergen(conn, pid, "chicken", "3")
        allergens.upsert_allergen(conn, pid, "chicken", "4")  # update, not duplicate
        rows = [r for r in allergens.list_allergens(conn, "Samson") if r["allergen"] == "chicken"]
    assert len(rows) == 1
    assert rows[0]["score"] == "4"
