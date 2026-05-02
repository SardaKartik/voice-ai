"""Resolve caller identity for appointment flows."""

from __future__ import annotations

import logging

from livekit.agents import RunContext

from app.database.db import get_user, upsert_user

logger = logging.getLogger(__name__)


async def identify_user(
    ctx: RunContext, phone_number: str, name: str | None = None
) -> str:
    """Identify or register a caller in the SQLite-backed user table.

    Args:
        ctx: LiveKit run context for the active voice session.
        phone_number: Caller phone number used as the patient identifier.
        name: Optional patient name collected during the conversation.

    Returns:
        A user-facing response string describing whether the caller is returning,
        newly registered, or has just provided their name.
    """
    _ = ctx
    try:
        existing_user = get_user(phone_number)
        user = upsert_user(phone_number, name)

        if name is not None:
            return f"Thank you {name}, I've got your details."

        if existing_user and existing_user.get("name"):
            return f"Welcome back {existing_user['name']}. How can I help you today?"

        if not existing_user:
            return "Got it, I've noted your number. Could I also get your name?"

        if user.get("name"):
            return f"Welcome back {user['name']}. How can I help you today?"

        return "Got it, I've noted your number. Could I also get your name?"
    except Exception as exc:  # pragma: no cover - safety fallback for voice flow
        logger.exception("Failed to identify user for %s: %s", phone_number, exc)
        return "I am having trouble accessing your profile right now. Please try again in a moment."
