from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.risk_engine import SignalInput, compute_risk

TZ_SHANGHAI = timezone(timedelta(hours=8))


def _now() -> datetime:
    return datetime(2024, 7, 15, 14, 0, 0, tzinfo=TZ_SHANGHAI)


class TestNormalInputs:
    def test_all_normal_low_risk(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=5.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=0.8, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=0.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.2, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.9, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        assert result.risk_level == "low"
        assert result.risk_score < 0.3
        assert result.confidence == 1.0
        assert result.data_status == "normal"
        assert len(result.conflicts) == 0

    def test_all_normal_high_risk(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=120.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=5.0, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=3.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.85, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.2, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        assert result.risk_level in ("high", "extreme")
        assert result.risk_score >= 0.6
        assert result.confidence == 1.0
        assert result.data_status == "normal"


class TestStaleInputs:
    def test_stale_rainfall(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=80.0, observed_at=now - timedelta(hours=2)),  # stale > 1hr
            "water_level_m": SignalInput(value=3.0, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        assert result.data_status == "degraded"
        # Stale signal is still used in calculation but reduces data_status
        stale_signals = [s for s in result.signals if s.data_status == "stale"]
        assert len(stale_signals) >= 1

    def test_all_stale(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=50.0, observed_at=now - timedelta(hours=5)),
            "water_level_m": SignalInput(value=3.0, observed_at=now - timedelta(hours=3)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(hours=6)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=8)),
            "drainage_capacity": SignalInput(value=0.5, observed_at=now - timedelta(hours=8)),
        }
        result = compute_risk(signals, now=now)
        assert result.data_status == "degraded"
        assert all(s.data_status == "stale" for s in result.signals)


class TestMissingInputs:
    def test_missing_rainfall(self):
        now = _now()
        signals = {
            # rainfall_mm is missing
            "water_level_m": SignalInput(value=2.0, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        assert result.data_status == "degraded"
        assert result.confidence < 1.0
        missing = [s for s in result.signals if s.data_status == "unknown"]
        assert len(missing) == 1
        assert missing[0].signal == "rainfall_mm"

    def test_all_missing(self):
        now = _now()
        result = compute_risk({}, now=now)
        assert result.data_status == "degraded"
        assert result.risk_score == 0.0
        assert result.confidence == 0.0
        assert all(s.data_status == "unknown" for s in result.signals)

    def test_missing_value_field(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=None, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=2.0, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        missing = [s for s in result.signals if s.data_status == "unknown"]
        assert len(missing) >= 1


class TestConflictingInputs:
    def test_high_rainfall_low_water(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=100.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=0.3, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=1.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.4, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.7, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        assert len(result.conflicts) > 0
        assert result.data_status == "degraded"
        assert result.confidence < 1.0  # penalized

    def test_low_rainfall_high_water(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=2.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=5.5, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        assert len(result.conflicts) > 0
        assert "upstream" in result.conflicts[0].lower() or "possible" in result.conflicts[0].lower()


class TestOutOfRangeInputs:
    def test_negative_rainfall(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=-5.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=2.0, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        oor = [s for s in result.signals if s.data_status == "out_of_range"]
        assert len(oor) == 1
        assert result.data_status == "degraded"

    def test_excessive_water_level(self):
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=30.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=100.0, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1)),
        }
        result = compute_risk(signals, now=now)
        oor = [s for s in result.signals if s.data_status == "out_of_range"]
        assert len(oor) >= 1
