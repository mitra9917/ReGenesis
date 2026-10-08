import json
import os

import boto3

from regenesis_common.aws_helpers import log_pipeline_event, utc_now_iso
from regenesis_common.planner import build_disassembly_plan

ddb = boto3.resource("dynamodb")


def handler(event, context):
    device_id = event["device_id"]
    device_model_key = event["device_model_key"]
    components = event.get("components", [])

    plan = build_disassembly_plan(device_model_key, components)
    components_table = ddb.Table(os.environ["COMPONENTS_TABLE"])

    for step in plan["steps"]:
        for comp in step["components"]:
            components_table.update_item(
                Key={"device_id": device_id, "component_id": comp["component_id"]},
                UpdateExpression="SET extraction_step = :e, planned_action = :a",
                ExpressionAttributeValues={
                    ":e": comp["extraction_step"],
                    ":a": comp.get("action", step["action"]),
                },
            )

    devices_table = ddb.Table(os.environ["DEVICES_TABLE"])
    devices_table.update_item(
        Key={"device_id": device_id},
        UpdateExpression="SET disassembly_plan = :p, updated_at = :u",
        ExpressionAttributeValues={":p": json.dumps(plan), ":u": utc_now_iso()},
    )
    log_pipeline_event(device_id, "plan", "succeeded", {"steps": len(plan["steps"])})

    return {**event, "disassembly_plan": plan}
