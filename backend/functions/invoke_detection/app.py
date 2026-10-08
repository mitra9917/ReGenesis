import json
import os
from typing import Any, Dict, List

import boto3

from regenesis_common.aws_helpers import log_pipeline_event
from regenesis_common.detection import catalog_assisted_detections, completeness_audit
from regenesis_common.catalog import get_device_spec

sm = boto3.client("sagemaker-runtime")
textract = boto3.client("textract")
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


def _textract_model_hint(bucket: str, key: str, device_model_key: str) -> str:
    if not key:
        return device_model_key
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        resp = textract.detect_document_text(Document={"Bytes": obj["Body"].read()})
        text = " ".join(
            b["Text"] for b in resp.get("Blocks", []) if b.get("BlockType") == "LINE"
        ).upper()
        spec = get_device_spec(device_model_key)
        for hint in spec.get("ocr_hints", []):
            if hint.upper() in text:
                return device_model_key
    except Exception:
        pass
    return device_model_key


def handler(event, context):
    device_id = event["device_id"]
    device_model_key = event.get("device_model_key", "poweredge_r740")
    bucket = event.get("bucket") or os.environ["ASSETS_BUCKET"]
    image_key = event.get("image_s3_key", "")

    mode = os.environ.get("DETECTION_MODE", "auto").lower()
    endpoint = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "").strip()
    min_conf = float(os.environ.get("DETECTION_MIN_CONFIDENCE", "0.45"))

    detection_source = "catalog-assisted"
    detections: List[Dict[str, Any]] = []

    log_pipeline_event(device_id, "detect", "started", {"mode": mode})

    if mode == "mock":
        detections = _mock_detections(device_model_key)
        detection_source = "mock"
    elif mode == "catalog":
        detections = catalog_assisted_detections(device_model_key)
        detection_source = "catalog-assisted"
    else:
        device_model_key = _textract_model_hint(bucket, image_key, device_model_key)
        tried_sagemaker = False
        if endpoint and image_key:
            try:
                detections = _sagemaker_detect(bucket, image_key, endpoint)
                tried_sagemaker = True
                if detections:
                    confs = [float(d.get("confidence", 0)) for d in detections]
                    mean_conf = sum(confs) / len(confs) if confs else 0
                    audit = completeness_audit(device_model_key, detections)
                    if mean_conf >= min_conf and audit["score"] >= 0.5:
                        detection_source = "vision"
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
    }
    log_pipeline_event(device_id, "detect", "succeeded", {"source": detection_source, "count": len(detections)})
    return out
