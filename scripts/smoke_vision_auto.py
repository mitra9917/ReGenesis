#!/usr/bin/env python3
"""I-3.1.1 live check: DETECTION_MODE=auto → detection_source=vision.

Requires the SageMaker endpoint to be InService (this starts billing).

  python scripts/smoke_vision_auto.py --image path/to/hdd-or-nic.jpg
  python scripts/smoke_vision_auto.py --image photo.jpg --e2e

Default: invoke the endpoint and apply the same merge/label rules as Lambda.
--e2e also POSTs /devices and polls until detection_source is persisted.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.detection import (  # noqa: E402
    api_detection_source,
    merge_vision_with_catalog_gaps,
    vision_detections_usable,
)

DEFAULT_ENDPOINT = "regenesis-yolo-dev"
DEFAULT_REGION = "ap-south-1"
DEFAULT_API = "https://roz4wu5br7.execute-api.ap-south-1.amazonaws.com/Prod"
DEFAULT_MODEL = "poweredge_r740"


def _die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def endpoint_status(sm, name: str) -> str:
    try:
        return sm.describe_endpoint(EndpointName=name)["EndpointStatus"]
    except sm.exceptions.ClientError as exc:
        if exc.response["Error"]["Code"] in {"ValidationException", "ResourceNotFound"}:
            return "Missing"
        raise


def invoke_endpoint(runtime, name: str, image_bytes: bytes) -> list:
    resp = runtime.invoke_endpoint(
        EndpointName=name,
        ContentType="application/x-image",
        Body=image_bytes,
    )
    payload = json.loads(resp["Body"].read().decode("utf-8"))
    if isinstance(payload, dict):
        return payload.get("detections", [])
    if isinstance(payload, list):
        return payload
    return []


def post_device(api_url: str, model_key: str, image_bytes: bytes, content_type: str) -> dict:
    body = json.dumps(
        {
            "device_model_key": model_key,
            "image_base64": base64.b64encode(image_bytes).decode("ascii"),
            "content_type": content_type,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/devices",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_device(api_url: str, device_id: str, execution_arn: str, timeout_s: int) -> dict:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        job = get_json(
            f"{api_url.rstrip('/')}/jobs?execution_arn={urllib.parse.quote(execution_arn, safe='')}"
        )
        device_wrap = get_json(f"{api_url.rstrip('/')}/devices/{device_id}")
        last = device_wrap
        status = job.get("status") or device_wrap.get("device", {}).get("status")
        source = (device_wrap.get("device") or {}).get("detection_source")
        print(f"  job={status} detection_source={source}")
        if status in {"SUCCEEDED", "COMPLETED", "FAILED", "TIMED_OUT", "ABORTED"}:
            return device_wrap
        if source:
            return device_wrap
        time.sleep(4)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(description="I-3.1.1 vision smoke (live SageMaker)")
    parser.add_argument("--image", required=True, help="HDD/NIC/e-waste interior JPEG or PNG")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--model-key", default=DEFAULT_MODEL)
    parser.add_argument("--min-confidence", type=float, default=0.45)
    parser.add_argument("--e2e", action="store_true", help="Also POST /devices and poll the API")
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        _die(f"image not found: {image_path}")
    image_bytes = image_path.read_bytes()
    content_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"

    sm = boto3.client("sagemaker", region_name=args.region)
    status = endpoint_status(sm, args.endpoint)
    print(f"Endpoint {args.endpoint}: {status}")
    if status != "InService":
        _die(
            "Endpoint is not InService. This starts billing:\n"
            "  aws sagemaker create-endpoint --endpoint-name regenesis-yolo-dev "
            "--endpoint-config-name regenesis-yolo-config-m5l-v2 --region ap-south-1\n"
            "Then wait until Status=InService (5–15 min) and re-run this script.\n"
            "Turn it off afterwards: aws sagemaker delete-endpoint "
            "--endpoint-name regenesis-yolo-dev --region ap-south-1"
        )

    runtime = boto3.client("sagemaker-runtime", region_name=args.region)
    print(f"Invoking {args.endpoint} with {image_path.name} ({len(image_bytes)} bytes)…")
    vision = invoke_endpoint(runtime, args.endpoint, image_bytes)
    print(json.dumps({"detections": vision}, indent=2))

    if not vision_detections_usable(vision, args.min_confidence):
        _die(
            "SageMaker returned no usable detections (empty or low confidence). "
            "Use an HDD/NIC/e-waste photo similar to the training set."
        )

    merged = merge_vision_with_catalog_gaps(args.model_key, vision, min_confidence=args.min_confidence)
    source = api_detection_source(merged["detection_source"])
    print(f"merge_source={merged['detection_source']} api_detection_source={source}")
    if source != "vision":
        _die(f"expected api_detection_source=vision, got {source}")
    print("OK: live endpoint path labels detection_source=vision")

    if not args.e2e:
        return 0

    print(f"POST {args.api_url.rstrip('/')}/devices …")
    try:
        created = post_device(args.api_url, args.model_key, image_bytes, content_type)
    except urllib.error.HTTPError as exc:
        _die(f"POST /devices failed: {exc.code} {exc.read().decode('utf-8', errors='replace')}")
    device_id = created.get("device_id")
    execution_arn = created.get("execution_arn")
    print(f"device_id={device_id}")
    print(f"execution_arn={execution_arn}")
    if not device_id or not execution_arn:
        _die("API did not return device_id + execution_arn")

    result = poll_device(args.api_url, device_id, execution_arn, args.timeout)
    persisted = (result.get("device") or {}).get("detection_source")
    print(f"persisted detection_source={persisted}")
    if persisted != "vision":
        _die(
            f"pipeline stored detection_source={persisted!r}, expected 'vision'. "
            "Redeploy SAM so InvokeDetection maps hybrid → vision, then retry --e2e."
        )
    print("OK: I-3.1.1 done — GET /devices reports detection_source=vision")
    return 0


if __name__ == "__main__":
    sys.exit(main())
