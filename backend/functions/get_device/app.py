import json
import os
from decimal import Decimal

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

    params = event.get("pathParameters") or {}
    device_id = (
        params.get("device_id")
        or params.get("id")
        or (event.get("queryStringParameters") or {}).get("device_id")
        or (event.get("queryStringParameters") or {}).get("id")
        or event.get("device_id")
    )
    if not device_id:
        return _response(400, {"error": "device_id required"})

    try:
        devices = ddb.Table(os.environ["DEVICES_TABLE"])
        device = devices.get_item(Key={"device_id": device_id}).get("Item")
        if not device:
            return _response(404, {"error": "not found"})

        comps_table = ddb.Table(os.environ["COMPONENTS_TABLE"])
        comps = []
        q_params = {"KeyConditionExpression": Key("device_id").eq(device_id)}
        while True:
            resp = comps_table.query(**q_params)
            comps.extend(resp.get("Items", []))
            if "LastEvaluatedKey" in resp:
                q_params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            else:
                break

        passports_table = ddb.Table(os.environ["PASSPORTS_TABLE"])
        passports = []
        p_params = {
            "IndexName": "DevicePassportsIndex",
            "KeyConditionExpression": Key("device_id").eq(device_id),
        }
        while True:
            resp = passports_table.query(**p_params)
            passports.extend(resp.get("Items", []))
            if "LastEvaluatedKey" in resp:
                p_params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            else:
                break

        events_table_name = os.environ.get("PIPELINE_EVENTS_TABLE")
        events = []
        if events_table_name:
            try:
                events_table = ddb.Table(events_table_name)
                e_params = {"KeyConditionExpression": Key("device_id").eq(device_id)}
                while True:
                    resp = events_table.query(**e_params)
                    events.extend(resp.get("Items", []))
                    if "LastEvaluatedKey" in resp:
                        e_params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
                    else:
                        break

                for ev in events:
                    if ev.get("detail") and isinstance(ev["detail"], str):
                        try:
                            ev["detail"] = json.loads(ev["detail"])
                        except json.JSONDecodeError:
                            pass

                events.sort(key=lambda x: str(x.get("created_at") or x.get("event_id") or ""))
            except Exception:
                pass

        for field in ("completeness_audit", "disassembly_plan", "impact_summary"):
            if device.get(field) and isinstance(device[field], str):
                try:
                    device[field] = json.loads(device[field])
                except json.JSONDecodeError:
                    pass

        if device.get("ocr_matched_hints") and isinstance(device["ocr_matched_hints"], str):
            try:
                device["ocr_matched_hints"] = json.loads(device["ocr_matched_hints"])
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

        plan = device.get("disassembly_plan")
        audit = device.get("completeness_audit")
        impact = device.get("impact_summary")

        return _response(
            200,
            {
                "device": device,
                "components": comps,
                "passports": passports,
                "events": events,
                "pipeline_events": events,
                "plan": plan,
                "disassembly_plan": plan,
                "audit": audit,
                "completeness_audit": audit,
                "impact": impact,
                "impact_summary": impact,
            },
        )

    except Exception as exc:
        return _response(500, {"error": str(exc)})
