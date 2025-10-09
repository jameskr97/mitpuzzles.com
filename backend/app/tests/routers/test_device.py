from sqlalchemy import select
import uuid

from app.modules.tracking import DEVICE_COOKIE_NAME, Device, DeviceThumbmark

thumbmark_1 = {
    "thumbmark": "this-is-number-01-test-thumbmark",  # must be 32 chars
    "components": {},
}

thumbmark_2 = {
    "thumbmark": "this-is-number-02-test-thumbmark",  # must be 32 chars
    "components": {},
}


def test_device_create_new_device(client, db):
    """First PUT with no device_d cookie creates a new device and thumbmark"""
    # client side requests
    res = client.put("/device", json={"thumbmark": thumbmark_1})

    # ensure a cookie was set
    assert res.status_code == 202, "Incorrect status code"
    device_id = res.cookies.get(DEVICE_COOKIE_NAME)
    assert device_id is not None, "Device Cookie not set"

    # ensure device matches intended server state
    device_uuid = uuid.UUID(device_id)
    device = db.execute(select(Device).where(Device.id == device_uuid)).scalar_one_or_none()

    # ensure thumbmark exists and is associated with above device
    thumbmarks = db.execute(select(DeviceThumbmark).where(DeviceThumbmark.device_id == device_uuid)).scalars().all()
    assert len(thumbmarks) == 1, f"Expected 1 thumbmark, found {len(thumbmarks)}"

    # ensure thumbmark matches our given thumbmark
    tm_record: DeviceThumbmark = thumbmarks[0]
    assert tm_record.thumbmark_id == thumbmark_1["thumbmark"], "Thumbmark ID mismatch"
    assert tm_record.thumbmark_data == thumbmark_1, "Thumbmark data mismatch"

    assert res.status_code == 202, "Incorrect Status Code"
    assert device is not None, "Device was not saved to database"
    assert str(device.id) == device_id, "Device ID mismatch"


def test_device_update_same_thumbmark(client, db):
    """Test: Subsequent PUT with same thumbmark_id doesn't create duplicate"""
    # First request - create device
    res1 = client.put("/device", json={"thumbmark": thumbmark_1})
    device_id = res1.cookies.get(DEVICE_COOKIE_NAME)
    device_uuid = uuid.UUID(device_id)

    # Second request with same thumbmark - should not create duplicate
    res2 = client.put(
        "/device",
        json={"thumbmark": thumbmark_1},
        cookies={DEVICE_COOKIE_NAME: device_id},
    )
    assert res2.status_code == 202, "Incorrect Status Code"
    returned_device_id = res2.cookies.get(DEVICE_COOKIE_NAME)
    assert str(returned_device_id) == device_id, "Device ID should remain the same"

    # Validate only one thumbmark exists (no duplicates)
    thumbmarks = db.execute(select(DeviceThumbmark).where(DeviceThumbmark.device_id == device_uuid)).scalars().all()
    assert len(thumbmarks) == 1, f"Expected 1 thumbmark, found {len(thumbmarks)} (no duplicates should be created)"


def test_device_update_different_thumbmark(client, db):
    """Test: Subsequent PUT with different thumbmark_id creates new thumbmark record"""

    # First request - create device with thumbmark_1
    res1 = client.put("/device", json={"thumbmark": thumbmark_1})
    device_id = res1.cookies.get(DEVICE_COOKIE_NAME)
    device_uuid = uuid.UUID(device_id)

    # Second request with different thumbmark - should create new thumbmark record
    res2 = client.put(
        "/device",
        json={"thumbmark": thumbmark_2},
        cookies={DEVICE_COOKIE_NAME: device_id},
    )

    assert res2.status_code == 202, "Incorrect Status Code"
    returned_device_id = res2.cookies.get(DEVICE_COOKIE_NAME)
    assert returned_device_id == device_id, "Device ID should remain the same"

    # Validate both thumbmarks exist for the same device
    thumbmarks = db.execute(select(DeviceThumbmark).where(DeviceThumbmark.device_id == device_uuid).order_by(DeviceThumbmark.date_created)).scalars().all()
    assert len(thumbmarks) == 2, f"Expected 2 thumbmarks, found {len(thumbmarks)}"

    # Validate first thumbmark
    assert thumbmarks[0].thumbmark_id == thumbmark_1["thumbmark"], "First thumbmark ID mismatch"
    assert thumbmarks[0].thumbmark_data == thumbmark_1, "First thumbmark data mismatch"

    # Validate second thumbmark
    assert thumbmarks[1].thumbmark_id == thumbmark_2["thumbmark"], "Second thumbmark ID mismatch"
    assert thumbmarks[1].thumbmark_data == thumbmark_2, "Second thumbmark data mismatch"

    # Validate both belong to same device
    assert thumbmarks[0].device_id == device_uuid, "First thumbmark device association"
    assert thumbmarks[1].device_id == device_uuid, "Second thumbmark device association"


def test_device_no_cookie_always_creates_new(client, db):
    """Test: Request without device_id cookie always creates new device, even with existing thumbmark"""
    # first request - creates device A with thumbmark_1
    res1 = client.put("/device", json={"thumbmark": thumbmark_1})
    device_id_1 = res1.cookies.get(DEVICE_COOKIE_NAME)

    # clear cookies to simulate no cookie scenario
    client.cookies.clear()

    # Second request without cookie - should create device B, even with same thumbmark
    res2 = client.put(
        "/device",
        json={"thumbmark": thumbmark_1},  # Same thumbmark, but no device cookie
    )
    device_id_2 = res2.cookies.get(DEVICE_COOKIE_NAME)

    assert device_id_1 != device_id_2, "Should create different devices when no cookie provided"

    # Validate both devices exist
    device_1 = db.execute(select(Device).where(Device.id == uuid.UUID(device_id_1))).scalar_one_or_none()
    device_2 = db.execute(select(Device).where(Device.id == uuid.UUID(device_id_2))).scalar_one_or_none()

    assert device_1 is not None, "First device should exist"
    assert device_2 is not None, "Second device should exist"

    # Validate each device has its own thumbmark record
    thumbmarks_1 = db.execute(select(DeviceThumbmark).where(DeviceThumbmark.device_id == uuid.UUID(device_id_1))).scalars().all()
    thumbmarks_2 = db.execute(select(DeviceThumbmark).where(DeviceThumbmark.device_id == uuid.UUID(device_id_2))).scalars().all()

    assert len(thumbmarks_1) == 1, "First device should have one thumbmark"
    assert len(thumbmarks_2) == 1, "Second device should have one thumbmark"


def test_malformed_thumbmark_field_missing(client, db):
    """Test handling of invalid thumbmark data"""
    # Missing thumbmark field
    res = client.put("/device", json={"thumbmark": {"components": {}}})
    assert res.status_code == 422


def test_malformed_thumbmark_field_null(client, db):
    # Null thumbmark
    res = client.put("/device", json={"thumbmark": {"thumbmark": None, "components": {}}})
    assert res.status_code == 422


def test_malformed_thumbmark_field_empty(client, db):
    # Empty thumbmark
    res = client.put("/device", json={"thumbmark": {"thumbmark": "", "components": {}}})
    assert res.status_code == 422


def test_malformed_thumbmark_field_malformed(client, db):
    # Empty thumbmark
    res = client.put("/device", json={"thumbmark": {"thumbmark": "12345", "components": {}}})
    assert res.status_code == 422


def test_missing_thumbmark_data(client, db):
    """Test handling of completely missing thumbmark data"""
    res = client.put("/device", json={})
    assert res.status_code == 422  # FastAPI should reject this
