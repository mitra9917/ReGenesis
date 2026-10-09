#!/usr/bin/env python3
"""I-2.2.3 — Local inference must match Lambda / SageMaker JSON schema.

Run (from ml/training, venv active):
  python verify_inference_schema.py
  python verify_inference_schema.py --weights ../weights/best.pt --images path1.jpg path2.jpg
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from class_schema import (
    ALLOWED_CLASSES,
    CLASS_MAP,
    REQUIRED_DETECTION_KEYS,
    RESERVED_FOR_LATER,
    TRAINED_NOW,
)
from sagemaker_inference import predict_fn
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = ROOT.parent / "weights" / "best.pt"
# Prefer clear single-object val shots (high conf) over cluttered product photos
DEFAULT_SAMPLES = [
    ROOT
    / "data/regenesis_yolo/val/images/1040536065_lg_jpg.rf.f35b31369e88c43f2dc65241562dd27e.jpg",  # HDD
    ROOT
    / "data/regenesis_yolo/val/images/10_jpg.rf.7a93de04cafe060235b24dd26990f74b.jpg",  # NIC
    ROOT
    / "data/regenesis_yolo/val/images/10_jpg.rf.50eda2f5fbb1dd1c4ff177a44b401f6b.jpg",  # Other
]
OUT_JSON = ROOT / "data" / "sample_inference_output.json"


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]
    if "detections" not in payload:
        return ["missing top-level 'detections'"]
    dets = payload["detections"]
    if not isinstance(dets, list):
        return ["'detections' must be a list"]

    for i, d in enumerate(dets):
        if not isinstance(d, dict):
            errors.append(f"[{i}] not an object")
            continue
        missing = REQUIRED_DETECTION_KEYS - set(d.keys())
        if missing:
            errors.append(f"[{i}] missing keys {sorted(missing)}")
            continue
        if d["class"] not in ALLOWED_CLASSES:
            errors.append(f"[{i}] unknown class {d['class']!r}")
        conf = d["confidence"]
        if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
            errors.append(f"[{i}] confidence out of range: {conf}")
        bbox = d["bbox"]
        if not (isinstance(bbox, list) and len(bbox) == 4):
            errors.append(f"[{i}] bbox must be [x,y,w,h]")
            continue
        if any(not isinstance(v, (int, float)) for v in bbox):
            errors.append(f"[{i}] bbox values must be numbers")
            continue
        x, y, w, h = map(float, bbox)
        # allow tiny float noise outside [0,1]
        for name, v in (("x", x), ("y", y), ("w", w), ("h", h)):
            if v < -0.02 or v > 1.02:
                errors.append(f"[{i}] bbox {name}={v} not normalized")
        if w <= 0 or h <= 0:
            errors.append(f"[{i}] bbox w/h must be > 0")
    return errors


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    p.add_argument("--images", type=Path, nargs="*", default=None)
    p.add_argument("--conf", type=float, default=0.25)
    args = p.parse_args()

    if not args.weights.is_file():
        print(f"Missing weights: {args.weights}", file=sys.stderr)
        return 1

    images = list(args.images) if args.images else [i for i in DEFAULT_SAMPLES if i.is_file()]
    if not images:
        print("No sample images found", file=sys.stderr)
        return 1

    print("CLASS_MAP (stable for later retrain):", CLASS_MAP)
    print("Trained now:", sorted(TRAINED_NOW))
    print("Reserved for later:", sorted(RESERVED_FOR_LATER))
    print(f"Loading {args.weights} …")
    mdl = YOLO(str(args.weights))

    combined: dict = {"detections": [], "samples": []}
    all_errors: list[str] = []

    for img_path in images:
        raw = img_path.read_bytes()
        payload = predict_fn(raw, mdl)
        # optional display filter (predict_fn uses fixed 0.25 for SageMaker compat)
        payload["detections"] = [
            d for d in payload["detections"] if d["confidence"] >= args.conf
        ]

        errs = validate_payload(payload)
        status = "OK" if not errs else "FAIL"
        print(f"\n=== {img_path.name} → {status} ({len(payload['detections'])} dets) ===")
        print(json.dumps(payload, indent=2)[:1200])
        if errs:
            for e in errs:
                print("  ERROR:", e)
            all_errors.extend(f"{img_path.name}: {e}" for e in errs)
        combined["samples"].append({"image": img_path.name, "payload": payload})
        combined["detections"].extend(payload["detections"])

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_JSON}")

    if all_errors:
        print("\nSCHEMA CHECK FAILED")
        return 1
    print("\nSCHEMA CHECK PASSED — matches invoke_detection contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
