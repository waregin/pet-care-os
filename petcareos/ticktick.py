"""TickTick write-back — PHASE 2 (reorder reminders). Not implemented in v1.

External Brain OS convention (mirrors priority-os): surface an action as a TickTick task
carrying a tag + due date + reminder, rather than a notification the user can lose. For
Pet Care OS the reorder reminder is cycle-level: ~10 days before the current 144-can /
~72-day cycle is projected to run out, create one task "Reorder cat food cycle".

Left as a stub so the seam is obvious and the dependency surface is documented.
"""

from __future__ import annotations

from datetime import date


def create_reorder_reminder(due: date, tag: str = "cat-food") -> None:  # pragma: no cover
    raise NotImplementedError(
        "Phase 2: create a TickTick task (tag + due date + reminder) via the priority-os "
        "write-back pattern. See issue tracker."
    )
