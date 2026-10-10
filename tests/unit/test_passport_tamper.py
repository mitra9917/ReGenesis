import base64
import json
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "shared" / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "shared" / "python"))
verify_passport_path = str(ROOT / "backend" / "functions" / "verify_passport")
if verify_passport_path not in sys.path:
    sys.path.insert(0, verify_passport_path)

from regenesis_common.passport import canonical_passport_bytes, strip_signature
import app as verify_app


@pytest.fixture
def sample_passport():
    return {
        "passport_id": "test-pass-001",
        "component_id": "test-comp-001",
        "device_id": "test-device-001",
        "timestamp": "2026-10-10T12:00:00Z",
        "component_type": "GPU",
        "manufacturer": "NVIDIA",
        "model": "Tesla T4",
        "serial": "SN-GPU-999",
        "extraction_step": 1,
        "tests": {"VRAM": "Pass", "Compute": "Pass"},
        "status": "qualified_for_reuse",
        "notes": "Verified working",
        "detection_source": "vision",
        "signature": base64.b64encode(b"dummy_rsa_signature").decode("ascii"),
    }


def test_tamper_changes_canonical_hash(sample_passport):
    """Verifies that altering any field changes the canonical payload bytes."""
    orig_bytes = canonical_passport_bytes(sample_passport)

    # Tamper with status
    tampered_passport = dict(sample_passport)
    tampered_passport["status"] = "fraudulent_certified"
    tampered_bytes = canonical_passport_bytes(tampered_passport)
    assert orig_bytes != tampered_bytes

    # Tamper with test results
    tampered_tests = dict(sample_passport)
    tampered_tests["tests"] = {"VRAM": "Fail", "Compute": "Fail"}
    assert orig_bytes != canonical_passport_bytes(tampered_tests)

    # Tamper with serial
    tampered_serial = dict(sample_passport)
    tampered_serial["serial"] = "SN-COUNTERFEIT"
    assert orig_bytes != canonical_passport_bytes(tampered_serial)


def test_verify_passport_untampered(sample_passport, monkeypatch):
    """Verifies that an authentic passport returns valid: True."""
    monkeypatch.setenv("PASSPORTS_TABLE", "test-passports")
    monkeypatch.setenv("ASSETS_BUCKET", "test-bucket")
    monkeypatch.setenv("PASSPORT_KMS_KEY_ID", "key-123")

    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {"passport_id": "test-pass-001", "s3_key": "passports/test-pass-001.json"}}

    mock_s3_body = MagicMock()
    mock_s3_body.read.return_value = json.dumps(sample_passport).encode("utf-8")

    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": mock_s3_body}

    mock_kms = MagicMock()
    mock_kms.verify.return_value = {"SignatureValid": True}

    with patch.object(verify_app.ddb, "Table", return_value=mock_table), \
         patch.object(verify_app, "s3", mock_s3), \
         patch.object(verify_app, "kms", mock_kms):

        event = {"pathParameters": {"passport_id": "test-pass-001"}}
        response = verify_app.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["valid"] is True
        assert body["passport_id"] == "test-pass-001"
        assert "tamper_detected" not in body


def test_verify_passport_tampered_fails(sample_passport, monkeypatch):
    """Verifies that a tampered passport raising KMSInvalidSignatureException returns valid: False."""
    monkeypatch.setenv("PASSPORTS_TABLE", "test-passports")
    monkeypatch.setenv("ASSETS_BUCKET", "test-bucket")
    monkeypatch.setenv("PASSPORT_KMS_KEY_ID", "key-123")

    # Tampered passport content
    tampered = dict(sample_passport)
    tampered["status"] = "tampered_unapproved"

    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": {"passport_id": "test-pass-001", "s3_key": "passports/test-pass-001.json"}}

    mock_s3_body = MagicMock()
    mock_s3_body.read.return_value = json.dumps(tampered).encode("utf-8")

    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": mock_s3_body}

    # Simulate KMS rejecting tampered signature
    error_response = {"Error": {"Code": "KMSInvalidSignatureException", "Message": "The signature is not valid."}}
    mock_kms = MagicMock()
    mock_kms.verify.side_effect = ClientError(error_response, "Verify")

    with patch.object(verify_app.ddb, "Table", return_value=mock_table), \
         patch.object(verify_app, "s3", mock_s3), \
         patch.object(verify_app, "kms", mock_kms):

        event = {"pathParameters": {"passport_id": "test-pass-001"}}
        response = verify_app.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["valid"] is False
        assert body["tamper_detected"] is True
        assert "tampered" in body["reason"].lower()
