"""Deterministic risk engine with configurable weights, evidence tracking,
freshness/confidence scoring.

Handles five input scenarios:
  - normal:   recent data within thresholds
  - stale:    data older than freshness threshold (>1 hour)
  - missing:  no data for a required signal
  - conflicting: signals disagree (e.g. rainfall high but water level low)
  - out-of-range: value outside physically plausible bounds
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

TZ_SHANGHAI = timezone(timedelta(hours=8))

# --- Configuration -----------------------------------------------------------

SIGNAL_WEIGHTS: dict[str, float] = {
    "rainfall_mm": 0.30,
    "water_level_m": 0.30,
    "alert_severity": 0.20,
    "ground_saturation": 0.10,
    "drainage_capacity": 0.10,
}

# Freshness thresholds per signal (seconds)
FRESHNESS_THRESHOLDS: dict[str, float] = {
    "rainfall_mm": 3600,        # 1 hour
    "water_level_m": 1800,      # 30 minutes
    "alert_severity": 7200,     # 2 hours
    "ground_saturation": 14400, # 4 hours
    "drainage_capacity": 14400,
}

# Physically plausible ranges [min, max]
PHYSICAL_RANGES: dict[str, tuple[float, float]] = {
    "rainfall_mm": (0.0, 500.0),
    "water_level_m": (0.0, 50.0),
    "alert_severity": (0.0, 4.0),  # 0=none,1=watch,2=warning,3=emergency,4=extreme
    "ground_saturation": (0.0, 1.0),
    "drainage_capacity": (0.0, 1.0),
}

# Normalized thresholds that map raw value -> risk sub-score [0..1]
NORMALIZATION: dict[str, dict[str, float]] = {
    "rainfall_mm": {"low": 10, "medium": 30, "high": 80, "extreme": 150},
    "water_level_m": {"low": 1.0, "medium": 2.5, "high": 4.0, "extreme": 6.0},
    "alert_severity": {"low": 1, "medium": 2, "high": 3, "extreme": 4},
    "ground_saturation": {"low": 0.3, "medium": 0.5, "high": 0.7, "extreme": 0.9},
    "drainage_capacity": {"low": 0.7, "medium": 0.5, "high": 0.3, "extreme": 0.1},
}


@dataclass
class SignalInput:
    value: float | None
    observed_at: datetime | None = None
    source: str = "unknown"


@dataclass
class SignalResult:
    signal: str
    value: float | None
    sub_score: float  # 0.0 .. 1.0
    weight: float
    data_status: str  # "normal" | "stale" | "unknown" | "out_of_range"
    freshness_seconds: float | None = None
    message: str = ""


@dataclass
class RiskResult:
    risk_score: float  # 0.0 .. 1.0
    risk_level: str    # "low" | "medium" | "high" | "extreme"
    confidence: float  # 0.0 .. 1.0
    data_status: str   # "normal" if all signals ok, else "degraded"
    signals: list[SignalResult] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    computed_at: datetime = field(default_factory=lambda: datetime.now(TZ_SHANGHAI))


def _normalize(signal: str, value: float) -> float:
    """Map a raw signal value to a 0..1 risk sub-score."""
    thresholds = NORMALIZATION.get(signal, {})
    if not thresholds:
        return 0.5

    if signal == "drainage_capacity":
        # Inverted: lower capacity = higher risk
        if value <= thresholds["extreme"]:
            return 1.0
        if value <= thresholds["high"]:
            return 0.8
        if value <= thresholds["medium"]:
            return 0.5
        if value <= thresholds["low"]:
            return 0.2
        return 0.0

    if value >= thresholds["extreme"]:
        return 1.0
    if value >= thresholds["high"]:
        return 0.8
    if value >= thresholds["medium"]:
        return 0.5
    if value >= thresholds["low"]:
        return 0.2
    return 0.05


def _check_range(signal: str, value: float) -> bool:
    rng = PHYSICAL_RANGES.get(signal)
    if rng is None:
        return True
    return rng[0] <= value <= rng[1]


def _freshness(signal: str, observed_at: datetime | None, now: datetime) -> tuple[float | None, str]:
    """Return (seconds_ago, status). status is 'normal' or 'stale'."""
    if observed_at is None:
        return None, "unknown"
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=TZ_SHANGHAI)
    delta = (now - observed_at).total_seconds()
    threshold = FRESHNESS_THRESHOLDS.get(signal, 3600)
    status = "stale" if delta > threshold else "normal"
    return delta, status


def _detect_conflicts(signals: dict[str, SignalResult]) -> list[str]:
    """Detect logical conflicts between signals."""
    conflicts: list[str] = []
    rainfall = signals.get("rainfall_mm")
    water = signals.get("water_level_m")
    if rainfall and water:
        if rainfall.sub_score > 0.7 and water.sub_score < 0.2:
            conflicts.append("High rainfall but low water level — possible data lag")
        if rainfall.sub_score < 0.2 and water.sub_score >= 0.8:
            conflicts.append("Low rainfall but high water level — upstream event possible")
    return conflicts


def compute_risk(
    signals: dict[str, SignalInput],
    now: datetime | None = None,
) -> RiskResult:
    """Compute deterministic risk score from signal inputs.

    Args:
        signals: mapping of signal name -> SignalInput
        now: override current time (for testing)

    Returns:
        RiskResult with score, level, confidence, evidence, conflicts
    """
    now = now or datetime.now(TZ_SHANGHAI)
    results: dict[str, SignalResult] = {}
    total_weight = 0.0
    weighted_sum = 0.0
    available_weight = 0.0
    degraded = False

    for signal, weight in SIGNAL_WEIGHTS.items():
        inp = signals.get(signal)
        total_weight += weight

        # Missing signal
        if inp is None or inp.value is None:
            results[signal] = SignalResult(
                signal=signal,
                value=None,
                sub_score=0.0,
                weight=weight,
                data_status="unknown",
                message=f"No data available for {signal}",
            )
            degraded = True
            continue

        value = inp.value

        # Out-of-range check
        if not _check_range(signal, value):
            results[signal] = SignalResult(
                signal=signal,
                value=value,
                sub_score=0.0,
                weight=weight,
                data_status="out_of_range",
                message=f"Value {value} outside plausible range {PHYSICAL_RANGES.get(signal)}",
            )
            degraded = True
            continue

        # Freshness check
        freshness_s, freshness_status = _freshness(signal, inp.observed_at, now)

        sub_score = _normalize(signal, value)

        status = freshness_status
        if freshness_status == "stale":
            degraded = True

        results[signal] = SignalResult(
            signal=signal,
            value=value,
            sub_score=sub_score,
            weight=weight,
            data_status=status,
            freshness_seconds=freshness_s,
            message="" if status == "normal" else f"Data is stale ({freshness_s:.0f}s old)",
        )

        weighted_sum += sub_score * weight
        available_weight += weight

    # Compute final score: redistribute weight from missing signals
    if available_weight > 0:
        risk_score = weighted_sum / available_weight
    else:
        # ALL signals missing — must NOT default to safe/green
        risk_score = 0.0
        degraded = True

    risk_score = round(min(max(risk_score, 0.0), 1.0), 4)

    # Confidence: fraction of weight backed by fresh, in-range data
    confidence = round(available_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Detect conflicts
    conflicts = _detect_conflicts(results)
    if conflicts:
        degraded = True
        confidence *= 0.8  # penalize confidence when signals conflict

    # Risk level — when ALL signals are missing, risk_level is "unknown"
    # This prevents the "missing data = safe" antipattern
    if available_weight == 0:
        risk_level = "unknown"
    elif risk_score >= 0.8:
        risk_level = "extreme"
    elif risk_score >= 0.6:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskResult(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=confidence,
        data_status="degraded" if degraded else "normal",
        signals=list(results.values()),
        conflicts=conflicts,
        computed_at=now,
    )
