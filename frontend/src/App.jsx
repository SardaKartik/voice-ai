import VoiceRoom from "./components/VoiceRoom.jsx";

/**
 * Root shell: full-viewport dark background with VoiceRoom centered in the layout.
 */
export default function App() {
  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        margin: 0,
        padding: 0,
        backgroundColor: "#0f0f0f",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          width: "100%",
          alignSelf: "stretch",
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <VoiceRoom />
      </div>
    </div>
  );
}
