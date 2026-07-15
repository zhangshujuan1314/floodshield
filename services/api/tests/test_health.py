from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "requestId" in body
    assert body["data"]["status"] == "healthy"
    assert body["data"]["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_v1_health(client: AsyncClient):
    resp = await client.get("/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "requestId" in body
    assert body["data"]["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_request_id_propagated(client: AsyncClient):
    resp = await client.get("/health", headers={"X-Request-ID": "test-req-123"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == "test-req-123"
    body = resp.json()
    assert body["requestId"] == "test-req-123"
