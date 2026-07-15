from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.core.errors import AppError, app_error_handler, generic_error_handler
from app.middleware.request_id import RequestIDMiddleware

TZ_SHANGHAI = timezone(timedelta(hours=8))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="FloodShield API",
    version="0.1.0",
    description="Flood warning platform API",
    lifespan=lifespan,
)

# CORS middleware — dev allows all origins but NOT credentials (security)
# In production, replace with explicit allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Never combine wildcard origins with credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)

# Error handlers — never expose stack traces
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Include routers
from app.api.v1.router import router as v1_router
from app.api.internal.router import router as internal_router

app.include_router(v1_router, prefix=settings.API_PREFIX)
app.include_router(internal_router, prefix=settings.INTERNAL_PREFIX)


@app.get("/health")
async def root_health(request: Request):
    """Root health check — lightweight, no DB dependency."""
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    return JSONResponse(
        content={
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {"status": "healthy", "version": "0.1.0"},
        }
    )
