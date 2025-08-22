import { useEffect, useRef, useState } from "react";
import { health, recommend, reindex, sttUpload } from "./api.js";
import BookCard from "./components/BookCard.jsx";
import Candidates from "./components/Candidates.jsx";

export default function App() {
  const [serverOk, setServerOk] = useState(false);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const [recording, setRecording] = useState(false);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    health().then(() => setServerOk(true)).catch(() => setServerOk(false));
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    if (!q.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const r = await recommend(q.trim());
      setResult(r);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function onReindex() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await reindex();
    } catch (err) {
      setError(err.message || "Reindex failed");
    } finally {
      setBusy(false);
    }
  }

  async function startRec() {
    if (recording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      mr.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        try {
          const text = await sttUpload(new File([blob], "speech.webm", { type: "audio/webm" }));
          setQ(text || "");
        } catch (err) {
          alert(err.message || "Transcription failed");
        }
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
      };
      mediaRef.current = mr;
      setRecording(true);
      mr.start();
      setTimeout(() => mr.state === "recording" && mr.stop(), 15000);
    } catch (err) {
      alert("Microphone access denied");
    }
  }

  function stopRec() {
    if (mediaRef.current && mediaRef.current.state === "recording") {
      mediaRef.current.stop();
    }
  }

  const isEmpty = !result;

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: isEmpty ? "center" : "flex-start",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 900,
          padding: "0 16px",
          marginTop: isEmpty ? 0 : 36,
        }}
      >
        <header
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            justifyContent: isEmpty ? "center" : "flex-start",
          }}
        >
          <h1 style={{ margin: 0 }}>Smart Librarian</h1>
          <span
            title={serverOk ? "API healthy" : "API unreachable"}
            style={{
              width: 10,
              height: 10,
              borderRadius: 10,
              background: serverOk ? "#10b981" : "#ef4444",
              display: "inline-block",
            }}
          />
        </header>

        <form
          onSubmit={onSubmit}
          style={{
            marginTop: 16,
            display: "flex",
            gap: 8,
            justifyContent: isEmpty ? "center" : "flex-start",
          }}
        >
          <input
            type="text"
            placeholder="Adventure quest with moral dilemmas"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            maxLength={500}
            style={{
              flex: isEmpty ? "0 1 560px" : 1,
              padding: "12px 14px",
              borderRadius: 10,
              border: "1px solid #e5e7eb",
              fontSize: 16,
            }}
          />
          <button
            type="submit"
            disabled={busy || !q.trim()}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #111827",
              background: "#111827",
              color: "white",
              cursor: busy || !q.trim() ? "not-allowed" : "pointer",
            }}
          >
            {busy ? "Thinking…" : "Ask"}
          </button>
          <button
            type="button"
            onClick={onReindex}
            disabled={busy}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #e5e7eb",
              background: "white",
              color: "#111827",
              cursor: busy ? "not-allowed" : "pointer",
            }}
          >
            Reindex
          </button>
          <button
            type="button"
            onClick={recording ? stopRec : startRec}
            disabled={busy}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #e5e7eb",
              background: "white",
              color: "#111827",
              cursor: busy ? "not-allowed" : "pointer",
            }}
          >
            {recording ? "Stop" : "🎙️ Voice"}
          </button>
        </form>

        <div
          style={{
            marginTop: 8,
            fontSize: 12,
            color: "#6b7280",
            textAlign: isEmpty ? "center" : "left",
          }}
        >
          Reindex reloads <i>book_summaries.json</i> into ChromaDB and re-embeds all entries. Voice mode records up to
          ~15s, transcribes to text, and places it in the input box.
        </div>

        {error && (
          <div
            style={{
              marginTop: 12,
              background: "#fee2e2",
              border: "1px solid #fecaca",
              color: "#991b1b",
              padding: 10,
              borderRadius: 8,
              textAlign: "center",
            }}
          >
            {error}
          </div>
        )}

        {!isEmpty && (
          <>
            <BookCard result={result} />
            <Candidates items={result?.candidates || []} />
          </>
        )}
      </div>
    </div>
  );
}