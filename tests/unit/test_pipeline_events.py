"""Unit tests for GET /devices/{device_id}/events (I-4.5 PipelineEvents table)."""
import importlib.util
import json
import os
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
GET_EVENTS_APP_PATH = ROOT / "backend" / "functions" / "get_events" / "app.py"
spec = importlib.util.spec_from_file_location("get_events_app", str(GET_EVENTS_APP_PATH))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("PIPELINE_EVENTS_TABLE", "mock-events-table")


def _sample_events():
    return [
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:00Z#aaaa",
            "event_type": "ingest",
            "status": "succeeded",
            "detail": json.dumps({"image_key": "images/dev-001.jpg", "has_plate_text": True}),
            "created_at": "2026-01-01T10:00:00Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:05Z#bbbb",
            "event_type": "detect",
            "status": "started",
            "detail": json.dumps({"mode": "catalog"}),
            "created_at": "2026-01-01T10:00:05Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:08Z#cccc",
            "event_type": "detect",
            "status": "succeeded",
            "detail": json.dumps({"source": "catalog-assisted", "count": 16}),
            "created_at": "2026-01-01T10:00:08Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:10Z#dddd",
            "event_type": "parse",
            "status": "succeeded",
            "detail": json.dumps({"components": 16}),
            "created_at": "2026-01-01T10:00:10Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:15Z#eeee",
            "event_type": "plan",
            "status": "succeeded",
            "detail": json.dumps({"steps": 7, "total_plan_rvs": 312.5}),
            "created_at": "2026-01-01T10:00:15Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:30Z#ffff",
            "event_type": "test",
            "status": "succeeded",
            "detail": json.dumps({"tested": 16}),
            "created_at": "2026-01-01T10:00:30Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:35Z#gggg",
            "event_type": "passport",
            "status": "succeeded",
            "detail": json.dumps({"count": 14}),
            "created_at": "2026-01-01T10:00:35Z",
        },
        {
            "device_id": "dev-001",
            "event_id": "2026-01-01T10:00:40Z#hhhh",
            "event_type": "impact",
            "status": "succeeded",
            "detail": json.dumps({"co2e_avoided_kg": 258.0}),
            "created_at": "2026-01-01T10:00:40Z",
        },
    ]


def test_missing_device_id():
    resp = app.handler({}, None)
    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "error" in body


def test_options_preflight():
    resp = app.handler({"httpMethod": "OPTIONS"}, None)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


def test_returns_events_for_device():
    sample = _sample_events()
    with patch.object(app.ddb, "Table") as mock_table_fn:
        t = MagicMock()
        t.query.return_value = {"Items": list(sample)}
        mock_table_fn.return_value = t

        resp = app.handler({"pathParameters": {"device_id": "dev-001"}}, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["device_id"] == "dev-001"
        assert body["total"] == 8
        events = body["events"]
        # Chronological ordering
        types_in_order = [e["event_type"] for e in events]
        assert types_in_order[0] == "ingest"
        assert types_in_order[-1] == "impact"


def test_detail_json_unpacked():
    sample = _sample_events()[:2]
    with patch.object(app.ddb, "Table") as mock_table_fn:
        t = MagicMock()
        t.query.return_value = {"Items": list(sample)}
        mock_table_fn.return_value = t

        resp = app.handler({"pathParameters": {"device_id": "dev-001"}}, None)
        body = json.loads(resp["body"])
        # detail should be a dict, not a raw JSON string
        assert isinstance(body["events"][0]["detail"], dict)


def test_stage_summary_contains_all_stages():
    sample = _sample_events()
    with patch.object(app.ddb, "Table") as mock_table_fn:
        t = MagicMock()
        t.query.return_value = {"Items": list(sample)}
        mock_table_fn.return_value = t

        resp = app.handler({"pathParameters": {"device_id": "dev-001"}}, None)
        body = json.loads(resp["body"])
        summary = body["stage_summary"]
        assert "ingest:succeeded" in summary
        assert "detect:started" in summary
        assert "detect:succeeded" in summary
        assert "impact:succeeded" in summary


def test_filter_by_event_type():
    sample = _sample_events()
    with patch.object(app.ddb, "Table") as mock_table_fn:
        t = MagicMock()
        t.query.return_value = {"Items": list(sample)}
        mock_table_fn.return_value = t

        resp = app.handler(
            {"pathParameters": {"device_id": "dev-001"}, "queryStringParameters": {"event_type": "detect"}},
            None,
        )
        body = json.loads(resp["body"])
        assert all(e["event_type"] == "detect" for e in body["events"])
        assert body["total"] == 2


def test_query_string_device_id():
    sample = _sample_events()[:1]
    with patch.object(app.ddb, "Table") as mock_table_fn:
        t = MagicMock()
        t.query.return_value = {"Items": list(sample)}
        mock_table_fn.return_value = t

        resp = app.handler(
            {"pathParameters": None, "queryStringParameters": {"device_id": "dev-001"}},
            None,
        )
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["device_id"] == "dev-001"


def test_pipeline_stages_always_in_response():
    with patch.object(app.ddb, "Table") as mock_table_fn:
        t = MagicMock()
        t.query.return_value = {"Items": []}
        mock_table_fn.return_value = t

        resp = app.handler({"pathParameters": {"device_id": "dev-empty"}}, None)
        body = json.loads(resp["body"])
        assert body["pipeline_stages"] == ["ingest", "detect", "parse", "plan", "test", "passport", "impact"]
        assert body["total"] == 0
        assert body["events"] == []
