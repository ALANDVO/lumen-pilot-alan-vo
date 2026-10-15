import pytest
from httpx import AsyncClient
from uuid import UUID


@pytest.mark.asyncio
async def test_create_deployment(async_client: AsyncClient):
    build_id = "00000000-0000-0000-0000-000000000001"
    device_id = "00000000-0000-0000-0000-000000000002"
    response = await async_client.post(
        "/api/v1/deployments",
        json={"build_id": build_id, "device_id": device_id},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert UUID(data["id"])
    assert data["build_id"] == build_id
    assert data["device_id"] == device_id
    assert data["status"] == "pending"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_deployments_empty(async_client: AsyncClient):
    response = await async_client.get("/api/v1/deployments")
    assert response.status_code == 200
    data = response.json()
    assert "deployments" in data
    assert isinstance(data["deployments"], list)
    assert len(data["deployments"]) == 0


@pytest.mark.asyncio
async def test_get_deployment_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/deployments/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404