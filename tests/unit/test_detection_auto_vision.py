import json
from pathlib import Path

from regenesis_common.detection import (
    api_detection_source,
    merge_vision_with_catalog_gaps,
    vision_detections_usable,
)

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "ml" / "training" / "data" / "sample_inference_output.json"
R740 = "poweredge_r740"


def test_api_source_maps_hybrid_and_vision_to_vision():
    assert api_detection_source("vision") == "vision"
    assert api_detection_source("hybrid") == "vision"
    assert api_detection_source("catalog-assisted") == "catalog-assisted"
    assert api_detection_source("mock") == "mock"


def test_trained_model_sample_is_usable_vision_for_auto_mode():
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    vision = payload["detections"]
    assert vision_detections_usable(vision, 0.45)

    merged = merge_vision_with_catalog_gaps(R740, vision, min_confidence=0.45)
    # Model only covers HDD/NIC/Other, so merge fills the R740 BOM.
    assert merged["detection_source"] == "hybrid"
    assert api_detection_source(merged["detection_source"]) == "vision"
    assert any(d.get("source") == "vision" for d in merged["detections"])


def test_empty_vision_stays_catalog_assisted_on_api():
    merged = merge_vision_with_catalog_gaps(R740, [], min_confidence=0.45)
    assert api_detection_source(merged["detection_source"]) == "catalog-assisted"
