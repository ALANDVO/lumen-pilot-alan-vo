import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, TypeDecorator, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.core.database import Base
import enum


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36) for other databases.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return uuid.UUID(value)


class DeviceStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNAUTHORIZED = "unauthorized"
    BOOTING = "booting"
    UNKNOWN = "unknown"


class BuildStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    INSTALLING = "installing"
    LAUNCHING = "launching"
    SUCCESS = "success"
    ERROR = "error"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    udid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    os_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(SQLEnum(DeviceStatus), default=DeviceStatus.UNKNOWN, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    builds: Mapped[list["Build"]] = relationship(back_populates="device")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="device")


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    configuration: Mapped[str] = mapped_column(String(32), default="debug", nullable=False)
    target: Mapped[str] = mapped_column(String(32), default="ios", nullable=False)
    status: Mapped[BuildStatus] = mapped_column(SQLEnum(BuildStatus), default=BuildStatus.PENDING, nullable=False)
    log: Mapped[str] = mapped_column(Text, default="", nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("devices.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["Device | None"] = relationship(back_populates="builds")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="build")


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    build_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("builds.id"), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("devices.id"), nullable=False)
    status: Mapped[DeploymentStatus] = mapped_column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False)
    log: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    build: Mapped["Build"] = relationship(back_populates="deployments")
    device: Mapped["Device"] = relationship(back_populates="deployments")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))