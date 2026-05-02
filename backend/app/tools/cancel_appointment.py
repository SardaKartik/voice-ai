"""Cancel an existing appointment."""

from __future__ import annotations

import logging

from livekit.agents import RunContext

from app.database.db import cancel_appointment as db_cancel

logger = logging.getLogger(__name__)


async def cancel_appointment(
    ctx: RunContext, appointment_id: int, phone_number: str
) -> str:
    """Cancel a booked visit for the caller's phone number.

    Args:
        ctx: LiveKit run context for the active voice session.
        appointment_id: Numeric appointment record ID (same as MYK-* reference).
        phone_number: Caller phone number; must match the booking owner.

    Returns:
        A confirmation message when cancelled, a clarification prompt when the
        booking cannot be found for this number, or a fallback on errors.
    """
    _ = ctx
    try:
        cancelled = db_cancel(appointment_id, phone_number)
    except Exception as exc:  # pragma: no cover - safety fallback for voice flow
        logger.exception(
            "Failed to cancel appointment id=%s phone=%s: %s",
            appointment_id,
            phone_number,
            exc,
        )
        return (
            "I'm having trouble cancelling that appointment right now. "
            "Please try again in a moment."
        )

    if not cancelled:
        return (
            "I couldn't find that appointment. "
            "Could you confirm the reference ID?"
        )

    return (
        f"Done. Your appointment MYK-{appointment_id} "
        "has been cancelled. Is there anything else I can help with?"
    )
