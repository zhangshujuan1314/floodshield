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


class TestUnknownRiskLevel:
    """Critical safety test: when ALL signals are missing, risk_level must be 'unknown',
    NOT 'low' or 'normal'. Missing data must NEVER be interpreted as safe."""

    def test_all_missing_returns_unknown_risk_level(self):
        """The most dangerous antipattern: no data = green/safe."""
        now = _now()
        result = compute_risk({}, now=now)
        assert result.risk_level == "unknown"
        assert result.risk_score == 0.0
        assert result.confidence == 0.0
        assert result.data_status == "degraded"

    def test_unknown_is_not_low(self):
        """Ensure 'unknown' is distinct from 'low' — they must not be confused."""
        now = _now()
        # All missing → unknown
        unknown_result = compute_risk({}, now=now)
        # All normal low → low
        low_result = compute_risk({
            "rainfall_mm": SignalInput(value=1.0, observed_at=now - timedelta(minutes=5)),
            "water_level_m": SignalInput(value=0.3, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=0.0, observed_at=now - timedelta(minutes=5)),
            "ground_saturation": SignalInput(value=0.1, observed_at=now - timedelta(minutes=5)),
            "drainage_capacity": SignalInput(value=0.95, observed_at=now - timedelta(minutes=5)),
        }, now=now)
        assert unknown_result.risk_level == "unknown"
        assert low_result.risk_level == "low"
        assert unknown_result.risk_level != low_result.risk_level

    def test_partial_missing_not_unknown(self):
        """If at least one signal is available, risk_level should not be 'unknown'."""
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=20.0, observed_at=now - timedelta(minutes=10)),
            # All others missing
        }
        result = compute_risk(signals, now=now)
        assert result.risk_level != "unknown"
        assert result.risk_level in ("low", "medium", "high", "extreme")


class TestRuleVersionReplay:
    """Risk snapshots must be reproducible from input snapshots."""

    def test_same_inputs_same_output(self):
        """Given identical inputs, risk engine must produce identical results."""
        now = _now()
        signals = {
            "rainfall_mm": SignalInput(value=50.0, observed_at=now - timedelta(minutes=15)),
            "water_level_m": SignalInput(value=2.5, observed_at=now - timedelta(minutes=10)),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(minutes=30)),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
            "drainage_capacity": SignalInput(value=0.5, observed_at=now - timedelta(hours=1)),
        }
        result1 = compute_risk(signals, now=now)
        result2 = compute_risk(signals, now=now)
        assert result1.risk_score == result2.risk_score
        assert result1.risk_level == result2.risk_level
        assert result1.confidence == result2.confidence
        assert result1.data_status == result2.data_status
        assert result1.conflicts == result2.conflicts

    def test_boundary_values(self):
        """Test exact threshold boundaries."""
        now = _now()
        # Exactly at "medium" threshold for rainfall (30mm)
        signals = {
            "rainfall_mm": SignalInput(value=30.0, observed_at=now - timedelta(minutes=10)),
            "water_level_m": SignalInput(value=0.5, observed_at=now - timedelta(minutes=5)),
            "alert_severity": SignalInput(value=0.0, observed_at=now - timedelta(minutes=5)),
            "ground_saturation": SignalInput(value=0.1, observed_at=now - timedelta(minutes=5)),
            "drainage_capacity": SignalInput(value=0.9, observed_at=now - timedelta(minutes=5)),
        }
        result = compute_risk(signals, now=now)
        # At threshold, should be at least "medium" level contribution
        rainfall_signal = next(s for s in result.signals if s.signal == "rainfall_mm")
        assert rainfall_signal.sub_score >= 0.5  # medium threshold
