"""Signal that the caller has finished and the agent session can end."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from livekit.agents import RunContext

logger = logging.getLogger(__name__)


async def end_conversation(
    ctx: RunContext, summary: str, user_preferences: str = ""
) -> str:
    """End the call and publish a JSON summary on the room data channel.

    Args:
        ctx: LiveKit run context for the active voice session (room access).
        summary: Short summary of the conversation for downstream clients.
        user_preferences: Optional preferences captured during the call.

    Returns:
        A fixed spoken closing line for the caller.
    """
    result = {
        "summary": summary,
        "preferences": user_preferences,
        "timestamp": datetime.now().isoformat(),
        "status": "ended",
    }
    payload = json.dumps(result).encode("utf-8")

    try:
        room = getattr(ctx, "room", None)
        if room is None:
            room = ctx.session.room_io.room
        await room.local_participant.publish_data(
            payload,
            reliable=True,
            topic="call_summary",
        )
    except Exception as exc:  # noqa: BLE001 — never block hang-up on publish failures
        logger.warning("Could not publish call_summary on data channel: %s", exc)

    return (
        "Thank you for calling Healthcare. "
        "We look forward to seeing you. Take care!"
    )
