from typing import List, Dict, Any, Optional
from openai import OpenAI
from .config import OPENAI_API_KEY, CHAT_MODEL, COLLECTION_NAME, TOP_K
from .db import get_client, get_or_create_collection
from .tools import get_summary_by_title
from chromadb.api import ClientAPI

SYSTEM_PROMPT = (
    "You are Smart Librarian. Recommend ONE book from the provided candidates that best matches "
    "the user's query. Respond as concise JSON with keys: "
    'title, reason. Do not invent titles.'
)

ASSISTANT_REC_PROMPT = (
    "You are Smart Librarian. Write a brief, friendly recommendation (2–3 sentences) "
    "for the chosen book. Mention title and author once, connect it to the user's query, "
    "and avoid spoilers."
)

def _find_by_title(cands, title):
    return next((c for c in cands if c.get("title") == title), {})

def _safe_parse_json(text: str, fallback_title: str, allowed_titles: set[str]) -> Dict[str, str]:
    """
    Best-effort parse of the model output.
    Returns a dict with keys: title, reason.
    Guarantees the title is one of allowed_titles; otherwise uses fallback_title.
    """
    import json, re

    def _validate(obj) -> Dict[str, str] | None:
        if isinstance(obj, dict):
            t = str(obj.get("title", "")).strip()
            r = str(obj.get("reason", "")).strip()
            if t in allowed_titles:
                return {"title": t, "reason": r}
        return None

    try:
        obj = json.loads((text or "").strip())
        valid = _validate(obj)
        if valid:
            return valid
    except Exception:
        pass

    m = re.search(r"\{.*?\}", text or "", re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            valid = _validate(obj)
            if valid:
                return valid
        except Exception:
            pass

    return {"title": fallback_title, "reason": "Closest thematic match by retriever."}

def _as_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        return [t.strip() for t in x.split(",") if t.strip()]
    return []

class RAGPipeline:
    def __init__(self, client: Optional[ClientAPI] = None):
        self.chroma = client or get_client()
        self.collection = get_or_create_collection(self.chroma)
        self.llm = OpenAI(api_key=OPENAI_API_KEY)

    def retrieve(self, query: str, k: int = TOP_K) -> List[Dict[str, Any]]:
        q = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["metadatas", "documents", "distances"],
        )
        results = []
        for i in range(len(q["ids"][0])):
            md = q["metadatas"][0][i]
            results.append({
                "title": md.get("title"),
                "author": md.get("author"),
                "short_summary": q["documents"][0][i],
                "themes": _as_list(md.get("themes", [])),
                "genres": _as_list(md.get("genres", [])),
                "distance": q["distances"][0][i],
            })
        return results

    def _format_candidates(self, cands: List[Dict[str, Any]]) -> str:
        lines = []
        for c in cands:
            lines.append(
                f"- {c['title']} by {c.get('author','?')}: "
                f"themes={c.get('themes',[])}, genres={c.get('genres',[])}; "
                f"summary={c['short_summary']}"
            )
        return "\n".join(lines)

    def recommend(self, query: str) -> Dict[str, Any]:
        candidates = self.retrieve(query)

        if not candidates:
            return {
                "query": query,
                "title": None,
                "reason": "No candidates found. Reindex the dataset first.",
                "candidates": []
            }
            

        content = (
            f"User query: {query}\n\n"
            f"Candidates:\n{self._format_candidates(candidates)}\n\n"
            "Return JSON."
        )

        try:
            resp = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.2,
            )
            text = resp.choices[0].message.content
        except Exception:
            best = min(candidates, key=lambda x: x.get("distance", float("inf")))
            detail = get_summary_by_title(best["title"])
            return {
                "query": query,
                "title": best["title"],
                "reason": "Best embedding match (LLM unavailable).",
                "detailed_summary": (detail or {}).get("detailed_summary", ""),
                "metadata": detail,
                "candidates": candidates,
            }

        allowed = {c["title"] for c in candidates}
        parsed = _safe_parse_json(text, fallback_title=candidates[0]["title"], allowed_titles=allowed)

        title = parsed["title"] or candidates[0]["title"]
        detail = get_summary_by_title(title)

        chosen = _find_by_title(candidates, title)
        short = chosen.get("short_summary", "")
        author = (detail or {}).get("author", "")
        genres = ", ".join((detail or {}).get("genres", []) or [])
        themes = ", ".join((detail or {}).get("themes", []) or [])

        assistant_message = ""
        try:
            resp2 = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": ASSISTANT_REC_PROMPT},
                    {"role": "user", "content":
                        f"User query: {query}\n"
                        f"Title: {title}\nAuthor: {author}\n"
                        f"Genres: {genres}\nThemes: {themes}\n"
                        f"Short summary: {short}"
                    },
                ],
                temperature=0.5,
            )
            assistant_message = (resp2.choices[0].message.content or "").strip()
        except Exception:
            assistant_message = f"I recommend '{title}' by {author}. {chosen.get('short_summary','')}"

        return {
            "query": query,
            "title": title,
            "reason": parsed.get("reason", ""),
            "assistant_message": assistant_message,          # <-- NEW field
            "detailed_summary": (detail or {}).get("detailed_summary", ""),
            "metadata": detail,
            "candidates": candidates,
        }

