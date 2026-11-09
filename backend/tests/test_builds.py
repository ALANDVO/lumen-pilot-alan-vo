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

@pytest.mark.asyncio
async def test_execute_build_no_advisory_without_llm_key(async_client: AsyncClient):
    # Create a build
    response = await async_client.post(
        "/api/v1/builds",
        json={"project_path": "/path/to/project", "configuration": "debug", "target": "ios"},
    )
    assert response.status_code == 201
    build_id = response.json()["id"]

    # Execute build (no LLM_API_KEY set, so no advisory)
    response = await async_client.post(f"/api/v1/builds/{build_id}/execute")
    assert response.status_code == 200
    data = response.json()
    assert "build" in data
    assert data["build"]["id"] == build_id
    assert data["build"]["status"] in ["completed", "error", "cancelled"]
    # Advisory should be None when no LLM_API_KEY
    assert data["advisory"] is None


@pytest.mark.asyncio
async def test_execute_build_advisory_structure(async_client: AsyncClient, db_session, monkeypatch):
    # Create a build
    response = await async_client.post(
        "/api/v1/builds",
        json={"project_path": "/path/to/project", "configuration": "debug", "target": "ios"},
    )
    assert response.status_code == 201
    build_id = response.json()["id"]

    # Mock LLM provider to return advisory
    from app.services.llm_advisory import AdvisoryResponse
    import app.services.llm_advisory as llm_advisory_module

    async def mock_get_build_failure_advisory(build_log: str, error_message: str):
        return AdvisoryResponse(
            provider="test",
            model="test-model",
            summary="Test advisory summary",
            suggestions=["Fix suggestion 1", "Fix suggestion 2"],
            confidence=0.85,
        )

    monkeypatch.setattr(llm_advisory_module, "get_build_failure_advisory", mock_get_build_failure_advisory)

    # Set LLM_API_KEY to enable advisory
    import app.core.config as config_module
    original_settings = config_module.get_settings()
    monkeypatch.setattr(original_settings, "llm_api_key", "test-key")
    monkeypatch.setattr(original_settings, "llm_provider", "openai-compatible")
    monkeypatch.setattr(original_settings, "llm_model", "test-model")
    monkeypatch.setattr(original_settings, "llm_base_url", "http://localhost:8000/v1")
    monkeypatch.setattr(original_settings, "llm_timeout", 30.0)

    # Need to manually set the build status to ERROR and add a log for advisory to trigger
    from app.models import BuildStatus
    from sqlalchemy import select
    from app.models import Build

    # Get db session and update build
    result = await db_session.execute(select(Build).where(Build.id == build_id))
    build = result.scalar_one()
    build.status = BuildStatus.ERROR
    build.log = "Build failed: missing dependency"
    await db_session.commit()

    # Execute build (should now have advisory)
    response = await async_client.post(f"/api/v1/builds/{build_id}/execute")
    assert response.status_code == 200
    data = response.json()
    assert "build" in data
    assert data["build"]["id"] == build_id
    assert data["advisory"] is not None
    assert data["advisory"]["provider"] == "test"
    assert data["advisory"]["model"] == "test-model"
    assert data["advisory"]["summary"] == "Test advisory summary"
    assert data["advisory"]["suggestions"] == ["Fix suggestion 1", "Fix suggestion 2"]
    assert data["advisory"]["confidence"] == 0.85
    assert data["advisory"]["advisory"] is True