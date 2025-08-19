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

COLLECTION_NAME = "books"
TOP_K = 5

ENABLE_MODERATION = True
MAX_QUERY_LEN = 500
RATE_LIMIT_PER_MIN = 30