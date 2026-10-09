# RE:GENESIS — detection model metrics (I-2.2.2)

Numbers for the hackathon blog / slides. Recorded from the local YOLOv8n training run used for M2.

## Run summary

| Field | Value |
|-------|-------|
| Date | 2026-10-10 |
| Base model | YOLOv8n (`yolov8n.pt`) |
| Epochs | 20 |
| Device | Apple MPS (M2) |
| Image size | 640 |
| Batch | 8 |
| Train / val images | 1184 / 337 |
| Weights | `ml/weights/best.pt` |
| Ultralytics run dir | `runs/detect/runs/train/regenesis-yolo-3/` |

## Overall validation (best checkpoint)

Best epoch by **mAP50**: **19** (final validation of `best.pt` matches these class rows).

| Metric | Value |
|--------|------:|
| Precision | **0.945** |
| Recall | **0.947** |
| **mAP@0.5** | **0.978** |
| **mAP@0.5:0.95** | **0.896** |

Pipeline target was mAP@0.5 ≥ 0.75 (stretch 0.80+). **Met** on classes that have labels in this dataset.

## Per-class (best.pt validation)

Only classes with labeled examples in the remapped e-waste set:

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|-------|-------:|----------:|----------:|-------:|------:|---------:|
| HDD | 39 | 43 | 0.975 | 0.920 | 0.983 | 0.901 |
| NIC | 57 | 58 | 0.959 | 1.000 | 0.994 | 0.919 |
| Other | 241 | 281 | 0.902 | 0.922 | 0.957 | 0.869 |

### Classes with **0** training samples (reserved for later)

`CPU`, `GPU`, `RAM`, `SSD`, `PSU`, `Fan` — no P/R/mAP to report yet. Ids stay in the 9-class schema (`ml/training/class_schema.py`) so SageMaker / Lambda stay compatible when we add data later. Post-M6: label → retrain → replace endpoint weights only.

## Plots (for slides)

From the train folder (local; large PNGs — don’t need to commit):

- `results.png` — loss + metric curves  
- `BoxPR_curve.png`, `BoxP_curve.png`, `BoxR_curve.png`, `BoxF1_curve.png`  
- `confusion_matrix_normalized.png`  
- `val_batch*_pred.jpg` — qualitative predictions  

## Honest demo note

This model is strong on **HDD / NIC / Other** from the e-waste export. The live R740 story can still use **mock / catalog-assisted** detection; vision path is validated on matching photos and for AWS wiring (M2.3).

## Reproduce

```bash
cd ml/training
source .venv/bin/activate
python train_yolo.py --data data/data.yaml --model yolov8n.pt --epochs 20 --batch 8 --device mps
```
