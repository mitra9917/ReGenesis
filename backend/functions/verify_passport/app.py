import base64
import json
import os

import boto3

from botocore.exceptions import ClientError

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

    is_valid = False
    verification_error = None
    try:
        verify = kms.verify(
            KeyId=os.environ["PASSPORT_KMS_KEY_ID"],
            Message=message,
            MessageType="RAW",
            Signature=sig,
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        is_valid = bool(verify.get("SignatureValid", False))
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("KMSInvalidSignatureException", "InvalidSignatureException"):
            is_valid = False
            verification_error = "Signature verification failed: document content has been tampered with or signature does not match."
        else:
            raise

    resp_body = {
        "passport_id": passport_id,
        "valid": is_valid,
        "algorithm": "RSASSA_PSS_SHA_256",
        "status": passport.get("status"),
        "component_type": passport.get("component_type"),
        "payload_preview": strip_signature(passport),
    }
    if verification_error:
        resp_body["tamper_detected"] = True
        resp_body["reason"] = verification_error

    return _response(200, resp_body)
