#!/usr/bin/env python3
"""Audit S3 bucket keys against conventions documented in docs/ARCHITECTURE.md.

Issue: [M3][I-3.2.2] Verify S3 key prefixes (images/logs/passports)

Usage:
  python scripts/verify_s3_prefixes.py [--bucket BUCKET_NAME] [--region REGION]
"""

from __future__ import annotations

import argparse
import re
import sys
import boto3

IMAGE_RE = re.compile(r"^images/[a-zA-Z0-9_-]+/(original\.(jpg|jpeg|png)|crops/[a-zA-Z0-9_-]+\.(jpg|jpeg|png))$")
LOG_RE = re.compile(r"^logs/[a-zA-Z0-9_-]+/tests/[a-zA-Z0-9_-]+\.json$")
PASSPORT_RE = re.compile(r"^passports/[a-zA-Z0-9_-]+\.json$")
MODEL_RE = re.compile(r"^models/[a-zA-Z0-9_-]+/.*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit S3 prefixes against ARCHITECTURE.md conventions.")
    parser.add_argument("--bucket", default="regenesis-dev-assetsbucket-xp9zjtzuwy50", help="S3 bucket name")
    parser.add_argument("--region", default="ap-south-1", help="AWS region")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    s3 = boto3.client("s3", region_name=args.region)

    print(f"Auditing S3 bucket '{args.bucket}' in {args.region}...")

    counts = {
        "images": 0,
        "logs": 0,
        "passports": 0,
        "models": 0,
        "other": 0,
    }
    violations: list[str] = []

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=args.bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.startswith("images/"):
                counts["images"] += 1
                if not IMAGE_RE.match(key):
                    violations.append(f"Invalid image key: {key}")
            elif key.startswith("logs/"):
                counts["logs"] += 1
                if not LOG_RE.match(key):
                    violations.append(f"Invalid log key: {key}")
            elif key.startswith("passports/"):
                counts["passports"] += 1
                if not PASSPORT_RE.match(key):
                    violations.append(f"Invalid passport key: {key}")
            elif key.startswith("models/"):
                counts["models"] += 1
            else:
                counts["other"] += 1
                violations.append(f"Unrecognized prefix: {key}")

    print("\n--- S3 Key Audit Results ---")
    print(f"  images/ keys   : {counts['images']}")
    print(f"  logs/ keys     : {counts['logs']}")
    print(f"  passports/ keys: {counts['passports']}")
    print(f"  models/ keys   : {counts['models']}")
    print(f"  other keys     : {counts['other']}")

    if violations:
        print(f"\n[FAILED] Found {len(violations)} prefix violation(s):")
        for v in violations[:10]:
            print(f"  - {v}")
        return 1

    print("\n[OK] SUCCESS: All live S3 keys strictly match docs/ARCHITECTURE.md conventions!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
