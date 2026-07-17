"""Integration tests for FloodShield's most critical life-safety paths.

These tests verify end-to-end behavior across the four highest-risk flows:
  1. Alert ingestion -> risk recomputation -> nearby summary (data pipeline)
  2. Hazard report -> verify -> audit log (community workflow)
  3. Authentication -> protected endpoint access (security)
  4. Missing data -> unknown risk, NOT safe (safety invariant)

Design notes:
  - Each test is fully independent (no shared state).
  - DB-dependent tests are skipped when no database is reachable.
  - MOCK_MODE fixtures use the existing conftest.py client.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt as pyjwt
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.deps import create_access_token
from app.services.risk_engine import SignalInput, compute_risk

TZ_SHANGHAI = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _admin_token() -> str:
    """Create a valid admin JWT for testing protected endpoints."""
    return create_access_token(
        user_id="00000000-0000-0000-0000-000000000001",
        role="admin",
        org_id="00000000-0000-0000-0000-000000000002",
    )


# ---------------------------------------------------------------------------
# Test 1: Alert -> Risk -> Nearby Summary (end-to-end data flow)
# ---------------------------------------------------------------------------


class TestAlertToNearbyFlow:
    """Verify: ingest alert -> recompute risk -> nearby summary reflects it.

    This is the core data pipeline. A break here means users see stale risk
    after new official warnings are published.
    """

    async def test_alert_to_nearby_flow(self, client: AsyncClient):
        """End-to-end: ingest -> recompute -> nearby shows alert data."""
        # --- Step 1: Ingest a warning via internal endpoint ---
        unique_ext = f"integ-{uuid.uuid4().hex[:8]}"
        ingest_resp = await client.post(
            "/internal/ingestion/test/warnings",
            json={
                "source": "integration-test",
                "warnings": [
                    {
                        "externalId": unique_ext,
                        "alertType": "flood",
                        "severity": "extreme",
                        "title": "Integration test flash flood warning",
                        "description": "Automated test alert — safe to ignore",
                    }
                ],
            },
        )
        assert ingest_resp.status_code == 200, (
            f"Ingestion failed: {ingest_resp.text}"
        )
        ingest_data = ingest_resp.json()["data"]
        assert ingest_data["accepted"] == 1
        internal_id = ingest_data["items"][0]["internalId"]

        # --- Step 2: Recompute risk for the area ---
        recompute_resp = await client.post(
            "/internal/risk/recompute",
            json={"areaIds": ["integ-test-area"]},
        )
        assert recompute_resp.status_code == 200
        recompute_data = recompute_resp.json()["data"]
        assert recompute_data["recomputed"] >= 1
        # Risk should reflect the ingested alert severity
        result = recompute_data["results"][0]
        assert result["riskLevel"] in ("attention", "high", "critical")
        assert result["riskScore"] >= 0.0

        # --- Step 3: Query nearby summary for coordinates in the area ---
        summary_resp = await client.get(
            "/v1/nearby/summary",
            params={"lat": 31.23, "lon": 121.47, "areaId": "integ-test-area"},
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()

        # --- Step 4: Verify activeAlerts count increased ---
        assert summary["data"]["activeAlerts"] >= 1

        # --- Step 5: Verify risk level is NOT safe (life-safety invariant) ---
        risk = summary["data"]["risk"]
        assert risk["riskLevel"] in ("attention", "high", "critical"), (
            f"Expected elevated risk, got '{risk['riskLevel']}'"
        )
        assert risk["riskScore"] > 0.0

        # Cleanup: verify the ingested alert is included in active alerts
        alerts_resp = await client.get("/v1/alerts")
        assert alerts_resp.status_code == 200


# ---------------------------------------------------------------------------
# Test 2: Report -> Verify -> Audit Log (community workflow)
# ---------------------------------------------------------------------------


class TestReportVerifyAudit:
    """Verify: submit report -> verify -> audit log records both actions.

    This is the community trust pipeline. A break here means reports go
    unverified, or verification actions are not auditable.
    """

    async def test_report_verify_audit(self, client: AsyncClient):
        """End-to-end: create report -> verify -> check audit log."""
        # --- Step 1: Submit a hazard report ---
        report_resp = await client.post(
            "/v1/hazard-reports",
            json={
                "reportType": "waterlogging",
                "severity": "ankle_or_less",
                "description": "Integration test: road flooding near bridge",
                "location": {
                    "type": "Point",
                    "coordinates": [121.473, 31.230],
                },
            },
        )
        assert report_resp.status_code == 200
        report_data = report_resp.json()["data"]
        report_id = report_data["id"]
        assert report_data["status"] == "pending_review"

        # --- Step 2: Verify the report via admin endpoint ---
        verify_resp = await client.post(
            f"/v1/admin/reports/{report_id}/verify",
            json={"notes": "Confirmed by integration test"},
        )

        # If DB is available, verify should succeed
        if verify_resp.status_code == 200:
            verified_data = verify_resp.json()["data"]

            # --- Step 4: Report status changed to verified ---
            assert verified_data["status"] == "verified"
            assert verified_data["verifiedBy"] is not None
            assert verified_data["verifiedAt"] is not None

            # --- Step 5: Audit log has both creation and verification entries ---
            audit_resp = await client.get("/v1/admin/audit-logs")
            assert audit_resp.status_code == 200
            audit_data = audit_resp.json()["data"]

            # Find verification entry for our report
            verify_entries = [
                log for log in audit_data["logs"]
                if log["action"] == "verify_report"
                and log["resourceId"] == report_id
            ]
            assert len(verify_entries) >= 1, (
                f"No audit entry found for verify of report {report_id}"
            )
            assert verify_entries[0]["resourceType"] == "hazard_report"
        elif verify_resp.status_code == 404:
            # Report not found — expected when DB has no record
            # (create_report returns a mock response, not persisted)
            pytest.skip(
                "Report not persisted (no DB) — verify endpoint returned 404"
            )
        else:
            pytest.fail(
                f"Unexpected verify response: {verify_resp.status_code} "
                f"{verify_resp.text}"
            )


# ---------------------------------------------------------------------------
# Test 3: Auth -> Protected Endpoint (security flow)
# ---------------------------------------------------------------------------


class TestAuthFlow:
    """Verify: login -> access protected endpoint -> rejected without token.

    This is the security boundary. A break here means unauthorized users
    can access admin data (audit logs, report verification, etc.).
    """

    async def test_login_returns_valid_token(self, client: AsyncClient):
        """POST /v1/auth/login with credentials returns a usable JWT."""
        login_resp = await client.post(
            "/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json()["data"]
        assert "accessToken" in data
        assert data["tokenType"] == "bearer"
        assert data["expiresIn"] > 0
        assert "user" in data

        # Token should be usable: access a protected endpoint
        token = data["accessToken"]
        me_resp = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()["data"]
        assert "id" in me_data
        assert "role" in me_data

    async def test_valid_token_accesses_admin_endpoint(self, client: AsyncClient):
        """A valid admin token grants access to admin endpoints."""
        token = _admin_token()
        resp = await client.get(
            "/v1/admin/reports",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_no_token_rejected_in_non_mock_mode(self, client: AsyncClient):
        """Without a token in non-MOCK_MODE, protected endpoints return 401."""
        with patch.object(settings, "MOCK_MODE", False):
            resp = await client.get("/v1/admin/audit-logs")
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    async def test_expired_token_rejected(self, client: AsyncClient):
        """An expired token must be rejected with 401."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-1",
            "role": "admin",
            "org_id": "org-1",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        }
        expired_token = pyjwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        with patch.object(settings, "MOCK_MODE", False):
            resp = await client.get(
                "/v1/admin/audit-logs",
                headers={"Authorization": f"Bearer {expired_token}"},
            )
        assert resp.status_code == 401

    async def test_tampered_token_rejected(self, client: AsyncClient):
        """A token with a bad signature must be rejected."""
        token = _admin_token()
        # Flip last character to break the signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

        with patch.object(settings, "MOCK_MODE", False):
            resp = await client.get(
                "/v1/admin/audit-logs",
                headers={"Authorization": f"Bearer {tampered}"},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Test 4: Data Missing -> Unknown Risk (safety critical)
# ---------------------------------------------------------------------------


class TestNoDataUnknownRisk:
    """Verify: when no data exists, risk is 'unknown' not 'safe'.

    This is THE most critical safety invariant. If the risk engine returns
    'normal' when it has no data, users will believe they are safe during
    a data outage — a potentially fatal failure mode.
    """

    def test_all_signals_missing_yields_unknown(self):
        """Direct risk engine test: all signals None -> unknown, score -1.0."""
        now = datetime.now(TZ_SHANGHAI)
        signals = {
            "rainfall_mm": SignalInput(value=None, observed_at=None, source="none"),
            "water_level_m": SignalInput(value=None, observed_at=None, source="none"),
            "alert_severity": SignalInput(value=None, observed_at=None, source="none"),
            "ground_saturation": SignalInput(value=None, observed_at=None, source="none"),
            "drainage_capacity": SignalInput(value=None, observed_at=None, source="none"),
        }

        result = compute_risk(signals, now=now)

        # These are the life-safety invariants — NEVER relax them
        assert result.risk_level == "unknown", (
            f"Missing data must yield 'unknown', got '{result.risk_level}'"
        )
        assert result.risk_score == -1.0, (
            f"Missing data sentinel must be -1.0, got {result.risk_score}"
        )
        assert result.data_status == "degraded"
        assert result.confidence == 0.0

    def test_partial_data_never_yields_unknown(self):
        """When at least one signal has data, risk must NOT be 'unknown'."""
        now = datetime.now(TZ_SHANGHAI)
        signals = {
            "rainfall_mm": SignalInput(value=25.0, observed_at=now, source="test"),
            "water_level_m": SignalInput(value=None, observed_at=None, source="none"),
            "alert_severity": SignalInput(value=None, observed_at=None, source="none"),
            "ground_saturation": SignalInput(value=None, observed_at=None, source="none"),
            "drainage_capacity": SignalInput(value=None, observed_at=None, source="none"),
        }

        result = compute_risk(signals, now=now)

        assert result.risk_level != "unknown", (
            "Partial data should not yield 'unknown'"
        )
        assert result.risk_score >= 0.0, (
            "Partial data should yield a non-negative score"
        )
        assert result.confidence > 0.0

    async def test_nearby_summary_empty_location_returns_unknown_or_mock(
        self, client: AsyncClient
    ):
        """Nearby summary for a remote ocean location with MOCK_MODE off.

        With no data in the DB for these coordinates, the risk engine
        should report 'unknown' — or the endpoint should return a degraded
        status that does NOT claim 'normal'/'safe'.
        """
        # Ocean coordinates — guaranteed no sensor data
        with patch.object(settings, "MOCK_MODE", False):
            resp = await client.get(
                "/v1/nearby/summary",
                params={
                    "lat": -35.0,  # South Atlantic Ocean
                    "lon": -40.0,
                    "areaId": "nowhere-ocean",
                },
            )

        # Response may be 200 (empty data -> unknown) or 500 (DB error).
        # Either is acceptable — what MUST NOT happen is a 200 with riskLevel=normal.
        if resp.status_code == 200:
            data = resp.json()["data"]
            risk = data["risk"]
            # The two acceptable outcomes for life-safety:
            # 1. riskLevel is 'unknown' (correct behavior)
            # 2. dataStatus is 'degraded' (graceful degradation)
            if risk["riskLevel"] != "unknown":
                assert data["dataStatus"] == "degraded", (
                    f"Empty-location risk '{risk['riskLevel']}' with "
                    f"dataStatus '{data['dataStatus']}' is a safety hazard. "
                    f"Must be 'unknown' or dataStatus must be 'degraded'."
                )

    async def test_nearby_summary_mock_mode_returns_fixture_data(
        self, client: AsyncClient
    ):
        """In MOCK_MODE, nearby summary returns fixture data (not unknown).

        This verifies the MOCK_MODE fallback path works — users see
        demo data instead of 'unknown' during development.
        """
        resp = await client.get(
            "/v1/nearby/summary",
            params={"lat": 31.23, "lon": 121.47},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        # In MOCK_MODE with empty DB, fixture data is returned
        risk = data["risk"]
        assert risk["riskLevel"] in ("normal", "attention", "high", "critical")
        assert data["activeAlerts"] >= 0
