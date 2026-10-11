# RE:GENESIS — detection model metrics

## Latest run (expanded classes) — 2026-10-11

| Field | Value |
|-------|-------|
| Base model | YOLOv8n |
| Epochs | 20 |
| Device | Apple MPS (M2) |
| Train / val | 4361 / 993 |
| Weights | `ml/weights/best.pt` |
| Ultralytics run | `runs/detect/runs/train/regenesis-yolo-5/` |
| SageMaker artifact | `s3://…/models/regenesis-yolo/model.tar.gz` (v3 expanded) |
| Endpoint model | `regenesis-yolo-model-v3` |

### Overall validation (epoch 20 / best)

| Metric | Value |
|--------|------:|
| Precision | **0.946** |
| Recall | **0.894** |
| **mAP@0.5** | **0.951** |
| **mAP@0.5:0.95** | **0.822** |

### Classes with labels now

`CPU`, `GPU`, `RAM`, `SSD`, `HDD`, `NIC`, `Other`

### Still reserved (0 samples)

`PSU`, `Fan`

### Prior run (HDD/NIC/Other only) — 2026-10-10

mAP@0.5 **0.978** on HDD/NIC/Other only; leftover classes had 0 samples.
