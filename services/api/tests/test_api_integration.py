"""Integration tests for API endpoints.

Tests the full request/response cycle including:
- Request ID propagation
- Error response format
- Input validation
- Mock provider responses
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoints:
    async def test_root_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["status"] == "healthy"
        assert "requestId" in data
        assert "timestamp" in data

    async def test_v1_health(self, client: AsyncClient):
        resp = await client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        # v1 health may be degraded if no DB, but must return 200
        assert "data" in data
        assert "status" in data["data"]

    async def test_request_id_generated(self, client: AsyncClient):
        resp = await client.get("/health")
        assert "x-request-id" in resp.headers
        data = resp.json()
        assert data["requestId"] == resp.headers["x-request-id"]

    async def test_custom_request_id_preserved(self, client: AsyncClient):
        custom_id = str(uuid.uuid4())
        resp = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert resp.headers["x-request-id"] == custom_id


class TestErrorFormat:
    """Error responses must never expose stack traces."""

    async def test_not_found_returns_structured_error(self, client: AsyncClient):
        resp = await client.get("/v1/alerts/nonexistent-id")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"

    async def test_error_no_traceback(self, client: AsyncClient):
        """Verify no Python traceback in any error response."""
        resp = await client.get("/v1/nonexistent-endpoint")
        text = resp.text
        assert "Traceback" not in text
        assert "File \"" not in text

    async def test_error_has_request_id(self, client: AsyncClient):
        resp = await client.get("/v1/alerts/nonexistent-id")
        data = resp.json()
        assert "requestId" in data["error"]


class TestNearbySummary:
    async def test_nearby_summary_structure(self, client: AsyncClient):
        resp = await client.get("/v1/nearby/summary?areaId=demo_001&lat=31.23&lon=121.47")
        assert resp.status_code == 200
        data = resp.json()
        assert "requestId" in data
        assert "dataStatus" in data
        assert "timestamp" in data

    async def test_nearby_requires_lon_not_lng(self, client: AsyncClient):
        """API uses 'lon' parameter, not 'lng'."""
        resp = await client.get("/v1/nearby/summary?areaId=demo_001&lat=31.23&lon=121.47")
        assert resp.status_code == 200


class TestAlerts:
    async def test_list_alerts(self, client: AsyncClient):
        resp = await client.get("/v1/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert "requestId" in data

    async def test_get_alert_not_found(self, client: AsyncClient):
        resp = await client.get("/v1/alerts/test-alert-001")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"


class TestHazardReports:
    async def test_create_report(self, client: AsyncClient):
        resp = await client.post("/v1/hazard-reports", json={
            "reportType": "waterlogging",
            "severity": "ankle_or_less",
            "description": "Road flooding near bridge",
            "location": {
                "type": "Point",
                "coordinates": [121.4731, 31.2304],
            },
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["reportType"] == "waterlogging"
        assert data["status"] == "pending"

    async def test_report_location_fuzzing(self, client: AsyncClient):
        """Coordinates must be fuzzed to ~100m precision."""
        resp = await client.post("/v1/hazard-reports", json={
            "reportType": "flood",
            "severity": "knee_or_less",
            "description": "Water rising",
            "location": {
                "type": "Point",
                "coordinates": [121.47314, 31.23042],
            },
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        coords = data["location"]["coordinates"]
        # 3 decimal places ≈ 111m
        assert coords[0] == round(121.47314, 3)
        assert coords[1] == round(31.23042, 3)

    async def test_report_requires_description(self, client: AsyncClient):
        resp = await client.post("/v1/hazard-reports", json={
            "reportType": "waterlogging",
            "severity": "ankle",
        })
        assert resp.status_code == 422  # missing required field


class TestShelters:
    async def test_nearby_shelters(self, client: AsyncClient):
        resp = await client.get("/v1/shelters/nearby?lat=31.23&lon=121.47")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestRoutes:
    async def test_evacuation_route(self, client: AsyncClient):
        resp = await client.post("/v1/routes/evacuation", json={
            "origin": {"type": "Point", "coordinates": [121.47, 31.23]},
            "destination": {"type": "Point", "coordinates": [121.48, 31.24]},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestVoice:
    async def test_voice_announcement(self, client: AsyncClient):
        resp = await client.post("/v1/voice/announcement", json={
            "areaId": "demo_001",
            "riskLevel": "high",
            "language": "zh",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "generatedScript" in data
        # AI safety fields
        assert data["needsHumanReview"] is True
        assert "generatedAt" in data
        assert "expiresAt" in data
        assert "sourceIds" in data
        assert "dataFreshness" in data

    async def test_voice_requires_area_id(self, client: AsyncClient):
        resp = await client.post("/v1/voice/announcement", json={
            "riskLevel": "high",
            "language": "zh",
        })
        assert resp.status_code == 422  # missing areaId


class TestMapLayers:
    async def test_map_layers(self, client: AsyncClient):
        resp = await client.get("/v1/map/layers?areaId=demo_001")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestNotifications:
    async def test_create_subscription(self, client: AsyncClient):
        resp = await client.post("/v1/notifications/subscriptions", json={
            "areaId": "demo_001",
            "channel": "push",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert data["data"]["areaId"] == "demo_001"
        assert data["data"]["channel"] == "push"
        assert data["data"]["isActive"] is True


class TestAdminEndpoints:
    """Admin endpoints require auth — mock always returns admin."""

    async def test_risk_overview(self, client: AsyncClient):
        resp = await client.get("/v1/admin/risk/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    async def test_admin_reports(self, client: AsyncClient):
        resp = await client.get("/v1/admin/reports")
        assert resp.status_code == 200

    async def test_admin_audit_logs(self, client: AsyncClient):
        resp = await client.get("/v1/admin/audit-logs")
        assert resp.status_code == 200


class TestInternalEndpoints:
    """Internal endpoints for data ingestion."""

    async def test_risk_recompute(self, client: AsyncClient):
        resp = await client.post("/internal/risk/recompute", json={
            "areaIds": ["demo_001"],
        })
        assert resp.status_code == 200

    async def test_data_quality_issues(self, client: AsyncClient):
        resp = await client.get("/internal/data-quality/issues")
        assert resp.status_code == 200
