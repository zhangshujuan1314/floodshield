"""Mock weather provider returning fixture data with proper timestamps."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

TZ_SHANGHAI = timezone(timedelta(hours=8))


class MockWeatherProvider:
    async def get_current(self, lat: float, lon: float) -> dict[str, Any]:
        now = datetime.now(TZ_SHANGHAI)
        return {
            "station_id": "MOCK-WS-001",
            "location": {"lat": lat, "lon": lon},
            "observed_at": now.isoformat(),
            "rainfall_mm": 25.4,
            "rainfall_1h_mm": 12.0,
            "rainfall_24h_mm": 45.2,
            "temperature_c": 28.5,
            "humidity_pct": 85.0,
            "wind_speed_ms": 5.2,
            "wind_direction_deg": 180,
            "pressure_hpa": 1008.5,
            "visibility_m": 8000,
            "source": "mock_weather_service",
            "quality_flag": "normal",
        }

    async def get_rainfall_series(self, lat: float, lon: float, hours: int = 24) -> list[dict[str, Any]]:
        now = datetime.now(TZ_SHANGHAI)
        series = []
        for i in range(hours):
            ts = now - timedelta(hours=hours - 1 - i)
            series.append({
                "station_id": "MOCK-WS-001",
                "observed_at": ts.isoformat(),
                "rainfall_mm": round(2.0 + (i % 6) * 1.5, 1),
                "source": "mock_weather_service",
            })
        return series

    async def get_forecast(self, lat: float, lon: float, hours: int = 48) -> list[dict[str, Any]]:
        now = datetime.now(TZ_SHANGHAI)
        forecasts = []
        for i in range(1, hours + 1):
            ts = now + timedelta(hours=i)
            forecasts.append({
                "forecast_at": ts.isoformat(),
                "rainfall_mm": round(5.0 + (i % 8) * 2.0, 1),
                "temperature_c": round(26.0 + (i % 12) * 0.5, 1),
                "source": "mock_weather_service",
            })
        return forecasts


provider = MockWeatherProvider()
