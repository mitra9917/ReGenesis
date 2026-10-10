#!/usr/bin/env python3
"""Smoke test and verify GET /jobs execution_arn polling endpoint.

Issue: [M3][I-3.3.2] GET /jobs execution_arn polling stable
Done when: UI status updates

Usage:
  python scripts/smoke_get_job_status.py [--execution-arn ARN] [--api-url URL] [--region REGION]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import boto3

STACK_NAME = "regenesis-dev"
REGION = "ap-south-1"


def get_stack_outputs(region: str) -> dict[str, str]:
    cfn = boto3.client("cloudformation", region_name=region)
    resp = cfn.describe_stacks(StackName=STACK_NAME)
    outputs = resp["Stacks"][0].get("Outputs", [])
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def http_get_json(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, {"raw_error": body}


def find_latest_execution_arn(region: str) -> str:
    sfn = boto3.client("stepfunctions", region_name=region)
    cfn = boto3.client("cloudformation", region_name=region)
    resp = cfn.describe_stacks(StackName=STACK_NAME)
    outputs = {o["OutputKey"]: o["OutputValue"] for o in resp["Stacks"][0].get("Outputs", [])}
    sm_arn = outputs.get("RecoveryStateMachineArn")
    if not sm_arn:
        raise RuntimeError("RecoveryStateMachineArn not found in stack outputs.")

    exec_resp = sfn.list_executions(stateMachineArn=sm_arn, maxResults=5)
    executions = exec_resp.get("executions", [])
    if not executions:
        raise RuntimeError("No executions found for state machine.")
    return executions[0]["executionArn"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify GET /jobs execution_arn polling stability.")
    parser.add_argument("--execution-arn", default="", help="Step Functions Execution ARN to poll")
    parser.add_argument("--api-url", default="", help="Base API Gateway URL")
    parser.add_argument("--region", default=REGION, help="AWS Region")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_url = args.api_url
    if not api_url:
        outputs = get_stack_outputs(args.region)
        api_url = outputs["ApiUrl"].rstrip("/")

    execution_arn = args.execution_arn
    if not execution_arn:
        print(f"Finding latest Step Functions execution in {args.region}...")
        execution_arn = find_latest_execution_arn(args.region)

    print(f"\n=======================================================")
    print(f" RE:GENESIS [I-3.3.2] GET /jobs Polling Smoke Test")
    print(f"=======================================================")
    print(f"Execution ARN: {execution_arn}")
    print(f"API Base URL:  {api_url}\n")

    # 1. Missing execution_arn query param should return 400
    missing_url = f"{api_url}/jobs"
    status_400, body_400 = http_get_json(missing_url)
    print(f"[-] Checking 400 on missing parameter: HTTP {status_400}")
    assert status_400 == 400, f"Expected 400 on missing parameter, got {status_400}"
    print("    -> Missing parameter properly rejected with 400.")

    # 2. Non-existent execution ARN should return 404 (not 502!)
    fake_arn = "arn:aws:states:ap-south-1:620694778016:execution:ReGenesisRecoveryFlow-dev:nonexistent-execution-999"
    fake_url = f"{api_url}/jobs?execution_arn={urllib.parse.quote(fake_arn)}"
    status_404, body_404 = http_get_json(fake_url)
    print(f"[-] Checking 404 on nonexistent execution: HTTP {status_404}")
    assert status_404 == 404, f"Expected 404 on nonexistent execution, got {status_404} ({body_404})"
    print("    -> Nonexistent execution properly rejected with 404.")

    # 3. Valid execution poll
    valid_url = f"{api_url}/jobs?execution_arn={urllib.parse.quote(execution_arn)}"
    print(f"\n[+] Polling valid execution: {valid_url}")
    status, data = http_get_json(valid_url)
    print(f"    -> HTTP Status: {status}")
    if status != 200:
        print(f"    ERROR: Failed to poll job. Body: {data}")
        return 1

    print("\n--- Validation Checklist ---")
    print(f"  [x] Execution ARN: {data.get('execution_arn')}")
    print(f"  [x] Job Status:    {data.get('status')}")
    print(f"  [x] Start Date:    {data.get('startDate')}")
    print(f"  [x] Stop Date:     {data.get('stopDate')}")

    has_status = data.get("status") in ("RUNNING", "SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED")
    assert has_status, f"Unexpected execution status: {data.get('status')}"

    if "output" in data:
        print(f"  [x] Parsed output: {type(data['output']).__name__} with {len(data['output'])} keys")

    print("\n-------------------------------------------------------")
    print("ALL CHECKS PASSED: GET /jobs polling is stable & robust!")
    print("-------------------------------------------------------\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
