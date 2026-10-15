from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.build_service import BuildService
from app.models import BuildStatus

router = APIRouter()


class BuildRequest(BaseModel):
    project_path: str
    configuration: str = "debug"
    target: str = "ios"
    device_id: Optional[UUID] = None


class BuildResponse(BaseModel):
    id: UUID
    project_path: str
    configuration: str
    target: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    log: str = ""


class BuildListResponse(BaseModel):
    builds: List[BuildResponse]


class BuildExecuteResponse(BaseModel):
    build: BuildResponse
    advisory: Optional[dict] = None


@router.post("/builds", response_model=BuildResponse, status_code=201)
async def create_build(request: BuildRequest, db: AsyncSession = Depends(get_db)) -> BuildResponse:
    service = BuildService(db)
    build = await service.create_build(
        project_path=request.project_path,
        configuration=request.configuration,
        target=request.target,
        device_id=request.device_id,
    )
    return BuildResponse(
        id=build.id,
        project_path=build.project_path,
        configuration=build.configuration,
        target=build.target,
        status=build.status.value,
        created_at=build.created_at,
        completed_at=build.completed_at,
        log=build.log,
    )


@router.get("/builds", response_model=BuildListResponse)
async def list_builds(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)) -> BuildListResponse:
    service = BuildService(db)
    builds = await service.list_builds(limit=limit, offset=offset)
    return BuildListResponse(
        builds=[
            BuildResponse(
                id=b.id,
                project_path=b.project_path,
                configuration=b.configuration,
                target=b.target,
                status=b.status.value,
                created_at=b.created_at,
                completed_at=b.completed_at,
                log=b.log,
            )
            for b in builds
        ]
    )


@router.get("/builds/{build_id}", response_model=BuildResponse)
async def get_build(build_id: UUID, db: AsyncSession = Depends(get_db)) -> BuildResponse:
    service = BuildService(db)
    build = await service.get_build(build_id)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return BuildResponse(
        id=build.id,
        project_path=build.project_path,
        configuration=build.configuration,
        target=build.target,
        status=build.status.value,
        created_at=build.created_at,
        completed_at=build.completed_at,
        log=build.log,
    )


@router.post("/builds/{build_id}/execute", response_model=BuildExecuteResponse)
async def execute_build(build_id: UUID, db: AsyncSession = Depends(get_db)) -> BuildExecuteResponse:
    service = BuildService(db)
    build = await service.execute_build(build_id)

    advisory = None
    if build.status == BuildStatus.ERROR and build.log:
        from app.services.llm_advisory import get_build_failure_advisory
        advisory_response = await get_build_failure_advisory(build.log, f"Build failed with status {build.status.value}")
        if advisory_response:
            advisory = {
                "provider": advisory_response.provider,
                "model": advisory_response.model,
                "summary": advisory_response.summary,
                "suggestions": advisory_response.suggestions,
                "confidence": advisory_response.confidence,
                "advisory": True,
            }

    return BuildExecuteResponse(
        build=BuildResponse(
            id=build.id,
            project_path=build.project_path,
            configuration=build.configuration,
            target=build.target,
            status=build.status.value,
            created_at=build.created_at,
            completed_at=build.completed_at,
            log=build.log,
        ),
        advisory=advisory,
    )