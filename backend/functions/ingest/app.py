import base64
import json
import os
import uuid
from decimal import Decimal

import boto3

from regenesis_common.aws_helpers import api_gateway_response, log_pipeline_event, utc_now_iso

s3 = boto3.client("s3")
sfn = boto3.client("stepfunctions")
ddb = boto3.resource("dynamodb")


def _table():
    return ddb.Table(os.environ["DEVICES_TABLE"])


def handler(event, context):
    try:
        if event.get("httpMethod") == "OPTIONS":
            return api_gateway_response(200, {})

        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        payload = json.loads(body) if isinstance(body, str) else body

        device_model_key = payload.get("device_model_key", "poweredge_r740")
        device_id = str(uuid.uuid4())
        bucket = os.environ["ASSETS_BUCKET"]
        content_type = payload.get("content_type", "image/jpeg")
        ext = "png" if "png" in content_type.lower() else "jpg"
        b64_img = payload.get("image_base64") or payload.get("image")
        has_image = bool(b64_img)
        image_key = f"images/{device_id}/original.{ext}" if has_image else ""

        if has_image:
            if isinstance(b64_img, str) and "," in b64_img:
                b64_img = b64_img.split(",", 1)[1]
            raw = base64.b64decode(b64_img)
            s3.put_object(Bucket=bucket, Key=image_key, Body=raw, ContentType=content_type)

        plate_text = (payload.get("plate_text") or payload.get("ocr_text") or "").strip()

        now = utc_now_iso()
        item = {
            "device_id": device_id,
            "device_model_key": device_model_key,
            "status": "RECOVERING",
            "image_s3_key": image_key,
            "serial_hint": payload.get("serial_hint", ""),
            "created_at": now,
            "updated_at": now,
        }
        if plate_text:
            item["plate_text"] = plate_text
        _table().put_item(Item=item)
        log_pipeline_event(
            device_id,
            "ingest",
            "succeeded",
            {"image_key": image_key, "has_plate_text": bool(plate_text)},
        )

        sf_input = {
            "device_id": device_id,
            "device_model_key": device_model_key,
            "image_s3_key": image_key,
            "bucket": bucket,
        }
        if plate_text:
            sf_input["plate_text"] = plate_text
        execution = sfn.start_execution(
            stateMachineArn=os.environ["RECOVERY_STATE_MACHINE_ARN"],
            name=f"rec-{device_id[:8]}-{uuid.uuid4().hex[:6]}",
            input=json.dumps(sf_input),
        )
        _table().update_item(
            Key={"device_id": device_id},
            UpdateExpression="SET execution_arn = :a, updated_at = :u",
            ExpressionAttributeValues={":a": execution["executionArn"], ":u": now},
        )

        return api_gateway_response(
            202,
            {
                "device_id": device_id,
                "execution_arn": execution["executionArn"],
                "status": "RECOVERY_STARTED",
                "image_s3_key": image_key,
            },
        )
    except Exception as exc:
        target_dev = device_id if "device_id" in locals() and device_id else "unknown"
        log_pipeline_event(target_dev, "ingest", "failed", {"error": str(exc)})
        return api_gateway_response(500, {"error": str(exc)})

