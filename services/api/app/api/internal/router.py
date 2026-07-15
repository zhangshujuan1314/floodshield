from fastapi import APIRouter, Header, Request

from app.core.config import settings
from app.core.errors import Forbidden
from app.api.internal.ingestion import router as ingestion_router
from app.api.internal.risk import router as risk_router
from app.api.internal.data_quality import router as data_quality_router

router = APIRouter()


async def verify_internal_auth(
    request: Request,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    """Service-to-service auth via shared internal key."""
    if settings.MOCK_MODE:
        return
    expected_key = f"internal-{settings.SECRET_KEY}"
    if x_internal_key != expected_key:
        request_id = getattr(request.state, "request_id", "")
        raise Forbidden("Invalid internal service key", request_id=request_id)


router.include_router(ingestion_router, prefix="/ingestion", tags=["internal-ingestion"])
router.include_router(risk_router, prefix="/risk", tags=["internal-risk"])
router.include_router(data_quality_router, prefix="/data-quality", tags=["internal-data-quality"])
