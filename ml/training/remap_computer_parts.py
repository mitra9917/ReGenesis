#!/usr/bin/env python3
"""Remap Roboflow Computer Parts labels → RE:GENESIS 9-class YOLO ids.

Source classes (computer-parts-zbh2e): GPU, HDD, RAM, SSD, cpu, memory
Target: CPU GPU RAM SSD HDD PSU NIC Fan Other (ids 0–8; do not reorder).
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

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

# Roboflow data.yaml name → RE:GENESIS id (case-insensitive match on export order)
NAME_TO_REGENESIS = {
    "cpu": 0,
    "gpu": 1,
    "ram": 2,
    "memory": 2,  # treat as RAM
    "ssd": 3,
    "hdd": 4,
    "psu": 5,
    "power": 5,
    "nic": 6,
    "fan": 7,
    "other": 8,
}


def load_source_names(data_yaml: Path) -> dict[int, str]:
    """Parse ultralytics-style names from a Roboflow data.yaml."""
    names: dict[int, str] = {}
    text = data_yaml.read_text()
    in_names = False
    for line in text.splitlines():
        raw = line.rstrip()
        if raw.strip().startswith("names:"):
            # inline list: names: ['a', 'b']
            rest = raw.split(":", 1)[1].strip()
            if rest.startswith("["):
                items = [x.strip().strip("'\"") for x in rest.strip("[]").split(",") if x.strip()]
                return {i: n for i, n in enumerate(items)}
            in_names = True
            continue
        if in_names:
            if not raw.startswith(" ") and not raw.startswith("\t") and raw.strip():
                break
            if ":" in raw:
                k, v = raw.split(":", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k.isdigit():
                    names[int(k)] = v
    if not names:
        raise SystemExit(f"Could not parse names from {data_yaml}")
    return names


def build_index_map(source_names: dict[int, str]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for src_id, name in source_names.items():
        key = name.strip().lower()
        if key not in NAME_TO_REGENESIS:
            print(f"WARN: unknown source class {src_id}:{name} → Other")
            mapping[src_id] = 8
        else:
            mapping[src_id] = NAME_TO_REGENESIS[key]
    return mapping


def convert_label_file(src: Path, dst: Path, index_map: dict[int, int]) -> int:
    kept = 0
    lines_out: list[str] = []
    for line in src.read_text().splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        src_cls = int(float(parts[0]))
        if src_cls not in index_map:
            continue
        dst_cls = index_map[src_cls]
        nums = parts[1:]
        # YOLO detect: cx cy w h  OR seg polygon (take bbox via min/max if longer)
        if len(nums) == 4:
            lines_out.append(f"{dst_cls} {' '.join(nums)}")
            kept += 1
        elif len(nums) >= 6 and len(nums) % 2 == 0:
            coords = [float(x) for x in nums]
            xs, ys = coords[0::2], coords[1::2]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            w, h = x_max - x_min, y_max - y_min
            if w <= 0 or h <= 0:
                continue
            cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
            lines_out.append(f"{dst_cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            kept += 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines_out) + ("\n" if lines_out else ""))
    return kept


def copy_split(
    src_root: Path,
    dst_root: Path,
    split: str,
    index_map: dict[int, int],
    prefix: str,
) -> tuple[int, int]:
    # Roboflow uses train/valid/test; we use train/val/test
    src_split = "valid" if split == "val" and (src_root / "valid").is_dir() else split
    img_dir = src_root / src_split / "images"
    lbl_dir = src_root / src_split / "labels"
    if not img_dir.is_dir():
        # flat layout fallback
        img_dir = src_root / src_split
        lbl_dir = src_root / src_split
    out_img = dst_root / split / "images"
    out_lbl = dst_root / split / "labels"
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)

    n_img = n_box = 0
    for img in sorted(img_dir.glob("*")):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            continue
        stem = img.stem
        label = lbl_dir / f"{stem}.txt"
        out_name = f"{prefix}_{img.name}"
        shutil.copy2(img, out_img / out_name)
        n_img += 1
        if label.is_file():
            n_box += convert_label_file(label, out_lbl / f"{prefix}_{stem}.txt", index_map)
        else:
            (out_lbl / f"{prefix}_{stem}.txt").write_text("")
    return n_img, n_box


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="Roboflow YOLOv8 export root")
    p.add_argument("--dst", required=True, help="Destination regenesis_yolo root (merged)")
    p.add_argument("--prefix", default="cparts", help="Filename prefix to avoid collisions")
    args = p.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    data_yaml = src / "data.yaml"
    if not data_yaml.is_file():
        raise SystemExit(f"missing {data_yaml}")

    source_names = load_source_names(data_yaml)
    index_map = build_index_map(source_names)
    print("Source names:", source_names)
    print("Index map:", {k: REGENESIS_NAMES[v] for k, v in index_map.items()})

    totals = {}
    for split in ("train", "val", "test"):
        n_img, n_box = copy_split(src, dst, split, index_map, args.prefix)
        totals[split] = (n_img, n_box)
        print(f"{split}: {n_img} images, {n_box} boxes")

    names_txt = dst / "names.txt"
    names_txt.write_text("\n".join(REGENESIS_NAMES[i] for i in range(9)) + "\n")
    print("Done. Merged into", dst.resolve())
    print("Totals:", totals)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
