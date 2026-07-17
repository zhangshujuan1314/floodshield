"""Request size limit middleware.

Rejects requests with Content-Length > 10 MB (except file upload endpoints).
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB
UPLOAD_PATHS = {"/upload", "/voice/upload"}  # exempt these prefixes


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose body exceeds a size limit."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            # Allow file upload endpoints
            path = request.url.path
            if any(path.startswith(p) for p in UPLOAD_PATHS):
                return await call_next(request)

            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                "Request body too large (%s bytes) from %s on %s %s",
                content_length, client_ip, request.method, path,
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large. Maximum size is 10 MB."},
            )

        return await call_next(request)
