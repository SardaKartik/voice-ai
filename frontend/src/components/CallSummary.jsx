/**
 * Post-call summary card. Renders only when `data` is non-null.
 *
 * @param {{ data: { summary?: string, timestamp?: string, preferences?: string } | null, embedded?: boolean }} props
 */
export default function CallSummary({ data, embedded = false }) {
  if (data == null) {
    return null;
  }

  const { summary, timestamp, preferences } = data;
  const prefs = typeof preferences === "string" ? preferences.trim() : "";
  const hasPrefs = prefs.length > 0;

  const timestampLabel = formatTimestamp(timestamp);

  const cardStyle = {
    position: embedded ? "relative" : "fixed",
    left: embedded ? "auto" : 0,
    right: embedded ? "auto" : 0,
    bottom: embedded ? "auto" : 0,
    width: embedded ? "100%" : "auto",
    zIndex: embedded ? "auto" : 40,
    padding: "16px 20px 20px",
    background: "linear-gradient(0deg, rgba(15, 20, 25, 0.98) 0%, rgba(15, 20, 25, 0.92) 100%)",
    borderTop: "1px solid rgba(255, 255, 255, 0.1)",
    boxShadow: "0 -8px 32px rgba(0, 0, 0, 0.2)",
    fontFamily:
      'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    color: "#e8eaed",
  };

  const titleStyle = {
    margin: "0 0 12px 0",
    fontSize: "16px",
    fontWeight: 600,
    color: "#f1f3f4",
  };

  const bodyStyle = {
    margin: 0,
    fontSize: "14px",
    lineHeight: 1.55,
    color: "rgba(255, 255, 255, 0.9)",
  };

  const metaStyle = {
    margin: "10px 0 0 0",
    fontSize: "12px",
    color: "rgba(255, 255, 255, 0.5)",
  };

  const prefsLabelStyle = {
    margin: "12px 0 4px 0",
    fontSize: "12px",
    fontWeight: 600,
    color: "rgba(255, 255, 255, 0.55)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  };

  const prefsStyle = {
    margin: 0,
    fontSize: "13px",
    lineHeight: 1.5,
    color: "rgba(255, 255, 255, 0.82)",
  };

  return (
    <section style={cardStyle} aria-label="Call summary">
      <h2 style={titleStyle}>📝 Call Summary</h2>
      {summary != null && summary !== "" && <p style={bodyStyle}>{summary}</p>}
      {timestampLabel != null && (
        <p style={metaStyle}>{timestampLabel}</p>
      )}
      {hasPrefs && (
        <>
          <p style={prefsLabelStyle}>Preferences</p>
          <p style={prefsStyle}>{prefs}</p>
        </>
      )}
    </section>
  );
}

/**
 * @param {unknown} value
 * @returns {string | null}
 */
function formatTimestamp(value) {
  if (value == null || value === "") {
    return null;
  }
  if (typeof value !== "string") {
    return String(value);
  }
  const parsed = Date.parse(value);
  if (!Number.isNaN(parsed)) {
    return new Date(parsed).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }
  return value;
}
