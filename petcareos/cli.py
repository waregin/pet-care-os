"""Pet Care OS command line. Boring argparse; one short-lived DB connection per command.

    petcareos migrate                 apply pending schema migrations
    petcareos add-food   ...          add a food to the catalog
    petcareos list-foods              show the catalog
    petcareos assess     ...          record a cat's verdict on a food
    petcareos reorder-list            the v1 deliverable: safe & accepted foods to order
"""

from __future__ import annotations

import argparse
import csv
import sys

from . import allergens, catalog, migrate, pets, preferences
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


def cmd_add_pet(args) -> int:
    with connect() as conn:
        p = pets.add_pet(
            conn,
            name=args.name,
            species=args.species,
            calories_per_meal=args.calories,
            can_cap=args.can_cap,
            is_safety_gate=args.safety_gate,
            is_acceptance_gate=args.acceptance_gate,
            notes=args.notes,
        )
    gates = []
    if p["is_safety_gate"]:
        gates.append("safety-gate")
    if p["is_acceptance_gate"]:
        gates.append("acceptance-gate")
    print(f"Added pet #{p['id']}: {p['name']} ({p['species']})"
          + (f" [{', '.join(gates)}]" if gates else ""))
    return 0


def cmd_list_pets(_args) -> int:
    with connect() as conn:
        rows = pets.list_pets(conn)
    _print_table(rows, ["id", "name", "species", "calories_per_meal", "can_cap",
                         "is_safety_gate", "is_acceptance_gate", "notes"])
    return 0


def cmd_list_assessments(args) -> int:
    with connect() as conn:
        rows = preferences.list_assessments(conn, pet=args.pet, food=args.food)
    _print_table(rows, ["pet", "brand", "food", "acceptance", "safety", "note"])
    return 0


def cmd_template(args) -> int:
    with connect() as conn:
        rows = preferences.template_rows(conn)
    out = open(args.out, "w", newline="") if args.out else sys.stdout
    try:
        w = csv.DictWriter(out, fieldnames=preferences.TEMPLATE_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r[c]) for c in preferences.TEMPLATE_COLUMNS})
    finally:
        if args.out:
            out.close()
    if args.out:
        print(f"Wrote {len(rows)} rows to {args.out}. Fill acceptance/safety, then "
              f"`petcareos import-assessments --in {args.out}`.")
    return 0


def cmd_import_assessments(args) -> int:
    applied, errors = 0, []
    with connect() as conn, open(args.infile, newline="") as fh:
        reader = csv.DictReader(fh)
        missing = set(preferences.TEMPLATE_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"CSV missing columns: {sorted(missing)}")
        for i, row in enumerate(reader, start=2):  # header is line 1
            try:
                if preferences.import_row(conn, row["brand"], row["name"], row["pet"],
                                          row["acceptance"], row["safety"], row["note"]):
                    applied += 1
            except ValueError as e:
                errors.append(f"  line {i}: {e}")
        if errors:
            # Whole import rolls back on any error (db.connect raises -> rollback).
            raise SystemExit(f"{len(errors)} row(s) failed; nothing imported:\n" + "\n".join(errors))
    print(f"Imported {applied} assessment row(s).")
    return 0


def cmd_import_allergens(args) -> int:
    applied = 0
    with connect() as conn, open(args.infile, newline="") as fh:
        pid = allergens._pet_id(conn, args.pet)
        reader = csv.DictReader(fh)
        cols = {c.lower(): c for c in (reader.fieldnames or [])}
        if "allergen" not in cols:
            raise SystemExit(f"CSV needs an 'allergen' column; got {reader.fieldnames}")
        for row in reader:
            allergen = (row[cols["allergen"]] or "").strip()
            if not allergen:
                continue
            score = (row.get(cols.get("score", ""), "") or "").strip() or None
            note = (row.get(cols.get("note", ""), "") or "").strip() or None
            allergens.upsert_allergen(conn, pid, allergen, score, note, source="import")
            applied += 1
    print(f"Imported {applied} allergen(s) for {args.pet}.")
    return 0


def cmd_list_allergens(args) -> int:
    with connect() as conn:
        rows = allergens.list_allergens(conn, pet=args.pet)
    _print_table(rows, ["pet", "allergen", "score", "note"])
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

    ap = sub.add_parser("add-pet", help="add a pet (e.g. a dog) beyond the seeded cats")
    ap.add_argument("--name", required=True)
    ap.add_argument("--species", default="cat")
    ap.add_argument("--calories", type=int, help="target kcal per meal")
    ap.add_argument("--can-cap", action="store_true", dest="can_cap",
                    help="capped at one full can/meal regardless of kcal")
    ap.add_argument("--safety-gate", action="store_true", dest="safety_gate",
                    help="this pet's allergies decide 'safe to buy at all'")
    ap.add_argument("--acceptance-gate", action="store_true", dest="acceptance_gate",
                    help="this pet's pickiness decides 'buy it again'")
    ap.add_argument("--notes")
    ap.set_defaults(func=cmd_add_pet)

    sub.add_parser("list-pets", help="show pets and their gates").set_defaults(func=cmd_list_pets)

    la = sub.add_parser("list-assessments", help="show current per-cat assessments")
    la.add_argument("--pet")
    la.add_argument("--food")
    la.set_defaults(func=cmd_list_assessments)

    tp = sub.add_parser("template",
                        help="export the food x cat capture CSV (stdout or --out FILE)")
    tp.add_argument("--out", help="write to FILE instead of stdout")
    tp.set_defaults(func=cmd_template)

    ia = sub.add_parser("import-assessments", help="load a filled-in capture CSV")
    ia.add_argument("--in", dest="infile", required=True, help="CSV path")
    ia.set_defaults(func=cmd_import_assessments)

    ial = sub.add_parser("import-allergens",
                         help="load an allergen panel CSV (columns: allergen[,score][,note])")
    ial.add_argument("--pet", required=True, help="e.g. Samson")
    ial.add_argument("--in", dest="infile", required=True, help="CSV path")
    ial.set_defaults(func=cmd_import_allergens)

    lal = sub.add_parser("list-allergens", help="show a pet's allergy panel")
    lal.add_argument("--pet")
    lal.set_defaults(func=cmd_list_allergens)

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
