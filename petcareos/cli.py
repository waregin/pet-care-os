"""Pet Care OS command line. Boring argparse; one short-lived DB connection per command.

    petcareos migrate                 apply pending schema migrations
    petcareos add-food   ...          add a food to the catalog
    petcareos list-foods              show the catalog
    petcareos assess     ...          record a cat's verdict on a food
    petcareos reorder-list            the v1 deliverable: safe & accepted foods to order
"""

from __future__ import annotations

import argparse
import sys

from . import catalog, migrate, preferences
from .db import connect


def _print_table(rows: list[dict], columns: list[str]) -> None:
    if not rows:
        print("(none)")
        return
    widths = {c: len(c) for c in columns}
    cells = []
    for r in rows:
        row = {c: ("" if r.get(c) is None else str(r.get(c))) for c in columns}
        for c in columns:
            widths[c] = max(widths[c], len(row[c]))
        cells.append(row)
    header = "  ".join(c.ljust(widths[c]) for c in columns)
    print(header)
    print("  ".join("-" * widths[c] for c in columns))
    for row in cells:
        print("  ".join(row[c].ljust(widths[c]) for c in columns))


def cmd_migrate(_args) -> int:
    applied = migrate.run()
    if applied:
        print("Applied:", ", ".join(applied))
    else:
        print("Already up to date.")
    return 0


def cmd_add_food(args) -> int:
    with connect() as conn:
        food = catalog.add_food(
            conn,
            name=args.name,
            brand=args.brand,
            form=args.form,
            can_size_oz=args.can_size,
            calories_per_can=args.calories,
        )
    print(f"Added food #{food['id']}: [{food['brand']}] {food['name']}")
    return 0


def cmd_list_foods(_args) -> int:
    with connect() as conn:
        rows = catalog.list_foods(conn)
    _print_table(rows, ["id", "brand", "name", "form", "can_size_oz", "calories_per_can", "source"])
    return 0


def cmd_assess(args) -> int:
    with connect() as conn:
        r = preferences.assess(
            conn,
            pet_name=args.pet,
            food_name=args.food,
            acceptance=args.acceptance,
            safety=args.safety,
            note=args.note,
            brand=args.brand,
        )
    print(f"{args.pet} -> {args.food}: acceptance={r['acceptance']} safety={r['safety']}")
    return 0


def cmd_reorder_list(_args) -> int:
    with connect() as conn:
        rows = preferences.reorder_list(conn)
    print("Safe & accepted to (re)order "
          "(safety gate = Samson/allergies, acceptance gate = Troy/pickiness):\n")
    _print_table(rows, ["brand", "name", "form", "safety_gate_status", "acceptance_gate_status"])
    print("\nNote: blank gate status = not yet assessed. A food is excluded only when a gate "
          "cat marks it unsafe (Samson) or rejects it (Troy).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="petcareos", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="apply pending schema migrations").set_defaults(func=cmd_migrate)

    af = sub.add_parser("add-food", help="add a food to the catalog")
    af.add_argument("--name", required=True)
    af.add_argument("--brand")
    af.add_argument("--form", help="pate / shredded / stew / ...")
    af.add_argument("--can-size", type=float, dest="can_size", help="oz, e.g. 5.5")
    af.add_argument("--calories", type=int, help="kcal per can")
    af.set_defaults(func=cmd_add_food)

    sub.add_parser("list-foods", help="show the catalog").set_defaults(func=cmd_list_foods)

    asmt = sub.add_parser("assess", help="record a cat's verdict on a food")
    asmt.add_argument("--pet", required=True, help="e.g. Troy / Gwen / Samson")
    asmt.add_argument("--food", required=True, help="food name (case-insensitive)")
    asmt.add_argument("--brand", help="disambiguate when two foods share a name")
    asmt.add_argument("--acceptance", choices=preferences.ACCEPTANCE_VALUES)
    asmt.add_argument("--safety", choices=preferences.SAFETY_VALUES)
    asmt.add_argument("--note")
    asmt.set_defaults(func=cmd_assess)

    sub.add_parser("reorder-list",
                   help="the v1 deliverable: safe & accepted foods to order").set_defaults(
        func=cmd_reorder_list)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
