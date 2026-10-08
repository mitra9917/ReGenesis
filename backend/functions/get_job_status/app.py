import json
import os
from urllib.parse import unquote

import boto3

sfn = boto3.client("stepfunctions")


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    execution_arn = params.get("execution_arn")
    if not execution_arn:
        return _response(400, {"error": "execution_arn query param required"})
    execution_arn = unquote(execution_arn)

    desc = sfn.describe_execution(executionArn=execution_arn)
    out = {
        "execution_arn": execution_arn,
        "status": desc["status"],
        "startDate": desc.get("startDate"),
        "stopDate": desc.get("stopDate"),
    }
    if desc.get("output"):
        try:
            out["output"] = json.loads(desc["output"])
        except json.JSONDecodeError:
            out["output_raw"] = desc["output"]
    return _response(200, out)
