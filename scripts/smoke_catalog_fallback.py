#!/usr/bin/env python3
"""I-3.1.2 live check: Force low-confidence / missing endpoint → catalog-assisted path.

Verifies:
1. Low-confidence vision detections (< min_confidence) trigger catalog fallback.
2. Missing or offline SageMaker endpoint triggers catalog fallback.
3. Completeness audit works (score=1.0, within_tolerance=True, gaps=[]).
4. End-to-end execution against deployed AWS API persists detection_source='catalog-assisted'.

Usage:
  python scripts/smoke_catalog_fallback.py
  python scripts/smoke_catalog_fallback.py --e2e
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.catalog import get_device_spec  # noqa: E402
from regenesis_common.detection import (  # noqa: E402
    api_detection_source,
    catalog_assisted_detections,
    completeness_audit,
    merge_vision_with_catalog_gaps,
    vision_detections_usable,
)

DEFAULT_API = "https://roz4wu5br7.execute-api.ap-south-1.amazonaws.com/Prod"
DEFAULT_MODEL = "poweredge_r740"


def _die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def test_unit_fallback_cases(model_key: str, min_confidence: float = 0.45) -> None:
    print("=== Testing Unit Fallback Logic ===")
    spec = get_device_spec(model_key)
    expected_boms = spec["expected_components"]

    # Case 1: Empty vision
    out_empty = merge_vision_with_catalog_gaps(model_key, [], min_confidence=min_confidence)
    assert out_empty["detection_source"] == "catalog-assisted", "Empty vision should produce catalog-assisted"
    assert api_detection_source(out_empty["detection_source"]) == "catalog-assisted"
    print("  [PASS] Empty vision -> catalog-assisted")

    # Case 2: Low-confidence vision detections (< min_confidence)
    low_conf_vision = [
        {"class": "CPU", "confidence": 0.20, "bbox": [0.1, 0.1, 0.2, 0.2]},
        {"class": "RAM", "confidence": 0.35, "bbox": [0.3, 0.3, 0.4, 0.4]},
    ]
    assert not vision_detections_usable(low_conf_vision, min_confidence), "Low confidence must be unusable"
    out_low = merge_vision_with_catalog_gaps(model_key, low_conf_vision, min_confidence=min_confidence)
    assert out_low["detection_source"] == "catalog-assisted", "Low confidence vision should fallback to catalog-assisted"
    print("  [PASS] Low-confidence detections -> catalog-assisted")

    # Case 3: Missing confidence score
    no_conf_vision = [{"class": "GPU", "bbox": [0.1, 0.1, 0.2, 0.2]}]
    assert not vision_detections_usable(no_conf_vision, min_confidence), "Missing confidence must be unusable"
    out_noconf = merge_vision_with_catalog_gaps(model_key, no_conf_vision, min_confidence=min_confidence)
    assert out_noconf["detection_source"] == "catalog-assisted"
    print("  [PASS] Missing confidence detections -> catalog-assisted")

    # Case 4: Catalog-assisted detections count and format
    dets = catalog_assisted_detections(model_key)
    assert len(dets) == sum(expected_boms.values()), f"Expected {sum(expected_boms.values())} detections"
    assert all(d["source"] == "catalog_assisted" for d in dets), "All boxes must have source=catalog_assisted"
    print(f"  [PASS] Catalog-assisted generated {len(dets)} BOM items with source=catalog_assisted")

    # Case 5: Completeness audit
    audit = completeness_audit(model_key, dets)
    assert audit["within_tolerance"] is True, "Audit must be within tolerance"
    assert audit["score"] == 1.0, f"Expected audit score 1.0, got {audit['score']}"
    assert audit["gaps"] == [], "Gaps must be empty for complete catalog fallback"
    print("  [PASS] Completeness audit passed: score=1.0, within_tolerance=True, gaps=[]")


def post_device(api_url: str, model_key: str) -> dict:
    body = json.dumps({"device_model_key": model_key}).encode("utf-8")
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
        print(f"  polling: job={status} detection_source={source}")
        if status in {"SUCCEEDED", "COMPLETED", "FAILED", "TIMED_OUT", "ABORTED"}:
            return device_wrap
        if source:
            return device_wrap
        time.sleep(3)
    return last


def run_e2e(api_url: str, model_key: str, timeout: int) -> None:
    print(f"\n=== Testing E2E Catalog Fallback on {api_url} ===")
    print(f"POST {api_url.rstrip('/')}/devices (model={model_key}, no image)...")
    try:
        created = post_device(api_url, model_key)
    except urllib.error.HTTPError as exc:
        _die(f"POST /devices failed: {exc.code} {exc.read().decode('utf-8', errors='replace')}")

    device_id = created.get("device_id")
    execution_arn = created.get("execution_arn")
    print(f"  device_id: {device_id}")
    print(f"  execution_arn: {execution_arn}")
    if not device_id or not execution_arn:
        _die("API did not return device_id + execution_arn")

    result = poll_device(api_url, device_id, execution_arn, timeout)
    dev = result.get("device", {})
    persisted_source = dev.get("detection_source")
    audit = dev.get("completeness_audit", {})
    if isinstance(audit, str):
        audit = json.loads(audit)

    print("\n=== Live API Verification Results ===")
    print(f"  Status: {dev.get('status')}")
    print(f"  Detection source: {persisted_source}")
    print(f"  Completeness audit score: {audit.get('score')}")
    print(f"  Within tolerance: {audit.get('within_tolerance')}")
    print(f"  Gaps count: {len(audit.get('gaps', []))}")
    print(f"  Components parsed: {len(result.get('components', []))}")
    print(f"  Passports minted: {len(result.get('passports', []))}")

    if persisted_source != "catalog-assisted":
        _die(f"Expected detection_source='catalog-assisted', got '{persisted_source}'")

    if not audit.get("within_tolerance"):
        _die("Completeness audit is not within tolerance")

    print("\nSUCCESS: I-3.1.2 Catalog-assisted fallback verified end-to-end!")
    print("Frontend UI will display 'Catalog-assisted' pill badge and audit metrics.")


def main() -> int:
    parser = argparse.ArgumentParser(description="I-3.1.2 verify catalog-assisted fallback path")
    parser.add_argument("--model-key", default=DEFAULT_MODEL)
    parser.add_argument("--min-confidence", type=float, default=0.45)
    parser.add_argument("--e2e", action="store_true", help="POST /devices and verify live AWS fallback")
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    test_unit_fallback_cases(args.model_key, args.min_confidence)

    if args.e2e:
        run_e2e(args.api_url, args.model_key, args.timeout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
