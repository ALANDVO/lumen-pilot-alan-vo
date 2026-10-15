import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_devices_empty(async_client: AsyncClient):
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert isinstance(data["devices"], list)
    assert len(data["devices"]) == 0


@pytest.mark.asyncio
async def test_list_devices_response_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"devices"}
    assert isinstance(data["devices"], list)