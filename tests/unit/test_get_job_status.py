import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[2]
GET_JOB_STATUS_APP_PATH = ROOT / "backend" / "functions" / "get_job_status" / "app.py"
spec = importlib.util.spec_from_file_location("get_job_status_app", str(GET_JOB_STATUS_APP_PATH))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_missing_execution_arn():
    resp = app.handler({}, None)
    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "error" in body


def test_options_preflight():
    resp = app.handler({"httpMethod": "OPTIONS"}, None)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "GET,OPTIONS" in resp["headers"]["Access-Control-Allow-Methods"]


def test_successful_running_job():
    mock_desc = {
        "status": "RUNNING",
        "startDate": "2026-10-10 12:00:00+00:00",
        "stopDate": None,
    }
    with patch.object(app.sfn, "describe_execution", return_value=mock_desc):
        arn = "arn:aws:states:ap-south-1:123456789012:execution:RecoveryFlow:test-run"
        resp = app.handler({"queryStringParameters": {"execution_arn": arn}}, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["status"] == "RUNNING"
        assert body["execution_arn"] == arn


def test_successful_succeeded_job_with_output():
    mock_desc = {
        "status": "SUCCEEDED",
        "startDate": "2026-10-10 12:00:00+00:00",
        "stopDate": "2026-10-10 12:01:00+00:00",
        "output": json.dumps({"device_id": "dev-01", "status": "COMPLETED"}),
    }
    with patch.object(app.sfn, "describe_execution", return_value=mock_desc):
        arn = "arn:aws:states:ap-south-1:123456789012:execution:RecoveryFlow:test-succeeded"
        resp = app.handler({"queryStringParameters": {"arn": arn}}, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["status"] == "SUCCEEDED"
        assert body["output"]["status"] == "COMPLETED"


def test_failed_job_includes_error_and_cause():
    mock_desc = {
        "status": "FAILED",
        "startDate": "2026-10-10 12:00:00+00:00",
        "stopDate": "2026-10-10 12:00:10+00:00",
        "error": "CustomPipelineFailure",
        "cause": "Image processing timed out",
    }
    with patch.object(app.sfn, "describe_execution", return_value=mock_desc):
        arn = "arn:aws:states:ap-south-1:123456789012:execution:RecoveryFlow:test-failed"
        resp = app.handler({"queryStringParameters": {"execution_arn": arn}}, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["status"] == "FAILED"
        assert body["error"] == "CustomPipelineFailure"
        assert body["cause"] == "Image processing timed out"


def test_nonexistent_execution_returns_404():
    err = ClientError(
        {"Error": {"Code": "ExecutionDoesNotExist", "Message": "Execution does not exist"}},
        "DescribeExecution",
    )
    with patch.object(app.sfn, "describe_execution", side_effect=err):
        arn = "arn:aws:states:ap-south-1:123456789012:execution:RecoveryFlow:missing"
        resp = app.handler({"queryStringParameters": {"execution_arn": arn}}, None)
        assert resp["statusCode"] == 404
        body = json.loads(resp["body"])
        assert "not found" in body["error"].lower()


def test_invalid_arn_returns_400():
    err = ClientError(
        {"Error": {"Code": "InvalidArn", "Message": "Invalid ARN provided"}},
        "DescribeExecution",
    )
    with patch.object(app.sfn, "describe_execution", side_effect=err):
        resp = app.handler({"queryStringParameters": {"execution_arn": "bad-arn"}}, None)
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert "invalid" in body["error"].lower()
