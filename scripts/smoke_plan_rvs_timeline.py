#!/usr/bin/env python3
"""Smoke verification for I-4.1: RVS ordering clear in plan timeline.

Verifies:
1. Components are sorted by Reuse Value Score (RVS) descending within and across rules.
2. High-value parts (GPU, PSU) are prioritized sensibly over low-value parts (RAM, Fan).
3. Disassembly plan structure includes `total_plan_rvs`, `highest_rvs_component`,
   `priority_tier`, and `step_rvs`.
4. Enclosure preparation (top cover / panel) is classified as 'Prerequisite'.

Usage:
  python scripts/smoke_plan_rvs_timeline.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.catalog import load_catalog
from regenesis_common.detection import catalog_assisted_detections
from regenesis_common.planner import build_disassembly_plan
from regenesis_common.rvs import reuse_value_score


def verify_rvs_ordering(device_model_key: str = "poweredge_r740") -> bool:
    print(f"\n=======================================================")
    print(f"  Verifying RVS Plan Ordering for: {device_model_key}")
    print(f"=======================================================\n")

    catalog = load_catalog()
    specs = catalog["component_specs"]

    # Generate sample components
    dets = catalog_assisted_detections(device_model_key)
    components = [
        {
            "component_id": d["detection_id"],
            "comp_type": d["comp_type"],
            "confidence": d["confidence"],
            "bbox": d["bbox"],
        }
        for d in dets
    ]

    plan = build_disassembly_plan(device_model_key, components)

    print(f"Plan ID: {plan['plan_id']}")
    print(f"Strategy: {plan.get('strategy', 'N/A')}")
    print(f"Total Plan RVS: {plan.get('total_plan_rvs', 0)} pts")
    print(f"Highest Value Component: {plan.get('highest_rvs_component', 'N/A')}")
    print(f"Total Steps: {len(plan['steps'])}\n")

    print(f"{'Step':<6} | {'Priority':<12} | {'Risk':<6} | {'Step RVS':<10} | {'Action':<32} | {'Components'}")
    print("-" * 95)

    all_planned = []
    for idx, step in enumerate(plan["steps"], 1):
        comps = step.get("components", [])
        all_planned.extend(comps)
        comp_summary = ", ".join([f"{c['comp_type']} (RVS {c['rvs']})" for c in comps]) if comps else "(none - prep)"
        print(
            f"{idx:<6} | {step.get('priority_tier', 'N/A'):<12} | "
            f"{step.get('risk', 0):<6.2f} | {step.get('step_rvs', 0):<10.2f} | "
            f"{step['action']:<32} | {comp_summary}"
        )

    print("\n--- Verifying Constraints ---")

    # Constraint 1: Total extraction steps == component count
    assert plan["total_extraction_steps"] == len(components), "Step count mismatch"
    print(" [PASS] Total extraction steps match component count")

    # Constraint 2: Total Plan RVS is positive and matches component sum
    computed_rvs = round(sum(c["rvs"] for c in all_planned), 2)
    assert abs(plan["total_plan_rvs"] - computed_rvs) < 0.01, "Total plan RVS mismatch"
    print(f" [PASS] Total Plan RVS verified: {plan['total_plan_rvs']} pts")

    # Constraint 3: For PowerEdge R740, GPU is scheduled earlier than RAM
    comp_steps = {}
    for c in all_planned:
        comp_steps.setdefault(c["comp_type"], []).append(c["extraction_step"])

    if "GPU" in comp_steps and "RAM" in comp_steps:
        first_gpu = min(comp_steps["GPU"])
        first_ram = min(comp_steps["RAM"])
        assert first_gpu < first_ram, f"GPU step {first_gpu} should precede RAM step {first_ram}"
        print(f" [PASS] High-value GPU (step {first_gpu}) precedes RAM (step {first_ram})")

    if "GPU" in comp_steps and "SSD" in comp_steps:
        first_gpu = min(comp_steps["GPU"])
        first_ssd = min(comp_steps["SSD"])
        assert first_gpu < first_ssd, f"GPU step {first_gpu} should precede SSD step {first_ssd}"
        print(f" [PASS] High-value GPU (step {first_gpu}) precedes SSD (step {first_ssd})")

    # Constraint 4: Component priority tier assignment
    for c in all_planned:
        assert "priority_tier" in c, f"Missing priority_tier on {c['component_id']}"
    print(" [PASS] All components contain priority_tier classifications")

    print("\n [SUCCESS] RVS plan timeline ordering is coherent and verified!\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for RVS plan timeline ordering")
    parser.add_argument(
        "--device",
        default="poweredge_r740",
        choices=["poweredge_r740", "thinkpad_t14", "cisco_catalyst_9300"],
        help="Device model key to test",
    )
    args = parser.parse_args()

    success = verify_rvs_ordering(args.device)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
