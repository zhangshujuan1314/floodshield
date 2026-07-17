"""Tests for map providers — mock and real (Amap).

Tests the mock provider directly, and tests the real provider with
mocked HTTP responses so no actual API key is needed.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.mock_map import MockMapProvider


# ---------------------------------------------------------------------------
# Mock provider tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_provider():
    return MockMapProvider()


class TestMockMapProvider:
    async def test_compute_route_normal(self, mock_provider):
        result = await mock_provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 31.24],
        )
        assert result["is_viable"] is True
        assert result["route_geojson"] is not None
        assert result["distance_m"] > 0
        assert result["duration_s"] > 0
        assert result["provider"] == "mock_map"

    async def test_compute_route_with_hazards(self, mock_provider):
        result = await mock_provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 30.5],
        )
        assert result["is_viable"] is True
        assert len(result["warnings"]) > 0
        assert result["safety_score"] < 0.9

    async def test_compute_route_no_route(self, mock_provider):
        result = await mock_provider.compute_route(
            origin=[121.47, 31.23],
            destination=[123.0, 31.24],
        )
        assert result["is_viable"] is False
        assert result["route_geojson"] is None
        assert result["distance_m"] == 0

    async def test_geocode_returns_results(self, mock_provider):
        result = await mock_provider.geocode("南京市江宁区")
        assert "results" in result
        assert len(result["results"]) >= 1
        place = result["results"][0]
        assert "lat" in place
        assert "lon" in place


# ---------------------------------------------------------------------------
# Real provider tests (with mocked HTTP)
# ---------------------------------------------------------------------------

def _amap_geocode_response(address: str = "上海市浦东新区") -> dict:
    """Build a realistic Amap geocode success response."""
    return {
        "status": "1",
        "info": "OK",
        "geocodes": [
            {
                "formatted_address": address,
                "location": "121.4737,31.2304",
                "level": "兴趣点",
                "city": ["上海市"],
                "district": ["浦东新区"],
            }
        ],
    }


def _amap_reverse_geocode_response() -> dict:
    return {
        "status": "1",
        "info": "OK",
        "regeocode": {
            "formatted_address": "上海市浦东新区陆家嘴环路1000号",
        },
    }


def _amap_walking_route_response() -> dict:
    return {
        "status": "1",
        "info": "OK",
        "route": {
            "paths": [
                {
                    "distance": "1200",
                    "duration": "900",
                    "steps": [
                        {
                            "polyline": "121.4700,31.2300;121.4750,31.2350;121.4800,31.2400",
                            "tmcs": [],
                        },
                        {
                            "polyline": "121.4800,31.2400;121.4850,31.2450",
                            "tmcs": [],
                        },
                    ],
                }
            ]
        },
    }


def _amap_driving_route_response() -> dict:
    return {
        "status": "1",
        "info": "OK",
        "route": {
            "paths": [
                {
                    "distance": "3500",
                    "duration": "600",
                    "steps": [
                        {
                            "polyline": "121.4700,31.2300;121.4800,31.2400",
                            "tmcs": [
                                {"status": "畅通", "lcodes": ""},
                            ],
                        },
                    ],
                }
            ]
        },
    }


def _amap_error_response(info: str = "INVALID_USER_KEY") -> dict:
    return {
        "status": "0",
        "info": info,
    }


class TestRealMapProvider:
    """Test RealMapProvider with mocked HTTP calls."""

    @pytest.fixture(autouse=True)
    def setup_provider(self):
        with patch("app.providers.real_map.settings") as mock_settings:
            mock_settings.MAP_API_KEY = "test-key-123"
            mock_settings.MAP_API_URL = "https://restapi.amap.com"
            from app.providers.real_map import RealMapProvider
            self.provider = RealMapProvider()

    # -- Geocode --

    async def test_geocode_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_geocode_response()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await self.provider.geocode("上海市浦东新区")

        assert len(result["results"]) == 1
        place = result["results"][0]
        assert place["lat"] == 31.2304
        assert place["lon"] == 121.4737
        assert place["source"] == "amap"
        assert place["name"] == "上海市浦东新区"

    async def test_geocode_api_error_returns_empty(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_error_response("INVALID_USER_KEY")

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await self.provider.geocode("bad query")

        assert result["results"] == []
        assert "error" in result

    async def test_geocode_http_exception_returns_empty(self):
        import httpx

        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("connection refused"),
        ):
            result = await self.provider.geocode("test")

        assert result["results"] == []
        assert "error" in result

    # -- Reverse Geocode --

    async def test_reverse_geocode_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_reverse_geocode_response()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            addr = await self.provider.reverse_geocode(31.2304, 121.4737)

        assert "浦东新区" in addr

    async def test_reverse_geocode_api_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_error_response("INVALID_USER_KEY")

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            addr = await self.provider.reverse_geocode(31.2304, 121.4737)

        assert "Error" in addr

    async def test_reverse_geocode_http_exception(self):
        import httpx

        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("timeout"),
        ):
            addr = await self.provider.reverse_geocode(31.2304, 121.4737)

        assert "Error" in addr

    # -- Route --

    async def test_compute_route_walking_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_walking_route_response()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await self.provider.compute_route(
                origin=[121.47, 31.23],
                destination=[121.49, 31.25],
                transport_mode="walking",
            )

        assert result["is_viable"] is True
        assert result["distance_m"] == 1200.0
        assert result["duration_s"] == 900.0
        assert result["provider"] == "amap"
        assert result["route_geojson"]["geometry"]["type"] == "LineString"
        assert len(result["route_geojson"]["geometry"]["coordinates"]) > 0

    async def test_compute_route_driving_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_driving_route_response()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await self.provider.compute_route(
                origin=[121.47, 31.23],
                destination=[121.49, 31.25],
                transport_mode="driving",
            )

        assert result["is_viable"] is True
        assert result["distance_m"] == 3500.0
        assert result["provider"] == "amap"

    async def test_compute_route_unsupported_mode(self):
        result = await self.provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.49, 31.25],
            transport_mode="helicopter",
        )
        assert result["is_viable"] is False
        assert "Unsupported" in result["warnings"][0]

    async def test_compute_route_api_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _amap_error_response("INVALID_USER_KEY")

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await self.provider.compute_route(
                origin=[121.47, 31.23],
                destination=[121.49, 31.25],
            )

        assert result["is_viable"] is False
        assert "error" in result["warnings"][0].lower()

    async def test_compute_route_http_exception(self):
        import httpx

        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("refused"),
        ):
            result = await self.provider.compute_route(
                origin=[121.47, 31.23],
                destination=[121.49, 31.25],
            )

        assert result["is_viable"] is False
        assert "failed" in result["warnings"][0].lower()

    async def test_compute_route_empty_paths(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "1", "info": "OK", "route": {"paths": []}}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await self.provider.compute_route(
                origin=[121.47, 31.23],
                destination=[121.49, 31.25],
            )

        assert result["is_viable"] is False


# ---------------------------------------------------------------------------
# Geocode cache tests
# ---------------------------------------------------------------------------

class TestGeocodeCache:
    """Verify the geocoding result cache works."""

    async def test_cache_returns_same_result(self):
        from app.providers.real_map import _cache_set, _cache_get, _GEOCODE_CACHE

        # Clear cache
        _GEOCODE_CACHE.clear()

        assert _cache_get("test query") is None
        _cache_set("test query", {"query": "test query", "results": []})
        cached = _cache_get("test query")
        assert cached is not None
        assert cached["query"] == "test query"

        _GEOCODE_CACHE.clear()

    async def test_cache_case_insensitive(self):
        from app.providers.real_map import _cache_set, _cache_get, _GEOCODE_CACHE

        _GEOCODE_CACHE.clear()
        _cache_set("Hello World", {"query": "Hello World", "results": []})
        assert _cache_get("hello world") is not None
        assert _cache_get("HELLO WORLD") is not None
        _GEOCODE_CACHE.clear()
