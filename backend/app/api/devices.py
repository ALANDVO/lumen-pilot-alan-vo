from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.device_service import DeviceService
from app.models import DeviceStatus

router = APIRouter()


class DeviceInfo(BaseModel):
    udid: str
    name: str
    os_version: str
    status: str


class DeviceListResponse(BaseModel):
    devices: List[DeviceInfo]


class DeviceSyncResponse(BaseModel):
    synced: int
    devices: List[DeviceInfo]


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(db: AsyncSession = Depends(get_db)) -> DeviceListResponse:
    service = DeviceService(db)
    devices = await service.list_devices()
    return DeviceListResponse(
        devices=[
            DeviceInfo(udid=d.udid, name=d.name, os_version=d.os_version, status=d.status.value)
            for d in devices
        ]
    )


@router.post("/devices/sync", response_model=DeviceSyncResponse)
async def sync_devices(db: AsyncSession = Depends(get_db)) -> DeviceSyncResponse:
    service = DeviceService(db)
    synced = await service.sync_devices()
    return DeviceSyncResponse(
        synced=len(synced),
        devices=[
            DeviceInfo(udid=d.udid, name=d.name, os_version=d.os_version, status=d.status.value)
            for d in synced
        ]
    )


@router.get("/devices/{udid}", response_model=DeviceInfo)
async def get_device(udid: str, db: AsyncSession = Depends(get_db)) -> DeviceInfo:
    service = DeviceService(db)
    device = await service.get_device_by_udid(udid)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceInfo(udid=device.udid, name=device.name, os_version=device.os_version, status=device.status.value)