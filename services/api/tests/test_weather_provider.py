"""Tests for mock and real weather providers."""

from __future__ import annotations

import pytest
import httpx

from app.providers.mock_weather import MockWeatherProvider


# ---------------------------------------------------------------------------
# Mock provider tests
# ---------------------------------------------------------------------------


class TestMockWeatherProvider:
    """Mock provider should return well-formed dicts every time."""

    @pytest.fixture()
    def provider(self):
        return MockWeatherProvider()

    @pytest.mark.asyncio
    async def test_get_current_returns_required_keys(self, provider):
        data = await provider.get_current(31.23, 121.47)
        for key in ("temperature_c", "humidity_pct", "rainfall_mm", "wind_speed_ms"):
            assert key in data, f"missing key: {key}"
        assert isinstance(data["temperature_c"], float)
        assert isinstance(data["humidity_pct"], float)

    @pytest.mark.asyncio
    async def test_get_rainfall_series_length(self, provider):
        series = await provider.get_rainfall_series(31.23, 121.47, hours=12)
        assert len(series) == 12
        for entry in series:
            assert "rainfall_mm" in entry
            assert "observed_at" in entry

    @pytest.mark.asyncio
    async def test_get_forecast_length(self, provider):
        forecasts = await provider.get_forecast(31.23, 121.47, hours=6)
        assert len(forecasts) == 6
        for entry in forecasts:
            assert "rainfall_mm" in entry
            assert "temperature_c" in entry
            assert "forecast_at" in entry


# ---------------------------------------------------------------------------
# Real provider tests (HTTP mocked)
# ---------------------------------------------------------------------------


OWM_CURRENT_RESPONSE = {
    "name": "Shanghai",
    "main": {"temp": 29.5, "humidity": 80, "pressure": 1010},
    "wind": {"speed": 4.1, "deg": 200},
    "rain": {"1h": 5.2},
    "visibility": 10000,
}

OWM_ONECALL_RESPONSE = {
    "hourly": [
        {
            "temp": 28.0 + i,
            "rain": {"1h": 1.0 + i * 0.3},
        }
        for i in range(48)
    ]
}


def _mock_handler(request: httpx.Request) -> httpx.Response:
    """Route requests to the right fixture based on URL path."""
    url = str(request.url)
    if "/onecall" in url:
        return httpx.Response(200, json=OWM_ONECALL_RESPONSE)
    if "/weather" in url:
        return httpx.Response(200, json=OWM_CURRENT_RESPONSE)
    return httpx.Response(404, json={"message": "not found"})


class TestRealWeatherProvider:
    """Real provider with a mocked HTTP transport."""

    @pytest.fixture(autouse=True)
    def _patch_settings(self, monkeypatch):
        monkeypatch.setattr(
            "app.core.config.settings.WEATHER_API_KEY", "test-key-12345"
        )
        monkeypatch.setattr(
            "app.core.config.settings.WEATHER_API_URL",
            "https://api.openweathermap.org/data/2.5",
        )
        monkeypatch.setattr(
            "app.core.config.settings.WEATHER_PROVIDER", "real"
        )

    @pytest.fixture()
    def provider(self):
        from app.providers.real_weather import RealWeatherProvider
        return RealWeatherProvider()

    @pytest.mark.asyncio
    async def test_get_current_success(self, provider, monkeypatch):
        """Verify parsed fields from a mocked OpenWeatherMap response."""

        async def _fake_fetch(path, params):
            return OWM_CURRENT_RESPONSE

        monkeypatch.setattr(provider, "_fetch", _fake_fetch)
        data = await provider.get_current(31.23, 121.47)
        assert data is not None
        assert data["temperature_c"] == 29.5
        assert data["humidity_pct"] == 80
        assert data["rainfall_mm"] == 5.2
        assert data["source"] == "openweathermap"

    @pytest.mark.asyncio
    async def test_get_current_returns_none_on_api_error(self, provider, monkeypatch):
        """API returning None should propagate as None, not crash."""

        async def _fail_fetch(path, params):
            return None

        monkeypatch.setattr(provider, "_fetch", _fail_fetch)
        data = await provider.get_current(31.23, 121.47)
        assert data is None

    @pytest.mark.asyncio
    async def test_get_rainfall_series(self, provider, monkeypatch):
        async def _fake_fetch(path, params):
            return OWM_ONECALL_RESPONSE

        monkeypatch.setattr(provider, "_fetch", _fake_fetch)
        series = await provider.get_rainfall_series(31.23, 121.47, hours=24)
        assert len(series) == 24
        for entry in series:
            assert "rainfall_mm" in entry
            assert "observed_at" in entry

    @pytest.mark.asyncio
    async def test_get_forecast(self, provider, monkeypatch):
        async def _fake_fetch(path, params):
            return OWM_ONECALL_RESPONSE

        monkeypatch.setattr(provider, "_fetch", _fake_fetch)
        forecasts = await provider.get_forecast(31.23, 121.47, hours=12)
        assert len(forecasts) == 12
        for entry in forecasts:
            assert "forecast_at" in entry
            assert "temperature_c" in entry

    @pytest.mark.asyncio
    async def test_get_rainfall_series_returns_empty_on_error(self, provider, monkeypatch):
        async def _fail_fetch(path, params):
            return None

        monkeypatch.setattr(provider, "_fetch", _fail_fetch)
        series = await provider.get_rainfall_series(31.23, 121.47, hours=24)
        assert series == []

    @pytest.mark.asyncio
    async def test_get_forecast_returns_empty_on_error(self, provider, monkeypatch):
        async def _fail_fetch(path, params):
            return None

        monkeypatch.setattr(provider, "_fetch", _fail_fetch)
        forecasts = await provider.get_forecast(31.23, 121.47, hours=12)
        assert forecasts == []

    @pytest.mark.asyncio
    async def test_cache_returns_same_data(self, provider, monkeypatch):
        """Second call should hit cache, not re-fetch."""
        call_count = 0

        async def _counting_fetch(path, params):
            nonlocal call_count
            call_count += 1
            return OWM_CURRENT_RESPONSE

        monkeypatch.setattr(provider, "_fetch", _counting_fetch)
        d1 = await provider.get_current(31.23, 121.47)
        d2 = await provider.get_current(31.23, 121.47)
        assert d1 is d2
        assert call_count == 1


# ---------------------------------------------------------------------------
# Fetch-level error handling tests
# ---------------------------------------------------------------------------


class TestRealWeatherFetchErrors:
    """Test the _fetch method directly against real HTTP errors."""

    @pytest.fixture(autouse=True)
    def _patch_settings(self, monkeypatch):
        monkeypatch.setattr(
            "app.core.config.settings.WEATHER_API_KEY", "test-key-12345"
        )
        monkeypatch.setattr(
            "app.core.config.settings.WEATHER_API_URL",
            "https://api.openweathermap.org/data/2.5",
        )

    @pytest.fixture()
    def provider(self):
        from app.providers.real_weather import RealWeatherProvider
        return RealWeatherProvider()

    @pytest.mark.asyncio
    async def test_fetch_timeout_returns_none(self, provider, monkeypatch):
        async def _timeout_get(url, params=None):
            raise httpx.TimeoutException("timed out")

        class FakeClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                pass
            get = _timeout_get

        monkeypatch.setattr("httpx.AsyncClient", FakeClient)
        result = await provider._fetch("/weather", {"lat": 1.0, "lon": 1.0})
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_401_returns_none(self, provider, monkeypatch):
        async def _unauthorized_get(url, params=None):
            return httpx.Response(401, json={"message": "Invalid API key"})

        class FakeClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                pass
            get = _unauthorized_get

        monkeypatch.setattr("httpx.AsyncClient", FakeClient)
        result = await provider._fetch("/weather", {"lat": 1.0, "lon": 1.0})
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_500_returns_none(self, provider, monkeypatch):
        async def _server_error_get(url, params=None):
            return httpx.Response(500, json={"message": "Internal Server Error"})

        class FakeClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                pass
            get = _server_error_get

        monkeypatch.setattr("httpx.AsyncClient", FakeClient)
        result = await provider._fetch("/weather", {"lat": 1.0, "lon": 1.0})
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_429_returns_none(self, provider, monkeypatch):
        async def _rate_limit_get(url, params=None):
            return httpx.Response(429, json={"message": "Rate limit exceeded"})

        class FakeClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                pass
            get = _rate_limit_get

        monkeypatch.setattr("httpx.AsyncClient", FakeClient)
        result = await provider._fetch("/weather", {"lat": 1.0, "lon": 1.0})
        assert result is None


# ---------------------------------------------------------------------------
# Factory / fallback tests
# ---------------------------------------------------------------------------


class TestWeatherProviderFactory:
    """get_weather_provider should pick the right backend."""

    @pytest.mark.asyncio
    async def test_factory_returns_mock_when_configured(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.WEATHER_PROVIDER", "mock")
        monkeypatch.setattr("app.core.config.settings.WEATHER_API_KEY", "")
        # Clear cached registry entries
        from app.providers import _REGISTRY
        _REGISTRY.pop("weather", None)

        from app.providers import get_weather_provider
        provider = get_weather_provider()
        assert isinstance(provider, MockWeatherProvider)

    @pytest.mark.asyncio
    async def test_factory_falls_back_to_mock_when_key_missing(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.WEATHER_PROVIDER", "real")
        monkeypatch.setattr("app.core.config.settings.WEATHER_API_KEY", "")
        from app.providers import _REGISTRY
        _REGISTRY.pop("weather", None)

        from app.providers import get_weather_provider
        provider = get_weather_provider()
        assert isinstance(provider, MockWeatherProvider)

    @pytest.mark.asyncio
    async def test_factory_returns_real_when_key_present(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.WEATHER_PROVIDER", "real")
        monkeypatch.setattr("app.core.config.settings.WEATHER_API_KEY", "valid-key")
        from app.providers import _REGISTRY
        _REGISTRY.pop("weather", None)

        from app.providers import get_weather_provider
        from app.providers.real_weather import RealWeatherProvider
        provider = get_weather_provider()
        assert isinstance(provider, RealWeatherProvider)
