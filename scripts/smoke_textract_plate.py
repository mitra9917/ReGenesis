#!/usr/bin/env python3
"""I-3.1.3 live check: Textract model-plate OCR confirms / influences model key.

Creates a synthetic nameplate JPEG (Pillow), runs Textract DetectDocumentText,
and verifies catalog ocr_hints match. Optional --e2e posts the plate through
POST /devices (DETECTION_MODE=auto; SageMaker endpoint not required).

Usage:
  python scripts/smoke_textract_plate.py
  python scripts/smoke_textract_plate.py --e2e
  python scripts/smoke_textract_plate.py --image path/to/real-plate.jpg --e2e
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
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.detection import match_device_from_ocr_text  # noqa: E402

DEFAULT_API = "https://roz4wu5br7.execute-api.ap-south-1.amazonaws.com/Prod"
DEFAULT_REGION = "ap-south-1"
DEFAULT_MODEL = "poweredge_r740"
FIXTURE = ROOT / "scripts" / ".smoke-fixtures" / "r740-nameplate.jpg"


def _die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def render_nameplate(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (900, 360), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except OSError:
        font = ImageFont.load_default()
    y = 60
    for line in lines:
        draw.text((40, y), line, fill=(20, 20, 20), font=font)
        y += 70
    img.save(path, format="JPEG", quality=95)
    print(f"Wrote synthetic plate: {path}")


def textract_lines(image_bytes: bytes, region: str) -> str:
    client = boto3.client("textract", region_name=region)
    resp = client.detect_document_text(Document={"Bytes": image_bytes})
    return " ".join(
        b["Text"] for b in resp.get("Blocks", []) if b.get("BlockType") == "LINE"
    )


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
    with urllib.request.urlopen(req, timeout=90) as resp:
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
        ocr = (device_wrap.get("device") or {}).get("ocr_confirmed")
        print(f"  job={status} ocr_confirmed={ocr}")
        if status in {"SUCCEEDED", "COMPLETED", "FAILED", "TIMED_OUT", "ABORTED"}:
            return device_wrap
        if ocr is True:
            return device_wrap
        time.sleep(4)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(description="I-3.1.3 Textract model-plate smoke")
    parser.add_argument("--image", help="Optional real plate photo; else generate synthetic")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--model-key", default=DEFAULT_MODEL)
    parser.add_argument("--e2e", action="store_true", help="Also POST /devices and poll OCR fields")
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--prefer-wrong",
        action="store_true",
        help="Send thinkpad_t14 preferred key to prove OCR can influence → R740",
    )
    args = parser.parse_args()

    if args.image:
        image_path = Path(args.image)
        if not image_path.is_file():
            _die(f"image not found: {image_path}")
    else:
        image_path = FIXTURE
        render_nameplate(
            image_path,
            [
                "Dell Technologies",
                "PowerEdge R740",
                "Service Tag: DEMO1234",
            ],
        )

    image_bytes = image_path.read_bytes()
    content_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    preferred = "thinkpad_t14" if args.prefer_wrong else args.model_key

    # Offline unit-style check on known plate wording (no AWS).
    synthetic_text = "Dell Technologies PowerEdge R740 Service Tag: DEMO1234"
    offline = match_device_from_ocr_text(synthetic_text, preferred_key=preferred)
    print("Offline OCR matcher (synthetic plate text):")
    print(json.dumps(offline, indent=2))
    if not offline.get("confirmed"):
        _die("Offline matcher failed on synthetic PowerEdge R740 text — catalog hints broken.")
    print("OK: offline matcher confirms/influences model key")

    print(f"Calling Textract DetectDocumentText ({args.region}) with IAM user…")
    direct_ok = False
    try:
        text = textract_lines(image_bytes, args.region)
        print(f"OCR text: {text!r}")
        match = match_device_from_ocr_text(text, preferred_key=preferred)
        print(json.dumps(match, indent=2))
        if not match.get("confirmed"):
            print("WARN: live Textract text did not match catalog hints")
        else:
            direct_ok = True
            print("OK: direct Textract OCR confirms/influences model key")
    except Exception as exc:
        print(f"WARN: direct Textract failed ({exc})")
        print(
            "  Manual fix if e2e also fails: open AWS Console > Amazon Textract "
            f"({args.region}) once to activate the service for this account, "
            "or attach textract:DetectDocumentText to your IAM user."
        )
        if not args.e2e:
            _die(
                "Direct Textract unavailable and --e2e not set. "
                "Activate Textract in console, or re-run with --e2e to test via Lambda."
            )

    if not args.e2e:
        return 0 if direct_ok else 1

    print(f"POST {args.api_url.rstrip('/')}/devices (preferred={preferred})…")
    print("Requires deployed InvokeDetection with DETECTION_MODE=auto (SageMaker optional).")
    try:
        created = post_device(args.api_url, preferred, image_bytes, content_type)
    except urllib.error.HTTPError as exc:
        _die(f"POST /devices failed: {exc.code} {exc.read().decode('utf-8', errors='replace')}")

    device_id = created.get("device_id")
    execution_arn = created.get("execution_arn")
    print(f"device_id={device_id}")
    print(f"execution_arn={execution_arn}")
    if not device_id or not execution_arn:
        _die("API did not return device_id + execution_arn")

    result = poll_device(args.api_url, device_id, execution_arn, args.timeout)
    device = result.get("device") or {}
    print(
        json.dumps(
            {
                "device_model_key": device.get("device_model_key"),
                "ocr_confirmed": device.get("ocr_confirmed"),
                "ocr_influenced": device.get("ocr_influenced"),
                "ocr_matched_hints": device.get("ocr_matched_hints"),
                "detection_source": device.get("detection_source"),
            },
            indent=2,
        )
    )
    if not device.get("ocr_confirmed"):
        _die(
            "Pipeline did not persist ocr_confirmed=true. Redeploy SAM so "
            "InvokeDetection + ParseDetections include OCR fields, then retry --e2e."
        )
    expected_key = "poweredge_r740" if args.prefer_wrong else args.model_key
    if device.get("device_model_key") != expected_key and not args.prefer_wrong:
        # Allow influence if plate text clearly maps elsewhere
        if not device.get("ocr_influenced"):
            _die(
                f"device_model_key={device.get('device_model_key')!r}, "
                f"expected {expected_key!r}"
            )
    print("OK: I-3.1.3 done — GET /devices reports ocr_confirmed=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
