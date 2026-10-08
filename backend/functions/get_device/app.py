import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource("dynamodb")


def _json_default(obj):
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    return str(obj)


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=_json_default),
    }


def handler(event, context):
    device_id = event.get("pathParameters", {}).get("device_id")
    if not device_id:
        return _response(400, {"error": "device_id required"})

    devices = ddb.Table(os.environ["DEVICES_TABLE"])
    device = devices.get_item(Key={"device_id": device_id}).get("Item")
    if not device:
        return _response(404, {"error": "not found"})

    comps = ddb.Table(os.environ["COMPONENTS_TABLE"]).query(
        KeyConditionExpression=Key("device_id").eq(device_id)
    ).get("Items", [])

    passports = ddb.Table(os.environ["PASSPORTS_TABLE"]).query(
        IndexName="DevicePassportsIndex",
        KeyConditionExpression=Key("device_id").eq(device_id),
    ).get("Items", [])

    for field in ("completeness_audit", "disassembly_plan", "impact_summary"):
        if device.get(field) and isinstance(device[field], str):
            try:
                device[field] = json.loads(device[field])
            except json.JSONDecodeError:
                pass

    for c in comps:
        if c.get("bbox") and isinstance(c["bbox"], str):
            try:
                c["bbox"] = json.loads(c["bbox"])
            except json.JSONDecodeError:
                pass
        if c.get("test_results") and isinstance(c["test_results"], str):
            try:
                c["test_results"] = json.loads(c["test_results"])
            except json.JSONDecodeError:
                pass

    return _response(
        200,
        {
            "device": device,
            "components": comps,
            "passports": passports,
        },
    )
