import { useState } from "react";
import { tts, coverUrl } from "../api.js";

export default function BookCard({ result }) {
  if (!result) return null;

  const { title, detailed_summary, metadata } = result;
  const blurb = result.assistant_message || result.reason;
  const [playing, setPlaying] = useState(false);

  async function onListen() {
    try {
      setPlaying(true);
      const speakText =
        blurb ||
        (metadata?.author
          ? `I recommend "${title}" by ${metadata.author}.`
          : `I recommend "${title}".`);
      const blob = await tts(speakText);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => setPlaying(false);
      audio.play();
    } catch (err) {
      setPlaying(false);
      alert(err.message || "Failed to play audio");
    }
  }

  const genres = Array.isArray(metadata?.genres)
    ? metadata.genres.join(", ")
    : String(metadata?.genres || "");

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        padding: 16,
        marginTop: 16,
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
      }}
    >
      <h2 style={{ margin: 0 }}>{title}</h2>

      <div style={{ display: "flex", gap: 8, margin: "8px 0 6px" }}>
        <button
          type="button"
          onClick={onListen}
          disabled={playing}
          style={{
            padding: "6px 10px",
            borderRadius: 8,
            border: "1px solid #111827",
            background: "#111827",
            color: "white",
            cursor: playing ? "not-allowed" : "pointer",
          }}
        >
          {playing ? "Playing…" : "Listen"}
        </button>
      </div>

      <div
        style={{
          display: "flex",
          gap: 16,
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: "1 1 420px", minWidth: 280 }}>
          {blurb && (
            <p style={{ margin: "6px 0 4px", color: "#111827" }}>{blurb}</p>
          )}
          {metadata && (
            <p style={{ margin: "4px 0 10px", fontSize: 14, color: "#4b5563" }}>
              <strong>Author:</strong> {metadata.author} ·{" "}
              <strong>Year:</strong> {metadata.year} ·{" "}
              <strong>Genres:</strong> {genres}
            </p>
          )}
          <h3 style={{ margin: "10px 0 6px", fontSize: 18, color: "#111827" }}>
            Summary
          </h3>
          <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.5, color: "#111827" }}>
            {detailed_summary}
          </p>
        </div>

        <div style={{ flex: "0 0 260px", maxWidth: 512, minWidth: 220 }}>
          <img
            src={coverUrl(title)}
            alt={`Illustrative cover concept for ${title}`}
            loading="lazy"
            style={{
              width: "100%",
              borderRadius: 12,
              border: "1px solid #e5e7eb",
            }}
          />
        </div>
      </div>
    </div>
  );
}