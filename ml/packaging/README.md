# SageMaker model packaging

Inference must emit the same JSON as `backend/functions/invoke_detection`:

```json
{"detections":[{"class":"HDD","confidence":0.91,"bbox":[0.1,0.2,0.3,0.4]}]}
```

`bbox` is normalized `[x, y, w, h]` in `[0, 1]`. Class names come from `ml/training/class_schema.py` (9 ids fixed; leftover classes reserved for post-M6 retrain).

## Local schema check (before packaging)

```bash
cd ml/training
source .venv/bin/activate
python verify_inference_schema.py --conf 0.25
# writes data/sample_inference_output.json
```

## Build `model.tar.gz`

```bash
cd ml/training
cp ../weights/best.pt sagemaker_artifact/model.pt
mkdir -p sagemaker_artifact/code
cp class_schema.py sagemaker_artifact/code/
cp sagemaker_inference.py sagemaker_artifact/code/inference.py
# optional: echo ultralytics pillow numpy > sagemaker_artifact/code/requirements.txt

cd sagemaker_artifact
tar -czvf model.tar.gz model.pt code/
aws s3 cp model.tar.gz s3://regenesis-dev-assetsbucket-xp9zjtzuwy50/models/regenesis-yolo/model.tar.gz --region ap-south-1
```

**Current artifact (I-2.3.1):**  
`s3://regenesis-dev-assetsbucket-xp9zjtzuwy50/models/regenesis-yolo/model.tar.gz` (~5.4 MB; contains `model.pt` + `code/inference.py` + `code/class_schema.py` + `requirements.txt`).

Use a PyTorch Deep Learning Container (or install `ultralytics` via `code/requirements.txt`). Point SAM parameter `SageMakerEndpointName` to the endpoint after deploy (I-2.3.2 / I-2.3.4).

## Adding CPU/GPU/RAM/SSD/PSU/Fan later

Keep the same class ids in `class_schema.py` / `data.yaml`. Retrain → replace `model.pt` → re-upload tarball → update endpoint. No Lambda/API/UI schema changes.
