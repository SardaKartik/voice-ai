import "./ToolCallFeed.css";

const TOOL_DISPLAY = {
  identify_user: { icon: "👤", label: "Identifying patient..." },
  fetch_slots: { icon: "📅", label: "Checking available slots..." },
  book_appointment: { icon: "✅", label: "Booking appointment..." },
  retrieve_appointments: { icon: "📋", label: "Retrieving appointments..." },
  cancel_appointment: { icon: "❌", label: "Cancelling appointment..." },
  modify_appointment: { icon: "✏️", label: "Rescheduling appointment..." },
  end_conversation: { icon: "🏁", label: "Wrapping up call..." },
};

const panelStyle = {
  position: "fixed",
  top: 0,
  right: 0,
  width: "min(360px, 100vw)",
  height: "100vh",
  boxSizing: "border-box",
  padding: "20px 16px",
  background: "linear-gradient(180deg, #0f1419 0%, #1a2332 100%)",
  borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
  boxShadow: "-8px 0 24px rgba(0, 0, 0, 0.25)",
  display: "flex",
  flexDirection: "column",
  gap: "16px",
  zIndex: 50,
  fontFamily:
    'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  color: "#e8eaed",
};

const titleStyle = {
  margin: 0,
  fontSize: "15px",
  fontWeight: 600,
  letterSpacing: "0.02em",
  color: "#f1f3f4",
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
  paddingBottom: "12px",
};

const listStyle = {
  listStyle: "none",
  margin: 0,
  padding: 0,
  overflowY: "auto",
  flex: 1,
  display: "flex",
  flexDirection: "column",
  gap: "10px",
};

const emptyStyle = {
  margin: 0,
  padding: "24px 12px",
  textAlign: "center",
  fontSize: "13px",
  color: "rgba(255, 255, 255, 0.45)",
  lineHeight: 1.5,
};

const itemStyle = {
  display: "flex",
  alignItems: "flex-start",
  gap: "10px",
  padding: "12px 12px",
  background: "rgba(255, 255, 255, 0.06)",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.06)",
};

const iconStyle = {
  fontSize: "18px",
  lineHeight: 1.2,
  flexShrink: 0,
};

const labelBlockStyle = {
  flex: 1,
  minWidth: 0,
};

const labelTextStyle = {
  margin: 0,
  fontSize: "13px",
  fontWeight: 500,
  lineHeight: 1.4,
  color: "#e8eaed",
};

const timeStyle = {
  margin: "6px 0 0 0",
  fontSize: "11px",
  color: "rgba(255, 255, 255, 0.4)",
};

/**
 * Live feed of agent tool calls for the session UI.
 *
 * @param {{ events: Array<{ tool?: string, timestamp?: string }> }} props
 */
export default function ToolCallFeed({ events = [] }) {
  const ordered = [...events].reverse();

  return (
    <aside style={panelStyle} aria-label="Agent actions">
      <h2 style={titleStyle}>Agent Actions</h2>

      {ordered.length === 0 ? (
        <p style={emptyStyle}>Waiting for agent actions...</p>
      ) : (
        <ul style={listStyle}>
          {ordered.map((ev, index) => {
            const key = `${ev.tool ?? "unknown"}-${index}-${ev.timestamp ?? ""}`;
            const meta = TOOL_DISPLAY[ev.tool] ?? {
              icon: "⚙️",
              label: ev.tool ? `${ev.tool}` : "Agent action",
            };

            return (
              <li key={key} className="toolcall-feed__item" style={itemStyle}>
                <span style={iconStyle} aria-hidden>
                  {meta.icon}
                </span>
                <div style={labelBlockStyle}>
                  <p style={labelTextStyle}>{meta.label}</p>
                  {ev.timestamp != null && ev.timestamp !== "" && (
                    <p style={timeStyle}>{ev.timestamp}</p>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
