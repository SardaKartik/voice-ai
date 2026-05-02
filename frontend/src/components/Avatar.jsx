/**
 * Center-screen animated avatar for Kara's speaking/listening state.
 *
 * @param {{ isSpeaking?: boolean }} props
 */
export default function Avatar({ isSpeaking = false }) {
  const ringColor = isSpeaking ? "#22c55e" : "#8b949e";
  const glowColor = isSpeaking ? "rgba(34, 197, 94, 0.45)" : "rgba(139, 148, 158, 0.2)";

  const wrapperStyle = {
    position: "fixed",
    inset: 0,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    pointerEvents: "none",
    zIndex: 20,
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  };

  const outerRingStyle = {
    width: "220px",
    height: "220px",
    borderRadius: "50%",
    border: `4px solid ${ringColor}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: `0 0 0 6px ${glowColor}`,
    animation: isSpeaking ? "karaPulse 1.3s ease-in-out infinite" : "none",
    transition: "all 220ms ease",
    background: "rgba(9, 14, 22, 0.65)",
  };

  const innerCircleStyle = {
    width: "160px",
    height: "160px",
    borderRadius: "50%",
    background: isSpeaking
      ? "linear-gradient(180deg, #1c2f1f 0%, #102013 100%)"
      : "linear-gradient(180deg, #1b232d 0%, #11161c 100%)",
    border: `2px solid ${isSpeaking ? "rgba(34, 197, 94, 0.45)" : "rgba(139, 148, 158, 0.35)"}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#f3f4f6",
    fontSize: "56px",
    lineHeight: 1,
    transition: "all 220ms ease",
  };

  const labelStyle = {
    marginTop: "18px",
    color: isSpeaking ? "#86efac" : "#c2c8cf",
    fontSize: "15px",
    fontWeight: 600,
    letterSpacing: "0.01em",
    textShadow: "0 1px 3px rgba(0, 0, 0, 0.35)",
  };

  return (
    <div style={wrapperStyle} aria-live="polite" aria-label="Kara voice avatar">
      <style>{`
        @keyframes karaPulse {
          0% {
            transform: scale(1);
            box-shadow: 0 0 0 6px ${glowColor};
          }
          50% {
            transform: scale(1.04);
            box-shadow: 0 0 0 14px rgba(34, 197, 94, 0.15);
          }
          100% {
            transform: scale(1);
            box-shadow: 0 0 0 6px ${glowColor};
          }
        }
      `}</style>

      <div style={outerRingStyle}>
        <div
          style={innerCircleStyle}
          role="img"
          aria-label={isSpeaking ? "Microphone active" : "Kara avatar"}
        >
          {isSpeaking ? "🎙️" : "🙂"}
        </div>
      </div>

      <p style={labelStyle}>
        {isSpeaking ? "Kara is speaking..." : "Kara is listening..."}
      </p>
    </div>
  );
}
