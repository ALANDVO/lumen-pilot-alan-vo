import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Build, BuildStatus


class BuildService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_build(self, project_path: str, configuration: str, target: str, device_id: UUID | None = None) -> Build:
        build = Build(
            project_path=project_path,
            configuration=configuration,
            target=target,
            status=BuildStatus.PENDING,
            device_id=device_id,
        )
        self.db.add(build)
        await self.db.commit()
        await self.db.refresh(build)
        return build

    async def get_build(self, build_id: UUID) -> Optional[Build]:
        result = await self.db.execute(select(Build).where(Build.id == build_id))
        return result.scalar_one_or_none()

    async def list_builds(self, limit: int = 50, offset: int = 0) -> List[Build]:
        result = await self.db.execute(
            select(Build).order_by(Build.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update_build_status(self, build_id: UUID, status: BuildStatus, log: str = "") -> Optional[Build]:
        build = await self.get_build(build_id)
        if build:
            build.status = status
            if log:
                build.log = log
            if status in (BuildStatus.SUCCESS, BuildStatus.ERROR, BuildStatus.CANCELLED):
                build.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(build)
        return build

    async def append_build_log(self, build_id: UUID, log_line: str) -> Optional[Build]:
        build = await self.get_build(build_id)
        if build:
            build.log += log_line + "\n"
            await self.db.commit()
            await self.db.refresh(build)
        return build

    def validate_project_path(self, project_path: str) -> bool:
        path = Path(project_path)
        return (path / "Package.swift").exists()

    def get_swift_build_command(self, project_path: str, configuration: str, target: str) -> List[str]:
        cmd = ["swift", "build", "--package-path", project_path]
        if configuration == "release":
            cmd.append("-c")
            cmd.append("release")
        if target == "ios":
            cmd.extend(["--triple", "arm64-apple-ios"])
        elif target == "ios-simulator":
            cmd.extend(["--triple", "arm64-apple-ios-simulator"])
        return cmd

    async def execute_build(self, build_id: UUID) -> Build:
        build = await self.get_build(build_id)
        if not build:
            raise ValueError(f"Build {build_id} not found")

        if not self.validate_project_path(build.project_path):
            await self.update_build_status(build_id, BuildStatus.ERROR, "Invalid project path: Package.swift not found")
            return await self.get_build(build_id)

        await self.update_build_status(build_id, BuildStatus.RUNNING, "Starting build...\n")

        cmd = self.get_swift_build_command(build.project_path, build.configuration, build.target)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout_lines = []
            async for line in process.stdout:
                decoded = line.decode("utf-8", errors="replace")
                stdout_lines.append(decoded)
                await self.append_build_log(build_id, decoded.rstrip())

            await process.wait()

            if process.returncode == 0:
                await self.update_build_status(build_id, BuildStatus.SUCCESS, "".join(stdout_lines))
            else:
                await self.update_build_status(build_id, BuildStatus.ERROR, "".join(stdout_lines))

        except Exception as e:
            await self.update_build_status(build_id, BuildStatus.ERROR, f"Build execution failed: {str(e)}")

        return await self.get_build(build_id)