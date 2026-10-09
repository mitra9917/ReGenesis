#!/usr/bin/env python3
"""I-2.1.2: Remap Roboflow e-waste labels → RE:GENESIS classes + YOLO bboxes.

Source labels may be YOLO-seg polygons (class + many xy pairs).
This script converts each polygon to an axis-aligned bbox and remaps class ids.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Official RE:GENESIS detector classes (must match invoke_detection / ml README)
REGENESIS_NAMES = {
    0: "CPU",
    1: "GPU",
    2: "RAM",
    3: "SSD",
    4: "HDD",
    5: "PSU",
    6: "NIC",
    7: "Fan",
    8: "Other",
}

# Roboflow export class index → RE:GENESIS class index
# Source names: 9V Battery, Battery, HDD, Keyboard, NetworkSwitch, PCB,
# Remote, Router, Smart Phone, USB, cable, mouse, internal HDD
SOURCE_TO_REGENESIS = {
    0: 8,  # 9V Battery → Other
    1: 8,  # Battery → Other
    2: 4,  # HDD → HDD
    3: 8,  # Keyboard → Other
    4: 6,  # NetworkSwitch → NIC
    5: 8,  # Printed Circuit Board PCB → Other
    6: 8,  # Remote control → Other
    7: 6,  # Router → NIC
    8: 8,  # Smart Phone → Other
    9: 8,  # USB Flash Drive → Other
    10: 8,  # cable → Other
    11: 8,  # computer mouse → Other
    12: 4,  # internal HDD → HDD
}


def polygon_to_yolo_bbox(coords: list[float]) -> tuple[float, float, float, float] | None:
    """coords are flat [x1,y1,x2,y2,...] normalized 0–1 → (cx, cy, w, h)."""
    if len(coords) < 4 or len(coords) % 2 != 0:
        return None
    xs = coords[0::2]
    ys = coords[1::2]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    w = x_max - x_min
    h = y_max - y_min
    if w <= 0 or h <= 0:
        return None
    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    # clamp
    cx = min(max(cx, 0.0), 1.0)
    cy = min(max(cy, 0.0), 1.0)
    w = min(max(w, 1e-6), 1.0)
    h = min(max(h, 1e-6), 1.0)
    return cx, cy, w, h


def convert_label_line(line: str) -> str | None:
    parts = line.strip().split()
    if len(parts) < 5:
        return None
    src_cls = int(float(parts[0]))
    if src_cls not in SOURCE_TO_REGENESIS:
        return None
    dst_cls = SOURCE_TO_REGENESIS[src_cls]
    nums = [float(x) for x in parts[1:]]

    # Already YOLO detect format: class cx cy w h
    if len(nums) == 4:
        cx, cy, w, h = nums
    else:
        box = polygon_to_yolo_bbox(nums)
        if box is None:
            return None
        cx, cy, w, h = box

    return f"{dst_cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


def process_split(src_root: Path, dst_root: Path, split: str) -> tuple[int, int]:
    src_img = src_root / split / "images"
    src_lbl = src_root / split / "labels"
    # Roboflow uses "valid"; we keep valid → val alias later in data.yaml (#22)
    dst_split = "val" if split == "valid" else split
    dst_img = dst_root / dst_split / "images"
    dst_lbl = dst_root / dst_split / "labels"
    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)

    images = 0
    boxes = 0
    if not src_img.is_dir():
        return 0, 0

    for img in sorted(src_img.iterdir()):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            continue
        images += 1
        shutil.copy2(img, dst_img / img.name)
        label_src = src_lbl / f"{img.stem}.txt"
        label_dst = dst_lbl / f"{img.stem}.txt"
        out_lines: list[str] = []
        if label_src.is_file():
            for line in label_src.read_text(encoding="utf-8").splitlines():
                converted = convert_label_line(line)
                if converted:
                    out_lines.append(converted)
                    boxes += 1
        label_dst.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    return images, boxes


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--src",
        type=Path,
        default=Path(__file__).resolve().parent / "data/images/raw/ewaste",
    )
    p.add_argument(
        "--dst",
        type=Path,
        default=Path(__file__).resolve().parent / "data/regenesis_yolo",
    )
    args = p.parse_args()

    if args.dst.exists():
        shutil.rmtree(args.dst)
    args.dst.mkdir(parents=True)

    mapping_doc = args.dst / "CLASS_MAPPING.md"
    mapping_doc.write_text(
        "\n".join(
            [
                "# RE:GENESIS class mapping (I-2.1.2)",
                "",
                "## Target classes",
                "",
                *[f"- `{i}`: {n}" for i, n in REGENESIS_NAMES.items()],
                "",
                "## Source → target",
                "",
                "| Source (Roboflow) | → | RE:GENESIS |",
                "|-------------------|---|------------|",
                "| HDD, internal HDD | → | HDD |",
                "| NetworkSwitch, Router | → | NIC |",
                "| Battery, 9V Battery, Keyboard, PCB, Remote, Phone, USB, cable, mouse | → | Other |",
                "",
                "## Coverage note",
                "",
                "This export has **no** labeled examples yet for: `CPU`, `GPU`, `RAM`, `SSD`, `PSU`, `Fan`.",
                "Those class ids stay reserved so the train script / Lambda schema match.",
                "Hackathon demo can still run; improve coverage later with more images.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    total_img = total_box = 0
    for split in ("train", "valid", "test"):
        imgs, boxes = process_split(args.src, args.dst, split)
        print(f"{split}: {imgs} images, {boxes} boxes")
        total_img += imgs
        total_box += boxes

    # Write a draft names file (full data.yaml is I-2.1.3)
    names_path = args.dst / "names.txt"
    names_path.write_text("\n".join(REGENESIS_NAMES[i] for i in range(9)) + "\n", encoding="utf-8")

    print(f"Wrote {total_img} images / {total_box} boxes → {args.dst}")
    print(f"Mapping notes: {mapping_doc}")


if __name__ == "__main__":
    main()
