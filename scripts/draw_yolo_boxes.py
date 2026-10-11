#!/usr/bin/env python3
"""Draw normalized YOLO detections onto an image.

Usage:
  .venv/bin/python scripts/draw_yolo_boxes.py \\
    --image test-photos/01-vision-smoke.jpg \\
    --detections-json /tmp/dets.json \\
    --out test-photos/yolo-boxes-sagemaker.jpg
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


COLORS = {
    "HDD": (0, 200, 120),
    "NIC": (0, 160, 255),
    "Other": (255, 170, 40),
    "CPU": (255, 80, 80),
    "GPU": (180, 80, 255),
    "RAM": (80, 200, 255),
    "SSD": (255, 220, 60),
    "PSU": (200, 200, 200),
    "Fan": (160, 255, 160),
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--detections-json", required=True, help="JSON file or '-' for stdin")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    raw = Path(args.detections_json).read_text() if args.detections_json != "-" else __import__("sys").stdin.read()
    payload = json.loads(raw)
    dets = payload.get("detections", payload) if isinstance(payload, (dict, list)) else []
    if isinstance(payload, dict):
        dets = payload.get("detections", [])

    img = Image.open(args.image).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", max(14, w // 40))
    except Exception:
        font = ImageFont.load_default()

    for d in dets:
        cls = str(d.get("class", "?"))
        conf = float(d.get("confidence", 0))
        bbox = d.get("bbox") or [0, 0, 0, 0]
        x, y, bw, bh = map(float, bbox)
        x1, y1 = int(x * w), int(y * h)
        x2, y2 = int((x + bw) * w), int((y + bh) * h)
        color = COLORS.get(cls, (255, 255, 255))
        draw.rectangle([x1, y1, x2, y2], outline=color, width=max(2, w // 200))
        label = f"{cls} {conf:.2f}"
        tw = draw.textlength(label, font=font) if hasattr(draw, "textlength") else len(label) * 8
        pad = 4
        draw.rectangle([x1, max(0, y1 - 22), x1 + int(tw) + pad * 2, y1], fill=color)
        draw.text((x1 + pad, max(0, y1 - 20)), label, fill=(0, 0, 0), font=font)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    print(f"Wrote {out} ({len(dets)} boxes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
