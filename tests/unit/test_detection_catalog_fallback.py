# pyrefly: ignore [missing-import]
from regenesis_common.catalog import get_device_spec
from regenesis_common.detection import (
    catalog_assisted_detections,
    completeness_audit,
    merge_vision_with_catalog_gaps,
)
from regenesis_common.planner import build_disassembly_plan

R740 = "poweredge_r740"


def _r740_expected():
    return get_device_spec(R740)["expected_components"]


def _assert_catalog_assisted_payload(out):
    assert out["detection_source"] == "catalog-assisted"
    dets = out["detections"]
    assert dets
    assert all(d.get("source") == "catalog_assisted" for d in dets)
    expected = _r740_expected()
    counts = {}
    for d in dets:
        cls = d["class"]
        counts[cls] = counts.get(cls, 0) + 1
    assert counts == expected


def _detections_to_components(detections):
    return [
        {"component_id": d["detection_id"], "comp_type": d["comp_type"]}
        for d in detections
    ]


def test_catalog_assisted_detections_match_bom():
    dets = catalog_assisted_detections(R740)
    expected = _r740_expected()
    assert len(dets) == sum(expected.values())
    assert all(d["source"] == "catalog_assisted" for d in dets)
    assert all("bbox" in d and "detection_id" in d for d in dets)


def test_empty_vision_merges_as_catalog_assisted():
    out = merge_vision_with_catalog_gaps(R740, [], min_confidence=0.45)
    _assert_catalog_assisted_payload(out)


def test_low_confidence_vision_merges_as_catalog_assisted():
    vision = [
        {"class": "CPU", "confidence": 0.2, "bbox": [0.1, 0.1, 0.2, 0.2]},
        {"class": "RAM", "confidence": 0.1, "bbox": [0.3, 0.1, 0.2, 0.2]},
    ]
    out = merge_vision_with_catalog_gaps(R740, vision, min_confidence=0.45)
    _assert_catalog_assisted_payload(out)


def test_missing_confidence_treated_as_unusable_vision():
    vision = [{"class": "GPU", "bbox": [0.1, 0.1, 0.2, 0.2]}]
    out = merge_vision_with_catalog_gaps(R740, vision, min_confidence=0.45)
    _assert_catalog_assisted_payload(out)


def test_catalog_assisted_audit_is_within_tolerance():
    dets = catalog_assisted_detections(R740)
    audit = completeness_audit(R740, dets)
    expected = _r740_expected()
    assert audit["within_tolerance"] is True
    assert audit["score"] == 1.0
    assert audit["gaps"] == []
    assert audit["expected"] == expected
    assert audit["detected"] == expected


def test_catalog_assisted_feeds_recovery_plan():
    dets = catalog_assisted_detections(R740)
    plan = build_disassembly_plan(R740, _detections_to_components(dets))
    assert plan["device_model_key"] == R740
    assert plan["steps"]
    assert plan["total_extraction_steps"] == len(dets)


def test_full_bom_vision_stays_vision_not_catalog_assisted():
    vision = []
    for comp_type, count in _r740_expected().items():
        for _ in range(count):
            vision.append(
                {"class": comp_type, "confidence": 0.9, "bbox": [0.1, 0.1, 0.2, 0.2]}
            )
    out = merge_vision_with_catalog_gaps(R740, vision, min_confidence=0.45)
    assert out["detection_source"] == "vision"
    assert all(d["source"] == "vision" for d in out["detections"])


def test_usable_partial_vision_stays_hybrid_not_catalog_assisted():
    vision = [{"class": "HDD", "confidence": 0.97, "bbox": [0.1, 0.1, 0.5, 0.5]}]
    out = merge_vision_with_catalog_gaps(R740, vision, min_confidence=0.45)
    assert out["detection_source"] == "hybrid"
    sources = {d["source"] for d in out["detections"]}
    assert sources == {"vision", "catalog_assisted"}
