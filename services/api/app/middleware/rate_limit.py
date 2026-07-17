"""In-memory rate limiter: {ip: [timestamps]}, 5 attempts/minute by default."""
from __future__ import annotations

import logging
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit specific endpoints by client IP."""

    def __init__(self, app, max_attempts: int = MAX_ATTEMPTS, window: int = WINDOW_SECONDS):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window = window
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def _prune(self, ip: str, now: float) -> None:
        cutoff = now - self.window
        self._attempts[ip] = [t for t in self._attempts[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.rstrip("/").endswith("/auth/login") and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            self._prune(client_ip, now)
            if len(self._attempts[client_ip]) >= self.max_attempts:
                logger.warning(
                    "Rate limit exceeded for %s on %s %s",
                    client_ip, request.method, request.url.path,
                )
                return JSONResponse(status_code=429, content={"detail": "Too many login attempts. Try again later."})
            self._attempts[client_ip].append(now)
        return await call_next(request)
