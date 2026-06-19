# Pet Care OS

A module of **External Brain OS** for pet care. **Phase 1 (mid-July 2026 deadline): cat food.**

Phase 1 answers the question that actually prevents a bad reorder:

> **What cat food is safe and accepted to (re)order right now?**

It does this with a **catalog** of foods plus **per-cat assessments**, combined by two independent gates:

| Gate | Cat | Decides |
|------|-----|---------|
| **Safety** | Samson (≈30 allergies) | Can this food be bought **at all**? |
| **Acceptance** | Troy (picky) | Can it be bought **again**? |

A food is **reorderable** only if it clears both: no safety-gate cat marks it `unsafe`, and no acceptance-gate cat `rejects` it. Gwen's preferences are recorded but don't gate.

Per-cat acceptance is a graded scale: `loves / eats / tolerates / rejects / never_tried`. Safety is `safe / unsafe / unknown`.

### What's deliberately **not** in v1
- Run-out projection + **TickTick** cycle-level reorder reminder (10-day lead) → **Phase 2** (seams stubbed in `petcareos/ticktick.py`, `cron/reorder_check.py`).
- **Scraping** (folding in ChewyScraper to populate candidate foods) → later. The catalog is scraper-ready (`foods.source` / `source_url`); v1 uses manual entry.
- Ingredient-level allergen modeling, portioning engine, med/vet/weight features → backlog (see issues + `REQUIREMENTS.md`).

## Conventions
PostgreSQL · Python 3.11+ · cron-runnable · TickTick write-back (priority-os pattern: tag + due date + reminder).

## Setup
```bash
pip install -e .
cp .env.example .env          # set DATABASE_URL
petcareos migrate             # apply migrations/*.sql (schema + seed)
```

## Usage
```bash
petcareos reorder-list                 # the v1 deliverable
petcareos list-foods
petcareos add-food --name "paw lickin chicken" --brand Weruva --form pate --can-size 5.5
petcareos assess --pet Samson --food "tuna & shrimp" --safety safe
petcareos assess --pet Troy   --food "tuna & shrimp" --acceptance loves
```

## Layout
```
migrations/        forward-only *.sql (001 schema, 002 seed)
petcareos/         config, db, migrate, catalog, preferences, cli, ticktick(stub)
cron/              reorder_check.py (Phase 2 stub)
```
