import base64
import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Load ingest handler cleanly
INGEST_APP_PATH = ROOT / "backend" / "functions" / "ingest" / "app.py"
spec_ingest = importlib.util.spec_from_file_location("ingest_app", str(INGEST_APP_PATH))
ingest_app = importlib.util.module_from_spec(spec_ingest)
spec_ingest.loader.exec_module(ingest_app)

# Load invoke_detection handler cleanly
DETECT_APP_PATH = ROOT / "backend" / "functions" / "invoke_detection" / "app.py"
spec_detect = importlib.util.spec_from_file_location("invoke_detect_app", str(DETECT_APP_PATH))
detect_app = importlib.util.module_from_spec(spec_detect)
spec_detect.loader.exec_module(detect_app)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("DEVICES_TABLE", "mock-devices-table")
    monkeypatch.setenv("ASSETS_BUCKET", "mock-assets-bucket")
    monkeypatch.setenv("RECOVERY_STATE_MACHINE_ARN", "arn:aws:states:ap-south-1:123456789012:stateMachine:MockFlow")
    monkeypatch.setenv("DETECTION_MODE", "auto")


def test_ingest_base64_image_upload_to_s3_and_step_functions():
    fake_img_bytes = b"FAKE_JPEG_IMAGE_CONTENT"
    b64_img = base64.b64encode(fake_img_bytes).decode("ascii")

    mock_table = MagicMock()
    mock_s3 = MagicMock()
    mock_sfn = MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:aws:states:mock:exec-123"}

    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "device_model_key": "poweredge_r740",
            "image_base64": b64_img,
            "content_type": "image/jpeg",
        }),
    }

    with patch.object(ingest_app, "ddb") as mock_ddb, \
         patch.object(ingest_app, "s3", mock_s3), \
         patch.object(ingest_app, "sfn", mock_sfn):
        mock_ddb.Table.return_value = mock_table

        resp = ingest_app.handler(event, None)
        assert resp["statusCode"] == 202
        body = json.loads(resp["body"])
        assert "device_id" in body
        assert "execution_arn" in body
        assert body["image_s3_key"].startswith(f"images/{body['device_id']}/original.jpg")

        # Verify S3 put_object was called with correct bucket, key, and raw bytes
        mock_s3.put_object.assert_called_once()
        s3_call = mock_s3.put_object.call_args[1]
        assert s3_call["Bucket"] == "mock-assets-bucket"
        assert s3_call["Key"] == body["image_s3_key"]
        assert s3_call["Body"] == fake_img_bytes
        assert s3_call["ContentType"] == "image/jpeg"

        # Verify Step Functions input received image_s3_key
        mock_sfn.start_execution.assert_called_once()
        sfn_input = json.loads(mock_sfn.start_execution.call_args[1]["input"])
        assert sfn_input["image_s3_key"] == body["image_s3_key"]
        assert sfn_input["bucket"] == "mock-assets-bucket"


def test_ingest_data_uri_prefix_stripped():
    fake_img_bytes = b"PNG_DATA_STREAM"
    b64_raw = base64.b64encode(fake_img_bytes).decode("ascii")
    data_uri = f"data:image/png;base64,{b64_raw}"

    mock_table = MagicMock()
    mock_s3 = MagicMock()
    mock_sfn = MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:aws:states:mock:exec-456"}

    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "device_model_key": "poweredge_r740",
            "image_base64": data_uri,
            "content_type": "image/png",
        }),
    }

    with patch.object(ingest_app, "ddb") as mock_ddb, \
         patch.object(ingest_app, "s3", mock_s3), \
         patch.object(ingest_app, "sfn", mock_sfn):
        mock_ddb.Table.return_value = mock_table

        resp = ingest_app.handler(event, None)
        assert resp["statusCode"] == 202
        body = json.loads(resp["body"])
        assert body["image_s3_key"].endswith(".png")

        s3_call = mock_s3.put_object.call_args[1]
        assert s3_call["Body"] == fake_img_bytes


def test_ingest_without_image_leaves_empty_key():
    mock_table = MagicMock()
    mock_s3 = MagicMock()
    mock_sfn = MagicMock()
    mock_sfn.start_execution.return_value = {"executionArn": "arn:aws:states:mock:exec-789"}

    event = {
        "httpMethod": "POST",
        "body": json.dumps({"device_model_key": "poweredge_r740"}),
    }

    with patch.object(ingest_app, "ddb") as mock_ddb, \
         patch.object(ingest_app, "s3", mock_s3), \
         patch.object(ingest_app, "sfn", mock_sfn):
        mock_ddb.Table.return_value = mock_table

        resp = ingest_app.handler(event, None)
        assert resp["statusCode"] == 202
        body = json.loads(resp["body"])
        assert body["image_s3_key"] == ""
        mock_s3.put_object.assert_not_called()


def test_invoke_detection_preserves_image_s3_key():
    event = {
        "device_id": "test-dev-123",
        "device_model_key": "poweredge_r740",
        "image_s3_key": "images/test-dev-123/original.jpg",
        "bucket": "mock-assets-bucket",
        "plate_text": "Dell PowerEdge R740",
    }

    with patch.object(detect_app, "log_pipeline_event"):
        out = detect_app.handler(event, None)
        assert out["image_s3_key"] == "images/test-dev-123/original.jpg"
        assert "detections" in out
        assert len(out["detections"]) > 0
