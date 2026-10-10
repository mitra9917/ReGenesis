#!/usr/bin/env python3
"""Smoke test and verify Issue [M3][I-3.3.3]: Image upload base64 -> S3 -> detection.

Issue: [M3][I-3.3.3] Image upload base64 path stores in S3 and is used by detection
Done when: image_s3_key used (non-empty)

Usage:
  python scripts/smoke_image_upload.py [--image PATH] [--api-url URL] [--region REGION]
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
import boto3

STACK_NAME = "regenesis-dev"
REGION = "ap-south-1"
DEFAULT_FIXTURE = Path(__file__).resolve().parent / ".smoke-fixtures" / "vision-smoke.jpg"


def get_stack_outputs(region: str) -> dict[str, str]:
    cfn = boto3.client("cloudformation", region_name=region)
    resp = cfn.describe_stacks(StackName=STACK_NAME)
    outputs = resp["Stacks"][0].get("Outputs", [])
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def http_post_json(url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, {"raw_error": body}


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify base64 image upload to S3 and detection.")
    parser.add_argument("--image", default=str(DEFAULT_FIXTURE), help="Path to sample image")
    parser.add_argument("--api-url", default="", help="Base API Gateway URL")
    parser.add_argument("--region", default=REGION, help="AWS Region")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = get_stack_outputs(args.region)
    api_url = args.api_url or outputs["ApiUrl"].rstrip("/")
    bucket = outputs.get("AssetsBucketName", "")

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"ERROR: Image fixture not found at {img_path}", file=sys.stderr)
        return 1

    img_bytes = img_path.read_bytes()
    b64_data = base64.b64encode(img_bytes).decode("ascii")
    content_type = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"

    print("\n==================================================================")
    print(" RE:GENESIS [I-3.3.3] Base64 Image Upload -> S3 -> Detection Test")
    print("==================================================================")
    print(f"Image Source: {img_path} ({len(img_bytes)} bytes)")
    print(f"Target API:   {api_url}/devices\n")

    # 1. POST /devices with base64 image
    payload = {
        "device_model_key": "poweredge_r740",
        "image_base64": b64_data,
        "content_type": content_type,
        "serial_hint": "SMOKE-IMG-TEST",
    }
    print("[1/4] Uploading image via POST /devices...")
    status, post_resp = http_post_json(f"{api_url}/devices", payload)
    print(f"      -> HTTP Status: {status}")
    if status != 202:
        print(f"      ERROR: Unexpected response: {post_resp}", file=sys.stderr)
        return 1

    device_id = post_resp.get("device_id")
    execution_arn = post_resp.get("execution_arn")
    image_key = post_resp.get("image_s3_key") or f"images/{device_id}/original.jpg"

    print(f"      -> Device ID:     {device_id}")
    print(f"      -> Execution ARN: {execution_arn}")
    print(f"      -> Image S3 Key:  {image_key}")

    assert device_id, "Missing device_id in response"
    assert execution_arn, "Missing execution_arn in response"
    assert image_key, "image_s3_key must be non-empty"

    # 2. Verify image exists in S3
    print(f"\n[2/4] Verifying image stored in S3 bucket '{bucket}'...")
    s3 = boto3.client("s3", region_name=args.region)
    head_resp = s3.head_object(Bucket=bucket, Key=image_key)
    stored_size = head_resp.get("ContentLength", 0)
    print(f"      -> S3 Object found: s3://{bucket}/{image_key}")
    print(f"      -> Size in S3: {stored_size} bytes (matches original: {stored_size == len(img_bytes)})")
    assert stored_size == len(img_bytes), f"S3 size {stored_size} != original {len(img_bytes)}"

    # 3. Poll Step Functions execution until complete
    print(f"\n[3/4] Polling Step Functions execution status via GET /jobs...")
    poll_url = f"{api_url}/jobs?execution_arn={urllib.parse.quote(execution_arn)}"
    job_status = "RUNNING"
    for attempt in range(1, 20):
        time.sleep(2)
        j_status, j_data = http_get_json(poll_url)
        if j_status == 200:
            job_status = j_data.get("status", "UNKNOWN")
            print(f"      Poll {attempt}: Step Functions status = {job_status}")
            if job_status in ("SUCCEEDED", "FAILED", "TIMED_OUT"):
                break
        else:
            print(f"      Poll {attempt}: HTTP {j_status}")

    assert job_status == "SUCCEEDED", f"Step Functions ended with unexpected status: {job_status}"

    # 4. Confirm device record has image_s3_key non-empty
    print(f"\n[4/4] Confirming device record via GET /devices/{device_id}...")
    d_status, d_data = http_get_json(f"{api_url}/devices/{device_id}")
    assert d_status == 200, f"Expected 200, got {d_status}"

    device = d_data.get("device", {})
    persisted_key = device.get("image_s3_key", "")
    print(f"      -> Persisted image_s3_key: '{persisted_key}'")
    print(f"      -> Device status:         {device.get('status')}")
    print(f"      -> Detection source:      {device.get('detection_source')}")
    print(f"      -> Components detected:   {len(d_data.get('components', []))}")
    assert persisted_key == image_key, f"Device image_s3_key mismatch: '{persisted_key}' != '{image_key}'"
    assert len(persisted_key) > 0, "image_s3_key must not be empty"

    print("\n------------------------------------------------------------------")
    print("ALL CHECKS PASSED: Base64 image stored in S3 and used by detection!")
    print("------------------------------------------------------------------\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
