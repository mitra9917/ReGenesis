#!/usr/bin/env python3
"""Print catalog summary for sanity checks."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
devices = json.loads((ROOT / "shared/catalog/devices.json").read_text())
specs = json.loads((ROOT / "shared/catalog/components_specs.json").read_text())

for key, dev in devices.items():
    exp = dev["expected_components"]
    total = sum(exp.values())
    print(f"{key}: {dev['display_name']} — {total} expected parts")

print(f"Component types in specs: {len(specs['component_types'])}")
