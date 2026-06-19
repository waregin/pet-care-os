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


def test_proven_vs_candidate_tiers():
    with connect() as conn:
        # Untried-but-safe food is a candidate, not proven
        before = {r["name"]: r["tier"] for r in preferences.reorder_list(conn)}
        assert before.get("Monterey medley") == "candidate"
        # Once the gate cat eats it, it becomes proven and appears under --proven
        preferences.assess(conn, "Troy", "Monterey medley", acceptance="eats")
        proven = _names(preferences.reorder_list(conn, tier="proven"))
        candidates = _names(preferences.reorder_list(conn, tier="candidate"))
    assert "Monterey medley" in proven
    assert "Monterey medley" not in candidates


def test_do_not_buy_excluded():
    with connect() as conn:
        # A do_not_buy food (seeded from the trial sheet) never appears
        n = conn.execute(
            "SELECT count(*) c FROM reorderable_foods r JOIN foods f ON f.id=r.id "
            "WHERE f.do_not_buy"
        ).fetchone()["c"]
    assert n == 0
