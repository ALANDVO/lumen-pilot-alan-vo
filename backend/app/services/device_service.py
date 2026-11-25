import subprocess
import json
import shutil
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Device, DeviceStatus


class DeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _usbmuxd_available() -> bool:
        """Check if usbmuxd tools (idevice_id, ideviceinfo) are available."""
        return (
            shutil.which("idevice_id") is not None
            and shutil.which("ideviceinfo") is not None
        )

    async def list_devices(self) -> List[Device]:
        result = await self.db.execute(select(Device).order_by(Device.created_at.desc()))
        return list(result.scalars().all())

    async def get_device(self, device_id: UUID) -> Optional[Device]:
        result = await self.db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    async def get_device_by_udid(self, udid: str) -> Optional[Device]:
        result = await self.db.execute(select(Device).where(Device.udid == udid))
        return result.scalar_one_or_none()

    async def upsert_device(self, udid: str, name: str, os_version: str, status: DeviceStatus = DeviceStatus.CONNECTED) -> Device:
        existing = await self.get_device_by_udid(udid)
        if existing:
            existing.name = name
            existing.os_version = os_version
            existing.status = status
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        device = Device(udid=udid, name=name, os_version=os_version, status=status)
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def update_device_status(self, udid: str, status: DeviceStatus) -> Optional[Device]:
        device = await self.get_device_by_udid(udid)
        if device:
            device.status = status
            await self.db.commit()
            await self.db.refresh(device)
        return device

    async def scan_usb_devices(self) -> List[Dict[str, str]]:
        """Scan for connected iOS devices via usbmuxd.

        Returns empty list if usbmuxd tools are not available,
        rather than failing silently.
        """
        if not self._usbmuxd_available():
            return []
        try:
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []
            udids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            devices = []
            for udid in udids:
                info_result = subprocess.run(
                    ["ideviceinfo", "-u", udid, "-k", "DeviceName", "-k", "ProductVersion"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                name = udid
                os_version = "unknown"
                if info_result.returncode == 0:
                    for line in info_result.stdout.splitlines():
                        if line.startswith("DeviceName:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("ProductVersion:"):
                            os_version = line.split(":", 1)[1].strip()
                devices.append({"udid": udid, "name": name, "os_version": os_version})
            return devices
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return []

    async def sync_devices(self) -> List[Device]:
        """Sync local database with actual connected devices.

        Devices present in the scan are upserted as CONNECTED. Devices that
        were previously marked CONNECTED but are no longer seen over usbmuxd
        are reconciled to DISCONNECTED so the device list reflects reality.
        """
        usb_devices = await self.scan_usb_devices()
        seen_udids = {d["udid"] for d in usb_devices}
        synced = []
        for usb_device in usb_devices:
            device = await self.upsert_device(
                udid=usb_device["udid"],
                name=usb_device["name"],
                os_version=usb_device["os_version"],
                status=DeviceStatus.CONNECTED,
            )
            synced.append(device)

        # Reconcile: any device still marked CONNECTED but absent from the
        # latest scan is now considered DISCONNECTED.
        result = await self.db.execute(
            select(Device).where(Device.status == DeviceStatus.CONNECTED)
        )
        for stale in result.scalars().all():
            if stale.udid not in seen_udids:
                stale.status = DeviceStatus.DISCONNECTED
        await self.db.commit()
        return synced
