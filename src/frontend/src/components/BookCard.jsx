import { useEffect, useState } from "react";
import { tts, genCover } from "../api.js";

export default function BookCard({ result }) {
  if (!result) return null;

  const { title, detailed_summary, metadata } = result;
  const blurb = result.assistant_message || result.reason;

  const [playing, setPlaying] = useState(false);
  const [imgBusy, setImgBusy] = useState(false);
  const [img, setImg] = useState(null); // { b64, type, size }
  const [imgErr, setImgErr] = useState("");

  // Auto-load the cover for each new title (uses backend defaults: 512 + webp/png)
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setImg(null);
      setImgErr("");
      setImgBusy(true);
      try {
        const body = await genCover(title); // no args -> server config
        if (!cancelled) {
          setImg({
            b64: body.image_b64,
            type: body.content_type || "image/webp",
            size: body.size || "512x512",
          });
        }
      } catch (e) {
        if (!cancelled) setImgErr(e.message || "Image generation failed");
      } finally {
        if (!cancelled) setImgBusy(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [title]);

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

  const container = {
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
  };

  return (
    <div style={container}>
      <h2 style={{ margin: 0 }}>{title}</h2>

      <div style={{ display: "flex", gap: 8, margin: "8px 0 6px" }}>
        <button
          type="button"
          onClick={onListen}
          disabled={playing}
          title="Listen to the recommendation"
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
        {/* Text column */}
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

        {/* Image column – only render when we truly have an image */}
        {img && (
          <div style={{ flex: "0 0 260px", maxWidth: 512, minWidth: 220 }}>
            <img
              src={`data:${img.type};base64,${img.b64}`}
              alt={`Illustrative cover concept for ${title}`}
              loading="lazy"
              style={{
                width: "100%",
                borderRadius: 12,
                border: "1px solid #e5e7eb",
              }}
            />
          </div>
        )}
      </div>

      {/* Optional: show a very subtle inline error if image couldn’t be generated */}
      {imgErr && (
        <div style={{ marginTop: 8, fontSize: 12, color: "#9ca3af" }}>
          {/* comment this line out entirely if you want zero text */}
          {/* Cover not available: {imgErr} */}
        </div>
      )}
    </div>
  );
}
