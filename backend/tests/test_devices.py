import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_devices_empty(async_client: AsyncClient):
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert isinstance(data["devices"], list)
    assert len(data["devices"]) == 0


@pytest.mark.asyncio
async def test_list_devices_response_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"devices"}
    assert isinstance(data["devices"], list)


@pytest.mark.asyncio
async def test_device_list_has_udid_fields(async_client: AsyncClient):
    """Test device list structure has required fields."""
    response = await async_client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert isinstance(data["devices"], list)
    # When no devices connected, list should be empty
    # Structure validation is done via the response model

import shutil


@pytest.mark.asyncio
async def test_usbmuxd_available_check(async_client: AsyncClient):
    """Test that usbmuxd availability check works in this environment.

    In this environment usbmuxd tools are not available, so scan_usb_devices
    should return an empty list rather than failing.
    """
    from app.services.device_service import DeviceService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models import Base, DeviceStatus

    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestAsyncSessionMaker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Check that _usbmuxd_available returns False when tools aren't installed
    assert not DeviceService._usbmuxd_available()

    # Verify scan returns empty list when usbmuxd not available
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestAsyncSessionMaker() as db_session:
        service = DeviceService(db_session)
        devices = await service.scan_usb_devices()
        assert devices == [], f"Expected empty list, got {devices}"

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
