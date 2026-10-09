import json
import os

import boto3

from regenesis_common.aws_helpers import log_pipeline_event, utc_now_iso
from regenesis_common.impact import compute_impact_summary

ddb = boto3.resource("dynamodb")
cw = boto3.client("cloudwatch")


def handler(event, context):
    device_id = event["device_id"]
    impact = compute_impact_summary(event.get("components", []))

    ddb.Table(os.environ["DEVICES_TABLE"]).update_item(
        Key={"device_id": device_id},
        UpdateExpression="SET impact_summary = :i, #status = :s, updated_at = :u",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":i": json.dumps(impact),
            ":s": "COMPLETED",
            ":u": utc_now_iso(),
        },
    )

    namespace = os.environ.get("METRICS_NAMESPACE", "ReGenesis")
    try:
        cw.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    "MetricName": "ComponentsRecovered",
                    "Value": impact["components_qualified"],
                    "Unit": "Count",
                },
                {
                    "MetricName": "CO2eAvoidedKg",
                    "Value": impact["co2e_avoided_kg"],
                    "Unit": "None",
                },
            ],
        )
        if event.get("detection_source") == "catalog-assisted":
            cw.put_metric_data(
                Namespace=namespace,
                MetricData=[{"MetricName": "DetectionFallbackUsed", "Value": 1, "Unit": "Count"}],
            )
    except Exception:
        pass

    log_pipeline_event(device_id, "impact", "succeeded", impact)
    return {**event, "impact_summary": impact, "status": "COMPLETED"}
