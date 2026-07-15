from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.core.database import async_session_factory

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/health")
async def health_check(request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    db_ok = True

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "status": "healthy" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
            "version": "0.1.0",
        },
    }
