from fastapi import APIRouter

from app.api.v1.admin.overview import router as overview_router
from app.api.v1.admin.reports import router as reports_router
from app.api.v1.admin.road_events import router as road_events_router
from app.api.v1.admin.shelters import router as shelters_router
from app.api.v1.admin.tasks import router as tasks_router
from app.api.v1.admin.notifications import router as notifications_router
from app.api.v1.admin.audit import router as audit_router

router = APIRouter()

router.include_router(overview_router, tags=["admin-overview"])
router.include_router(reports_router, tags=["admin-reports"])
router.include_router(road_events_router, tags=["admin-road-events"])
router.include_router(shelters_router, tags=["admin-shelters"])
router.include_router(tasks_router, tags=["admin-tasks"])
router.include_router(notifications_router, tags=["admin-notifications"])
router.include_router(audit_router, tags=["admin-audit"])
