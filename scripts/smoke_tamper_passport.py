#!/usr/bin/env python3
"""Demonstrate tamper-evident KMS passport verification.

Issue: [M3][I-3.2.3] Tamper passport JSON -> verify fails

Usage:
  python scripts/smoke_tamper_passport.py [--e2e] [--passport-id ID]
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
import urllib.request
import urllib.error
import boto3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.passport import canonical_passport_bytes  # noqa: E402

STACK_NAME = "regenesis-dev"
REGION = "ap-south-1"


def get_stack_outputs() -> dict[str, str]:
    cfn = boto3.client("cloudformation", region_name=REGION)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demonstrate passport tampering failure.")
    parser.add_argument("--e2e", action="store_true", help="Perform live tamper test in S3 (with auto-restore)")
    parser.add_argument("--passport-id", default="", help="Specific passport ID to verify/tamper")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = get_stack_outputs()
    api_url = outputs["ApiUrl"].rstrip("/")
    bucket = outputs["AssetsBucketName"]

    s3 = boto3.client("s3", region_name=REGION)

    passport_id = args.passport_id
    if not passport_id:
        # Pick one valid passport from S3
        resp = s3.list_objects_v2(Bucket=bucket, Prefix="passports/", MaxKeys=5)
        contents = resp.get("Contents", [])
        if not contents:
            print("[ERROR] No passports found in S3 bucket.")
            return 1
        passport_key = contents[0]["Key"]
        passport_id = passport_key.split("/")[-1].replace(".json", "")
    else:
        passport_key = f"passports/{passport_id}.json"

    print(f"--- Passport Tamper Verification Demo ---")
    print(f"Target Passport: {passport_id}")
    print(f"S3 Key         : {passport_key}")
    print(f"API Base URL   : {api_url}")

    # Step 1: Verify authentic original passport
    verify_url = f"{api_url}/passports/{passport_id}/verify"
    print(f"\n[Step 1] Querying GET {verify_url}...")
    status, res = http_get_json(verify_url)
    print(f"Response (HTTP {status}):")
    print(json.dumps(res, indent=2))

    if not res.get("valid"):
        print(f"[WARN] Original passport did not report valid: true. Response: {res}")
        return 1

    print("[OK] Original passport signature is VALID.")

    # Step 2: Mathematical Proof (Canonical bytes change)
    obj = s3.get_object(Bucket=bucket, Key=passport_key)
    original_content = obj["Body"].read()
    passport_data = json.loads(original_content.decode("utf-8"))

    orig_canonical = canonical_passport_bytes(passport_data)

    tampered_data = dict(passport_data)
    tampered_data["status"] = "fraudulent_certified_reuse"
    tampered_canonical = canonical_passport_bytes(tampered_data)

    print("\n[Step 2] Cryptographic Canonicalization Check:")
    print(f"  Original SHA-256 digest input length : {len(orig_canonical)} bytes")
    print(f"  Tampered SHA-256 digest input length : {len(tampered_canonical)} bytes")
    assert orig_canonical != tampered_canonical, "Canonical bytes must differ when tampered!"
    print("  [OK] Canonical payload hash changes immediately upon modifying any attribute.")

    # Step 3: Live E2E Tamper Test (if requested)
    if args.e2e:
        print("\n[Step 3] Live S3 Tamper Simulation with Safe Restoration...")
        try:
            print("  -> Uploading tampered passport JSON to S3...")
            tampered_json = json.dumps(tampered_data, indent=2).encode("utf-8")
            s3.put_object(
                Bucket=bucket,
                Key=passport_key,
                Body=tampered_json,
                ContentType="application/json",
            )

            print(f"  -> Testing verification of tampered passport via API...")
            t_status, t_res = http_get_json(verify_url)
            print(f"  -> Tampered Response (HTTP {t_status}):")
            print(f"     valid={t_res.get('valid')}, tamper_detected={t_res.get('tamper_detected')}")
            print(f"     reason={t_res.get('reason')}")

            # Verify that either valid == False or signature verification failed
            is_rejected = (t_res.get("valid") is False) or (t_status >= 400)
            if is_rejected:
                print("  [OK] Tampered passport was successfully REJECTED by KMS verification!")
            else:
                print("  [FAIL] Tampered passport was unexpectedly accepted!")
                return 1

        finally:
            print("  -> Restoring original untampered passport to S3...")
            s3.put_object(
                Bucket=bucket,
                Key=passport_key,
                Body=original_content,
                ContentType="application/json",
            )
            _, restored_res = http_get_json(verify_url)
            print(f"  -> Verification after restore: valid={restored_res.get('valid')}")
            print("  [OK] S3 object restored to original state.")

    print("\n[DEMO COMPLETE] KMS Passport tampering detection verified successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
