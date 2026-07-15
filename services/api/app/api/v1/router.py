from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.nearby import router as nearby_router
from app.api.v1.reports import router as reports_router
from app.api.v1.shelters import router as shelters_router
from app.api.v1.routes import router as routes_router
from app.api.v1.map_layers import router as map_layers_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.voice import router as voice_router
from app.api.v1.admin.router import router as admin_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
router.include_router(nearby_router, prefix="/nearby", tags=["nearby"])
router.include_router(reports_router, prefix="/hazard-reports", tags=["hazard-reports"])
router.include_router(shelters_router, prefix="/shelters", tags=["shelters"])
router.include_router(routes_router, prefix="/routes", tags=["routes"])
router.include_router(map_layers_router, prefix="/map", tags=["map"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
router.include_router(voice_router, prefix="/voice", tags=["voice"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
