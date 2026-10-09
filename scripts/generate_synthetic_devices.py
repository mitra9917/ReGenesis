#!/usr/bin/env python3
"""Generate synthetic device JSONL for demos and offline tests."""

import argparse
import datetime as dt
import json
import random
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / "shared" / "catalog" / "devices.json"
DEFAULT_OUTPUT = REPO_ROOT / "shared" / "data" / "synthetic_devices.jsonl"

# Legacy hackathon samples (kept if --legacy is passed)
LEGACY_DEVICES = {
    "ServerX1": {"CPU": 2, "RAM": 8, "SSD": 4, "GPU": 2},
    "SwitchY10": {"Ports": 24, "RAM": 2, "FPGA": 1},
}


def load_catalog(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {
        key: {
            "display_name": entry.get("display_name", key),
            "expected_components": entry["expected_components"],
        }
        for key, entry in raw.items()
    }


def generate_one(device_model_key: str, comps: dict, display_name: str | None = None) -> dict:
    dev = {
        "device_id": str(uuid.uuid4()),
        "device_model_key": device_model_key,
        "model": display_name or device_model_key,
        "timestamp": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "components": [],
    }
    for comp, count in comps.items():
        singular = comp.rstrip("s") if comp.endswith("s") and comp not in ("SSD", "GPU") else comp
        if comp == "Ports":
            singular = "NIC"
        if comp == "FPGA":
            singular = "NIC"
        for _ in range(count):
            dev["components"].append(
                {
                    "component_id": str(uuid.uuid4()),
                    "type": singular,
                    "expected": True,
                    "health_score": random.uniform(0.6, 1.0),
                    "usage_hours": random.randint(1000, 10000),
                }
            )
    if random.random() < 0.2 and dev["components"]:
        dev["components"][random.randrange(len(dev["components"]))]["health_score"] = random.uniform(0, 0.4)
    return dev


def main():
    p = argparse.ArgumentParser(description="Write synthetic device records as JSONL.")
    p.add_argument("-n", type=int, default=12, help="Number of records (default: 12)")
    p.add_argument("-o", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL path")
    p.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="devices.json path (default: shared/catalog/devices.json)",
    )
    p.add_argument("--legacy", action="store_true", help="Use legacy ServerX1/SwitchY10 models only")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.legacy:
        pool = {k: {"display_name": k, "expected_components": v} for k, v in LEGACY_DEVICES.items()}
    else:
        pool = load_catalog(args.catalog)

    keys = list(pool.keys())
    args.o.parent.mkdir(parents=True, exist_ok=True)

    with open(args.o, "w", encoding="utf-8") as f:
        for _ in range(args.n):
            key = random.choice(keys)
            entry = pool[key]
            rec = generate_one(key, entry["expected_components"], entry["display_name"])
            f.write(json.dumps(rec) + "\n")

    print(f"Wrote {args.n} records to {args.o} (models: {', '.join(keys)})")


if __name__ == "__main__":
    main()
