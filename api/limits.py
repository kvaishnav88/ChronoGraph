import os
import threading
import time
from collections import defaultdict, deque
from datetime import date

from fastapi import HTTPException, Request

MAX_PER_MIN = int(os.getenv("CHAT_PER_MIN", "8"))
DAILY_CHATS = int(os.getenv("DAILY_CHAT_BUDGET", "300"))

_lock = threading.Lock()
_hits = defaultdict(deque)
_day = {"d": date.today(), "n": 0}


def client_ip(request: Request) -> str:
    h = request.headers
    for name in ("true-client-ip", "cf-connecting-ip"):
        if h.get(name):
            return h[name].strip()
    fwd = h.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def chat_guard(request: Request):
    ip = client_ip(request)
    now = time.monotonic()
    with _lock:
        today = date.today()
        if _day["d"] != today:
            _day["d"], _day["n"] = today, 0
        if _day["n"] >= DAILY_CHATS:
            raise HTTPException(
                status_code=429,
                detail="The demo has reached its daily limit. Please try again tomorrow.",
            )
        if len(_hits) > 5000:
            for k in [k for k, v in _hits.items() if not v]:
                del _hits[k]
        dq = _hits[ip]
        while dq and now - dq[0] > 60:
            dq.popleft()
        if len(dq) >= MAX_PER_MIN:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait a minute and try again.",
            )
        dq.append(now)
        _day["n"] += 1