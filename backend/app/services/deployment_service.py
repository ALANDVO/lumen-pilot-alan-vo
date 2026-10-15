import asyncio
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Deployment, DeploymentStatus, Build, Device


class DeploymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deployment(self, build_id: UUID, device_id: UUID) -> Deployment:
        deployment = Deployment(
            build_id=build_id,
            device_id=device_id,
            status=DeploymentStatus.PENDING,
        )
        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)
        return deployment

    async def get_deployment(self, deployment_id: UUID) -> Optional[Deployment]:
        result = await self.db.execute(select(Deployment).where(Deployment.id == deployment_id))
        return result.scalar_one_or_none()

    async def list_deployments(self, limit: int = 50, offset: int = 0) -> List[Deployment]:
        result = await self.db.execute(
            select(Deployment).order_by(Deployment.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update_deployment_status(self, deployment_id: UUID, status: DeploymentStatus, log: str = "") -> Optional[Deployment]:
        deployment = await self.get_deployment(deployment_id)
        if deployment:
            deployment.status = status
            if log:
                deployment.log = log
            if status in (DeploymentStatus.SUCCESS, DeploymentStatus.ERROR):
                deployment.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(deployment)
        return deployment

    async def append_deployment_log(self, deployment_id: UUID, log_line: str) -> Optional[Deployment]:
        deployment = await self.get_deployment(deployment_id)
        if deployment:
            deployment.log += log_line + "\n"
            await self.db.commit()
            await self.db.refresh(deployment)
        return deployment

    def find_app_bundle(self, build: Build) -> Optional[Path]:
        project_path = Path(build.project_path)
        build_dir = project_path / ".build"
        if not build_dir.exists():
            return None
        for app_bundle in build_dir.rglob("*.app"):
            return app_bundle
        return None

    async def execute_deployment(self, deployment_id: UUID) -> Deployment:
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        build_result = await self.db.execute(select(Build).where(Build.id == deployment.build_id))
        build = build_result.scalar_one_or_none()
        if not build:
            await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, "Associated build not found")
            return await self.get_deployment(deployment_id)

        device_result = await self.db.execute(select(Device).where(Device.id == deployment.device_id))
        device = device_result.scalar_one_or_none()
        if not device:
            await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, "Target device not found")
            return await self.get_deployment(deployment_id)

        await self.update_deployment_status(deployment_id, DeploymentStatus.INSTALLING, "Finding app bundle...\n")

        app_bundle = self.find_app_bundle(build)
        if not app_bundle:
            await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, "App bundle not found in build directory")
            return await self.get_deployment(deployment_id)

        await self.append_deployment_log(deployment_id, f"Found app bundle: {app_bundle}\n")

        await self.update_deployment_status(deployment_id, DeploymentStatus.INSTALLING, f"Installing to device {device.udid}...\n")

        try:
            install_process = await asyncio.create_subprocess_exec(
                "ideviceinstaller", "-u", device.udid, "-i", str(app_bundle),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout_lines = []
            async for line in install_process.stdout:
                decoded = line.decode("utf-8", errors="replace")
                stdout_lines.append(decoded)
                await self.append_deployment_log(deployment_id, decoded.rstrip())

            await install_process.wait()

            if install_process.returncode != 0:
                await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, "".join(stdout_lines))
                return await self.get_deployment(deployment_id)

            await self.append_deployment_log(deployment_id, "Install successful\n")
            await self.update_deployment_status(deployment_id, DeploymentStatus.LAUNCHING, "Launching app...\n")

            bundle_id = app_bundle.stem
            launch_process = await asyncio.create_subprocess_exec(
                "idevicedebug", "-u", device.udid, "run", bundle_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout_lines = []
            async for line in launch_process.stdout:
                decoded = line.decode("utf-8", errors="replace")
                stdout_lines.append(decoded)
                await self.append_deployment_log(deployment_id, decoded.rstrip())

            await launch_process.wait()

            if launch_process.returncode == 0:
                await self.update_deployment_status(deployment_id, DeploymentStatus.SUCCESS, "".join(stdout_lines))
            else:
                await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, "".join(stdout_lines))

        except FileNotFoundError:
            await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, "Required tools (ideviceinstaller, idevicedebug) not found")
        except Exception as e:
            await self.update_deployment_status(deployment_id, DeploymentStatus.ERROR, f"Deployment failed: {str(e)}")

        return await self.get_deployment(deployment_id)