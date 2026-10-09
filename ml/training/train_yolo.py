#!/usr/bin/env python3
"""Train YOLOv8 for RE:GENESIS component detection."""

import argparse
import json
import os
import shutil
from pathlib import Path

from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/data.yaml", help="YOLO data.yaml path")
    p.add_argument("--model", default="yolov8s.pt", help="Base checkpoint")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--export", choices=["none", "onnx"], default="none")
    p.add_argument("--output-dir", default="runs/train")
    p.add_argument(
        "--device",
        default="",
        help="Ultralytics device: ''=auto, mps (Apple), cuda, cpu",
    )
    return p.parse_args()


def write_sample_data_yaml(path: Path) -> None:
    """Minimal template if user has not prepared data yet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    sample = {
        "path": str(path.parent.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {
            0: "CPU",
            1: "GPU",
            2: "RAM",
            3: "SSD",
            4: "HDD",
            5: "PSU",
            6: "NIC",
            7: "Fan",
            8: "Other",
        },
    }
    import yaml

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(sample, f)


def main():
    args = parse_args()
    data_path = Path(args.data)
    write_sample_data_yaml(data_path)

    model = YOLO(args.model)
    train_kwargs = {
        "data": str(data_path),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": args.output_dir,
        "name": "regenesis-yolo",
    }
    if args.device:
        train_kwargs["device"] = args.device
    results = model.train(**train_kwargs)

    best = Path(results.save_dir) / "weights" / "best.pt"
    manifest = {
        "best_weights": str(best),
        "epochs": args.epochs,
        "classes": list(model.names.values()) if hasattr(model, "names") else [],
    }
    print(json.dumps(manifest, indent=2))

    if args.export == "onnx" and best.exists():
        export_model = YOLO(str(best))
        export_model.export(format="onnx")

    # SageMaker packaging helper
    sm_dir = Path("sagemaker_artifact")
    sm_dir.mkdir(exist_ok=True)
    if best.exists():
        shutil.copy(best, sm_dir / "model.pt")
    code_dir = sm_dir / "code"
    code_dir.mkdir(exist_ok=True)
    inference_src = Path(__file__).parent / "sagemaker_inference.py"
    if inference_src.exists():
        shutil.copy(inference_src, code_dir / "inference.py")
    print(f"Artifact staged in {sm_dir.resolve()} — tar for SageMaker deployment.")


if __name__ == "__main__":
    main()
