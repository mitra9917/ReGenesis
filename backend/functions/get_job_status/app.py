import json
import os
from urllib.parse import unquote

import boto3
from botocore.exceptions import ClientError

sfn = boto3.client("stepfunctions")


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {})

    params = event.get("queryStringParameters") or {}
    execution_arn = (
        params.get("execution_arn")
        or params.get("arn")
        or params.get("executionArn")
        or (event.get("pathParameters") or {}).get("execution_arn")
    )
    if not execution_arn:
        return _response(400, {"error": "execution_arn query param required"})

    execution_arn = unquote(str(execution_arn)).strip()

    try:
        desc = sfn.describe_execution(executionArn=execution_arn)
        out = {
            "execution_arn": execution_arn,
            "status": desc["status"],
            "startDate": desc.get("startDate"),
            "stopDate": desc.get("stopDate"),
        }
        if desc.get("error"):
            out["error"] = desc["error"]
        if desc.get("cause"):
            out["cause"] = desc["cause"]

        if desc.get("output"):
            try:
                out["output"] = json.loads(desc["output"])
            except json.JSONDecodeError:
                out["output_raw"] = desc["output"]

        return _response(200, out)

    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        msg = exc.response.get("Error", {}).get("Message", str(exc))
        if code == "ExecutionDoesNotExist":
            return _response(404, {"error": "Execution not found", "execution_arn": execution_arn})
        elif code in ("InvalidArn", "ValidationException"):
            return _response(400, {"error": "Invalid execution ARN", "message": msg, "execution_arn": execution_arn})
        return _response(500, {"error": f"Step Functions error: {code}", "message": msg})
    except Exception as exc:
        return _response(500, {"error": str(exc)})

