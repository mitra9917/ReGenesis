import uuid
from typing import Any, Dict, List

from regenesis_common.catalog import get_device_spec


def completeness_audit(
    device_model_key: str,
    detections: List[Dict[str, Any]],
    tolerance: float = 0.5,
) -> Dict[str, Any]:
    expected = get_device_spec(device_model_key)["expected_components"]
    detected_counts: Dict[str, int] = {}
    for d in detections:
        cls = d.get("class") or d.get("comp_type")
        if cls:
            detected_counts[cls] = detected_counts.get(cls, 0) + 1

    gaps: List[Dict[str, Any]] = []
    score_parts: List[float] = []
    for comp_type, exp_count in expected.items():
        det = detected_counts.get(comp_type, 0)
        ratio = min(det, exp_count) / exp_count if exp_count else 1.0
        score_parts.append(ratio)
        if det < exp_count * tolerance:
            gaps.append(
                {
                    "comp_type": comp_type,
                    "expected": exp_count,
                    "detected": det,
                    "severity": "high" if det == 0 else "medium",
                }
            )

    overall = sum(score_parts) / len(score_parts) if score_parts else 0.0
    return {
        "expected": expected,
        "detected": detected_counts,
        "gaps": gaps,
        "score": round(overall, 3),
        "within_tolerance": len(gaps) == 0,
    }


def catalog_assisted_detections(
    device_model_key: str,
    image_width: int = 1,
    image_height: int = 1,
) -> List[Dict[str, Any]]:
    """Generate normalized placeholder boxes arranged in a grid from BOM."""
    spec = get_device_spec(device_model_key)
    expected = spec["expected_components"]
    detections: List[Dict[str, Any]] = []
    idx = 0
    for comp_type, count in expected.items():
        for _ in range(count):
            row = idx // 4
            col = idx % 4
            w, h = 0.18, 0.12
            x = 0.05 + col * 0.22
            y = 0.05 + row * 0.15
            detections.append(
                {
                    "detection_id": str(uuid.uuid4()),
                    "class": comp_type,
                    "comp_type": comp_type,
                    "confidence": 0.75,
                    "bbox": [x, y, w, h],
                    "source": "catalog_assisted",
                }
            )
            idx += 1
    return detections


def _normalize_vision_det(d: Dict[str, Any]) -> Dict[str, Any]:
    cls = d.get("class") or d.get("comp_type") or "Other"
    out = {
        "detection_id": d.get("detection_id") or str(uuid.uuid4()),
        "class": cls,
        "comp_type": d.get("comp_type") or cls,
        "confidence": float(d.get("confidence", 0)),
        "bbox": d.get("bbox") or [0.0, 0.0, 0.1, 0.1],
        "source": "vision",
    }
    return out


def vision_detections_usable(
    detections: List[Dict[str, Any]],
    min_mean_confidence: float = 0.45,
) -> bool:
    """True if vision returned at least one box with healthy mean confidence."""
    if not detections:
        return False
    confs = [float(d.get("confidence", 0)) for d in detections]
    return (sum(confs) / len(confs)) >= min_mean_confidence


def merge_vision_with_catalog_gaps(
    device_model_key: str,
    vision_detections: List[Dict[str, Any]],
    min_confidence: float = 0.45,
) -> Dict[str, Any]:
    """Keep confident vision boxes; catalog only fills missing BOM type counts.

    Extra vision classes not in the BOM (e.g. HDD on an R740 job) are kept.
    """
    kept = [
        _normalize_vision_det(d)
        for d in vision_detections
        if float(d.get("confidence", 0)) >= min_confidence
    ]

    expected = get_device_spec(device_model_key)["expected_components"]
    counts: Dict[str, int] = {}
    for d in kept:
        cls = d["class"]
        counts[cls] = counts.get(cls, 0) + 1

    # Place gap fillers after vision boxes in the grid
    idx = len(kept)
    fillers: List[Dict[str, Any]] = []
    for comp_type, exp_count in expected.items():
        have = counts.get(comp_type, 0)
        need = max(0, exp_count - have)
        for _ in range(need):
            row = idx // 4
            col = idx % 4
            fillers.append(
                {
                    "detection_id": str(uuid.uuid4()),
                    "class": comp_type,
                    "comp_type": comp_type,
                    "confidence": 0.75,
                    "bbox": [0.05 + col * 0.22, 0.05 + row * 0.15, 0.18, 0.12],
                    "source": "catalog_assisted",
                }
            )
            idx += 1

    merged = kept + fillers
    if kept and fillers:
        source = "hybrid"
    elif kept:
        source = "vision"
    else:
        source = "catalog-assisted"
        merged = catalog_assisted_detections(device_model_key)

    return {"detections": merged, "detection_source": source}


# Back-compat alias (older callers / docs)
def should_use_sagemaker_path(
    detections: List[Dict[str, Any]],
    audit: Dict[str, Any],
    min_mean_confidence: float = 0.45,
) -> bool:
    return vision_detections_usable(detections, min_mean_confidence)
