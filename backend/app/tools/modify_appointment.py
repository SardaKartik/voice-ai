"""Reschedule or modify an appointment."""

from __future__ import annotations

import logging

from livekit.agents import RunContext

from app.database.db import modify_appointment as db_modify

logger = logging.getLogger(__name__)


async def modify_appointment(
    ctx: RunContext, appointment_id: int, new_date: str, new_time: str
) -> str:
    """Reschedule an appointment to a new date and time.

    Args:
        ctx: LiveKit run context for the active voice session.
        appointment_id: Numeric ID of the appointment to update.
        new_date: Target date (YYYY-MM-DD).
        new_time: Target time (e.g. HH:MM AM/PM).

    Returns:
        A confirmation when rescheduled, a conflict message if the slot is taken,
        or a fallback when an error occurs.
    """
    _ = ctx
    try:
        row = db_modify(appointment_id, new_date, new_time)
    except Exception as exc:  # pragma: no cover - safety fallback for voice flow
        logger.exception(
            "Failed to modify appointment id=%s to %s %s: %s",
            appointment_id,
            new_date,
            new_time,
            exc,
        )
        return (
            "I'm having trouble rescheduling that appointment right now. "
            "Please try again in a moment."
        )

    if row is None:
        return (
            "That new slot is already taken. "
            "Would you like to try a different time?"
        )

    return (
        f"Done. Your appointment has been rescheduled to "
        f"{new_date} at {new_time}."
    )
