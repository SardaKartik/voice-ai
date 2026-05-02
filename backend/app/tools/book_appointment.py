"""Book a new appointment."""

from __future__ import annotations

import logging

from livekit.agents import RunContext

from app.database.db import insert_appointment

logger = logging.getLogger(__name__)


async def book_appointment(
    ctx: RunContext,
    phone_number: str,
    patient_name: str,
    department: str,
    date: str,
    time: str,
) -> str:
    """Create a confirmed appointment and return a voice-friendly response.

    Args:
        ctx: LiveKit run context for the active voice interaction.
        phone_number: Caller phone number used as patient identifier.
        patient_name: Full name of the patient.
        department: Department or clinic unit.
        date: Appointment date (ISO or agreed format).
        time: Appointment time as confirmed with the caller.

    Returns:
        A confirmation message with appointment reference when successful, or a
        conflict/fallback message when booking cannot be completed.
    """
    _ = ctx
    try:
        appointment = insert_appointment(
            phone_number,
            patient_name,
            department,
            date,
            time,
        )
        if appointment is None:
            return (
                "I'm sorry, that slot is no longer available. "
                "Let me check other options for you."
            )

        appointment_id = appointment["id"]
        return (
            f"Your appointment is confirmed. {patient_name}, you are booked "
            f"for {department} on {date} at {time}. "
            f"Your reference ID is MYK-{appointment_id}."
        )
    except Exception as exc:  # pragma: no cover - safety fallback for voice flow
        logger.exception(
            "Failed to book appointment for phone=%s department=%s date=%s time=%s: %s",
            phone_number,
            department,
            date,
            time,
            exc,
        )
        return (
            "I am having trouble booking your appointment right now. "
            "Please try again in a moment."
        )
