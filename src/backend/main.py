from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from .db import index_books
from .rag_pipeline import RAGPipeline
from .tools import get_summary_by_title
from .safety import moderate_query
from .rate_limit import RateLimiter
from .config import RATE_LIMIT_PER_MIN
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Smart Librarian API")
pipeline: Optional[RAGPipeline] = None
limiter = RateLimiter(limit=RATE_LIMIT_PER_MIN, window_s=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendIn(BaseModel):
    query: str

@app.on_event("startup")
def _startup():
    global pipeline
    pipeline = RAGPipeline()

@app.get("/")
def root():
    return {"name": "Smart Librarian API", "endpoints": ["/health", "/docs", "/recommend", "/summary"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/admin/reindex")
def admin_reindex():
    n = index_books()
    return {"indexed": n}

@app.post("/recommend")
def recommend(payload: RecommendIn, request: Request):
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")

    ip = request.client.host if request.client else "unknown"
    if not limiter.allow(ip):
        raise HTTPException(status_code=429, detail="Too many requests, please slow down.")

    ok, msg = moderate_query(payload.query)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    result = pipeline.recommend(msg)
    if not result.get("title"):
        raise HTTPException(status_code=404, detail=result.get("reason", "No recommendation found"))
    return result

@app.get("/summary")
def summary(title: str):
    r = get_summary_by_title(title)
    if not r:
        raise HTTPException(status_code=404, detail="Title not found")
    return r
