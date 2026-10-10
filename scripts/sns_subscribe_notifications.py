#!/usr/bin/env python3
"""Manage and test optional SNS subscriptions for recovery completion notifications.

Issue: [M3][I-3.2.4] SNS job-complete notification

Usage:
  python scripts/sns_subscribe_notifications.py --status
  python scripts/sns_subscribe_notifications.py --email operator@example.com
  python scripts/sns_subscribe_notifications.py --publish-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import boto3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

REGION = "ap-south-1"
TOPIC_NAME = "regenesis-recovery-complete-dev"


def get_topic_arn(sns_client) -> str:
    topics = sns_client.list_topics().get("Topics", [])
    for t in topics:
        if TOPIC_NAME in t["TopicArn"]:
            return t["TopicArn"]
    raise RuntimeError(f"SNS Topic '{TOPIC_NAME}' not found in region {REGION}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage optional SNS recovery completion subscriptions.")
    parser.add_argument("--status", action="store_true", help="List current topic subscriptions")
    parser.add_argument("--email", default="", help="Subscribe an email address to recovery complete notifications")
    parser.add_argument("--publish-test", action="store_true", help="Publish a simulated recovery completion event")
    parser.add_argument("--unsubscribe", default="", help="SubscriptionArn to unsubscribe")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sns = boto3.client("sns", region_name=REGION)

    try:
        topic_arn = get_topic_arn(sns)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

    print(f"--- RE:GENESIS SNS Notification Manager ---")
    print(f"Topic ARN: {topic_arn}")

    if args.email:
        print(f"\nSubscribing email '{args.email}' to topic...")
        resp = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=args.email,
            ReturnSubscriptionArn=True,
        )
        sub_arn = resp.get("SubscriptionArn", "")
        print(f"[OK] Subscription request sent!")
        print(f"     Status: PendingConfirmation")
        print(f"     AWS sent a confirmation link to: {args.email}")
        print(f"     Click the confirmation link in the email to activate alerts.")
        return 0

    if args.unsubscribe:
        print(f"\nUnsubscribing {args.unsubscribe}...")
        sns.unsubscribe(SubscriptionArn=args.unsubscribe)
        print("[OK] Unsubscribed successfully.")
        return 0

    if args.publish_test:
        print("\nPublishing simulated recovery complete event...")
        payload = {
            "event": "RECOVERY_COMPLETE",
            "device_id": "test-device-r740",
            "device_model_key": "poweredge_r740",
            "status": "COMPLETED",
            "components_recovered": 7,
            "passports_issued": 7,
            "impact_summary": {
                "co2e_avoided_kg": 42.5,
                "e_waste_diverted_kg": 18.2,
            },
        }
        res = sns.publish(
            TopicArn=topic_arn,
            Subject="[RE:GENESIS] Device Recovery Complete - Dell PowerEdge R740",
            Message=json.dumps(payload, indent=2),
        )
        print(f"[OK] Notification published successfully! MessageId: {res.get('MessageId')}")
        return 0

    # Default: Show status and subscriptions
    print("\nListing existing subscriptions:")
    subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn).get("Subscriptions", [])
    if not subs:
        print("  (No subscriptions currently attached - notifications are optional)")
        print("\nTo subscribe an operator or ITAD email alert, run:")
        print("  python scripts/sns_subscribe_notifications.py --email your-email@example.com")
    else:
        for s in subs:
            print(f"  - Protocol: {s['Protocol']}, Endpoint: {s['Endpoint']}, Status: {s['SubscriptionArn']}")

    print("\nTo publish a test alert, run:")
    print("  python scripts/sns_subscribe_notifications.py --publish-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
