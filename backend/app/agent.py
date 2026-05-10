"""LiveKit Voice AI agent worker for Healthcare.ai."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeVar

# Ensure package imports work when started as `python app/agent.py start`.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, RunContext, function_tool
from livekit.plugins import cartesia, deepgram, openai, silero

from app.tools.book_appointment import book_appointment
from app.tools.cancel_appointment import cancel_appointment
from app.tools.end_conversation import end_conversation
from app.tools.fetch_slots import fetch_slots
from app.tools.identify_user import identify_user
from app.tools.modify_appointment import modify_appointment
from app.tools.retrieve_appointments import retrieve_appointments

from app.prompts import get_system_prompt

logger = logging.getLogger("healthcare.agent")

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


# -----------------------------------------------------------------------------
# Tool call event publishing
# -----------------------------------------------------------------------------
def _build_tools(job_room: Any) -> list[Any]:
    """Register all Healthcare.ai appointment tools, capturing job_room for data events.

    RunContext (passed to tool functions in livekit-agents 1.x) no longer
    exposes .room, so the LiveKit Room from JobContext is captured here via
    closure so tool event publishing doesn't depend on RunContext internals.
    """
    async def _publish(tool_name: str) -> None:
        event = {
            "type": "tool_call",
            "tool": tool_name,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await job_room.local_participant.publish_data(
            json.dumps(event).encode(),
            reliable=True,
        )

    def _wrap(fn: F) -> Any:
        tool_name = fn.__name__

        @wraps(fn)
        async def _wrapped(ctx: RunContext, *args: Any, **kwargs: Any) -> Any:
            try:
                result = await fn(ctx, *args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Tool %s failed: %s", tool_name, exc)
                raise
            try:
                await _publish(tool_name)
            except Exception as pub_exc:  # noqa: BLE001
                logger.warning("Failed to publish tool event for %s: %s", tool_name, pub_exc)
            return result

        return function_tool(_wrapped)

    raw_tools = [
        identify_user,
        fetch_slots,
        book_appointment,
        retrieve_appointments,
        cancel_appointment,
        modify_appointment,
        end_conversation,
    ]
    return [_wrap(tool_fn) for tool_fn in raw_tools]


# -----------------------------------------------------------------------------
# Main job entrypoint
# -----------------------------------------------------------------------------
async def entrypoint(ctx: JobContext) -> None:
    """Connect to room, start voice session, and greet the caller."""
    room_name = ctx.room.name
    try:
        # ── Step 1: Connect to the LiveKit room ──────────────────────────────
        # ctx.connect() joins the room as a server-side participant. Until this
        # returns, the agent cannot publish audio or receive participant events.
        logger.info("[%s] Agent connecting to room...", room_name)
        await ctx.connect()
        logger.info(
            "[%s] Connected. Existing participants: %d",
            room_name,
            len(ctx.room.remote_participants),
        )

        # ── Step 2: Room lifecycle event hooks ───────────────────────────────
        def _on_participant_connected(participant: Any) -> None:
            identity = getattr(participant, "identity", "unknown")
            kind = getattr(participant, "kind", "unknown")
            logger.info(
                "[%s] Participant connected — identity=%s kind=%s",
                room_name, identity, kind,
            )

        def _on_participant_disconnected(participant: Any) -> None:
            identity = getattr(participant, "identity", "unknown")
            logger.info(
                "[%s] Participant disconnected — identity=%s",
                room_name, identity,
            )

        ctx.room.on("participant_connected", _on_participant_connected)
        ctx.room.on("participant_disconnected", _on_participant_disconnected)

        # ── Step 3: Validate required Azure OpenAI credentials ───────────────
        # All four variables must be non-empty; a missing one means the LLM
        # call will fail at runtime with a cryptic auth error, so we fail fast.
        logger.debug("[%s] Reading Azure OpenAI environment variables...", room_name)
        deployment = (os.getenv("AZURE_OPENAI_DEPLOYMENT") or "").strip()
        endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip().rstrip("/")
        api_key = (os.getenv("AZURE_OPENAI_API_KEY") or "").strip()
        api_version = (os.getenv("AZURE_OPENAI_API_VERSION") or "").strip()
        missing = [
            name
            for name, value in (
                ("AZURE_OPENAI_DEPLOYMENT", deployment),
                ("AZURE_OPENAI_ENDPOINT", endpoint),
                ("AZURE_OPENAI_API_KEY", api_key),
                ("AZURE_OPENAI_API_VERSION", api_version),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        # ── Step 4: Initialise STT (Deepgram) ────────────────────────────────
        # endpointing_ms: silence duration before Deepgram closes an utterance
        # and emits a final transcript. Must be long enough to span natural
        # inter-word pauses (200–400 ms) or Deepgram fires a final mid-sentence
        # while Silero VAD still sees the user as speaking. That conflict triggers
        # "stt end of speech received while user is speaking, resetting vad" and
        # the SDK discards the whole utterance — the agent appears deaf.
        # 800 ms ensures finals only arrive at real sentence boundaries.
        logger.debug("[%s] Initialising Deepgram STT (nova-2, endpointing=800 ms)...", room_name)
        stt = deepgram.STT(
            model="nova-2",
            language="en-US",
            endpointing_ms=800,
        )
        logger.info("[%s] STT ready (Deepgram nova-2)", room_name)

        # ── Step 5: Initialise LLM (Azure OpenAI) ────────────────────────────
        logger.debug("[%s] Initialising Azure OpenAI LLM (%s)...", room_name, deployment)
        llm = openai.LLM.with_azure(
            model=deployment,
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        logger.info("[%s] LLM ready (Azure OpenAI / %s)", room_name, deployment)

        # ── Step 6: Initialise TTS (Cartesia) ────────────────────────────────
        logger.debug("[%s] Initialising Cartesia TTS...", room_name)
        tts = cartesia.TTS()
        logger.info("[%s] TTS ready (Cartesia)", room_name)

        # ── Step 7: Initialise VAD (Silero) ──────────────────────────────────
        # activation_threshold=0.55: default is 0.5. Slightly above default to
        #   ignore light background noise, but low enough to reliably detect
        #   normal human speech. 0.7 was too high — Silero stopped detecting the
        #   user's voice entirely, so no VAD turn ever opened and the LLM was
        #   never called (transcript appeared in logs but session stayed silent).
        # min_silence_duration=0.5: 500 ms of silence after speech ends before
        #   the turn closes. Matches the default closely but is explicit so we
        #   can tune it without hunting for where it's set.
        logger.debug("[%s] Loading Silero VAD model...", room_name)
        vad = silero.VAD.load(
            activation_threshold=0.55,
            min_silence_duration=0.5,
        )
        logger.info("[%s] VAD ready (Silero, threshold=0.55, silence=0.5s)", room_name)

        # ── Step 8: Build agent with tools ───────────────────────────────────
        tools = _build_tools(ctx.room)
        logger.info("[%s] Agent tools registered: %d tools", room_name, len(tools))
        agent = Agent(instructions=get_system_prompt(), tools=tools)

        # ── Step 9: Create AgentSession ──────────────────────────────────────
        # turn_detection=None: let the SDK auto-select the best available mode.
        #   With livekit-agents[turn-detector] installed the SDK picks
        #   "realtime_llm" — the neural semantic turn detector. This is the
        #   purpose-built option: it analyses the transcript to decide whether
        #   the user has finished speaking rather than relying on audio silence
        #   thresholds, so it handles overlapping speech and trailing pauses far
        #   better than VAD endpointing.
        #   NOTE: do NOT use "stt" — that mode causes a death-loop where
        #   Deepgram END_OF_SPEECH resets Silero → Silero fires START_OF_SPEECH
        #   (echo) → cancels the committed turn → repeat, Kiara never replies.
        # vad=vad: Silero is kept for INTERRUPTION detection (detecting mid-
        #   sentence user speech while Kiara is talking), not turn detection.
        # aec_warmup_duration=0.3: discard 300 ms of STT input after Kiara
        #   speaks to suppress TTS echo bleed into Silero.
        # endpointing.min_delay / max_delay: window after turn-detector fires
        #   before the turn is committed to the LLM.
        logger.debug("[%s] Creating AgentSession...", room_name)
        session = AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
            aec_warmup_duration=0.3,
            turn_handling={
                "turn_detection": None,
                "endpointing": {
                    "min_delay": 0.3,
                    "max_delay": 6.0,
                },
            },
        )
        logger.info("[%s] AgentSession created", room_name)

        # ── Step 10: Session event hooks ─────────────────────────────────────
        def _on_user_transcript(ev: Any) -> None:
            text = (getattr(ev, "transcript", None) or "").strip()
            is_final = getattr(ev, "is_final", False)
            if is_final and text:
                logger.info("[%s] User said (final): %s", room_name, text)
            elif text:
                # Interim transcripts are useful during debugging to confirm
                # that STT is receiving audio before Deepgram emits a final.
                logger.debug("[%s] User said (interim): %s", room_name, text)

        def _on_agent_speaking_started(ev: Any) -> None:  # noqa: ARG001
            logger.info("[%s] Agent started speaking", room_name)

        def _on_agent_speaking_stopped(ev: Any) -> None:  # noqa: ARG001
            logger.info("[%s] Agent stopped speaking", room_name)

        def _on_user_started_speaking(ev: Any) -> None:  # noqa: ARG001
            logger.info("[%s] User started speaking (VAD)", room_name)

        def _on_user_stopped_speaking(ev: Any) -> None:  # noqa: ARG001
            logger.info("[%s] User stopped speaking (VAD)", room_name)

        def _on_agent_state_changed(ev: Any) -> None:
            old = getattr(ev, "old_state", None)
            new = getattr(ev, "new_state", getattr(ev, "state", "unknown"))
            if old:
                logger.info("[%s] Agent state: %s → %s", room_name, old, new)
            else:
                logger.info("[%s] Agent state: %s", room_name, new)

        def _on_conversation_item_added(ev: Any) -> None:
            item = getattr(ev, "item", None)
            if item is None:
                return
            role = getattr(item, "role", "unknown")
            if role != "assistant":
                return
            # content may be a string or a list of content blocks
            content = getattr(item, "text_content", None) or getattr(item, "content", "")
            if isinstance(content, list):
                content = " ".join(
                    getattr(c, "text", str(c)) for c in content
                    if getattr(c, "text", None) or isinstance(c, str)
                )
            text = (str(content) if content else "").strip()
            if text:
                logger.info("[%s] Kiara said: %s", room_name, text)

        session.on("user_input_transcribed", _on_user_transcript)
        session.on("agent_speaking_started", _on_agent_speaking_started)
        session.on("agent_speaking_stopped", _on_agent_speaking_stopped)
        session.on("user_started_speaking", _on_user_started_speaking)
        session.on("user_stopped_speaking", _on_user_stopped_speaking)
        session.on("agent_state_changed", _on_agent_state_changed)
        session.on("conversation_item_added", _on_conversation_item_added)

        # ── Step 11: Start session and deliver opening greeting ───────────────
        logger.info("[%s] Starting agent session...", room_name)
        await session.start(room=ctx.room, agent=agent)
        logger.info("[%s] Agent session started successfully", room_name)

        # allow_interruptions=False: greeting must finish before the session
        # enters listening mode. With allow_interruptions=True, user speech
        # during the greeting interrupted it and was never processed as a turn —
        # the LLM was never called. Making it non-interruptible + keeping
        # discard_audio_if_uninterruptible=False (in turn_handling above) means
        # any speech during the greeting is buffered, not discarded, and will
        # be processed once the greeting finishes.
        logger.debug("[%s] Delivering opening greeting (non-interruptible)...", room_name)
        await session.say(
            "Hi, I'm Kiara from Healthcare. How can I help you?",
            allow_interruptions=False,
        )
        logger.info("[%s] Opening greeting delivered — now listening", room_name)

    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] Agent entrypoint failed: %s", room_name, exc)
        raise


# -----------------------------------------------------------------------------
# Worker bootstrap
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    load_dotenv()
    agent_name = os.getenv("LIVEKIT_AGENT_NAME", "healthcare-agent").strip() or "healthcare-agent"
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name=agent_name)
    )
