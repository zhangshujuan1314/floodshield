"""Real map provider using Amap (高德地图) API.

Endpoints used:
  - Geocoding:  /v3/geocode/geo
  - Reverse geocoding: /v3/geocode/regeo
  - Walking route: /v3/direction/walking
  - Driving route: /v3/direction/driving
  - Transit route: /v3/direction/transit/integrated
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TZ_SHANGHAI = timezone(timedelta(hours=8))

# Simple TTL cache for geocoding results
_GEOCODE_CACHE: dict[str, tuple[float, Any]] = {}
_GEOCODE_TTL_S = 3600  # 1 hour


def _cache_key(query: str) -> str:
    return query.strip().lower()


def _cache_get(query: str) -> Any | None:
    key = _cache_key(query)
    entry = _GEOCODE_CACHE.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.time() - ts > _GEOCODE_TTL_S:
        del _GEOCODE_CACHE[key]
        return None
    return value


def _cache_set(query: str, value: Any) -> None:
    key = _cache_key(query)
    _GEOCODE_CACHE[key] = (time.time(), value)


# Mapping from our transport modes to Amap API endpoints
_ROUTE_ENDPOINTS = {
    "walking": "/v3/direction/walking",
    "driving": "/v3/direction/driving",
    "transit": "/v3/direction/transit/integrated",
}


class RealMapProvider:
    """Amap-backed map provider for production use."""

    def __init__(self) -> None:
        self._api_key = settings.MAP_API_KEY
        self._base_url = settings.MAP_API_URL.rstrip("/")

    async def compute_route(
        self,
        origin: list[float],
        destination: list[float],
        transport_mode: str = "walking",
        avoid_hazards: bool = True,
    ) -> dict[str, Any]:
        now = datetime.now(TZ_SHANGHAI)
        endpoint = _ROUTE_ENDPOINTS.get(transport_mode)
        if endpoint is None:
            return {
                "id": str(uuid.uuid4()),
                "is_viable": False,
                "route_geojson": None,
                "distance_m": 0,
                "duration_s": 0,
                "safety_score": 0.0,
                "warnings": [f"Unsupported transport mode: {transport_mode}"],
                "provider": "amap",
                "computed_at": now.isoformat(),
            }

        # Amap expects "lon,lat" format
        origin_str = f"{origin[0]},{origin[1]}"
        dest_str = f"{destination[0]},{destination[1]}"

        params: dict[str, str] = {
            "key": self._api_key,
            "origin": origin_str,
            "destination": dest_str,
        }
        if transport_mode == "driving":
            params["strategy"] = "10"  # avoid congestion

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{self._base_url}{endpoint}", params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("Amap routing API error: %s", exc)
            return {
                "id": str(uuid.uuid4()),
                "is_viable": False,
                "route_geojson": None,
                "distance_m": 0,
                "duration_s": 0,
                "safety_score": 0.0,
                "warnings": [f"Routing API request failed: {exc}"],
                "provider": "amap",
                "computed_at": now.isoformat(),
            }
        except Exception as exc:
            logger.error("Unexpected error calling Amap routing: %s", exc)
            return {
                "id": str(uuid.uuid4()),
                "is_viable": False,
                "route_geojson": None,
                "distance_m": 0,
                "duration_s": 0,
                "safety_score": 0.0,
                "warnings": [f"Unexpected routing error: {exc}"],
                "provider": "amap",
                "computed_at": now.isoformat(),
            }

        if data.get("status") != "1":
            error_info = data.get("info", "unknown error")
            logger.warning("Amap routing returned non-success: %s", error_info)
            return {
                "id": str(uuid.uuid4()),
                "is_viable": False,
                "route_geojson": None,
                "distance_m": 0,
                "duration_s": 0,
                "safety_score": 0.0,
                "warnings": [f"Amap routing error: {error_info}"],
                "provider": "amap",
                "computed_at": now.isoformat(),
            }

        route = data.get("route", {})
        return self._parse_route(route, transport_mode, now)

    def _parse_route(
        self, route: dict[str, Any], transport_mode: str, now: datetime
    ) -> dict[str, Any]:
        """Parse Amap route response into our standard format."""
        # Walking/driving: route.paths[0]
        # Transit: route.transits[0]
        paths = route.get("paths", [])
        transits = route.get("transits", [])

        if transport_mode == "transit" and transits:
            return self._parse_transit(transits[0], now)
        if paths:
            return self._parse_path(paths[0], transport_mode, now)

        return {
            "id": str(uuid.uuid4()),
            "is_viable": False,
            "route_geojson": None,
            "distance_m": 0,
            "duration_s": 0,
            "safety_score": 0.0,
            "warnings": ["No route found in Amap response"],
            "provider": "amap",
            "computed_at": now.isoformat(),
        }

    def _parse_path(
        self, path: dict[str, Any], transport_mode: str, now: datetime
    ) -> dict[str, Any]:
        distance_m = float(path.get("distance", 0))
        duration_s = float(path.get("duration", 0))

        # Build GeoJSON LineString from steps
        coordinates: list[list[float]] = []
        for step in path.get("steps", []):
            polyline = step.get("polyline", "")
            for point_str in polyline.split(";"):
                parts = point_str.strip().split(",")
                if len(parts) == 2:
                    try:
                        lon, lat = float(parts[0]), float(parts[1])
                        coordinates.append([lon, lat])
                    except ValueError:
                        continue

        route_geojson = None
        if coordinates:
            route_geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
                "properties": {"transport_mode": transport_mode},
            }

        warnings: list[str] = []
        safety_score = 0.9
        # Check for traffic restrictions (TMC)
        for step in path.get("steps", []):
            tmcs = step.get("tmcs", [])
            for tmc in tmcs:
                status = tmc.get("status", "")
                if status in ("拥堵", "严重拥堵", "缓行"):
                    warnings.append(f"Traffic congestion detected: {tmc.get('lcodes', '')}")
                    safety_score = min(safety_score, 0.6)

        return {
            "id": str(uuid.uuid4()),
            "is_viable": True,
            "route_geojson": route_geojson,
            "distance_m": distance_m,
            "duration_s": duration_s,
            "safety_score": safety_score,
            "warnings": warnings,
            "provider": "amap",
            "computed_at": now.isoformat(),
        }

    def _parse_transit(self, transit: dict[str, Any], now: datetime) -> dict[str, Any]:
        distance_m = float(transit.get("distance", 0))
        duration_s = float(transit.get("duration", 0))

        coordinates: list[list[float]] = []
        for segment in transit.get("segments", []):
            # Walking segments
            walking = segment.get("walking", {})
            if walking:
                for step in walking.get("steps", []):
                    for point_str in step.get("polyline", "").split(";"):
                        parts = point_str.strip().split(",")
                        if len(parts) == 2:
                            try:
                                coordinates.append([float(parts[0]), float(parts[1])])
                            except ValueError:
                                continue
            # Bus segments
            bus = segment.get("bus", {})
            if bus:
                for bline in bus.get("buslines", []):
                    for point_str in bline.get("polyline", "").split(";"):
                        parts = point_str.strip().split(",")
                        if len(parts) == 2:
                            try:
                                coordinates.append([float(parts[0]), float(parts[1])])
                            except ValueError:
                                continue

        route_geojson = None
        if coordinates:
            route_geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
                "properties": {"transport_mode": "transit"},
            }

        return {
            "id": str(uuid.uuid4()),
            "is_viable": True,
            "route_geojson": route_geojson,
            "distance_m": distance_m,
            "duration_s": duration_s,
            "safety_score": 0.85,
            "warnings": [],
            "provider": "amap",
            "computed_at": now.isoformat(),
        }

    async def geocode(self, query: str) -> dict[str, Any]:
        cached = _cache_get(query)
        if cached is not None:
            return cached

        params = {
            "key": self._api_key,
            "address": query,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._base_url}/v3/geocode/geo", params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("Amap geocode API error: %s", exc)
            return {
                "query": query,
                "results": [],
                "error": f"Geocode API request failed: {exc}",
            }
        except Exception as exc:
            logger.error("Unexpected error calling Amap geocode: %s", exc)
            return {
                "query": query,
                "results": [],
                "error": f"Unexpected geocode error: {exc}",
            }

        if data.get("status") != "1":
            error_info = data.get("info", "unknown error")
            logger.warning("Amap geocode returned non-success: %s", error_info)
            return {
                "query": query,
                "results": [],
                "error": f"Amap geocode error: {error_info}",
            }

        geocodes = data.get("geocodes", [])
        results = []
        for g in geocodes:
            location = g.get("location", "")
            parts = location.split(",")
            if len(parts) != 2:
                continue
            try:
                lon, lat = float(parts[0]), float(parts[1])
            except ValueError:
                continue

            results.append({
                "name": g.get("formatted_address", query),
                "lat": lat,
                "lon": lon,
                "confidence": 1.0,  # Amap does not provide a confidence score
                "level": g.get("level", ""),
                "city": g.get("city", ""),
                "district": g.get("district", ""),
                "source": "amap",
            })

        result = {"query": query, "results": results}
        _cache_set(query, result)
        return result

    async def reverse_geocode(self, lat: float, lon: float) -> str:
        params = {
            "key": self._api_key,
            "location": f"{lon},{lat}",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._base_url}/v3/geocode/regeo", params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("Amap reverse geocode API error: %s", exc)
            return f"Error: {exc}"
        except Exception as exc:
            logger.error("Unexpected error calling Amap reverse geocode: %s", exc)
            return f"Error: {exc}"

        if data.get("status") != "1":
            return f"Error: {data.get('info', 'unknown error')}"

        regeocode = data.get("regeocode", {})
        return regeocode.get("formatted_address", "Unknown address")


provider = RealMapProvider()
