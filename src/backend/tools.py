from typing import Optional, Dict, Any
from .config import COLLECTION_NAME
from .db import get_client, get_or_create_collection
from chromadb.api import ClientAPI

def _collection(client: Optional[ClientAPI] = None):
    client = client or get_client()
    return get_or_create_collection(client)

def _as_list(x):
    if isinstance(x, list): return x
    if isinstance(x, str):  return [t.strip() for t in x.split(",") if t.strip()]
    return []

def get_summary_by_title(title: str) -> Optional[Dict[str, Any]]:
    coll = _collection()
    res = coll.get(where={"title": title})
    if not res or not res.get("ids"):
        return None
    md = res["metadatas"][0]
    return {
        "title": md.get("title"),
        "author": md.get("author"),
        "detailed_summary": md.get("detailed_summary", ""),
        "themes": _as_list(md.get("themes", "")),
        "genres": _as_list(md.get("genres", "")),
        "year": md.get("year"),
    }
