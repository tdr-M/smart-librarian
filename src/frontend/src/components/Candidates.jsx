export default function Candidates({ items = [] }) {
  if (!items.length) return null;
  return (
    <div style={{ marginTop: 16 }}>
      <h3 style={{ marginBottom: 8 }}>Candidates</h3>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {items.map((c, i) => (
          <li key={i} style={{
            border: "1px dashed #e5e7eb",
            borderRadius: 10,
            padding: 10,
            marginBottom: 8
          }}>
            <strong>{c.title}</strong> — {c.author} ·{" "}
            <em>{(c.genres || []).join(", ")}</em>
            <div style={{ fontSize: 13, color: "#6b7280" }}>
              {Array.isArray(c.themes) ? c.themes.join(", ") : ""}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
