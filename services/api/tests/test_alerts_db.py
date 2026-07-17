"""Tests for alerts endpoints backed by real database (OfficialAlert model).

Verifies:
- list_alerts queries the DB and applies filters
- get_alert queries by UUID and raises NotFound when missing
- MOCK_MODE fallback returns fixture data when DB is empty
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.alerts import _alert_to_dict, _build_fixtures, _filter_fixtures
from app.models.base import OfficialAlert

TZ_SHANGHAI = timezone(timedelta(hours=8))


def _make_alert(
    alert_id: uuid.UUID | None = None,
    source: str = "CMA",
    external_id: str | None = "ext-001",
    alert_type: str = "flood",
    severity: str = "high",
    title: str = "Test Alert",
    description: str = "Test description",
    is_active: bool = True,
    expires_hours: int = 24,
) -> OfficialAlert:
    """Build an OfficialAlert ORM instance (not persisted)."""
    now = datetime.now(TZ_SHANGHAI)
    alert = OfficialAlert(
        id=alert_id or uuid.uuid4(),
        source=source,
        external_id=external_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        area_geojson=None,
        effective_at=now,
        expires_at=now + timedelta(hours=expires_hours),
        is_active=is_active,
        created_at=now - timedelta(hours=1),
        updated_at=now,
    )
    return alert


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# -----------------------------------------------------------------------
# list_alerts
# -----------------------------------------------------------------------

class TestListAlertsDB:
    """list_alerts backed by database session."""

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=[])
    async def test_empty_db_non_mock_returns_empty(self, mock_query, mock_settings, client: AsyncClient):
        """When MOCK_MODE is off and DB is empty, return empty data list."""
        mock_settings.MOCK_MODE = False

        resp = await client.get("/v1/alerts?activeOnly=false")

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["dataStatus"] == "normal"

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts")
    async def test_returns_db_rows(self, mock_query, mock_settings, client: AsyncClient):
        """When DB has rows, return them as camelCase dicts."""
        mock_settings.MOCK_MODE = False
        alert = _make_alert(alert_type="rainfall", severity="extreme")
        mock_query.return_value = [_alert_to_dict(alert)]

        resp = await client.get("/v1/alerts?activeOnly=false")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        item = data["data"][0]
        assert item["alertType"] == "rainfall"
        assert item["severity"] == "extreme"
        assert item["id"] == str(alert.id)

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=[])
    async def test_active_only_filter_calls_query(self, mock_query, mock_settings, client: AsyncClient):
        """activeOnly=true is forwarded to the query helper."""
        mock_settings.MOCK_MODE = False

        resp = await client.get("/v1/alerts?activeOnly=true")

        assert resp.status_code == 200
        mock_query.assert_called_once_with(active_only=True, severity=None, alert_type=None)

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=[])
    async def test_severity_filter_forwarded(self, mock_query, mock_settings, client: AsyncClient):
        """severity query param is forwarded to the query helper."""
        mock_settings.MOCK_MODE = False

        resp = await client.get("/v1/alerts?activeOnly=false&severity=high")

        assert resp.status_code == 200
        mock_query.assert_called_once_with(active_only=False, severity="high", alert_type=None)

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=[])
    async def test_alert_type_filter_forwarded(self, mock_query, mock_settings, client: AsyncClient):
        """alertType query param is forwarded to the query helper."""
        mock_settings.MOCK_MODE = False

        resp = await client.get("/v1/alerts?activeOnly=false&alertType=flood")

        assert resp.status_code == 200
        mock_query.assert_called_once_with(active_only=False, severity=None, alert_type="flood")


# -----------------------------------------------------------------------
# get_alert
# -----------------------------------------------------------------------

class TestGetAlertDB:
    """get_alert backed by database session."""

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_get_alert")
    async def test_valid_uuid_returns_alert(self, mock_get, mock_settings, client: AsyncClient):
        """Querying with a valid UUID that exists returns the alert."""
        mock_settings.MOCK_MODE = False
        alert_id = uuid.uuid4()
        alert = _make_alert(alert_id=alert_id)
        mock_get.return_value = _alert_to_dict(alert)

        resp = await client.get(f"/v1/alerts/{alert_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == str(alert_id)
        assert data["data"]["alertType"] == "flood"

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_get_alert", return_value=None)
    async def test_missing_uuid_raises_not_found(self, mock_get, mock_settings, client: AsyncClient):
        """Querying with a UUID not in DB raises NotFound (404)."""
        mock_settings.MOCK_MODE = False

        resp = await client.get(f"/v1/alerts/{uuid.uuid4()}")

        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"

    @patch("app.api.v1.alerts.settings")
    async def test_invalid_uuid_raises_not_found(self, mock_settings, client: AsyncClient):
        """A non-UUID string raises NotFound."""
        mock_settings.MOCK_MODE = False

        resp = await client.get("/v1/alerts/not-a-valid-uuid")
        assert resp.status_code == 404


# -----------------------------------------------------------------------
# MOCK_MODE fallback
# -----------------------------------------------------------------------

class TestMockModeFallback:
    """When MOCK_MODE is on and DB is empty, fixture data is returned."""

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=[])
    async def test_list_returns_fixtures_when_db_empty(self, mock_query, mock_settings, client: AsyncClient):
        """MOCK_MODE=True + empty DB => fixture alerts returned."""
        mock_settings.MOCK_MODE = True

        resp = await client.get("/v1/alerts?activeOnly=false")

        assert resp.status_code == 200
        data = resp.json()
        fixtures = _build_fixtures()
        assert len(data["data"]) == len(fixtures)
        assert data["data"][0]["id"] == fixtures[0]["id"]

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=None)
    async def test_list_returns_fixtures_when_db_unavailable(self, mock_query, mock_settings, client: AsyncClient):
        """MOCK_MODE=True + DB unavailable (None) => fixture alerts returned."""
        mock_settings.MOCK_MODE = True

        resp = await client.get("/v1/alerts?activeOnly=false")

        assert resp.status_code == 200
        data = resp.json()
        fixtures = _build_fixtures()
        assert len(data["data"]) == len(fixtures)

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_get_alert", return_value=None)
    async def test_get_returns_fixture_when_db_empty(self, mock_get, mock_settings, client: AsyncClient):
        """MOCK_MODE=True + missing UUID => check fixtures for match."""
        mock_settings.MOCK_MODE = True

        fixture_id = "a0000000-0000-0000-0000-000000000001"
        resp = await client.get(f"/v1/alerts/{fixture_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == fixture_id

    @patch("app.api.v1.alerts.settings")
    @patch("app.api.v1.alerts._try_query_alerts", return_value=[])
    async def test_mock_mode_still_filters_fixtures(self, mock_query, mock_settings, client: AsyncClient):
        """MOCK_MODE fallback still applies severity/type filters."""
        mock_settings.MOCK_MODE = True

        resp = await client.get("/v1/alerts?activeOnly=false&severity=extreme")

        assert resp.status_code == 200
        data = resp.json()
        for item in data["data"]:
            assert item["severity"] == "extreme"


# -----------------------------------------------------------------------
# _alert_to_dict helper
# -----------------------------------------------------------------------

class TestAlertToDict:
    def test_converts_orm_to_camelcase_dict(self):
        alert = _make_alert()
        d = _alert_to_dict(alert)
        assert d["id"] == str(alert.id)
        assert d["alertType"] == alert.alert_type
        assert d["isActive"] == alert.is_active
        assert d["areaGeojson"] is None
        assert "createdAt" in d

    def test_iso_format_datetimes(self):
        alert = _make_alert()
        d = _alert_to_dict(alert)
        datetime.fromisoformat(d["effectiveAt"])
        datetime.fromisoformat(d["expiresAt"])
        datetime.fromisoformat(d["createdAt"])


# -----------------------------------------------------------------------
# _filter_fixtures helper
# -----------------------------------------------------------------------

class TestFilterFixtures:
    def test_active_only_filters_inactive(self):
        fixtures = _build_fixtures()
        result = _filter_fixtures(fixtures, active_only=True)
        for item in result:
            assert item["isActive"] is True

    def test_severity_filter(self):
        fixtures = _build_fixtures()
        result = _filter_fixtures(fixtures, active_only=False, severity="extreme")
        for item in result:
            assert item["severity"] == "extreme"

    def test_alert_type_filter(self):
        fixtures = _build_fixtures()
        result = _filter_fixtures(fixtures, active_only=False, alert_type="flood")
        for item in result:
            assert item["alertType"] == "flood"
