import base64
import json
import os

import boto3

from regenesis_common.passport import canonical_passport_bytes, strip_signature

s3 = boto3.client("s3")
kms = boto3.client("kms")
ddb = boto3.resource("dynamodb")


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }


def handler(event, context):
    passport_id = event.get("pathParameters", {}).get("passport_id")
    if not passport_id:
        return _response(400, {"error": "passport_id required"})

    table = ddb.Table(os.environ["PASSPORTS_TABLE"])
    row = table.get_item(Key={"passport_id": passport_id}).get("Item")
    if not row:
        return _response(404, {"error": "not found"})

    obj = s3.get_object(Bucket=os.environ["ASSETS_BUCKET"], Key=row["s3_key"])
    passport = json.loads(obj["Body"].read().decode("utf-8"))
    sig = base64.b64decode(passport.get("signature", ""))
    message = canonical_passport_bytes(passport)

    verify = kms.verify(
        KeyId=os.environ["PASSPORT_KMS_KEY_ID"],
        Message=message,
        MessageType="RAW",
        Signature=sig,
        SigningAlgorithm="RSASSA_PSS_SHA_256",
    )

    return _response(
        200,
        {
            "passport_id": passport_id,
            "valid": verify.get("SignatureValid", False),
            "algorithm": "RSASSA_PSS_SHA_256",
            "status": passport.get("status"),
            "component_type": passport.get("component_type"),
            "payload_preview": strip_signature(passport),
        },
    )
