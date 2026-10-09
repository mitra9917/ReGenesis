# ML — component detection (YOLO on SageMaker)

## Goal

Detect hardware component classes in decommissioned device interior photos:

`CPU`, `GPU`, `RAM`, `SSD`, `HDD`, `PSU`, `NIC`, `Fan`, `Other`

## Datasets (open)

- [TU Wien PCB Dataset](https://labsites.research.google.com/pcb/) — IC/chip detection on PCBs
- [Roboflow PCB](https://universe.roboflow.com/) — export YOLOv8 format
- Stock Creative Commons server teardown images for fine-tuning (label 50–100 images minimum)

## Train locally

```bash
cd ml/training
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python train_yolo.py --data ./data/data.yaml --epochs 30 --export onnx
```

## SageMaker training job

1. Upload `data/` and `train_yolo.py` to S3.
2. Use SageMaker Python SDK `PyTorch` or custom `SKLearn` container with `pip install ultralytics`.
3. Output `model.tar.gz` containing `model.pt` and `inference.py`.

### `model.tar.gz` layout

```
model.tar.gz
├── model.pt          # YOLO weights
└── code/
    ├── inference.py      # loads model, returns JSON detections
    ├── class_schema.py   # fixed 9-class map (reserved ids for later)
    └── requirements.txt
```

### Inference response format (required by `invoke_detection` Lambda)

```json
{
  "detections": [
    {"class": "GPU", "confidence": 0.91, "bbox": [0.1, 0.2, 0.18, 0.12]}
  ]
}
```

`bbox` is normalized `[x, y, w, h]` relative to image dimensions (0–1).

Canonical class ids (do not reorder — leftover classes stay empty until post-M6): see `training/class_schema.py`.

### Local schema check (I-2.2.3)

```bash
cd ml/training
source .venv/bin/activate
python verify_inference_schema.py --conf 0.25
# → SCHEMA CHECK PASSED; writes data/sample_inference_output.json
```

## Packaged artifact (I-2.3.1)

```
s3://regenesis-dev-assetsbucket-xp9zjtzuwy50/models/regenesis-yolo/model.tar.gz
```

Rebuild locally: see [packaging/README.md](packaging/README.md).

## Deploy endpoint

After the tarball is in S3:

```bash
aws sagemaker create-model ...
aws sagemaker create-endpoint-config ...
aws sagemaker create-endpoint --endpoint-name regenesis-yolo-dev
```

Redeploy SAM with:

```bash
sam deploy --parameter-overrides SageMakerEndpointName=regenesis-yolo-dev DetectionMode=auto
```

## Hackathon fallback

Set `DetectionMode=mock` or leave `SageMakerEndpointName` empty — pipeline uses **catalog-assisted** detections + Textract hints. Demo remains fully functional.

## Evaluation target

- mAP@0.5 ≥ 0.75 on held-out set (stretch: 0.80+)
- Report precision/recall per class in submission blog
