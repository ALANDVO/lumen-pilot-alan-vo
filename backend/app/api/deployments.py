from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.deployment_service import DeploymentService
from app.models import DeploymentStatus

router = APIRouter()


class DeploymentRequest(BaseModel):
    build_id: UUID
    device_id: UUID


class DeploymentResponse(BaseModel):
    id: UUID
    build_id: UUID
    device_id: UUID
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    log: str = ""


class DeploymentListResponse(BaseModel):
    deployments: List[DeploymentResponse]


@router.post("/deployments", response_model=DeploymentResponse, status_code=201)
async def create_deployment(request: DeploymentRequest, db: AsyncSession = Depends(get_db)) -> DeploymentResponse:
    service = DeploymentService(db)
    deployment = await service.create_deployment(request.build_id, request.device_id)
    return DeploymentResponse(
        id=deployment.id,
        build_id=deployment.build_id,
        device_id=deployment.device_id,
        status=deployment.status.value,
        created_at=deployment.created_at,
        completed_at=deployment.completed_at,
        log=deployment.log,
    )


@router.get("/deployments", response_model=DeploymentListResponse)
async def list_deployments(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)) -> DeploymentListResponse:
    service = DeploymentService(db)
    deployments = await service.list_deployments(limit=limit, offset=offset)
    return DeploymentListResponse(
        deployments=[
            DeploymentResponse(
                id=d.id,
                build_id=d.build_id,
                device_id=d.device_id,
                status=d.status.value,
                created_at=d.created_at,
                completed_at=d.completed_at,
                log=d.log,
            )
            for d in deployments
        ]
    )


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: UUID, db: AsyncSession = Depends(get_db)) -> DeploymentResponse:
    service = DeploymentService(db)
    deployment = await service.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return DeploymentResponse(
        id=deployment.id,
        build_id=deployment.build_id,
        device_id=deployment.device_id,
        status=deployment.status.value,
        created_at=deployment.created_at,
        completed_at=deployment.completed_at,
        log=deployment.log,
    )


@router.post("/deployments/{deployment_id}/execute", response_model=DeploymentResponse)
async def execute_deployment(deployment_id: UUID, db: AsyncSession = Depends(get_db)) -> DeploymentResponse:
    service = DeploymentService(db)
    deployment = await service.execute_deployment(deployment_id)
    return DeploymentResponse(
        id=deployment.id,
        build_id=deployment.build_id,
        device_id=deployment.device_id,
        status=deployment.status.value,
        created_at=deployment.created_at,
        completed_at=deployment.completed_at,
        log=deployment.log,
    )