export default function BookCard({ result }) {
  if (!result) return null;
  const { title, detailed_summary, metadata } = result;
  const blurb = result.assistant_message || result.reason;

  return (
    <div style={{
      border: "1px solid #e5e7eb",
      borderRadius: 12,
      padding: 16,
      marginTop: 16,
      boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
    }}>
      <h2 style={{ margin: 0 }}>{title}</h2>

      {blurb && (
        <p style={{ margin: "6px 0 4px", color: "#111827" }}>
          {blurb}
        </p>
      )}

      {metadata && (
        <p style={{ margin: "4px 0 10px", fontSize: 14, color: "#4b5563" }}>
          <strong>Author:</strong> {metadata.author} · <strong>Year:</strong> {metadata.year} ·{" "}
          <strong>Genres:</strong> {(metadata.genres || []).join(", ")}
        </p>
      )}

      
      <h3 style={{ margin: "10px 0 6px", fontSize: 18, color: "#111827" }}>Summary</h3>
      <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.5, color: "#111827" }}>
        {detailed_summary}
      </p>
    </div>
  );
}
