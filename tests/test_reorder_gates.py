"""Regression guard on the one invariant that matters: the reorder gates.

Needs a throwaway PostgreSQL (set TEST_DATABASE_URL or DATABASE_URL); skips otherwise.
Runs migrations into the target DB, so point it at a scratch database.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", ""))

if not os.environ.get("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set; skipping DB-backed gate tests", allow_module_level=True)

from petcareos import migrate, preferences  # noqa: E402
from petcareos.db import connect  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _migrated():
    migrate.run()


def _names(rows):
    return {r["name"] for r in rows}


def test_troy_rejection_excludes_food():
    with connect() as conn:
        names = _names(preferences.reorder_list(conn))
    # Seeded as Troy 'rejects'
    assert "fisherman's stew" not in names
    assert "saucey pate chicken & duck" not in names


def test_samson_unsafe_excludes_food():
    with connect() as conn:
        preferences.assess(conn, "Samson", "Mideast Feast", safety="unsafe")
        names = _names(preferences.reorder_list(conn))
        assert "Mideast Feast" not in names
        # Clearing the allergy flag brings it back
        preferences.assess(conn, "Samson", "Mideast Feast", safety="safe")
        assert "Mideast Feast" in _names(preferences.reorder_list(conn))


def test_unknown_does_not_exclude():
    with connect() as conn:
        names = _names(preferences.reorder_list(conn))
    # Never-assessed-by-gates food is still offered (just not vetted)
    assert "Monterey medley" in names
