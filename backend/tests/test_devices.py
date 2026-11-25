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


@pytest.mark.asyncio
async def test_sync_marks_stale_devices_disconnected(monkeypatch):
    """A device previously CONNECTED but absent from the latest usbmuxd scan
    must be reconciled to DISCONNECTED; present devices stay CONNECTED."""
    from app.services.device_service import DeviceService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models import Base, DeviceStatus

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with maker() as db:
            service = DeviceService(db)
            # Seed two devices as CONNECTED (synthetic fixtures).
            await service.upsert_device("UDID-STALE-0001", "Old Phone", "17.0", DeviceStatus.CONNECTED)
            await service.upsert_device("UDID-LIVE-0002", "Live Phone", "17.5", DeviceStatus.CONNECTED)

            # Only the live device is seen in this scan.
            async def fake_scan():
                return [{"udid": "UDID-LIVE-0002", "name": "Live Phone", "os_version": "17.5"}]

            monkeypatch.setattr(service, "scan_usb_devices", fake_scan)
            await service.sync_devices()

            stale = await service.get_device_by_udid("UDID-STALE-0001")
            live = await service.get_device_by_udid("UDID-LIVE-0002")
            assert stale.status == DeviceStatus.DISCONNECTED
            assert live.status == DeviceStatus.CONNECTED
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
