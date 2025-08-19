import { useEffect, useMemo, useState } from "react";
import { health, recommend, reindex } from "./api.js";
import BookCard from "./components/BookCard.jsx";
import Candidates from "./components/Candidates.jsx";

const placeholders = [
  "Recommend a book about friendship and magic",
  "What do you suggest for someone who loves war stories?",
  "Fantasy with a coming-of-age vibe",
  "Historical fiction with strong sisterhood",
  "Adventure quest with moral dilemmas"
];

export default function App() {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [serverOk, setServerOk] = useState(false);

  const ph = useMemo(
    () => placeholders[Math.floor(Math.random() * placeholders.length)],
    []
  );

  useEffect(() => {
    health().then(() => setServerOk(true)).catch(() => setServerOk(false));
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    if (!q.trim()) return;

    setBusy(true);
    try {
      const data = await recommend(q.trim());
      setResult(data);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function onReindex() {
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

  return (
    <div style={{ maxWidth: 820, margin: "40px auto", padding: "0 16px" }}>
      <header style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ margin: 0 }}>Smart Librarian</h1>
        <span
          title={serverOk ? "API healthy" : "API unreachable"}
          style={{
            width: 10, height: 10, borderRadius: 10,
            background: serverOk ? "#10b981" : "#ef4444",
            display: "inline-block"
          }}
        />
      </header>

      <form onSubmit={onSubmit} style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <input
          type="text"
          placeholder={ph}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          maxLength={500}
          style={{
            flex: 1,
            padding: "12px 14px",
            borderRadius: 10,
            border: "1px solid #e5e7eb",
            fontSize: 16
          }}
        />
        <button
          type="submit"
          disabled={busy || !q.trim()}
          style={{
            padding: "12px 16px",
            borderRadius: 10,
            border: "1px solid #111827",
            background: "#111827",
            color: "white",
            cursor: busy ? "not-allowed" : "pointer"
          }}
        >
          {busy ? "Thinking..." : "Ask"}
        </button>
        <button
          type="button"
          onClick={onReindex}
          disabled={busy}
          style={{
            padding: "12px 16px",
            borderRadius: 10,
            border: "1px solid #6b7280",
            background: "white",
            color: "#374151",
            cursor: busy ? "not-allowed" : "pointer"
          }}
          title="Re-embed current dataset"
        >
          Reindex
        </button>
      </form>

      {error && (
        <div
          style={{
            marginTop: 12,
            color: "#b91c1c",
            background: "#fee2e2",
            border: "1px solid #fecaca",
            padding: 10,
            borderRadius: 10
          }}
        >
          {error}
        </div>
      )}

      <BookCard result={result} />
      <Candidates items={result?.candidates || []} />

      <footer style={{ marginTop: 32, fontSize: 13, color: "#6b7280" }}>
        API base: {import.meta.env.VITE_API_BASE_URL}
      </footer>
    </div>
  );
}
