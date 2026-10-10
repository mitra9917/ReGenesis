"""Unit tests for completeness audit under-detection flagging (I-4.2)."""

from regenesis_common.catalog import get_device_spec
from regenesis_common.detection import (
    catalog_assisted_detections,
    completeness_audit,
)

R740 = "poweredge_r740"


def test_complete_detection_has_no_gaps():
    dets = catalog_assisted_detections(R740)
    audit = completeness_audit(R740, dets)
    assert audit["within_tolerance"] is True
    assert audit["score"] == 1.0
    assert audit["gaps"] == []
    assert audit["total_missing"] == 0
    assert audit["under_detected_classes"] == []


def test_under_detection_produces_meaningful_gaps():
    # Only 2 RAMs and 1 NIC detected (missing: 2 CPUs, 6 RAMs, 4 SSDs, 2 GPUs, 2 PSUs)
    partial_detections = [
        {"class": "RAM", "confidence": 0.85},
        {"class": "RAM", "confidence": 0.82},
        {"class": "NIC", "confidence": 0.90},
    ]
    audit = completeness_audit(R740, partial_detections)

    assert audit["within_tolerance"] is False
    assert audit["score"] < 0.5
    assert len(audit["gaps"]) > 0
    assert audit["total_missing"] == (19 - 3)

    # Check RAM gap
    ram_gap = next(g for g in audit["gaps"] if g["comp_type"] == "RAM")
    assert ram_gap["expected"] == 8
    assert ram_gap["detected"] == 2
    assert ram_gap["missing"] == 6
    assert ram_gap["deficit_pct"] == 75.0
    assert "Under-detected" in ram_gap["reason"]
    assert "remediation" in ram_gap

    # Check GPU gap (zero detected -> critical severity)
    gpu_gap = next(g for g in audit["gaps"] if g["comp_type"] == "GPU")
    assert gpu_gap["expected"] == 2
    assert gpu_gap["detected"] == 0
    assert gpu_gap["missing"] == 2
    assert gpu_gap["deficit_pct"] == 100.0
    assert gpu_gap["severity"] == "critical"


def test_surplus_detection_flagged():
    # Detect expected parts plus an unexpected HDD
    dets = catalog_assisted_detections(R740)
    dets.append({"class": "HDD", "confidence": 0.88})

    audit = completeness_audit(R740, dets)
    assert audit["within_tolerance"] is True
    assert audit["score"] == 1.0
    assert len(audit["surplus"]) == 1
    assert audit["surplus"][0]["comp_type"] == "HDD"
    assert audit["surplus"][0]["extra"] == 1


def test_thinkpad_under_detection():
    # Thinkpad expected: RAM: 2, SSD: 1, Battery: 1, WiFi: 1
    dets = [
        {"class": "RAM", "confidence": 0.9},
        {"class": "SSD", "confidence": 0.9},
    ]
    audit = completeness_audit("thinkpad_t14", dets)
    assert audit["within_tolerance"] is False
    assert "Battery" in audit["under_detected_classes"]
    assert "WiFi" in audit["under_detected_classes"]
    assert "RAM" in audit["under_detected_classes"]
