import pytest
from httpx import AsyncClient
from uuid import UUID


@pytest.mark.asyncio
async def test_create_build(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/builds",
        json={"project_path": "/path/to/project", "configuration": "debug", "target": "ios"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert UUID(data["id"])
    assert data["project_path"] == "/path/to/project"
    assert data["configuration"] == "debug"
    assert data["target"] == "ios"
    assert data["status"] == "pending"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_build_defaults(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/builds",
        json={"project_path": "/path/to/project"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["configuration"] == "debug"
    assert data["target"] == "ios"


@pytest.mark.asyncio
async def test_list_builds_empty(async_client: AsyncClient):
    response = await async_client.get("/api/v1/builds")
    assert response.status_code == 200
    data = response.json()
    assert "builds" in data
    assert isinstance(data["builds"], list)
    assert len(data["builds"]) == 0


@pytest.mark.asyncio
async def test_get_build_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/builds/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404