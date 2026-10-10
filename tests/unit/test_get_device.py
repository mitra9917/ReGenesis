import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GET_DEVICE_APP_PATH = ROOT / "backend" / "functions" / "get_device" / "app.py"
spec = importlib.util.spec_from_file_location("get_device_app", str(GET_DEVICE_APP_PATH))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("DEVICES_TABLE", "mock-devices-table")
    monkeypatch.setenv("COMPONENTS_TABLE", "mock-components-table")
    monkeypatch.setenv("PASSPORTS_TABLE", "mock-passports-table")


def test_missing_device_id():
    resp = app.handler({}, None)
    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "error" in body

    # Also test pathParameters is None
    resp2 = app.handler({"pathParameters": None}, None)
    assert resp2["statusCode"] == 400


def test_options_preflight():
    resp = app.handler({"httpMethod": "OPTIONS"}, None)
    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "GET,OPTIONS" in resp["headers"]["Access-Control-Allow-Methods"]


def test_device_not_found():
    with patch.object(app.ddb, "Table") as mock_table:
        devices_mock = MagicMock()
        devices_mock.get_item.return_value = {}
        mock_table.return_value = devices_mock

        resp = app.handler({"pathParameters": {"device_id": "missing-id"}}, None)
        assert resp["statusCode"] == 404
        body = json.loads(resp["body"])
        assert body["error"] == "not found"


def test_get_device_success_with_plan_audit_impact():
    sample_plan = {
        "plan_id": "plan-123",
        "device_model_key": "poweredge_r740",
        "steps": [
            {"action": "Extract PSUs", "risk": 0.25, "components": [{"comp_type": "PSU", "rvs": 26.89}]}
        ],
    }
    sample_audit = {
        "score": 1.0,
        "gaps": [],
        "expected": {"CPU": 2},
        "detected": {"CPU": 2},
    }
    sample_impact = {
        "components_qualified": 16,
        "mass_diverted_kg": 4.5,
        "co2e_avoided_kg": 520.0,
        "co2e_avoided_kg_range": {"low": 450.0, "high": 590.0},
    }

    mock_device_item = {
        "device_id": "dev-001",
        "device_model_key": "poweredge_r740",
        "status": "COMPLETED",
        "disassembly_plan": json.dumps(sample_plan),
        "completeness_audit": json.dumps(sample_audit),
        "impact_summary": json.dumps(sample_impact),
        "ocr_matched_hints": json.dumps(["PowerEdge", "R740"]),
        "confidence_score": Decimal("0.98"),
        "step_count": Decimal("5.0"),
    }

    mock_comps = [
        {
            "device_id": "dev-001",
            "component_id": "comp-01",
            "comp_type": "PSU",
            "bbox": "[0.1, 0.2, 0.3, 0.4]",
            "test_results": json.dumps({"passed": True, "voltage": 12.0}),
        }
    ]

    mock_passports = [
        {
            "passport_id": "pass-01",
            "device_id": "dev-001",
            "component_id": "comp-01",
            "status": "qualified_for_reuse",
        }
    ]

    with patch.object(app.ddb, "Table") as mock_table:
        def table_side_effect(name):
            t = MagicMock()
            if name == "mock-devices-table":
                t.get_item.return_value = {"Item": dict(mock_device_item)}
            elif name == "mock-components-table":
                t.query.return_value = {"Items": list(mock_comps)}
            elif name == "mock-passports-table":
                t.query.return_value = {"Items": list(mock_passports)}
            return t

        mock_table.side_effect = table_side_effect

        resp = app.handler({"pathParameters": {"device_id": "dev-001"}}, None)
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])

        # Check top-level keys
        assert "device" in data
        assert "components" in data
        assert "passports" in data
        assert "plan" in data
        assert "audit" in data
        assert "impact" in data

        # Check plan structure
        assert data["plan"]["plan_id"] == "plan-123"
        assert len(data["plan"]["steps"]) == 1

        # Check audit structure
        assert data["audit"]["score"] == 1.0
        assert data["audit"]["gaps"] == []

        # Check impact structure
        assert data["impact"]["components_qualified"] == 16
        assert data["impact"]["mass_diverted_kg"] == 4.5

        # Check device nested fields were also parsed
        assert data["device"]["disassembly_plan"]["plan_id"] == "plan-123"
        assert data["device"]["completeness_audit"]["score"] == 1.0
        assert data["device"]["impact_summary"]["components_qualified"] == 16
        assert data["device"]["ocr_matched_hints"] == ["PowerEdge", "R740"]
        assert data["device"]["confidence_score"] == 0.98
        assert data["device"]["step_count"] == 5

        # Check components bbox and test_results were parsed
        comp = data["components"][0]
        assert comp["bbox"] == [0.1, 0.2, 0.3, 0.4]
        assert comp["test_results"] == {"passed": True, "voltage": 12.0}

        # Check passports
        assert len(data["passports"]) == 1
        assert data["passports"][0]["passport_id"] == "pass-01"


def test_get_device_using_id_alias():
    with patch.object(app.ddb, "Table") as mock_table:
        t = MagicMock()
        t.get_item.return_value = {"Item": {"device_id": "dev-alias-test"}}
        t.query.return_value = {"Items": []}
        mock_table.return_value = t

        resp = app.handler({"pathParameters": {"id": "dev-alias-test"}}, None)
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["device"]["device_id"] == "dev-alias-test"


def test_json_default_serialization():
    assert app._json_default(Decimal("12.34")) == 12.34
    assert app._json_default(Decimal("10.0")) == 10
    assert app._json_default(Decimal("0")) == 0
    assert app._json_default({"a", "b"}) in (["a", "b"], ["b", "a"])
    assert app._json_default((1, 2)) == [1, 2]
