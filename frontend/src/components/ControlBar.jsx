/**
 * Bottom control bar for LiveKit call actions.
 *
 * @param {{
 *   connected: boolean,
 *   isMuted: boolean,
 *   onConnect: () => void,
 *   onDisconnect: () => void,
 *   onToggleMute: () => void,
 *   connecting?: boolean,
 * }} props
 *
 * Use `connecting` while the room is joining so the bar can show the disabled
 * "Connecting..." state (optional; defaults to false).
 */
export default function ControlBar({
  connected,
  isMuted,
  onConnect,
  onDisconnect,
  onToggleMute,
  connecting = false,
}) {
  const barStyle = {
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 45,
    padding: "14px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
    background: "rgba(15, 20, 26, 0.92)",
    borderTop: "1px solid rgba(255, 255, 255, 0.08)",
    boxShadow: "0 -4px 24px rgba(0, 0, 0, 0.25)",
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  };

  const btnBase = {
    padding: "12px 22px",
    fontSize: "14px",
    fontWeight: 600,
    borderRadius: "10px",
    border: "none",
    cursor: "pointer",
    transition: "opacity 0.15s ease, transform 0.1s ease",
  };

  const startStyle = {
    ...btnBase,
    background: "#16a34a",
    color: "#fff",
    boxShadow: "0 2px 8px rgba(22, 163, 74, 0.35)",
  };

  const connectingStyle = {
    ...btnBase,
    background: "#374151",
    color: "rgba(255, 255, 255, 0.75)",
    cursor: "not-allowed",
    opacity: 0.85,
  };

  const muteStyle = {
    ...btnBase,
    background: isMuted ? "#4b5563" : "#2563eb",
    color: "#fff",
  };

  const endStyle = {
    ...btnBase,
    background: "#dc2626",
    color: "#fff",
    boxShadow: "0 2px 8px rgba(220, 38, 38, 0.35)",
  };

  let content;
  if (connecting) {
    content = (
      <button type="button" style={connectingStyle} disabled>
        Connecting...
      </button>
    );
  } else if (!connected) {
    content = (
      <button type="button" style={startStyle} onClick={onConnect}>
        Start Call
      </button>
    );
  } else {
    content = (
      <>
        <button type="button" style={muteStyle} onClick={onToggleMute}>
          {isMuted ? "Unmute" : "Mute"}
        </button>
        <button type="button" style={endStyle} onClick={onDisconnect}>
          End Call
        </button>
      </>
    );
  }

  return (
    <nav style={barStyle} aria-label="Call controls">
      {content}
    </nav>
  );
}
