from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from typing import Optional
from .db import index_books
from .rag_pipeline import RAGPipeline
from .tools import get_summary_by_title
from .safety import moderate_query
from .rate_limit import RateLimiter
from .config import (
    RATE_LIMIT_PER_MIN,
    TRANSCRIBE_MODEL,
    TTS_MODEL,
    IMAGE_MODEL,
    IMAGE_SIZE,
    IMAGE_OUTPUT_FORMAT,
    IMAGE_WEBP_QUALITY,
    IMAGE_RETURN_PX,
    DATA_DIR,
)
from base64 import b64encode, b64decode
from io import BytesIO
from PIL import Image
import tempfile, os
import logging, traceback, hashlib, json
from starlette.middleware.gzip import GZipMiddleware

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
app.add_middleware(GZipMiddleware, minimum_size=800)
log = logging.getLogger("cover")

class RecommendIn(BaseModel):
    query: str

class TTSIn(BaseModel):
    text: str
    voice: str | None = "alloy"

class CoverIn(BaseModel):
    title: str
    hint: str | None = None
    size: str | None = None
    format: str | None = None

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

@app.post("/tts")
def tts(payload: TTSIn):
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")
    text = text[:4000]
    try:
        speech = pipeline.llm.audio.speech.create(
            model=TTS_MODEL,
            voice=payload.voice or "alloy",
            input=text,
        )
        audio_bytes = getattr(speech, "content", None)
        if not audio_bytes:
            raise RuntimeError("No audio content returned")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")
    return Response(content=audio_bytes, media_type="audio/mpeg")

@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    suffix = ".webm"
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    tmp_path = None
    try:
        data = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        with open(tmp_path, "rb") as fh:
            tr = pipeline.llm.audio.transcriptions.create(
                model=TRANSCRIBE_MODEL,
                file=fh,
            )
        text = (getattr(tr, "text", "") or "").strip()
        if not text:
            raise RuntimeError("Empty transcription")
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

ALLOWED_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}

def _postprocess_and_encode(png_bytes: bytes, fmt: str, max_px: int) -> tuple[str, str]:
    im = Image.open(BytesIO(png_bytes)).convert("RGB")
    if max_px and max(im.width, im.height) > max_px:
        scale = max_px / max(im.width, im.height)
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    buf = BytesIO()
    fmt = (fmt or "png").lower()
    if fmt == "webp":
        im.save(buf, format="WEBP", quality=IMAGE_WEBP_QUALITY, method=6)
        return b64encode(buf.getvalue()).decode("ascii"), "image/webp"
    im.save(buf, format="PNG")
    return b64encode(buf.getvalue()).decode("ascii"), "image/png"

@app.post("/cover")
def cover(payload: CoverIn):
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Missing title")
    md = get_summary_by_title(title) or {}
    author = md.get("author", "")
    genres = md.get("genres", [])
    themes = md.get("themes", [])
    short = (md.get("detailed_summary", "") or "")[:400]
    clean_hint = ""
    if payload.hint:
        ok, clean_hint = moderate_query(payload.hint)
        if not ok:
            clean_hint = ""
    req_size = (payload.size or IMAGE_SIZE)
    if req_size not in ALLOWED_SIZES:
        req_size = "1024x1024"
    out_fmt = (payload.format or IMAGE_OUTPUT_FORMAT).lower()
    full_prompt = (
        f"Design an original, tasteful, illustrative book-cover concept for '{title}'"
        f"{(' by ' + author) if author else ''}. "
        f"Capture the mood and themes ({', '.join(themes)[:120]}). "
        f"Genres: {', '.join(genres)[:80]}. "
        f"Brief context: {short} {clean_hint}. "
        "Avoid logos/trademarks and avoid rendering any text."
    )
    minimal_prompt = f"Illustrative cover concept for '{title}'. Clean composition, no text."
    attempts = [
        (full_prompt, req_size),
        (minimal_prompt, req_size),
        (minimal_prompt, "auto"),
    ]
    errors = []
    for prompt, size in attempts:
        try:
            img = pipeline.llm.images.generate(
                model=IMAGE_MODEL,
                prompt=prompt,
                size=size,
            )
            b64_png = getattr(img.data[0], "b64_json", None)
            if not b64_png:
                raise RuntimeError("images.generate returned no b64_json")
            raw_png = b64decode(b64_png)
            b64_final, content_type = _postprocess_and_encode(
                raw_png, fmt=out_fmt, max_px=IMAGE_RETURN_PX
            )
            return {
                "image_b64": b64_final,
                "content_type": content_type,
                "size": size,
            }
        except Exception as e:
            log.error("images.generate failed (size=%s): %s\n%s", size, e, traceback.format_exc())
            errors.append(f"{type(e).__name__}: {e}")
    raise HTTPException(
        status_code=502,
        detail=f"Image generation failed after retries: {' | '.join(errors)}",
    )

COVERS_DIR = DATA_DIR / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

def _cache_key(title: str, hint: str, size: str, fmt: str) -> str:
    blob = json.dumps({"t": title, "h": hint or "", "s": size, "f": fmt}, sort_keys=True).encode("utf-8")
    return hashlib.sha1(blob).hexdigest()

def _postprocess_to_bytes(png_bytes: bytes, fmt: str, max_px: int) -> tuple[bytes, str]:
    im = Image.open(BytesIO(png_bytes)).convert("RGB")
    if max_px and max(im.width, im.height) > max_px:
        scale = max_px / max(im.width, im.height)
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    buf = BytesIO()
    if (fmt or "webp").lower() == "webp":
        im.save(buf, format="WEBP", quality=IMAGE_WEBP_QUALITY, method=6)
        return buf.getvalue(), "image/webp"
    im.save(buf, format="PNG")
    return buf.getvalue(), "image/png"

@app.get("/cover/img")
def cover_img(title: str, hint: str | None = None, size: str | None = None, fmt: str | None = None):
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Missing title")
    req_size = (size or IMAGE_SIZE)
    if req_size not in ALLOWED_SIZES:
        req_size = "1024x1024"
    out_fmt = (fmt or IMAGE_OUTPUT_FORMAT).lower()
    key = _cache_key(title, hint or "", req_size, out_fmt)
    ext = "webp" if out_fmt == "webp" else "png"
    path = COVERS_DIR / f"{key}.{ext}"
    if path.exists():
        return FileResponse(
            path,
            media_type="image/webp" if ext == "webp" else "image/png",
            headers={"Cache-Control": "public, max-age=604800"},
        )
    md = get_summary_by_title(title) or {}
    author = md.get("author", "")
    genres = md.get("genres", [])
    themes = md.get("themes", [])
    short = (md.get("detailed_summary", "") or "")[:400]
    clean_hint = ""
    if hint:
        ok, clean_hint = moderate_query(hint)
        if not ok:
            clean_hint = ""
    full_prompt = (
        f"Design an original, tasteful, illustrative book-cover concept for '{title}'"
        f"{(' by ' + author) if author else ''}. "
        f"Capture the mood and themes ({', '.join(themes)[:120]}). "
        f"Genres: {', '.join(genres)[:80]}. "
        f"Brief context: {short} {clean_hint}. "
        "Avoid logos/trademarks and avoid rendering any text."
    )
    minimal_prompt = f"Illustrative cover concept for '{title}'. Clean composition, no text."
    attempts = [(full_prompt, req_size), (minimal_prompt, req_size), (minimal_prompt, "auto")]
    errors = []
    for prompt, model_size in attempts:
        try:
            gen = pipeline.llm.images.generate(model=IMAGE_MODEL, prompt=prompt, size=model_size)
            b64_png = getattr(gen.data[0], "b64_json", None)
            if not b64_png:
                raise RuntimeError("images.generate returned no b64_json")
            final_bytes, content_type = _postprocess_to_bytes(b64decode(b64_png), out_fmt, IMAGE_RETURN_PX)
            with open(path, "wb") as f:
                f.write(final_bytes)
            return Response(
                content=final_bytes,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=604800"},
            )
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
    raise HTTPException(status_code=502, detail=f"Image generation failed after retries: {' | '.join(errors)}")