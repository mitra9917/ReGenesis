import json
import os
import uuid

import boto3

from regenesis_common.aws_helpers import log_pipeline_event, utc_now_iso

ddb = boto3.resource("dynamodb")


def handler(event, context):
    device_id = event["device_id"]
    detections = event.get("detections", [])
    components_table = ddb.Table(os.environ["COMPONENTS_TABLE"])
    devices_table = ddb.Table(os.environ["DEVICES_TABLE"])

    components = []
    for d in detections:
        comp_id = d.get("detection_id") or str(uuid.uuid4())
        comp_type = d.get("class") or d.get("comp_type", "Other")
        item = {
            "device_id": device_id,
            "component_id": comp_id,
            "comp_type": comp_type,
            "detection_confidence": str(d.get("confidence", 0)),
            "bbox": json.dumps(d.get("bbox", [])),
            "status": "pending",
            "created_at": utc_now_iso(),
        }
        components_table.put_item(Item=item)
        components.append(
            {
                "component_id": comp_id,
                "comp_type": comp_type,
                "confidence": float(d.get("confidence", 0)),
                "bbox": d.get("bbox", []),
            }
        )

    devices_table.update_item(
        Key={"device_id": device_id},
        UpdateExpression=(
            "SET detection_source = :s, completeness_audit = :a, updated_at = :u, "
            "device_model_key = :m, ocr_confirmed = :oc, ocr_influenced = :oi, "
            "ocr_matched_hints = :oh, ocr_engine = :oe"
        ),
        ExpressionAttributeValues={
            ":s": event.get("detection_source", "unknown"),
            ":a": json.dumps(event.get("completeness_audit", {})),
            ":u": utc_now_iso(),
            ":m": event.get("device_model_key", "poweredge_r740"),
            ":oc": bool(event.get("ocr_confirmed", False)),
            ":oi": bool(event.get("ocr_influenced", False)),
            ":oh": list(event.get("ocr_matched_hints") or []),
            ":oe": event.get("ocr_engine") or "none",
        },
    )
    log_pipeline_event(
        device_id,
        "parse",
        "succeeded",
        {
            "components": len(components),
            "ocr_confirmed": bool(event.get("ocr_confirmed", False)),
        },
    )

    return {**event, "components": components}
