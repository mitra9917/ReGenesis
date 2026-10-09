"""SageMaker inference script for YOLO component detector.

Must stay schema-compatible with backend/functions/invoke_detection/app.py:
  {"detections": [{"class": str, "confidence": float, "bbox": [x,y,w,h]}]}
  bbox normalized 0–1.

Class ids come from class_schema.CLASS_MAP (9 slots reserved for future labels).
"""

import io
import json
from typing import Any, Dict, List

import numpy as np
from PIL import Image
from ultralytics import YOLO

try:
    from class_schema import CLASS_MAP
except ImportError:
    # Fallback if class_schema.py is missing from the tarball (should not happen)
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


def _bytes_to_rgb_array(input_data: bytes) -> np.ndarray:
    """Decode image bytes to HxWx3 uint8 for Ultralytics (BytesIO alone is unsupported)."""
    img = Image.open(io.BytesIO(input_data)).convert("RGB")
    return np.asarray(img)


def predict_fn(input_data: bytes, mdl) -> Dict[str, Any]:
    # Signature must stay (input_data, model) — SageMaker may pass a 3rd Context arg
    # positionally if we add kwargs; never name a param `conf`.
    score_thresh = 0.25
    arr = _bytes_to_rgb_array(input_data)
    results = mdl.predict(source=arr, conf=score_thresh, verbose=False)
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
