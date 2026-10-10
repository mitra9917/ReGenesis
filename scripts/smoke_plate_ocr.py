#!/usr/bin/env python3
"""I-3.1.3 check: model-plate OCR via local Tesseract (no Textract).

Paths:
  1) Offline matcher with plate text (always free).
  2) Optional --e2e POST /devices with image and/or plate_text through Lambda
     (Lambda uses Tesseract layer — free, pay only for Lambda invocations).

Usage:
  python scripts/smoke_plate_ocr.py
  python scripts/smoke_plate_ocr.py --e2e
  python scripts/smoke_plate_ocr.py --e2e --prefer-wrong
  python scripts/smoke_plate_ocr.py --image scripts/.smoke-fixtures/r740-nameplate.jpg --e2e
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

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.detection import match_device_from_ocr_text  # noqa: E402

DEFAULT_API = "https://roz4wu5br7.execute-api.ap-south-1.amazonaws.com/Prod"
DEFAULT_MODEL = "poweredge_r740"
FIXTURE = ROOT / "scripts" / ".smoke-fixtures" / "r740-nameplate.jpg"
PLATE_LINES = ["Dell Technologies", "PowerEdge R740", "Service Tag: DEMO1234"]


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


def post_device(
    api_url: str,
    model_key: str,
    image_bytes: bytes | None,
    content_type: str,
    plate_text: str,
) -> dict:
    payload: dict = {"device_model_key": model_key}
    if plate_text:
        payload["plate_text"] = plate_text
    if image_bytes:
        payload["image_base64"] = base64.b64encode(image_bytes).decode("ascii")
        payload["content_type"] = content_type
    body = json.dumps(payload).encode("utf-8")
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
        engine = (device_wrap.get("device") or {}).get("ocr_engine")
        print(f"  job={status} ocr_confirmed={ocr} ocr_engine={engine}")
        if status in {"SUCCEEDED", "COMPLETED", "FAILED", "TIMED_OUT", "ABORTED"}:
            return device_wrap
        if ocr is True:
            return device_wrap
        time.sleep(4)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(description="I-3.1.3 Tesseract / plate_text OCR smoke")
    parser.add_argument("--image", help="Optional plate photo; else generate synthetic JPEG")
    parser.add_argument("--model-key", default=DEFAULT_MODEL)
    parser.add_argument("--plate-text", default="", help="Skip image OCR; send this text to API")
    parser.add_argument("--e2e", action="store_true")
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--prefer-wrong",
        action="store_true",
        help="Prefer thinkpad_t14 so OCR/plate_text must influence -> poweredge_r740",
    )
    parser.add_argument(
        "--text-only-e2e",
        action="store_true",
        help="E2E with plate_text only (no image). Proves matcher without Tesseract binary.",
    )
    args = parser.parse_args()

    plate_blob = " ".join(PLATE_LINES)
    preferred = "thinkpad_t14" if args.prefer_wrong else args.model_key

    offline = match_device_from_ocr_text(plate_blob, preferred_key=preferred)
    print("Offline matcher:")
    print(json.dumps(offline, indent=2))
    if not offline.get("confirmed"):
        _die("Offline matcher failed on PowerEdge R740 plate text")
    if args.prefer_wrong and offline["device_model_key"] != "poweredge_r740":
        _die("expected influence to poweredge_r740")
    print("OK: offline OCR matcher confirms/influences model key")

    if not args.e2e:
        return 0

    image_bytes = None
    content_type = "image/jpeg"
    plate_text = (args.plate_text or "").strip()

    if args.text_only_e2e or plate_text:
        plate_text = plate_text or plate_blob
        print(f"E2E using plate_text only ({len(plate_text)} chars)")
    else:
        if args.image:
            image_path = Path(args.image)
            if not image_path.is_file():
                _die(f"image not found: {image_path}")
        else:
            image_path = FIXTURE
            render_nameplate(image_path, PLATE_LINES)
        image_bytes = image_path.read_bytes()
        content_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
        print(f"E2E using image {image_path} ({len(image_bytes)} bytes) via Lambda Tesseract")

    print(f"POST {args.api_url.rstrip('/')}/devices (preferred={preferred})…")
    try:
        created = post_device(args.api_url, preferred, image_bytes, content_type, plate_text)
    except urllib.error.HTTPError as exc:
        _die(f"POST /devices failed: {exc.code} {exc.read().decode('utf-8', errors='replace')}")

    device_id = created.get("device_id")
    execution_arn = created.get("execution_arn")
    print(f"device_id={device_id}")
    print(f"execution_arn={execution_arn}")
    result = poll_device(args.api_url, device_id, execution_arn, args.timeout)
    device = result.get("device") or {}
    print(
        json.dumps(
            {
                "device_model_key": device.get("device_model_key"),
                "ocr_confirmed": device.get("ocr_confirmed"),
                "ocr_influenced": device.get("ocr_influenced"),
                "ocr_matched_hints": device.get("ocr_matched_hints"),
                "ocr_engine": device.get("ocr_engine"),
                "detection_source": device.get("detection_source"),
                "ocr_error": device.get("ocr_error"),
            },
            indent=2,
        )
    )
    if not device.get("ocr_confirmed"):
        _die(
            "Pipeline did not persist ocr_confirmed=true. "
            "Ensure Tesseract layer is fetched + SAM redeployed, or use --text-only-e2e."
        )
    print("OK: I-3.1.3 done — plate OCR confirms model key without Textract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
