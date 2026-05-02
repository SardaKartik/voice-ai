"""List existing appointments for the identified patient."""

from __future__ import annotations

import logging

from livekit.agents import RunContext

from app.database.db import get_appointments

logger = logging.getLogger(__name__)


async def retrieve_appointments(ctx: RunContext, phone_number: str) -> str:
    """Return a short, voice-friendly summary of upcoming appointments.

    Args:
        ctx: LiveKit run context for the active voice session.
        phone_number: Caller phone number used to look up appointments.

    Returns:
        A speech-friendly summary of confirmed appointments, or a no-results/
        fallback message when nothing is found or an error occurs.
    """
    _ = ctx
    try:
        appointments = get_appointments(phone_number)
    except Exception as exc:  # pragma: no cover - safety fallback for voice flow
        logger.exception("Failed to retrieve appointments for %s: %s", phone_number, exc)
        return (
            "I'm having trouble retrieving your appointments right now. "
            "Please try again in a moment."
        )

    if not appointments:
        return "I don't see any upcoming appointments for your number."

    lines = [f"You have {len(appointments)} appointment(s)."]
    for index, appt in enumerate(appointments, start=1):
        lines.append(
            f"{index}. {appt['department']} on {appt['date']} at {appt['time']}."
        )

    return "\n".join(lines)
