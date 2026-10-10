#!/usr/bin/env python3
"""Smoke test for I-4.2: Completeness audit flags under-detection.

Verifies:
1. Complete detection achieves 100% score with empty gaps array.
2. Partial/under-detection flags meaningful gap entries with:
   - expected, detected, missing counts
   - deficit percentages
   - severity tiers (critical, high, medium)
   - human-readable reason and catalog remediation notes
3. Surplus detections (e.g. unexpected component outside BOM) are captured.

Usage:
  python scripts/smoke_completeness_audit.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))

from regenesis_common.catalog import get_device_spec
from regenesis_common.detection import (
    catalog_assisted_detections,
    completeness_audit,
)


def verify_completeness_audit() -> bool:
    print("\n=======================================================")
    print("  Verifying Completeness Audit & Under-Detection Flags")
    print("=======================================================\n")

    model_key = "poweredge_r740"
    spec = get_device_spec(model_key)
    expected_bom = spec["expected_components"]

    print(f"Device: {model_key} (Dell PowerEdge R740)")
    print(f"Expected BOM: {expected_bom}")
    print(f"Total BOM Components: {sum(expected_bom.values())}\n")

    # Case 1: Complete Detection (Catalog fallback or ideal vision)
    print("--- Case 1: 100% Complete BOM Detection ---")
    complete_dets = catalog_assisted_detections(model_key)
    audit_complete = completeness_audit(model_key, complete_dets)

    print(f"  Score: {audit_complete['score'] * 100:.1f}%")
    print(f"  Within Tolerance: {audit_complete['within_tolerance']}")
    print(f"  Gaps Count: {len(audit_complete['gaps'])}")
    assert audit_complete["score"] == 1.0, "Complete audit score must be 1.0"
    assert audit_complete["within_tolerance"] is True, "Complete audit must be within tolerance"
    assert len(audit_complete["gaps"]) == 0, "Gaps array must be empty"
    print("  [PASS] 100% complete detection validated with zero gaps.\n")

    # Case 2: Under-detection scenario (Vision detects partial hardware)
    print("--- Case 2: Partial Vision Under-Detection ---")
    partial_vision = [
        {"class": "RAM", "confidence": 0.88},
        {"class": "RAM", "confidence": 0.85},
        {"class": "SSD", "confidence": 0.92},
        {"class": "NIC", "confidence": 0.89},
        {"class": "HDD", "confidence": 0.91},  # Surplus component
    ]
    audit_partial = completeness_audit(model_key, partial_vision)

    print(f"  Vision Score: {audit_partial['score'] * 100:.1f}%")
    print(f"  Within Tolerance: {audit_partial['within_tolerance']}")
    print(f"  Total Expected: {audit_partial['total_expected']}")
    print(f"  Total Detected: {audit_partial['total_detected']}")
    print(f"  Total Missing: {audit_partial['total_missing']}")
    print(f"  Under-Detected Classes: {audit_partial['under_detected_classes']}")
    print(f"  Gaps Flagged: {len(audit_partial['gaps'])}\n")

    assert audit_partial["within_tolerance"] is False, "Partial vision must not be within tolerance"
    assert len(audit_partial["gaps"]) > 0, "Gaps array must be populated"

    print("  Meaningful Gap Breakdown:")
    print("  " + "-" * 75)
    for g in audit_partial["gaps"]:
        print(f"  [{g['severity'].upper():<8}] {g['comp_type']:<5} | Detected {g['detected']}/{g['expected']} ({g['missing']} missing, -{g['deficit_pct']}%)")
        print(f"             Reason: {g['reason']}")
        print(f"             Action: {g['remediation']}")

    # Verify critical components flagged with appropriate severity
    gpu_gap = next((g for g in audit_partial["gaps"] if g["comp_type"] == "GPU"), None)
    assert gpu_gap is not None, "GPU gap must be flagged"
    assert gpu_gap["severity"] == "critical", "Zero GPU detection must be critical severity"
    print(f"\n  [PASS] Critical under-detection flagged for GPU: {gpu_gap['reason']}")

    # Verify surplus detection
    assert len(audit_partial["surplus"]) == 1, "Surplus HDD must be flagged"
    print(f"  [PASS] Surplus component identified: {audit_partial['surplus'][0]['comp_type']}")

    print("\n=======================================================")
    print("  [SUCCESS] Completeness Audit Under-Detection Verified!")
    print("=======================================================\n")
    return True


if __name__ == "__main__":
    success = verify_completeness_audit()
    sys.exit(0 if success else 1)
