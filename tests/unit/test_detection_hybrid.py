from regenesis_common.detection import merge_vision_with_catalog_gaps, vision_detections_usable


def test_vision_usable_mean_conf():
    assert vision_detections_usable([{"confidence": 0.9}], 0.45)
    assert not vision_detections_usable([{"confidence": 0.2}], 0.45)
    assert not vision_detections_usable([], 0.45)


def test_hybrid_keeps_vision_and_fills_gaps():
    vision = [{"class": "HDD", "confidence": 0.97, "bbox": [0.1, 0.1, 0.5, 0.5]}]
    out = merge_vision_with_catalog_gaps("poweredge_r740", vision, min_confidence=0.45)
    assert out["detection_source"] == "hybrid"
    dets = out["detections"]
    sources = {d["source"] for d in dets}
    assert "vision" in sources
    assert "catalog_assisted" in sources
    assert any(d["class"] == "HDD" and d["source"] == "vision" for d in dets)
    # BOM types still present via fillers
    classes = {d["class"] for d in dets}
    assert "CPU" in classes and "RAM" in classes
