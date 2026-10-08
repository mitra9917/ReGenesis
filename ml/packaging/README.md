# SageMaker model packaging

```bash
cd ml/training/sagemaker_artifact
tar -czvf model.tar.gz model.pt code/
aws s3 cp model.tar.gz s3://YOUR_BUCKET/models/regenesis-yolo/model.tar.gz
```

Create model with primary container image supporting Python 3.10+ and install `ultralytics` via `requirements.txt` in `code/`, or use AWS Deep Learning Container for PyTorch.

Point SAM parameter `SageMakerEndpointName` to your endpoint after deploy.
