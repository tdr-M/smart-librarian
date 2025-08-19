from typing import List, Dict, Any
import json
from chromadb.api import ClientAPI
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from .config import CHROMA_DIR, BOOKS_JSON, COLLECTION_NAME, OPENAI_API_KEY, EMBED_MODEL

def get_client() -> ClientAPI:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return PersistentClient(path=str(CHROMA_DIR))

def get_or_create_collection(client: ClientAPI):
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBED_MODEL,
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

def _normalize_record(idx: int, r: Dict[str, Any]):
    doc = r.get("short_summary", "")
    metadata = {
        "title": r.get("title", f"book-{idx}"),
        "author": r.get("author", "Unknown"),
        "genres": r.get("genres", []),
        "themes": r.get("themes", []),
        "year": r.get("year", None),
        "detailed_summary": r.get("detailed_summary", ""),
    }
    return str(idx), doc, metadata

def load_books(path=BOOKS_JSON) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("book_summaries.json must be a list of records")
    return data

def index_books():
    client = get_client()
    coll = get_or_create_collection(client)
    books = load_books()
    ids, docs, metas = [], [], []
    for i, r in enumerate(books):
        _id, doc, meta = _normalize_record(i, r)
        ids.append(_id); docs.append(doc); metas.append(meta)
    coll.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(books)

def _to_primitive(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return v 

def _normalize_record(idx: int, r: Dict[str, Any]):
    doc = r.get("short_summary", "")
    metadata = {
        "title": r.get("title", f"book-{idx}"),
        "author": r.get("author", "Unknown"),
        "genres": _to_primitive(r.get("genres", [])),
        "themes": _to_primitive(r.get("themes", [])),  
        "year": r.get("year", None),
        "detailed_summary": r.get("detailed_summary", ""),
    }
    return str(idx), doc, metadata

if __name__ == "__main__":
    n = index_books()
    print(f"Indexed {n} books")
