"""
Minimal in-memory rate limiter for auth endpoints (login, forgot/reset
password) - the endpoints most worth protecting against brute-forcing,
since they gate account access directly.

Deliberately simple: no Redis, no extra dependency. Render's free tier
runs a single instance, so an in-process dict is enough to meaningfully
slow down automated guessing. It resets on every deploy/restart, which
is an acceptable trade-off for what this protects - if you outgrow a
single instance, swap this for a shared store (Redis, etc.) instead.
"""

import time
import threading
from collections import defaultdict

from fastapi import HTTPException, Request

_attempts: dict[str, list[float]] = defaultdict(list)
_lock = threading.Lock()


def rate_limit(key_prefix: str, max_attempts: int, window_seconds: int):
    """Dependency factory. Limits attempts per (key_prefix + client IP)
    to max_attempts within a rolling window_seconds. Raises 429 with a
    plain, non-technical message once exceeded."""

    def checker(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        now = time.time()

        with _lock:
            attempts = _attempts[key]
            attempts[:] = [t for t in attempts if now - t < window_seconds]

            if len(attempts) >= max_attempts:
                raise HTTPException(
                    status_code=429,
                    detail="Too many attempts. Please wait a few minutes and try again.",
                )

            attempts.append(now)

    return checker
