import json
import os

import boto3

s3 = boto3.client("s3")
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

    row = ddb.Table(os.environ["PASSPORTS_TABLE"]).get_item(Key={"passport_id": passport_id}).get("Item")
    if not row:
        return _response(404, {"error": "not found"})

    obj = s3.get_object(Bucket=os.environ["ASSETS_BUCKET"], Key=row["s3_key"])
    passport = json.loads(obj["Body"].read().decode("utf-8"))
    return _response(200, passport)
