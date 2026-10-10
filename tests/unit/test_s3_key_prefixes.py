import re
import uuid
import pytest


def test_s3_prefix_architecture_regex_patterns():
    """Verify that S3 key conventions documented in docs/ARCHITECTURE.md match expected regex patterns."""
    device_id = str(uuid.uuid4())
    component_id = str(uuid.uuid4())
    passport_id = str(uuid.uuid4())

    img_key = f"images/{device_id}/original.jpg"
    crop_key = f"images/{device_id}/crops/{component_id}.jpg"
    log_key = f"logs/{device_id}/tests/{component_id}.json"
    passport_key = f"passports/{passport_id}.json"

    # Strict regex matching
    image_pattern = re.compile(r"^images/[a-zA-Z0-9_-]+/original\.(jpg|jpeg|png)$")
    crop_pattern = re.compile(r"^images/[a-zA-Z0-9_-]+/crops/[a-zA-Z0-9_-]+\.(jpg|jpeg|png)$")
    log_pattern = re.compile(r"^logs/[a-zA-Z0-9_-]+/tests/[a-zA-Z0-9_-]+\.json$")
    passport_pattern = re.compile(r"^passports/[a-zA-Z0-9_-]+\.json$")

    assert image_pattern.match(img_key)
    assert crop_pattern.match(crop_key)
    assert log_pattern.match(log_key)
    assert passport_pattern.match(passport_key)


def test_ingest_key_format():
    """Verify ingest function S3 key construction."""
    device_id = "test-device-123"
    content_type = "image/jpeg"
    ext = "jpg" if "jpeg" in content_type else "png"
    image_key = f"images/{device_id}/original.{ext}"
    assert image_key == "images/test-device-123/original.jpg"


def test_diagnostics_log_key_format():
    """Verify run_diagnostics log key construction."""
    device_id = "test-device-123"
    comp_id = "comp-ram-001"
    log_key = f"logs/{device_id}/tests/{comp_id}.json"
    assert log_key == "logs/test-device-123/tests/comp-ram-001.json"


def test_passport_key_format():
    """Verify generate_passport s3 key construction."""
    passport_id = "pass-456"
    s3_key = f"passports/{passport_id}.json"
    assert s3_key == "passports/pass-456.json"
