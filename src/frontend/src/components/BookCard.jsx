export default function BookCard({ result }) {
  if (!result) return null;
  const { title, reason, detailed_summary, metadata } = result;

  return (
    <div style={{
      border: "1px solid #e5e7eb",
      borderRadius: 12,
      padding: 16,
      marginTop: 16,
      boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
    }}>
      <h2 style={{ margin: 0 }}>{title}</h2>
      <p style={{ margin: "4px 0", color: "#6b7280" }}>{reason}</p>
      {metadata && (
        <p style={{ margin: "4px 0", fontSize: 14, color: "#4b5563" }}>
          <strong>Author:</strong> {metadata.author} · <strong>Year:</strong> {metadata.year} ·{" "}
          <strong>Genres:</strong> {(metadata.genres || []).join(", ")}
        </p>
      )}
      <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{detailed_summary}</p>
    </div>
  );
}
