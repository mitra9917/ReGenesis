import json
import os
from typing import Any, Dict, List

import boto3

from regenesis_common.aws_helpers import log_pipeline_event
from regenesis_common.detection import (
    api_detection_source,
    catalog_assisted_detections,
    completeness_audit,
    match_device_from_ocr_text,
    merge_vision_with_catalog_gaps,
    vision_detections_usable,
)
from regenesis_common.ocr import resolve_plate_text

sm = boto3.client("sagemaker-runtime")
s3 = boto3.client("s3")


def _mock_detections(device_model_key: str) -> List[Dict[str, Any]]:
    return catalog_assisted_detections(device_model_key)


def _parse_yolo_response(payload: bytes) -> List[Dict[str, Any]]:
    data = json.loads(payload.decode("utf-8"))
    if isinstance(data, dict) and "detections" in data:
        return data["detections"]
    if isinstance(data, list):
        return data
    return []


def _sagemaker_detect(bucket: str, key: str, endpoint: str) -> List[Dict[str, Any]]:
    if not key:
        return []
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()
    resp = sm.invoke_endpoint(
        EndpointName=endpoint,
        ContentType="application/x-image",
        Body=body,
    )
    return _parse_yolo_response(resp["Body"].read())


def _ocr_model_hint(
    bucket: str,
    key: str,
    device_model_key: str,
    plate_text: str = "",
) -> Dict[str, Any]:
    """Confirm or influence device_model_key via Tesseract (or explicit plate_text)."""
    empty = {
        "device_model_key": device_model_key,
        "confirmed": False,
        "influenced": False,
        "matched_hints": [],
        "error": "",
        "engine": "none",
    }
    resolved = resolve_plate_text(
        plate_text=plate_text,
        bucket=bucket,
        image_key=key,
        s3_client=s3,
    )
    text = resolved.get("text") or ""
    engine = resolved.get("engine") or "none"
    if resolved.get("error"):
        empty["error"] = resolved["error"]
        empty["engine"] = engine
        return empty
    if not text:
        empty["engine"] = engine
        return empty

    match = match_device_from_ocr_text(text, preferred_key=device_model_key)
    if not match.get("device_model_key"):
        match["device_model_key"] = device_model_key
    match["error"] = ""
    match["engine"] = engine
    match["ocr_text_preview"] = text[:240]
    return match


def handler(event, context):
    device_id = event["device_id"]
    device_model_key = event.get("device_model_key", "poweredge_r740")
    bucket = event.get("bucket") or os.environ["ASSETS_BUCKET"]
    image_key = event.get("image_s3_key", "")
    plate_text = event.get("plate_text", "") or ""

    mode = os.environ.get("DETECTION_MODE", "auto").lower()
    endpoint = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "").strip()
    min_conf = float(os.environ.get("DETECTION_MIN_CONFIDENCE", "0.45"))

    detection_source = "catalog-assisted"
    detections: List[Dict[str, Any]] = []
    ocr = {
        "confirmed": False,
        "influenced": False,
        "matched_hints": [],
        "engine": "none",
    }

    log_pipeline_event(device_id, "detect", "started", {"mode": mode})

    if mode == "mock":
        detections = _mock_detections(device_model_key)
        detection_source = "mock"
    elif mode == "catalog":
        detections = catalog_assisted_detections(device_model_key)
        detection_source = "catalog-assisted"
    else:
        ocr = _ocr_model_hint(bucket, image_key, device_model_key, plate_text=plate_text)
        device_model_key = ocr.get("device_model_key") or device_model_key
        tried_sagemaker = False
        if endpoint and image_key:
            try:
                vision = _sagemaker_detect(bucket, image_key, endpoint)
                tried_sagemaker = True
                if vision_detections_usable(vision, min_conf):
                    merged = merge_vision_with_catalog_gaps(
                        device_model_key, vision, min_confidence=min_conf
                    )
                    detections = merged["detections"]
                    detection_source = api_detection_source(merged["detection_source"])
                else:
                    detections = catalog_assisted_detections(device_model_key)
                    detection_source = "catalog-assisted"
            except Exception:
                detections = catalog_assisted_detections(device_model_key)
                detection_source = "catalog-assisted"
        else:
            detections = catalog_assisted_detections(device_model_key)
            detection_source = "catalog-assisted" if not tried_sagemaker else detection_source

    audit = completeness_audit(device_model_key, detections)

    out = {
        **event,
        "device_model_key": device_model_key,
        "detections": detections,
        "detection_source": detection_source,
        "completeness_audit": audit,
        "ocr_confirmed": bool(ocr.get("confirmed")),
        "ocr_influenced": bool(ocr.get("influenced")),
        "ocr_matched_hints": list(ocr.get("matched_hints") or []),
        "ocr_engine": ocr.get("engine") or "none",
    }
    if ocr.get("error"):
        out["ocr_error"] = ocr["error"]
    log_pipeline_event(
        device_id,
        "detect",
        "succeeded",
        {
            "source": detection_source,
            "count": len(detections),
            "ocr_confirmed": out["ocr_confirmed"],
            "ocr_matched_hints": out["ocr_matched_hints"],
            "ocr_engine": out["ocr_engine"],
            "ocr_error": ocr.get("error") or "",
        },
    )
    return out
