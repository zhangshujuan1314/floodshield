"""Input sanitization middleware.

Logs suspicious XSS-like payloads in query parameters at WARNING level.
Does NOT modify the request — audit-only.
"""

from __future__ import annotations

import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Common XSS patterns in query strings
_XSS_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*img[^>]+onerror", re.IGNORECASE),
]


class SanitizeMiddleware(BaseHTTPMiddleware):
    """Log suspicious XSS payloads found in query parameters."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        qs = str(request.url.query)
        if qs:
            for pattern in _XSS_PATTERNS:
                if pattern.search(qs):
                    client_ip = request.client.host if request.client else "unknown"
                    logger.warning(
                        "Suspicious input from %s on %s %s: %s",
                        client_ip, request.method, request.url.path, qs[:200],
                    )
                    break

        return await call_next(request)
