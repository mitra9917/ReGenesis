import base64
import json
import os
import uuid
from decimal import Decimal

import boto3

from regenesis_common.aws_helpers import log_pipeline_event, utc_now_iso

s3 = boto3.client("s3")
sfn = boto3.client("stepfunctions")
ddb = boto3.resource("dynamodb")


def _table():
    return ddb.Table(os.environ["DEVICES_TABLE"])


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def handler(event, context):
    try:
        if event.get("httpMethod") == "OPTIONS":
            return _response(200, {})

        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        payload = json.loads(body) if isinstance(body, str) else body

        device_model_key = payload.get("device_model_key", "poweredge_r740")
        device_id = str(uuid.uuid4())
        bucket = os.environ["ASSETS_BUCKET"]
        content_type = payload.get("content_type", "image/jpeg")
        ext = "jpg" if "jpeg" in content_type else "png"
        image_key = f"images/{device_id}/original.{ext}"

        if payload.get("image_base64"):
            raw = base64.b64decode(payload["image_base64"])
            s3.put_object(Bucket=bucket, Key=image_key, Body=raw, ContentType=content_type)

        now = utc_now_iso()
        item = {
            "device_id": device_id,
            "device_model_key": device_model_key,
            "status": "RECOVERING",
            "image_s3_key": image_key if payload.get("image_base64") else "",
            "serial_hint": payload.get("serial_hint", ""),
            "created_at": now,
            "updated_at": now,
        }
        _table().put_item(Item=item)
        log_pipeline_event(device_id, "ingest", "succeeded", {"image_key": image_key})

        sf_input = {
            "device_id": device_id,
            "device_model_key": device_model_key,
            "image_s3_key": image_key,
            "bucket": bucket,
        }
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

        return _response(
            202,
            {
                "device_id": device_id,
                "execution_arn": execution["executionArn"],
                "status": "RECOVERY_STARTED",
            },
        )
    except Exception as exc:
        return _response(500, {"error": str(exc)})
