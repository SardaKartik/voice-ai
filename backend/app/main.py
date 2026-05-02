from contextlib import asynccontextmanager
import logging
import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from livekit import api

from app.database.db import get_appointments, init_db

load_dotenv()

logger = logging.getLogger("mykare.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize application resources once when the API starts."""
    try:
        init_db()
        logger.info("Database initialized on API startup")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to initialize database on startup: %s", exc)
        raise
    yield


app = FastAPI(title="Mykare Voice API", lifespan=lifespan)

# Allow cross-origin calls from frontend clients (including Vercel deployments).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Healthcheck endpoint used by Docker compose and uptime checks."""
    return {"status": "ok", "service": "mykare-voice-api"}


@app.get("/token")
async def token(
    room: str | None = Query(default=None),
    participant: str = Query(default="user"),
) -> dict[str, str]:
    """Create a LiveKit room-join token and request agent dispatch for this session.

    If ``room`` is omitted, a unique room name is generated so the room is created
    fresh on connect — required for token-based agent dispatch (existing rooms
    would otherwise ignore the embedded dispatch).
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    ws_url = os.getenv("LIVEKIT_URL")
    agent_name = os.getenv("LIVEKIT_AGENT_NAME", "mykare-agent").strip() or "mykare-agent"

    if not api_key or not api_secret or not ws_url:
        logger.error("Missing LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET")
        raise HTTPException(
            status_code=500,
            detail="LiveKit environment variables are not configured correctly.",
        )

    try:
        room_name = (room or "").strip() or f"mykare-{uuid4()}"
        grant = api.VideoGrants(room_join=True, room=room_name)
        jwt = (
            api.AccessToken(api_key=api_key, api_secret=api_secret)
            .with_identity(participant)
            .with_grants(grant)
            .with_room_config(
                api.RoomConfiguration(
                    agents=[api.RoomAgentDispatch(agent_name=agent_name)],
                ),
            )
            .to_jwt()
        )
        return {"token": jwt, "ws_url": ws_url, "room": room_name}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate LiveKit token: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate token.") from exc


@app.get("/appointments/{phone_number}")
async def appointments(phone_number: str) -> list[dict]:
    """Fetch confirmed appointments for a caller phone number."""
    try:
        return get_appointments(phone_number)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch appointments for %s: %s", phone_number, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch appointments.") from exc
