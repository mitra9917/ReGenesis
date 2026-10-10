#!/usr/bin/env python3
"""Smoke test and verify GET /devices/{id} API endpoint.

Issue: [M3][I-3.3.1] GET /devices/{id} returns plan + audit + impact
Done when: Matches UI needs

Usage:
  python scripts/smoke_get_device.py [--device-id ID] [--api-url URL] [--region REGION]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
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


def find_latest_device_id(region: str) -> str:
    ddb = boto3.client("dynamodb", region_name=region)
    # Find DevicesTable
    tables = ddb.list_tables()["TableNames"]
    dev_tables = [t for t in tables if "DevicesTable" in t]
    if not dev_tables:
        raise RuntimeError("No DevicesTable found in region.")
    table_name = dev_tables[0]

    resp = ddb.scan(TableName=table_name, Limit=10)
    items = resp.get("Items", [])
    if not items:
        raise RuntimeError(f"No devices found in table {table_name}")

    # Prefer COMPLETED device
    completed = [i for i in items if i.get("status", {}).get("S") == "COMPLETED"]
    target = completed[0] if completed else items[0]
    return target["device_id"]["S"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify GET /devices/{id} returns plan + audit + impact.")
    parser.add_argument("--device-id", default="", help="Device ID to query (default: scans table for latest)")
    parser.add_argument("--api-url", default="", help="Base API Gateway URL")
    parser.add_argument("--region", default=REGION, help="AWS Region")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_url = args.api_url
    if not api_url:
        outputs = get_stack_outputs(args.region)
        api_url = outputs["ApiUrl"].rstrip("/")

    device_id = args.device_id
    if not device_id:
        print(f"Scanning DynamoDB for latest device in {args.region}...")
        device_id = find_latest_device_id(args.region)

    endpoint_url = f"{api_url}/devices/{device_id}"
    print(f"\n==================================================")
    print(f" RE:GENESIS [I-3.3.1] GET /devices/{{id}} Smoke Test")
    print(f"==================================================")
    print(f"Target URL: {endpoint_url}\n")

    # 1. Test 404 with nonexistent ID
    nonexistent_url = f"{api_url}/devices/00000000-0000-0000-0000-000000000000"
    status_404, body_404 = http_get_json(nonexistent_url)
    print(f"[-] Checking 404 handling on nonexistent ID: HTTP {status_404}")
    assert status_404 == 404, f"Expected 404 on nonexistent ID, got {status_404}"
    print("    -> Nonexistent ID properly rejected with 404.")

    # 2. Test live device query
    print(f"\n[+] Fetching device '{device_id}'...")
    status, data = http_get_json(endpoint_url)
    print(f"    -> HTTP Status: {status}")
    if status != 200:
        print(f"    ERROR: Failed to fetch device. Body: {data}")
        return 1

    device = data.get("device", {})
    plan = data.get("plan") or device.get("disassembly_plan")
    audit = data.get("audit") or device.get("completeness_audit")
    impact = data.get("impact") or device.get("impact_summary")
    components = data.get("components", [])
    passports = data.get("passports", [])

    print("\n--- Validation Checklist ---")

    # Verify device record
    print(f"  [x] Device Model: {device.get('device_model_key')}")
    print(f"  [x] Device Status: {device.get('status')}")
    print(f"  [x] Detection Source: {device.get('detection_source', 'N/A')}")

    # Verify Disassembly Plan
    has_plan = plan is not None and "steps" in plan
    print(f"  [{'x' if has_plan else ' '}] Disassembly Plan (RVS): "
          f"{len(plan.get('steps', []))} steps found" if has_plan else "  [ ] Disassembly Plan missing!")
    assert has_plan, "Disassembly plan is missing or malformed"

    # Verify Completeness Audit
    has_audit = audit is not None and "score" in audit
    print(f"  [{'x' if has_audit else ' '}] Completeness Audit: "
          f"Score={audit.get('score')}, Gaps={len(audit.get('gaps', []))}" if has_audit else "  [ ] Completeness Audit missing!")
    assert has_audit, "Completeness audit is missing or malformed"

    # Verify Environmental Impact
    has_impact = impact is not None and "co2e_avoided_kg" in impact
    print(f"  [{'x' if has_impact else ' '}] Impact Summary: "
          f"CO2e Avoided={impact.get('co2e_avoided_kg')} kg, Diverted={impact.get('mass_diverted_kg')} kg" if has_impact else "  [ ] Impact summary missing!")
    assert has_impact, "Impact summary is missing or malformed"

    # Verify Components & Passports
    print(f"  [x] Components list: {len(components)} items")
    print(f"  [x] Passports list: {len(passports)} items")

    print("\n--------------------------------------------------")
    print("ALL CHECKS PASSED: GET /devices/{id} matches UI needs!")
    print("--------------------------------------------------\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
