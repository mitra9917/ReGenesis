"""Unit tests for second device type paths (I-4.6 Stretch).

Tests that ThinkPad T14 (laptop) and Cisco Catalyst 9300 (switch) work through
the full pipeline stack: catalog, detection, audit, plan, OCR matching, and impact.
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.catalog import load_catalog, get_device_spec
from regenesis_common.detection import (
    catalog_assisted_detections,
    completeness_audit,
    match_device_from_ocr_text,
)
from regenesis_common.impact import compute_impact_summary
from regenesis_common.planner import build_disassembly_plan


# ---- Catalog presence ----

def test_all_three_devices_in_catalog():
    catalog = load_catalog()
    assert "poweredge_r740" in catalog["devices"]
    assert "thinkpad_t14" in catalog["devices"]
    assert "cisco_catalyst_9300" in catalog["devices"]


def test_thinkpad_bom():
    spec = get_device_spec("thinkpad_t14")
    bom = spec["expected_components"]
    assert "RAM" in bom
    assert "SSD" in bom
    assert "Battery" in bom
    assert "WiFi" in bom
    assert spec["category"] == "laptop"


def test_catalyst_bom():
    spec = get_device_spec("cisco_catalyst_9300")
    bom = spec["expected_components"]
    assert "PSU" in bom
    assert "Fan" in bom
    assert "RAM" in bom
    assert "NIC" in bom
    assert spec["category"] == "network_switch"


# ---- Component spec coverage ----

def test_battery_and_wifi_in_component_specs():
    catalog = load_catalog()
    specs = catalog["component_specs"]
    assert "Battery" in specs
    assert "WiFi" in specs
    assert "Fan" in specs
    # All should have LCA ranges
    for comp_type in ("Battery", "WiFi", "Fan"):
        assert "embodied_co2e_range_kg" in specs[comp_type]
        assert specs[comp_type]["embodied_co2e_range_kg"]["low"] < specs[comp_type]["embodied_co2e_range_kg"]["high"]


# ---- OCR hint matching ----

@pytest.mark.parametrize("plate_text,expected_key", [
    ("ThinkPad T14 Lenovo Type 20UD", "thinkpad_t14"),
    ("Cisco Catalyst 9300 Series WS-C9300-24P", "cisco_catalyst_9300"),
    ("Dell PowerEdge R740 Enterprise Server", "poweredge_r740"),
])
def test_ocr_resolves_correct_device(plate_text, expected_key):
    result = match_device_from_ocr_text(plate_text, preferred_key=None)
    assert result["device_model_key"] == expected_key
    assert result["confirmed"] is True
    assert len(result["matched_hints"]) >= 2


# ---- Catalog-assisted detection ----

@pytest.mark.parametrize("device_key,expected_count", [
    ("thinkpad_t14", 5),      # 2 RAM + 1 SSD + 1 Battery + 1 WiFi
    ("cisco_catalyst_9300", 9),  # 2 PSU + 3 Fan + 2 RAM + 1 SSD + 1 NIC
])
def test_catalog_detections_count(device_key, expected_count):
    detections = catalog_assisted_detections(device_key)
    assert len(detections) == expected_count


# ---- Completeness audit ----

@pytest.mark.parametrize("device_key", ["thinkpad_t14", "cisco_catalyst_9300"])
def test_completeness_audit_full_coverage(device_key):
    detections = catalog_assisted_detections(device_key, device_id=f"{device_key}-test")
    audit = completeness_audit(device_key, detections)
    assert audit["score"] >= 0.99
    assert len(audit["gaps"]) == 0
    assert audit["within_tolerance"] is True
    assert audit["total_missing"] == 0


# ---- Disassembly plan ----

@pytest.mark.parametrize("device_key,min_steps", [
    ("thinkpad_t14", 4),
    ("cisco_catalyst_9300", 4),
])
def test_disassembly_plan_has_steps(device_key, min_steps):
    detections = catalog_assisted_detections(device_key, device_id=f"{device_key}-plan-test")
    components = [
        {"component_id": f"c-{i}", "comp_type": d["comp_type"], "rvs": None}
        for i, d in enumerate(detections)
    ]
    plan = build_disassembly_plan(device_key, components)
    assert len(plan["steps"]) >= min_steps
    assert plan["total_plan_rvs"] > 0
    # All components should be assigned to a step
    assigned_ids = {c["component_id"] for s in plan["steps"] for c in s["components"]}
    all_ids = {c["component_id"] for c in components}
    assert assigned_ids == all_ids


# ---- Impact summary ----

@pytest.mark.parametrize("device_key", ["thinkpad_t14", "cisco_catalyst_9300"])
def test_impact_summary_for_second_devices(device_key):
    detections = catalog_assisted_detections(device_key)
    qualified = [{"comp_type": d["comp_type"], "status": "qualified"} for d in detections]
    impact = compute_impact_summary(qualified)
    assert impact["components_qualified"] == len(detections)
    assert impact["co2e_avoided_kg"] > 0
    co2_range = impact["co2e_avoided_kg_range"]
    assert co2_range["low"] < co2_range["high"]
    assert "factor_citations" in impact
    # Citations should cover all component types in this device
    bom_types = {d["comp_type"] for d in detections}
    cited_types = set(impact["factor_citations"].keys())
    assert bom_types == cited_types


# ---- Regression: R740 still works ----

def test_r740_not_broken():
    detections = catalog_assisted_detections("poweredge_r740")
    audit = completeness_audit("poweredge_r740", detections)
    assert audit["score"] >= 0.99
    assert audit["total_expected"] == 19  # 2+8+4+2+2+1
