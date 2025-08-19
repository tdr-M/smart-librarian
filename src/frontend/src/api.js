const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function jsonFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = body?.detail || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body;
}

export async function health() {
  return jsonFetch("/health");
}

export async function reindex() {
  return jsonFetch("/admin/reindex", { method: "POST" });
}

export async function recommend(query) {
  return jsonFetch("/recommend", {
    method: "POST",
    body: JSON.stringify({ query })
  });
}

export async function summaryByTitle(title) {
  const enc = encodeURIComponent(title);
  return jsonFetch(`/summary?title=${enc}`);
}
