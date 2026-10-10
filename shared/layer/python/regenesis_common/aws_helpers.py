import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def env(name: str, default: Optional[str] = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise RuntimeError(f"Missing env var: {name}")
    return val


def ddb_table(name_env: str):
    return boto3.resource("dynamodb").Table(os.environ[name_env])


def api_gateway_response(status: int, body: Any, default=str) -> Dict[str, Any]:
    """JSON response with CORS headers for browser clients (S3-hosted UI, Vite dev)."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, default=default),
    }


logger = logging.getLogger("regenesis.events")


def _safe_json_default(obj: Any) -> Any:
    if isinstance(obj, (set, tuple)):
        return list(obj)
    return str(obj)


def log_pipeline_event(
    device_id: str,
    event_type: str,
    status: str,
    detail: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Record an audit event to the PipelineEvents DynamoDB table.

    Never raises exceptions, ensuring diagnostic logging never crashes pipeline execution.
    """
    table_name = os.environ.get("PIPELINE_EVENTS_TABLE")
    if not table_name:
        return None
    try:
        table = boto3.resource("dynamodb").Table(table_name)
        now = utc_now_iso()
        eid = f"{now}#{uuid.uuid4()}"
        item = {
            "device_id": device_id,
            "event_id": eid,
            "event_type": event_type,
            "status": status,
            "detail": json.dumps(detail or {}, default=_safe_json_default),
            "created_at": now,
        }
        table.put_item(Item=item)
        return eid
    except Exception as exc:
        logger.warning("Failed to record pipeline event for %s (%s): %s", device_id, event_type, exc)
        return None


def get_pipeline_events(
    device_id: str,
    table_name: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Retrieve and chronologically order all pipeline audit events for a device."""
    target_table = table_name or os.environ.get("PIPELINE_EVENTS_TABLE")
    if not target_table:
        return []
    try:
        from boto3.dynamodb.conditions import Key

        table = boto3.resource("dynamodb").Table(target_table)
        events: List[Dict[str, Any]] = []
        q_params: Dict[str, Any] = {
            "KeyConditionExpression": Key("device_id").eq(device_id),
            "Limit": limit,
        }
        while True:
            resp = table.query(**q_params)
            events.extend(resp.get("Items", []))
            if "LastEvaluatedKey" in resp and len(events) < limit:
                q_params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            else:
                break

        for ev in events:
            if ev.get("detail") and isinstance(ev["detail"], str):
                try:
                    ev["detail"] = json.loads(ev["detail"])
                except Exception:
                    pass

        # Sort chronologically by created_at then event_id
        events.sort(key=lambda x: str(x.get("created_at") or x.get("event_id") or ""))
        return events
    except Exception as exc:
        logger.warning("Failed to query pipeline events for %s: %s", device_id, exc)
        return []

