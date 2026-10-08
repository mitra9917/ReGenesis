import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

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


def log_pipeline_event(
    device_id: str,
    event_type: str,
    status: str,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    table_name = os.environ.get("PIPELINE_EVENTS_TABLE")
    if not table_name:
        return
    table = boto3.resource("dynamodb").Table(table_name)
    eid = f"{utc_now_iso()}#{uuid.uuid4()}"
    table.put_item(
        Item={
            "device_id": device_id,
            "event_id": eid,
            "event_type": event_type,
            "status": status,
            "detail": json.dumps(detail or {}),
            "created_at": utc_now_iso(),
        }
    )
