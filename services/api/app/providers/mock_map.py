"""Mock map provider returning fixture routes.

Three scenarios:
  1. Normal route available
  2. Route with hazard warnings
  3. No viable route found
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

TZ_SHANGHAI = timezone(timedelta(hours=8))


class MockMapProvider:
    async def compute_route(
        self,
        origin: list[float],
        destination: list[float],
        transport_mode: str = "walking",
        avoid_hazards: bool = True,
    ) -> dict[str, Any]:
        scenario = self._pick_scenario(origin, destination)

        now = datetime.now(TZ_SHANGHAI)

        if scenario == "no_route":
            return {
                "id": str(uuid.uuid4()),
                "is_viable": False,
                "route_geojson": None,
                "distance_m": 0,
                "duration_s": 0,
                "safety_score": 0.0,
                "warnings": ["No viable evacuation route found. All paths blocked by flooding."],
                "provider": "mock_map",
                "computed_at": now.isoformat(),
            }

        warnings: list[str] = []
        safety_score = 0.95

        if scenario == "with_hazards":
            warnings = [
                "Flood water on Zhongshan Rd between km 2-3",
                "Temporary road closure at intersection of Nanjing Rd and Xinhua Rd",
            ]
            safety_score = 0.55

        mid_lon = (origin[0] + destination[0]) / 2
        mid_lat = (origin[1] + destination[1]) / 2

        return {
            "id": str(uuid.uuid4()),
            "is_viable": True,
            "route_geojson": {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        origin,
                        [mid_lon - 0.005, mid_lat + 0.003],
                        [mid_lon + 0.002, mid_lat - 0.004],
                        destination,
                    ],
                },
                "properties": {"transport_mode": transport_mode},
            },
            "distance_m": round(random.uniform(800, 5000), 1),
            "duration_s": round(random.uniform(600, 3600), 1),
            "safety_score": safety_score,
            "warnings": warnings,
            "provider": "mock_map",
            "computed_at": now.isoformat(),
        }

    async def geocode(self, query: str) -> dict[str, Any]:
        return {
            "query": query,
            "results": [
                {
                    "name": query,
                    "lat": 31.2304,
                    "lon": 121.4737,
                    "confidence": 0.9,
                    "source": "mock_map",
                }
            ],
        }

    def _pick_scenario(self, origin: list[float], destination: list[float]) -> str:
        """Deterministic scenario selection based on coordinates."""
        # If destination is far east (lon > 122), no route
        if destination[0] > 122.0:
            return "no_route"
        # If destination is south (lat < 31), route with hazards
        if destination[1] < 31.0:
            return "with_hazards"
        return "normal"


provider = MockMapProvider()
