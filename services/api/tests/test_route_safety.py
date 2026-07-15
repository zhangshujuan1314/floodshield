"""Route safety tests.

Critical safety requirements:
- Official road closures must be HARD BLOCKS
- Unknown-risk segments must NOT be labeled safe
- No route available → clear failure message
- Routes must include evidence and expiration
"""

from __future__ import annotations

import pytest

from app.providers.mock_map import MockMapProvider


@pytest.fixture
def provider():
    return MockMapProvider()


class TestRouteScenarios:
    """Mock map provider must support all three scenarios."""

    async def test_normal_route(self, provider):
        """Normal route between two nearby points."""
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 31.24],
        )
        assert result["is_viable"] is True
        assert result["route_geojson"] is not None
        assert result["distance_m"] > 0
        assert result["duration_s"] > 0

    async def test_route_has_safety_fields(self, provider):
        """Route response must include safety metadata."""
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 31.24],
        )
        assert "safety_score" in result
        assert "warnings" in result
        assert "computed_at" in result
        assert "provider" in result

    async def test_route_has_geometry(self, provider):
        """Route must include geometry for display."""
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 31.24],
        )
        assert result["route_geojson"]["type"] == "Feature"
        assert result["route_geojson"]["geometry"]["type"] == "LineString"
        assert len(result["route_geojson"]["geometry"]["coordinates"]) >= 2

    async def test_route_with_hazards(self, provider):
        """Route through hazard area must show warnings."""
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 30.5],  # south → with_hazards scenario
        )
        assert result["is_viable"] is True
        assert len(result["warnings"]) > 0
        assert result["safety_score"] < 0.9  # Lower safety due to hazards

    async def test_no_route_scenario(self, provider):
        """When no viable route, must return clear failure."""
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[123.0, 31.24],  # far east → no_route scenario
        )
        assert result["is_viable"] is False
        assert result["route_geojson"] is None
        assert len(result["warnings"]) > 0
        assert "blocked" in result["warnings"][0].lower() or "no viable" in result["warnings"][0].lower()


class TestGeocode:
    async def test_geocode_returns_results(self, provider):
        result = await provider.geocode("南京市江宁区")
        assert "results" in result
        assert len(result["results"]) >= 1

    async def test_geocode_result_has_location(self, provider):
        result = await provider.geocode("南京市江宁区")
        place = result["results"][0]
        assert "name" in place
        assert "lat" in place
        assert "lon" in place
        assert "confidence" in place


class TestScenarioSelection:
    """Scenario selection must be deterministic based on coordinates."""

    async def test_normal_for_nearby_points(self, provider):
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 31.24],
        )
        assert result["is_viable"] is True
        assert result["safety_score"] >= 0.9

    async def test_hazards_for_south_destination(self, provider):
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[121.48, 30.5],
        )
        assert result["is_viable"] is True
        assert result["safety_score"] < 0.9

    async def test_no_route_for_far_east(self, provider):
        result = await provider.compute_route(
            origin=[121.47, 31.23],
            destination=[123.0, 31.24],
        )
        assert result["is_viable"] is False
