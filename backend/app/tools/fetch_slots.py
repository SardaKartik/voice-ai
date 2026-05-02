"""Fetch available appointment slots."""

from __future__ import annotations

import logging
from datetime import datetime

from livekit.agents import RunContext

from app.database.db import get_connection

logger = logging.getLogger(__name__)

AVAILABLE_SLOTS = {
    "Monday": ["9:00 AM", "10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"],
    "Tuesday": ["9:00 AM", "10:30 AM", "12:00 PM", "2:30 PM", "4:00 PM"],
    "Wednesday": ["9:00 AM", "11:00 AM", "1:00 PM", "3:00 PM"],
    "Thursday": ["10:00 AM", "11:30 AM", "2:00 PM", "4:30 PM"],
    "Friday": ["9:00 AM", "10:00 AM", "12:00 PM", "3:00 PM"],
    "Saturday": ["9:00 AM", "10:00 AM", "11:00 AM"],
}


async def fetch_slots(ctx: RunContext, date: str, department: str) -> str:
    """Return available slots for a department and date.

    Args:
        ctx: LiveKit run context for the current voice interaction.
        date: Appointment date in YYYY-MM-DD format.
        department: Department to check slot availability for.

    Returns:
        A voice-friendly prompt listing open times, or a fallback message when
        no slots remain or the provided date format is invalid.
    """
    _ = ctx

    try:
        weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    except ValueError:
        return (
            "I couldn't understand that date format. "
            "Please share the date as YYYY-MM-DD."
        )

    base_slots = AVAILABLE_SLOTS.get(weekday, [])
    if not base_slots:
        return (
            f"I'm sorry, no slots are available for {department} on {date}. "
            "Would you like to try another date?"
        )

    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT time
                FROM appointments
                WHERE date = ? AND department = ? AND status = 'confirmed'
                """,
                (date, department),
            ).fetchall()
    except Exception as exc:  # pragma: no cover - safety fallback in voice flow
        logger.exception(
            "Failed to fetch booked slots for department=%s date=%s: %s",
            department,
            date,
            exc,
        )
        return (
            "I'm having trouble checking available slots right now. "
            "Please try again in a moment."
        )

    booked_times = {row["time"] for row in rows}
    open_slots = [slot for slot in base_slots if slot not in booked_times]

    if not open_slots:
        return (
            f"I'm sorry, no slots are available for {department} on {date}. "
            "Would you like to try another date?"
        )

    slot_list = ", ".join(open_slots)
    return (
        f"For {department} on {date}, I have slots at {slot_list}. "
        "Which works best for you?"
    )
