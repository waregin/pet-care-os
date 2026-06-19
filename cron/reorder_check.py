#!/usr/bin/env python3
"""Cron entrypoint — PHASE 2. Runs daily, projects cycle run-out, and (when due) writes a
TickTick reorder reminder. Stubbed in v1; the schema and seams exist so this stays a small add.

Intended crontab (External Brain OS convention — one daily check):
    0 8 * * *  cd /path/to/pet-care-os && python -m cron.reorder_check
"""

from __future__ import annotations


def main() -> int:  # pragma: no cover
    raise NotImplementedError(
        "Phase 2: project cycle run-out (cycle start + ~72 days) and, at the 10-day lead, "
        "call petcareos.ticktick.create_reorder_reminder()."
    )


if __name__ == "__main__":
    raise SystemExit(main())
