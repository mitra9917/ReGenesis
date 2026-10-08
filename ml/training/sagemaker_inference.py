"""SageMaker inference script for YOLO component detector."""

import io
import json
from typing import Any, Dict, List

from ultralytics import YOLO

CLASS_MAP = {
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

model = None


def model_fn(model_dir: str):
    global model
    model = YOLO(f"{model_dir}/model.pt")
    return model


def input_fn(request_body: bytes, content_type: str):
    return request_body


def predict_fn(input_data: bytes, mdl) -> Dict[str, Any]:
    results = mdl.predict(source=io.BytesIO(input_data), verbose=False)
    detections: List[Dict[str, Any]] = []
    if not results:
        return {"detections": detections}
    r0 = results[0]
    h, w = r0.orig_shape
    for box in r0.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = xyxy
        detections.append(
            {
                "class": CLASS_MAP.get(cls_id, "Other"),
                "confidence": conf,
                "bbox": [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h],
            }
        )
    return {"detections": detections}


def output_fn(prediction: Dict[str, Any], accept: str) -> bytes:
    return json.dumps(prediction).encode("utf-8")
