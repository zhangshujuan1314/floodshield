from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/layers")
async def list_map_layers(request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    layers = [
        {
            "id": "layer-risk-zones",
            "name": "Flood Risk Zones",
            "type": "polygon",
            "source": "risk_engine",
            "description": "Current flood risk zones by area",
            "style": {
                "fillColors": {
                    "normal": "#4CAF50",
                    "attention": "#FF9800",
                    "high": "#F44336",
                    "critical": "#9C27B0",
                },
                "opacity": 0.4,
            },
            "updatedAt": now.isoformat(),
        },
        {
            "id": "layer-active-alerts",
            "name": "Active Alerts",
            "type": "polygon",
            "source": "official_alerts",
            "description": "Boundaries of currently active official alerts",
            "style": {"fillColor": "#FF5722", "opacity": 0.3, "strokeColor": "#BF360C"},
            "updatedAt": now.isoformat(),
        },
        {
            "id": "layer-water-levels",
            "name": "Water Level Stations",
            "type": "point",
            "source": "observations",
            "description": "Real-time water level readings at monitoring stations",
            "style": {"markerType": "circle", "sizeByValue": True, "colorScale": "blue"},
            "updatedAt": (now - timedelta(minutes=5)).isoformat(),
        },
        {
            "id": "layer-road-events",
            "name": "Road Closures & Events",
            "type": "line",
            "source": "road_events",
            "description": "Active road closures, diversions, and flood-affected roads",
            "style": {"strokeColor": "#FF0000", "strokeWidth": 3, "dashPattern": [10, 5]},
            "updatedAt": now.isoformat(),
        },
        {
            "id": "layer-shelters",
            "name": "Emergency Shelters",
            "type": "point",
            "source": "shelters",
            "description": "Designated emergency shelter locations with capacity info",
            "style": {"markerType": "icon", "icon": "shelter", "color": "#2196F3"},
            "updatedAt": now.isoformat(),
        },
        {
            "id": "layer-rainfall-heatmap",
            "name": "Rainfall Heatmap",
            "type": "raster",
            "source": "weather",
            "description": "Rainfall intensity heatmap from weather stations and radar",
            "style": {"opacity": 0.6, "colorScale": "precipitation"},
            "updatedAt": (now - timedelta(minutes=10)).isoformat(),
        },
    ]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": layers,
    }
