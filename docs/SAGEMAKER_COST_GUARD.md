# SageMaker cost guard (I-2.3.3 / #28)

**Billing reality:** a realtime endpoint (`ml.m5.large`) charges **while `InService`**, even with zero traffic.  
S3 model tarball + DynamoDB + Lambda are cheap. **Endpoint hours are the credit risk.**

## Names (ap-south-1)

| Resource | Name |
|----------|------|
| Endpoint | `regenesis-yolo-dev` |
| Endpoint config | `regenesis-yolo-config-m5l-v2` |
| Model | `regenesis-yolo-model-v2` |
| Model data | `s3://regenesis-dev-assetsbucket-xp9zjtzuwy50/models/regenesis-yolo/model.tar.gz` |
| Exec role | `arn:aws:iam::620694778016:role/regenesis-sagemaker-exec` |

## When ON vs OFF

| Situation | Action |
|-----------|--------|
| Wire SAM / smoke-test vision / record demo video | **ON** (create endpoint) |
| Coding, sleep, dinner, submit form | **OFF** (delete endpoint) |
| After Oct 11 submission (default) | **OFF** — app stays up on `DetectionMode=mock` / catalog |
| Live judge wants real vision | **ON** ~1–2 h, then **OFF** again |
| Winners announced / project done | Delete endpoint (+ optionally whole stack) |

**Default for hackathon survival:** endpoint **OFF**. Prove vision with video + `docs/ML_METRICS.md`.

## OFF (stop billing) — run this

```bash
./scripts/sagemaker_endpoint.sh off
# Optional: flip Lambdas back to mock so they don’t call a missing endpoint
cd infrastructure/sam && source ../../scripts/sam-env.sh
sam deploy --no-confirm-changeset --parameter-overrides 'Environment=dev DetectionMode=mock SageMakerEndpointName='
```

(`auto` + empty endpoint also falls back to catalog — mock is clearer for demos.)

## ON (start billing) — run this

```bash
./scripts/sagemaker_endpoint.sh on
./scripts/sagemaker_endpoint.sh wait   # until InService (5–15 min)
cd infrastructure/sam && source ../../scripts/sam-env.sh
sam deploy --no-confirm-changeset --parameter-overrides 'Environment=dev DetectionMode=auto SageMakerEndpointName=regenesis-yolo-dev'
```

Then prove I-3.1.1 (`detection_source=vision`) with an HDD/NIC/e-waste photo:

```bash
python scripts/smoke_vision_auto.py --image path/to/photo.jpg
python scripts/smoke_vision_auto.py --image path/to/photo.jpg --e2e
```

## Status check

```bash
./scripts/sagemaker_endpoint.sh status
```

## Rough cost intuition

- **OFF:** ~$0 for SageMaker inference
- **ON a few hours** for wiring + video: usually **a few dollars**
- **ON for 2–4 weeks** waiting for judges: can **seriously dent $200 credits**

Keep billing alarms at $25 / $50.
