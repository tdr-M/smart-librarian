from __future__ import annotations
from typing import Optional, Tuple
import re
from openai import OpenAI
from .config import OPENAI_API_KEY, ENABLE_MODERATION, MAX_QUERY_LEN


_INJECTION_PATTERNS = [
    r"\bignore (all|previous) instructions\b",
    r"\bdisregard (the )?rules\b",
    r"\b(jail|un)break\b",
    r"\b(system|developer) prompt\b",
    r"\breveal (the )?(prompt|secrets?)\b",
    r"\bact as\b",
    r"\bbypass\b",
]

def _normalize(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _overlong(s: str) -> bool:
    return len(s) > MAX_QUERY_LEN

def _looks_injection(s: str) -> bool:
    t = s.lower()
    return any(re.search(p, t) for p in _INJECTION_PATTERNS)

def moderate_query(query: str, client: Optional[OpenAI] = None) -> Tuple[bool, str]:
    """
    Uses OpenAI moderation (if enabled) + simple heuristic checks.
    """
    q = _normalize(query)
    if not q:
        return False, "Empty query."
    if _overlong(q):
        return False, f"Query too long (>{MAX_QUERY_LEN} characters)."
    if _looks_injection(q):
        return False, "Please phrase your request as a book preference or question."

    if ENABLE_MODERATION and OPENAI_API_KEY:
        try:
            client = client or OpenAI(api_key=OPENAI_API_KEY)
            resp = client.moderations.create(model="omni-moderation-latest", input=q)
            if getattr(resp.results[0], "flagged", False):
                return False, "Please rephrase your request."
        except Exception:
            pass

    return True, q