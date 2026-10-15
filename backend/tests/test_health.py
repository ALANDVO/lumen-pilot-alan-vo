import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "lumen-pilot"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"status", "service", "version"}
    assert isinstance(data["status"], str)
    assert isinstance(data["service"], str)
    assert isinstance(data["version"], str)