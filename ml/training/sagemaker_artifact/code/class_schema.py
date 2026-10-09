"""Canonical RE:GENESIS detector classes (I-2.2.3 / future retrain).

Keep this list stable end-to-end:
  data.yaml names ↔ train labels ↔ SageMaker inference ↔ invoke_detection Lambda

When adding leftover classes later (CPU/GPU/RAM/SSD/PSU/Fan images):
  1. Label with the SAME ids below (do not reorder).
  2. Retrain → replace model.pt / best.pt.
  3. Redeploy SageMaker endpoint (same name OK).
  No API, SAM route, or UI schema changes required.
"""

from __future__ import annotations

# Fixed indices — never reorder after M2 wiring
CLASS_MAP: dict[int, str] = {
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

# Classes with training data in the current e-waste export (others reserved)
TRAINED_NOW: frozenset[str] = frozenset({"HDD", "NIC", "Other"})
RESERVED_FOR_LATER: frozenset[str] = frozenset({"CPU", "GPU", "RAM", "SSD", "PSU", "Fan"})

REQUIRED_DETECTION_KEYS = frozenset({"class", "confidence", "bbox"})
ALLOWED_CLASSES = frozenset(CLASS_MAP.values())
