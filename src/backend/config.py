from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / ".chroma"
BOOKS_JSON = DATA_DIR / "book_summaries.json"

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "whisper-1")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")

IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1024")
IMAGE_RETURN_PX = int(os.getenv("IMAGE_RETURN_PX", "512"))   
IMAGE_OUTPUT_FORMAT = os.getenv("IMAGE_OUTPUT_FORMAT", "png")  
IMAGE_WEBP_QUALITY = int(os.getenv("IMAGE_WEBP_QUALITY", "82"))

COLLECTION_NAME = "books"
TOP_K = 5

ENABLE_MODERATION = True
MAX_QUERY_LEN = 500
RATE_LIMIT_PER_MIN = 30