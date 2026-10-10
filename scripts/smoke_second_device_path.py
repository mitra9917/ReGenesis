"""Smoke script for Issue #46: Second device type path — Laptop (ThinkPad T14) + Switch (Cisco Catalyst 9300).

Demonstrates the full catalog-assisted pipeline for both non-R740 device types:
  1. Lenovo ThinkPad T14 (laptop): Battery, SSD, RAM, WiFi
  2. Cisco Catalyst 9300 (switch): PSU, NIC, SSD, RAM, Fan

Covers:
  - catalog_assisted_detections for both device types
  - completeness_audit for both
  - build_disassembly_plan for both
  - compute_impact_summary for components
  - ocr_hints matching (ThinkPad/T14/Lenovo, Catalyst/9300/Cisco)

Usage:
  python scripts/smoke_second_device_path.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.catalog import load_catalog
from regenesis_common.detection import (
    catalog_assisted_detections,
    completeness_audit,
    match_device_from_ocr_text,
)
from regenesis_common.impact import compute_impact_summary
from regenesis_common.planner import build_disassembly_plan


def run_device(device_model_key: str, ocr_plate_text: str = "") -> None:
    catalog = load_catalog()
    spec = catalog["devices"][device_model_key]
    print(f"\n{'='*60}")
    print(f"  Device: {spec['display_name']}  [{device_model_key}]")
    print(f"  Category: {spec['category']}")
    print(f"  Expected BOM: {spec['expected_components']}")
    print(f"{'='*60}")

    # 1. OCR hint matching
    if ocr_plate_text:
        ocr_result = match_device_from_ocr_text(ocr_plate_text, preferred_key=None)
        print(f"\n[OCR Matching] plate: '{ocr_plate_text}'")
        print(f"  Identified as: {ocr_result['device_model_key']}  "
              f"(confirmed={ocr_result['confirmed']}, hints={ocr_result['matched_hints']})")
        assert ocr_result["device_model_key"] == device_model_key, \
            f"Expected {device_model_key}, got {ocr_result['device_model_key']}"
        assert ocr_result["confirmed"]
        print(f"  [OK] OCR resolved to correct device")

    # 2. Catalog-assisted detections
    detections = catalog_assisted_detections(device_model_key, device_id=f"{device_model_key}-smoke-001")
    print(f"\n[Detection] catalog_assisted_detections -> {len(detections)} components")
    det_by_type: dict = {}
    for d in detections:
        t = d["comp_type"]
        det_by_type[t] = det_by_type.get(t, 0) + 1
    for t, cnt in det_by_type.items():
        print(f"  {t:<10} x{cnt}")

    # 3. Completeness audit
    audit = completeness_audit(device_model_key, detections)
    print(f"\n[Completeness Audit]")
    print(f"  Score: {audit['score']*100:.0f}%  Gaps: {len(audit['gaps'])}")
    assert audit["score"] >= 0.99, f"Expected 1.0 score for catalog-assisted, got {audit['score']}"
    assert len(audit["gaps"]) == 0, f"Expected 0 gaps, got {audit['gaps']}"
    print(f"  [OK] 100% BOM coverage, 0 gaps")

    # 4. Build disassembly plan
    components_for_plan = [
        {"component_id": f"comp-{i}", "comp_type": d["comp_type"], "rvs": None}
        for i, d in enumerate(detections)
    ]
    plan = build_disassembly_plan(device_model_key, components_for_plan)
    print(f"\n[Disassembly Plan]")
    print(f"  Steps: {len(plan['steps'])}  Total RVS: {plan.get('total_plan_rvs', 0):.2f}")
    for i, step in enumerate(plan["steps"]):
        types_in_step = ", ".join(set(c["comp_type"] for c in step.get("components", []))) or "(no components)"
        print(f"  Step {step.get('catalog_step', i+1)}: {step['action']:<40}  [{types_in_step}]")


    # 5. Impact summary
    qualified_comps = [
        {"comp_type": d["comp_type"], "status": "qualified"}
        for d in detections
    ]
    impact = compute_impact_summary(qualified_comps)
    print(f"\n[Impact Summary]")
    print(f"  Qualified: {impact['components_qualified']} components")
    print(f"  Mass diverted: {impact['mass_diverted_kg']} kg "
          f"[{impact['mass_diverted_kg_range']['low']} - {impact['mass_diverted_kg_range']['high']} kg]")
    print(f"  CO2e avoided: {impact['co2e_avoided_kg']} kg")
    print(f"  Honest range: [{impact['co2e_avoided_kg_range']['low']} .. {impact['co2e_avoided_kg_range']['high']}] kg CO2e")

    print(f"\n  [OK] {spec['display_name']} pipeline path verified successfully!")


def main():
    print("--- [I-4.6 Smoke Test] Second Device Type Path ---")
    print("Devices under test:")
    print("  1. Lenovo ThinkPad T14 (laptop) -> [thinkpad_t14]")
    print("  2. Cisco Catalyst 9300 (switch) -> [cisco_catalyst_9300]")

    # ThinkPad T14 with plate OCR simulation
    run_device("thinkpad_t14", ocr_plate_text="ThinkPad T14 Lenovo Type 20UD")

    # Cisco Catalyst 9300 with plate OCR simulation
    run_device("cisco_catalyst_9300", ocr_plate_text="Cisco Catalyst 9300 Series WS-C9300-24P")

    # Cross-catalog: ensure R740 still works unchanged
    print(f"\n{'='*60}")
    print(f"  Regression check: Dell PowerEdge R740 still works")
    print(f"{'='*60}")
    detections_r740 = catalog_assisted_detections("poweredge_r740", device_id="r740-regression-001")
    audit_r740 = completeness_audit("poweredge_r740", detections_r740)
    assert audit_r740["score"] >= 0.99, f"R740 regression failed: score {audit_r740['score']}"
    print(f"  R740 score: {audit_r740['score']*100:.0f}%  Gaps: {len(audit_r740['gaps'])}  [OK]")

    print(f"\n--- All second-device-path smoke tests PASSED! ---")
    print(f"\n== Devices supported in UI dropdown ==")
    print(f"  - Dell PowerEdge R740 (rack server)")
    print(f"  - Lenovo ThinkPad T14 (laptop)")
    print(f"  - Cisco Catalyst 9300 (switch)")
    print(f"\nTo trigger a laptop run via API:")
    print(f"  POST /devices {{device_model_key: 'thinkpad_t14', image_base64: '...'}}")
    print(f"To trigger a switch run via API:")
    print(f"  POST /devices {{device_model_key: 'cisco_catalyst_9300', image_base64: '...'}}")


if __name__ == "__main__":
    main()
