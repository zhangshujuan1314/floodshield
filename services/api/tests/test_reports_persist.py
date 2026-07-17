"""Tests for reports endpoints backed by database persistence.

Verifies:
- POST / creates a HazardReport in DB with correct fields
- POST / stores both precise and fuzzed locations
- POST / allows anonymous reports (no user)
- POST / creates an AuditLog entry
- GET /{id} retrieves from DB
- MOCK_MODE fallback when DB fails
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db_session
from app.core.deps import get_optional_user
from app.models.base import AuditLog, HazardReport

TZ_SHANGHAI = timezone(timedelta(hours=8))
MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"


def _make_mock_session():
    """Build a mock AsyncSession that tracks add() calls."""
    session = AsyncMock()
    added_objects: list = []

    def capture_add(obj):
        added_objects.append(obj)

    session.add = MagicMock(side_effect=capture_add)
    session._added = added_objects
    return session


def _override_db(session):
    """Return an async generator function matching get_db_session's signature."""
    async def _gen():
        yield session
    return _gen


def _override_user(user_dict):
    """Return a coroutine that returns the given user (or None for anonymous)."""
    async def _get():
        return user_dict
    return _get


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------
# POST / - create report
# -----------------------------------------------------------------------

class TestCreateReportPersists:

    @patch("app.api.v1.reports.settings")
    async def test_post_creates_db_record(self, mock_settings, client: AsyncClient):
        """POST creates a HazardReport in DB with correct fields."""
        from app.main import app
        mock_settings.MOCK_MODE = False
        session = _make_mock_session()

        def fake_refresh(obj):
            if not obj.id:
                obj.id = uuid.uuid4()
            if not obj.created_at:
                obj.created_at = datetime.now(TZ_SHANGHAI)

        session.refresh = AsyncMock(side_effect=fake_refresh)
        app.dependency_overrides[get_db_session] = _override_db(session)
        app.dependency_overrides[get_optional_user] = _override_user(
            {"id": MOCK_USER_ID, "role": "viewer"}
        )

        payload = {
            "reportType": "flood",
            "severity": "high",
            "description": "Test flood report",
            "location": {"type": "Point", "coordinates": [121.473, 31.235]},
        }

        resp = await client.post("/v1/hazard-reports", json=payload)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["reportType"] == "flood"
        assert data["severity"] == "high"
        assert data["status"] == "pending_review"
        assert data["id"] is not None

        reports = [o for o in session._added if isinstance(o, HazardReport)]
        assert len(reports) == 1
        report = reports[0]
        assert report.reporter_id == uuid.UUID(MOCK_USER_ID)
        assert report.report_type == "flood"
        assert report.severity == "high"
        assert report.description == "Test flood report"
        assert report.status == "pending_review"

    @patch("app.api.v1.reports.settings")
    async def test_post_stores_both_locations(self, mock_settings, client: AsyncClient):
        """POST stores precise location_geojson and fuzzed location_fuzzed_geojson."""
        from app.main import app
        mock_settings.MOCK_MODE = False
        session = _make_mock_session()

        def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(TZ_SHANGHAI)

        session.refresh = AsyncMock(side_effect=fake_refresh)
        app.dependency_overrides[get_db_session] = _override_db(session)
        app.dependency_overrides[get_optional_user] = _override_user(
            {"id": MOCK_USER_ID, "role": "viewer"}
        )

        payload = {
            "reportType": "flood",
            "severity": "high",
            "description": "Precise vs fuzzed test",
            "location": {"type": "Point", "coordinates": [121.4731, 31.2356]},
        }

        resp = await client.post("/v1/hazard-reports", json=payload)
        assert resp.status_code == 200

        report = [o for o in session._added if isinstance(o, HazardReport)][0]

        # Precise coords preserved
        assert report.location_geojson["coordinates"] == [121.4731, 31.2356]
        # Fuzzed coords truncated to 3 decimals
        assert report.location_fuzzed_geojson["coordinates"] == [121.473, 31.236]
        assert report.location_fuzzed_geojson["precision"] == "approximate"

    @patch("app.api.v1.reports.settings")
    async def test_post_anonymous_report(self, mock_settings, client: AsyncClient):
        """POST with no user creates an anonymous report (reporter_id=None)."""
        from app.main import app
        mock_settings.MOCK_MODE = False
        session = _make_mock_session()

        def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(TZ_SHANGHAI)

        session.refresh = AsyncMock(side_effect=fake_refresh)
        app.dependency_overrides[get_db_session] = _override_db(session)
        app.dependency_overrides[get_optional_user] = _override_user(None)

        payload = {
            "reportType": "road_damage",
            "severity": "medium",
            "description": "Anonymous report test",
        }

        resp = await client.post("/v1/hazard-reports", json=payload)
        assert resp.status_code == 200

        report = [o for o in session._added if isinstance(o, HazardReport)][0]
        assert report.reporter_id is None

    @patch("app.api.v1.reports.settings")
    async def test_post_creates_audit_log(self, mock_settings, client: AsyncClient):
        """POST creates an AuditLog entry for report submission."""
        from app.main import app
        mock_settings.MOCK_MODE = False
        session = _make_mock_session()

        def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(TZ_SHANGHAI)

        session.refresh = AsyncMock(side_effect=fake_refresh)
        app.dependency_overrides[get_db_session] = _override_db(session)
        app.dependency_overrides[get_optional_user] = _override_user(
            {"id": MOCK_USER_ID, "role": "viewer"}
        )

        payload = {
            "reportType": "flood",
            "severity": "low",
            "description": "Audit log test",
        }

        resp = await client.post("/v1/hazard-reports", json=payload)
        assert resp.status_code == 200

        logs = [o for o in session._added if isinstance(o, AuditLog)]
        assert len(logs) == 1
        log = logs[0]
        assert log.action == "submit_report"
        assert log.resource_type == "hazard_report"
        assert log.actor_id == uuid.UUID(MOCK_USER_ID)
        assert log.resource_id is not None


# -----------------------------------------------------------------------
# GET /{report_id} - retrieve from DB
# -----------------------------------------------------------------------

class TestGetReportFromDB:

    @patch("app.api.v1.reports.settings")
    async def test_get_returns_db_record(self, mock_settings, client: AsyncClient):
        """GET retrieves report from DB using fuzzed location for display."""
        from app.main import app
        mock_settings.MOCK_MODE = False

        report_id = uuid.uuid4()
        now = datetime.now(TZ_SHANGHAI)
        mock_report = MagicMock(spec=HazardReport)
        mock_report.id = report_id
        mock_report.report_type = "flood"
        mock_report.severity = "high"
        mock_report.description = "DB test"
        mock_report.photo_url = None
        mock_report.location_fuzzed_geojson = {
            "type": "Point", "coordinates": [121.473, 31.236], "precision": "approximate",
        }
        mock_report.status = "pending_review"
        mock_report.created_at = now

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_report

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db_session] = _override_db(session)

        resp = await client.get(f"/v1/hazard-reports/{report_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == str(report_id)
        assert data["reportType"] == "flood"
        assert data["location"]["precision"] == "approximate"

    @patch("app.api.v1.reports.settings")
    async def test_get_not_found_raises(self, mock_settings, client: AsyncClient):
        """GET with non-existent UUID raises 404."""
        from app.main import app
        mock_settings.MOCK_MODE = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db_session] = _override_db(session)

        resp = await client.get(f"/v1/hazard-reports/{uuid.uuid4()}")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    @patch("app.api.v1.reports.settings")
    async def test_get_invalid_uuid_raises(self, mock_settings, client: AsyncClient):
        """GET with non-UUID string raises 404."""
        mock_settings.MOCK_MODE = False

        resp = await client.get("/v1/hazard-reports/not-a-uuid")
        assert resp.status_code == 404


# -----------------------------------------------------------------------
# MOCK_MODE fallback
# -----------------------------------------------------------------------

class TestMockModeFallback:

    @patch("app.api.v1.reports.settings")
    async def test_post_mock_fallback(self, mock_settings, client: AsyncClient):
        """When DB fails and MOCK_MODE is on, POST returns mock response."""
        from app.main import app
        mock_settings.MOCK_MODE = True
        session = _make_mock_session()
        session.commit = AsyncMock(side_effect=Exception("DB unavailable"))
        app.dependency_overrides[get_db_session] = _override_db(session)
        app.dependency_overrides[get_optional_user] = _override_user(
            {"id": MOCK_USER_ID, "role": "viewer"}
        )

        payload = {
            "reportType": "flood",
            "severity": "high",
            "description": "Mock fallback test",
        }

        resp = await client.post("/v1/hazard-reports", json=payload)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["reportType"] == "flood"
        assert data["status"] == "pending_review"
        assert data["id"] is not None

    @patch("app.api.v1.reports.settings")
    async def test_get_mock_fallback(self, mock_settings, client: AsyncClient):
        """When report not in DB and MOCK_MODE is on, GET returns fixture."""
        from app.main import app
        mock_settings.MOCK_MODE = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db_session] = _override_db(session)

        report_id = str(uuid.uuid4())
        resp = await client.get(f"/v1/hazard-reports/{report_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == report_id
        assert data["reportType"] == "flood"
        assert data["severity"] == "high"


# -----------------------------------------------------------------------
# Location fuzzing helper
# -----------------------------------------------------------------------

class TestFuzzLocation:

    def test_fuzzes_point_coordinates(self):
        from app.api.v1.reports import _fuzz_location
        raw = {"type": "Point", "coordinates": [121.47312, 31.23567]}
        fuzzed = _fuzz_location(raw)
        assert fuzzed["coordinates"] == [121.473, 31.236]
        assert fuzzed["precision"] == "approximate"

    def test_preserves_non_point(self):
        from app.api.v1.reports import _fuzz_location
        raw = {"type": "Polygon", "coordinates": [[[121.47, 31.23]]]}
        fuzzed = _fuzz_location(raw)
        assert fuzzed == raw

    def test_fuzzing_reduces_precision(self):
        from app.api.v1.reports import _fuzz_location
        raw = {"type": "Point", "coordinates": [114.273456, 30.582901]}
        fuzzed = _fuzz_location(raw)
        # 3 decimal places ~ 111m
        assert len(str(fuzzed["coordinates"][0]).split(".")[-1]) <= 3
        assert len(str(fuzzed["coordinates"][1]).split(".")[-1]) <= 3
