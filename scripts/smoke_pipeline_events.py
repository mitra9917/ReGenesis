"""Smoke script for Issue #45: PipelineEvents table debuggable (I-4.5).

Demonstrates:
  1. Unit-level simulation of the get_events Lambda handler
  2. Full-pipeline event trace: ingest -> detect -> parse -> plan -> test -> passport -> impact
  3. Event filtering by stage
  4. Stage summary generation

Usage:
  python scripts/smoke_pipeline_events.py
"""
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

# Load the get_events app
GET_EVENTS_PATH = ROOT / "backend" / "functions" / "get_events" / "app.py"
spec = importlib.util.spec_from_file_location("get_events_app", str(GET_EVENTS_PATH))
events_app = importlib.util.module_from_spec(spec)

os.environ.setdefault("PIPELINE_EVENTS_TABLE", "PipelineEvents-smoke")
spec.loader.exec_module(events_app)

# --- Simulate a complete golden R740 pipeline event trace ---
DEVICE_ID = "dev-r740-smoke-001"

SAMPLE_EVENTS = [
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:00Z#aaaa",
        "event_type": "ingest",
        "status": "succeeded",
        "detail": json.dumps({"image_key": f"images/{DEVICE_ID}.jpg", "has_plate_text": True}),
        "created_at": "2026-01-01T10:00:00Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:05Z#bbbb",
        "event_type": "detect",
        "status": "started",
        "detail": json.dumps({"mode": "catalog"}),
        "created_at": "2026-01-01T10:00:05Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:09Z#cccc",
        "event_type": "detect",
        "status": "succeeded",
        "detail": json.dumps({"source": "catalog-assisted", "count": 16, "audit_score": 1.0, "audit_gaps": 0}),
        "created_at": "2026-01-01T10:00:09Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:12Z#dddd",
        "event_type": "parse",
        "status": "succeeded",
        "detail": json.dumps({"components": 16, "ocr_confirmed": True}),
        "created_at": "2026-01-01T10:00:12Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:15Z#eeee",
        "event_type": "plan",
        "status": "succeeded",
        "detail": json.dumps({"steps": 7, "total_plan_rvs": 312.5, "highest_rvs_component": "GPU"}),
        "created_at": "2026-01-01T10:00:15Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:30Z#ffff",
        "event_type": "test",
        "status": "succeeded",
        "detail": json.dumps({"tested": 16}),
        "created_at": "2026-01-01T10:00:30Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:35Z#gggg",
        "event_type": "passport",
        "status": "succeeded",
        "detail": json.dumps({"count": 14}),
        "created_at": "2026-01-01T10:00:35Z",
    },
    {
        "device_id": DEVICE_ID,
        "event_id": "2026-01-01T10:00:40Z#hhhh",
        "event_type": "impact",
        "status": "succeeded",
        "detail": json.dumps({"co2e_avoided_kg": 258.0, "components_qualified": 14, "mass_diverted_kg": 1.53}),
        "created_at": "2026-01-01T10:00:40Z",
    },
]


def call_handler(path_device_id=None, query_event_type=None):
    ev = {
        "pathParameters": {"device_id": path_device_id} if path_device_id else None,
        "queryStringParameters": {},
    }
    if query_event_type:
        ev["queryStringParameters"]["event_type"] = query_event_type

    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": list(SAMPLE_EVENTS)}

    with patch.object(events_app.ddb, "Table", return_value=mock_table):
        return events_app.handler(ev, None)


def main():
    print(f"--- [I-4.5 Smoke Test] PipelineEvents Audit Table for device {DEVICE_ID[:16]}... ---\n")

    # 1. Fetch all events
    resp = call_handler(path_device_id=DEVICE_ID)
    assert resp["statusCode"] == 200, f"Expected 200, got {resp['statusCode']}: {resp['body']}"
    body = json.loads(resp["body"])

    print(f"Total events:   {body['total']}")
    print(f"Pipeline stages: {' -> '.join(body['pipeline_stages'])}")
    print(f"\nStage Summary:")
    for key, count in sorted(body["stage_summary"].items()):
        status_mark = "[OK]" if "succeeded" in key else ("[..]" if "started" in key else "[!!]")
        print(f"  {status_mark}  {key:<30} (x{count})")

    print(f"\nFull Chronological Event Trace:")
    for ev in body["events"]:
        detail = ev.get("detail", {})
        detail_str = ", ".join(f"{k}={v}" for k, v in (detail.items() if isinstance(detail, dict) else {}.items()))
        print(f"  [{ev['created_at']}] {ev['event_type']:10} -> {ev['status']:12}  {detail_str}")

    # 2. Filter to detect stage only
    resp2 = call_handler(path_device_id=DEVICE_ID, query_event_type="detect")
    body2 = json.loads(resp2["body"])
    assert all(e["event_type"] == "detect" for e in body2["events"])
    print(f"\n'detect' stage filtered: {body2['total']} events (started + succeeded)")

    # 3. Empty device test
    mock_table_empty = MagicMock()
    mock_table_empty.query.return_value = {"Items": []}
    ev_empty = {"pathParameters": {"device_id": "dev-not-exist"}}
    with patch.object(events_app.ddb, "Table", return_value=mock_table_empty):
        resp3 = events_app.handler(ev_empty, None)
    body3 = json.loads(resp3["body"])
    assert body3["total"] == 0
    print(f"\nEmpty device returns 0 events: [OK]")

    print("\n--- Smoke test completed successfully! ---")

    print("\n== API endpoint (after sam deploy) ==")
    print(f"  GET {{API_URL}}/devices/{DEVICE_ID}/events")
    print(f"  GET {{API_URL}}/devices/{DEVICE_ID}/events?event_type=detect")
    print(f"  GET {{API_URL}}/devices/{DEVICE_ID}/events?limit=50")


if __name__ == "__main__":
    main()
