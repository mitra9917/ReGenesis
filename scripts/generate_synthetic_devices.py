#!/usr/bin/env python3
"""Generate synthetic device JSON for testing (from hackathon report)."""

import argparse
import datetime
import json
import random
import uuid
from pathlib import Path

DEVICES = {
    "ServerX1": {"CPU": 2, "RAM": 8, "SSD": 4, "GPU": 2},
    "SwitchY10": {"Ports": 24, "RAM": 2, "FPGA": 1},
}


def generate_one(device_model: str, comps: dict) -> dict:
    dev = {
        "device_id": str(uuid.uuid4()),
        "model": device_model,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
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
    p = argparse.ArgumentParser()
    p.add_argument("-n", type=int, default=3, help="Number of records")
    p.add_argument("-o", type=Path, default=Path("synthetic_devices.jsonl"))
    args = p.parse_args()

    with open(args.o, "w", encoding="utf-8") as f:
        for _ in range(args.n):
            model = random.choice(list(DEVICES.keys()))
            rec = generate_one(model, DEVICES[model])
            f.write(json.dumps(rec) + "\n")
    print(f"Wrote {args.n} records to {args.o}")


if __name__ == "__main__":
    main()
