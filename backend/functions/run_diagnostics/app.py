import json
import os

import boto3

from regenesis_common.aws_helpers import log_pipeline_event, utc_now_iso
from regenesis_common.diagnostics import run_component_diagnostics

ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")


def handler(event, context):
    device_id = event["device_id"]
    bucket = event.get("bucket") or os.environ["ASSETS_BUCKET"]
    components_table = ddb.Table(os.environ["COMPONENTS_TABLE"])

    tested = []
    for comp in event.get("components", []):
        result = run_component_diagnostics(comp)
        status = "qualified" if result["status"] == "qualified_for_reuse" else "failed"
        log_key = f"logs/{device_id}/tests/{comp['component_id']}.json"
        s3.put_object(
            Bucket=bucket,
            Key=log_key,
            Body=json.dumps(result).encode("utf-8"),
            ContentType="application/json",
        )
        components_table.update_item(
            Key={"device_id": device_id, "component_id": comp["component_id"]},
            UpdateExpression="SET #status = :s, test_results = :t, test_log_s3_key = :k, health_score = :h, diagnostics_grade = :g",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":s": status,
                ":t": json.dumps(result["test_results"]),
                ":k": log_key,
                ":h": str(result["health_score"]),
                ":g": result.get("diagnostics_grade", "Grade B"),
            },
        )
        tested.append({**comp, **result, "status": status})

    log_pipeline_event(device_id, "test", "succeeded", {"tested": len(tested)})
    return {**event, "components": tested, "updated_at": utc_now_iso()}
