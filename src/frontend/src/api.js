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

export async function tts(text, voice = "alloy") {
  const res = await fetch(`${BASE_URL}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice })
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => "TTS failed");
    throw new Error(msg);
  }
  return await res.blob();
}

export async function sttUpload(file) {
  const fd = new FormData();
  fd.append("file", file, file.name || "speech.webm");
  const res = await fetch(`${BASE_URL}/stt`, { method: "POST", body: fd });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
  return body.text;
}

export async function genCover(title, hint = "", size = "512x512", format = "webp") {
  const res = await fetch(`${BASE_URL}/cover`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, hint, size, format })
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
  return body;
}
