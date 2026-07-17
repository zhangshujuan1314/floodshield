"""Real weather provider using OpenWeatherMap API with in-memory TTL cache."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TZ_SHANGHAI = timezone(timedelta(hours=8))

_CACHE_TTL_CURRENT = 300  # 5 minutes
_CACHE_TTL_FORECAST = 900  # 15 minutes


class _Cache:
    """Dead-simple in-memory TTL cache keyed by string."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str, ttl: float) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic(), value)


class RealWeatherProvider:
    """Weather provider backed by OpenWeatherMap (or compatible CMA proxy)."""

    def __init__(self) -> None:
        self._base_url = settings.WEATHER_API_URL.rstrip("/")
        self._api_key = settings.WEATHER_API_KEY
        self._cache = _Cache()

    # ------------------------------------------------------------------
    # Public interface (matches MockWeatherProvider)
    # ------------------------------------------------------------------

    async def get_current(self, lat: float, lon: float) -> dict[str, Any] | None:
        cache_key = f"current:{lat:.4f},{lon:.4f}"
        cached = self._cache.get(cache_key, _CACHE_TTL_CURRENT)
        if cached is not None:
            return cached

        data = await self._fetch("/weather", {"lat": lat, "lon": lon, "units": "metric"})
        if data is None:
            return None

        now = datetime.now(TZ_SHANGHAI)
        result: dict[str, Any] = {
            "station_id": data.get("name", "unknown"),
            "location": {"lat": lat, "lon": lon},
            "observed_at": now.isoformat(),
            "rainfall_mm": self._extract_rain(data, 1),
            "rainfall_1h_mm": self._extract_rain(data, 1),
            "rainfall_24h_mm": self._extract_rain(data, 24),
            "temperature_c": data.get("main", {}).get("temp"),
            "humidity_pct": data.get("main", {}).get("humidity"),
            "wind_speed_ms": data.get("wind", {}).get("speed"),
            "wind_direction_deg": data.get("wind", {}).get("deg"),
            "pressure_hpa": data.get("main", {}).get("pressure"),
            "visibility_m": data.get("visibility"),
            "source": "openweathermap",
            "quality_flag": "normal",
        }
        self._cache.set(cache_key, result)
        return result

    async def get_rainfall_series(
        self, lat: float, lon: float, hours: int = 24
    ) -> list[dict[str, Any]]:
        cache_key = f"rainfall:{lat:.4f},{lon:.4f},{hours}"
        cached = self._cache.get(cache_key, _CACHE_TTL_CURRENT)
        if cached is not None:
            return cached

        # OpenWeatherMap "onecall" endpoint provides hourly data.
        data = await self._fetch(
            "/onecall",
            {"lat": lat, "lon": lon, "units": "metric", "exclude": "minutely,daily,alerts"},
        )
        if data is None:
            return []

        hourly = data.get("hourly", [])[:hours]
        now = datetime.now(TZ_SHANGHAI)
        series: list[dict[str, Any]] = []
        for i, entry in enumerate(hourly):
            ts = now - timedelta(hours=hours - 1 - i)
            series.append(
                {
                    "station_id": "openweathermap",
                    "observed_at": ts.isoformat(),
                    "rainfall_mm": entry.get("rain", {}).get("1h", 0.0),
                    "source": "openweathermap",
                }
            )

        self._cache.set(cache_key, series)
        return series

    async def get_forecast(
        self, lat: float, lon: float, hours: int = 48
    ) -> list[dict[str, Any]]:
        cache_key = f"forecast:{lat:.4f},{lon:.4f},{hours}"
        cached = self._cache.get(cache_key, _CACHE_TTL_FORECAST)
        if cached is not None:
            return cached

        data = await self._fetch(
            "/onecall",
            {"lat": lat, "lon": lon, "units": "metric", "exclude": "minutely,current,alerts"},
        )
        if data is None:
            return []

        # hourly forecast is under "hourly" (first 48h)
        hourly = data.get("hourly", [])[:hours]
        now = datetime.now(TZ_SHANGHAI)
        forecasts: list[dict[str, Any]] = []
        for i, entry in enumerate(hourly):
            ts = now + timedelta(hours=i + 1)
            forecasts.append(
                {
                    "forecast_at": ts.isoformat(),
                    "rainfall_mm": entry.get("rain", {}).get("1h", 0.0),
                    "temperature_c": entry.get("temp"),
                    "source": "openweathermap",
                }
            )

        self._cache.set(cache_key, forecasts)
        return forecasts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_rain(data: dict[str, Any], hours: int) -> float:
        """Pull rainfall from OpenWeatherMap current-weather response."""
        rain = data.get("rain", {})
        if hours <= 1:
            return rain.get("1h", 0.0)
        return rain.get("1h", 0.0) * hours  # rough estimate when 24h not present

    async def _fetch(self, path: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """GET from the weather API. Returns parsed JSON or None on any failure."""
        params["appid"] = self._api_key
        url = f"{self._base_url}{path}"
        logger.info("weather_api_call url=%s params=%s", url, {k: v for k, v in params.items() if k != "appid"})

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)

            if resp.status_code == 401:
                logger.warning("weather_api_auth_failed status=401 url=%s", url)
                return None
            if resp.status_code == 429:
                logger.warning("weather_api_rate_limited status=429 url=%s", url)
                return None
            if resp.status_code >= 500:
                logger.warning("weather_api_server_error status=%d url=%s", resp.status_code, url)
                return None
            if resp.status_code >= 400:
                logger.warning("weather_api_client_error status=%d url=%s", resp.status_code, url)
                return None

            return resp.json()

        except httpx.TimeoutException:
            logger.warning("weather_api_timeout url=%s", url)
            return None
        except httpx.HTTPError as exc:
            logger.warning("weather_api_http_error url=%s error=%s", url, exc)
            return None
        except Exception:
            logger.exception("weather_api_unexpected_error url=%s", url)
            return None


provider = RealWeatherProvider()
