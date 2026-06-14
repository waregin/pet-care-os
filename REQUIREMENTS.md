# pet-care-os — Requirements & Context (NEW REPO)

> **HARD DEADLINE: the cat food portion must be working by mid-July 2026.** This is the most time-sensitive coding project in the queue.

## Purpose
Module of External Brain OS for pet care management. Household has multiple pets (dogs incl. Henry/Soma/Jett/Samson, cats incl. Troy/Gwen, guinea pigs, others) with recurring care tasks currently scattered across TickTick Habits (Atopivet collar changes, paraneal sack checks, guinea pig cage cleaning, etc.).

## Phase 1 (the mid-July deliverable): cat food
Define precisely in session, but likely some combination of:
- Track cat food inventory/consumption rate and predict reorder dates
- Price/availability watching (consumes ChewyScraper/ChewyData output — coordinate; don't duplicate scraping)
- Reorder reminders surfaced through TickTick (reuse priority-os write-back pattern: tag + due date + reminder)

## Later phases (backlog, do not build now)
- Medication/supplement schedules (Atopivet, Bravecto — note Samson had a Bravecto reaction, recorded in Personal Notes "Samson Bravecto reaction"; a med-reaction log is a natural feature)
- Vet visit records, weight tracking, Pet Log import (Personal Notes "0 Pet Log")
- Food preference tracking ("the best food is the one they'll eat" — Reggie's cat food comparison website idea could become a public-facing spinoff)

## Requirements
- **Non-functional:** External Brain OS conventions (PostgreSQL, Python, cron, TickTick surfacing); boring and reliable beats clever — a missed cat food reorder is the failure mode that matters
- **Constraint:** Mid-July deadline means phase 1 must be scoped to days, not weeks

## First session objectives
1. Scope phase 1 to the smallest thing that prevents running out of cat food
2. Decide data sourcing (manual entry vs ChewyData integration) — manual-first is acceptable for v1
3. Scaffold repo; open issues; build the walking skeleton in-session if time allows
