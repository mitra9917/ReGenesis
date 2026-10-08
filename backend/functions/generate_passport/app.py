import base64
import json
import os
import uuid

import boto3

from regenesis_common.aws_helpers import log_pipeline_event, utc_now_iso
from regenesis_common.passport import canonical_passport_bytes

kms = boto3.client("kms")
s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")


def handler(event, context):
    device_id = event["device_id"]
    bucket = event.get("bucket") or os.environ["ASSETS_BUCKET"]
    key_id = os.environ["PASSPORT_KMS_KEY_ID"]
    passports_table = ddb.Table(os.environ["PASSPORTS_TABLE"])
    components_table = ddb.Table(os.environ["COMPONENTS_TABLE"])

    passports = []
    for comp in event.get("components", []):
        if comp.get("status") not in ("qualified", "qualified_for_reuse"):
            continue

        passport_id = str(uuid.uuid4())
        body = {
            "passport_id": passport_id,
            "component_id": comp["component_id"],
            "device_id": device_id,
            "timestamp": utc_now_iso(),
            "component_type": comp.get("comp_type"),
            "manufacturer": comp.get("manufacturer", "Unknown"),
            "model": comp.get("model", comp.get("comp_type", "")),
            "serial": comp.get("serial", ""),
            "extraction_step": comp.get("extraction_step", 0),
            "tests": comp.get("test_results", {}),
            "status": "qualified_for_reuse",
            "notes": "All simulated diagnostics passed. Reuse recommended.",
            "detection_source": event.get("detection_source", ""),
        }
        digest = canonical_passport_bytes(body)
        sign_resp = kms.sign(
            KeyId=key_id,
            Message=digest,
            MessageType="RAW",
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        body["signature"] = base64.b64encode(sign_resp["Signature"]).decode("ascii")
        s3_key = f"passports/{passport_id}.json"
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json.dumps(body, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        passports_table.put_item(
            Item={
                "passport_id": passport_id,
                "device_id": device_id,
                "component_id": comp["component_id"],
                "s3_key": s3_key,
                "status": "qualified_for_reuse",
                "created_at": utc_now_iso(),
            }
        )
        components_table.update_item(
            Key={"device_id": device_id, "component_id": comp["component_id"]},
            UpdateExpression="SET passport_id = :p, status = :s",
            ExpressionAttributeValues={":p": passport_id, ":s": "qualified"},
        )
        passports.append(body)

    log_pipeline_event(device_id, "passport", "succeeded", {"count": len(passports)})
    return {**event, "passports": passports}
