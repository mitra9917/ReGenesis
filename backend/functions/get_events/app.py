"""GET /devices/{device_id}/events — Returns PipelineEvents for a device chronologically.

Provides audit trail across all pipeline stages:
  ingest → detect (started/succeeded/failed) → parse → plan → test → passport → impact

Useful for debugging stuck pipelines or understanding what happened in each stage.
"""
import json
import os
from decimal import Decimal
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource("dynamodb")


def _json_default(obj):
    if isinstance(obj, Decimal):
        try:
            return int(obj) if obj % 1 == 0 else float(obj)
        except Exception:
            return float(obj)
    if isinstance(obj, (set, tuple)):
        return list(obj)
    return str(obj)


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body, default=_json_default),
    }


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {})

    # Support both path parameter and query string
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}
    device_id = (
        path_params.get("device_id")
        or query_params.get("device_id")
        or event.get("device_id")
    )
    if device_id:
        device_id = unquote(str(device_id)).strip()

    if not device_id:
        return _response(400, {"error": "device_id is required"})

    table_name = os.environ.get("PIPELINE_EVENTS_TABLE")
    if not table_name:
        return _response(500, {"error": "PIPELINE_EVENTS_TABLE not configured"})

    # Optional limit parameter, default 100
    try:
        limit = min(int(query_params.get("limit", "100")), 500)
    except (ValueError, TypeError):
        limit = 100

    # Optional filter by event_type
    filter_type = query_params.get("event_type", "").strip()

    try:
        table = ddb.Table(table_name)
        events = []
        q_params = {
            "KeyConditionExpression": Key("device_id").eq(device_id),
        }

        while len(events) < limit:
            resp = table.query(**q_params)
            events.extend(resp.get("Items", []))
            if "LastEvaluatedKey" in resp:
                q_params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            else:
                break

        events = events[:limit]

        # Parse detail JSON strings
        for ev in events:
            if ev.get("detail") and isinstance(ev["detail"], str):
                try:
                    ev["detail"] = json.loads(ev["detail"])
                except (json.JSONDecodeError, Exception):
                    pass

        # Sort chronologically
        events.sort(key=lambda x: str(x.get("created_at") or x.get("event_id") or ""))

        # Filter by event_type if requested
        if filter_type:
            events = [e for e in events if e.get("event_type") == filter_type]

        # Build summary of stages seen
        stage_summary = {}
        for ev in events:
            etype = ev.get("event_type", "unknown")
            estatus = ev.get("status", "unknown")
            key = f"{etype}:{estatus}"
            stage_summary[key] = stage_summary.get(key, 0) + 1

        return _response(
            200,
            {
                "device_id": device_id,
                "events": events,
                "total": len(events),
                "stage_summary": stage_summary,
                "pipeline_stages": ["ingest", "detect", "parse", "plan", "test", "passport", "impact"],
            },
        )

    except Exception as exc:
        return _response(500, {"error": str(exc)})
