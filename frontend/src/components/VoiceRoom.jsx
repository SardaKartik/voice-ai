import { useCallback, useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track } from "livekit-client";

import { getToken } from "../api/backend";
import { useToolEvents } from "../hooks/useToolEvents";

import Avatar from "./Avatar";
import ToolCallFeed from "./ToolCallFeed";
import CallSummary from "./CallSummary";
import ControlBar from "./ControlBar";

/**
 * Build RMS-based speaking detection for a remote audio track.
 * @param {import("livekit-client").RemoteTrack} track
 * @param {(speaking: boolean) => void} setSpeaking
 */
function startRemoteAudioLevelMonitor(track, setSpeaking) {
  const mediaTrack = track.mediaStreamTrack;
  if (!mediaTrack) {
    return () => {};
  }

  const audioCtx = new AudioContext();
  const stream = new MediaStream([mediaTrack]);
  const source = audioCtx.createMediaStreamSource(stream);
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 1024;
  analyser.smoothingTimeConstant = 0.35;
  source.connect(analyser);

  const buf = new Float32Array(analyser.fftSize);
  const threshold = 0.012;
  let raf = 0;

  const tick = () => {
    analyser.getFloatTimeDomainData(buf);
    let sum = 0;
    for (let i = 0; i < buf.length; i += 1) {
      const s = buf[i];
      sum += s * s;
    }
    const rms = Math.sqrt(sum / buf.length);
    setSpeaking(rms > threshold);
    raf = requestAnimationFrame(tick);
  };

  audioCtx.resume().catch(() => {});
  raf = requestAnimationFrame(tick);

  return () => {
    cancelAnimationFrame(raf);
    source.disconnect();
    analyser.disconnect();
    audioCtx.close().catch(() => {});
    setSpeaking(false);
  };
}

/**
 * Main LiveKit voice session UI (avatar, tool feed, summary, controls).
 */
export default function VoiceRoom() {
  const [room] = useState(() => new Room());
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [agentSpeaking, setAgentSpeaking] = useState(false);

  const { toolEvents, summary } = useToolEvents(room);
  const speakingCleanupRef = useRef(null);
  const audioTracksRef = useRef([]);

  const connect = useCallback(async () => {
    // Resume AudioContext NOW while still inside the click-handler gesture chain.
    // Any await before this call (getToken, room.connect) breaks the gesture
    // chain and the browser silently blocks autoplay for the agent's audio.
    room.startAudio().catch((e) => {
      console.warn("[VoiceRoom] startAudio (early):", e);
    });
    setConnecting(true);
    try {
      const { token, ws_url } = await getToken();
      await room.connect(ws_url, token);
      await room.localParticipant.setMicrophoneEnabled(true);
      setIsMuted(false);
      setConnected(true);
    } catch (err) {
      console.error("[VoiceRoom] connect failed:", err);
      setConnected(false);
    } finally {
      setConnecting(false);
    }
  }, [room]);

  const disconnect = useCallback(() => {
    if (speakingCleanupRef.current) {
      speakingCleanupRef.current();
      speakingCleanupRef.current = null;
    }
    audioTracksRef.current.forEach((t) => t.detach());
    audioTracksRef.current = [];
    room.disconnect();
    setConnected(false);
    setAgentSpeaking(false);
  }, [room]);

  const toggleMute = useCallback(async () => {
    if (!connected) return;
    const next = !isMuted;
    try {
      await room.localParticipant.setMicrophoneEnabled(next);
      setIsMuted(next);
    } catch (err) {
      console.error("[VoiceRoom] toggleMute failed:", err);
    }
  }, [connected, isMuted, room]);

  useEffect(() => {
    if (!connected) {
      if (speakingCleanupRef.current) {
        speakingCleanupRef.current();
        speakingCleanupRef.current = null;
      }
      audioTracksRef.current.forEach((t) => t.detach());
      audioTracksRef.current = [];
      setAgentSpeaking(false);
      return undefined;
    }

    /** @param {import("livekit-client").RemoteTrack} track */
    function onTrackSubscribed(track, _publication, participant) {
      if (participant.isLocal) return;
      if (track.kind !== Track.Kind.Audio) return;

      // Attach the track to an <audio> element so it actually plays through
      // the speakers. track.attach() creates the element; without this call
      // the audio is received but never routed to any output device.
      const audioEl = track.attach();
      audioEl.style.display = "none";
      document.body.appendChild(audioEl);
      audioTracksRef.current.push(track);

      // Ensure AudioContext is running — covers the race where the agent
      // publishes audio during room.connect(), before this handler was set up.
      room.startAudio().catch(() => {});

      if (speakingCleanupRef.current) {
        speakingCleanupRef.current();
        speakingCleanupRef.current = null;
      }
      speakingCleanupRef.current = startRemoteAudioLevelMonitor(
        track,
        setAgentSpeaking
      );
    }

    // TrackSubscribed fires during room.connect(), before this useEffect runs
    // (React re-renders after setConnected(true)). Walk existing participants
    // to catch audio tracks that were already subscribed.
    for (const participant of room.remoteParticipants.values()) {
      for (const pub of participant.audioTrackPublications.values()) {
        if (pub.track && pub.isSubscribed) {
          onTrackSubscribed(pub.track, pub, participant);
        }
      }
    }

    room.on(RoomEvent.TrackSubscribed, onTrackSubscribed);
    return () => {
      room.off(RoomEvent.TrackSubscribed, onTrackSubscribed);
      if (speakingCleanupRef.current) {
        speakingCleanupRef.current();
        speakingCleanupRef.current = null;
      }
    };
  }, [connected, room]);

  const shellStyle = {
    minHeight: "100vh",
    background: "#0a0e14",
    color: "#e8eaed",
    position: "relative",
    overflow: "hidden",
    paddingRight: "min(360px, 100vw)",
    boxSizing: "border-box",
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  };

  const titleStyle = {
    position: "fixed",
    top: "20px",
    left: "24px",
    zIndex: 50,
    margin: 0,
    fontSize: "20px",
    fontWeight: 700,
    letterSpacing: "0.02em",
    color: "#f8fafc",
    textShadow: "0 2px 8px rgba(0,0,0,0.4)",
  };

  const bottomStackStyle = {
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 45,
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    pointerEvents: "auto",
  };

  return (
    <div style={shellStyle}>
      <h1 style={titleStyle}>Healthcare.ai</h1>

      <Avatar isSpeaking={agentSpeaking} />

      <ToolCallFeed events={toolEvents} />

      <div style={bottomStackStyle}>
        {summary != null ? (
          <CallSummary data={summary} embedded />
        ) : null}
        <ControlBar
          connected={connected}
          connecting={connecting}
          isMuted={isMuted}
          onConnect={connect}
          onDisconnect={disconnect}
          onToggleMute={toggleMute}
        />
      </div>
    </div>
  );
}
