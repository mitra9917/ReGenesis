# AWS services mapping

Hackathon requirement: use at least one AWS open-source tool **or** deploy on AWS. This project uses **Ship It** (deployed serverless stack) plus **SAM CLI** (Build It) for local iteration.

| Service | Role in RE:GENESIS | Demo talking point |
|---------|-------------------|-------------------|
| **SAM / CloudFormation** | Infrastructure as code | Repeatable deploy for any facility |
| **API Gateway** | REST API for UI | Single entry for ingest and verify |
| **Lambda** | All business logic | Pay-per-recovery-job, scales with volume |
| **Step Functions** | RecoveryFlow orchestration | Visual trace of detect → plan → test → passport |
| **S3** | Images, logs, passports | Durable artifact store |
| **DynamoDB** | Devices, components, passports, events | Low-latency job status for UI |
| **SageMaker** | YOLO endpoint (optional param) | Custom vision for PCB/server internals |
| **Tesseract (Lambda layer)** | Model plate OCR in `DETECTION_MODE=auto` | Free local OCR confirms / influences `device_model_key` via catalog `ocr_hints` (I-3.1.3). Layer: `scripts/fetch_tesseract_layer.py`. Optional `plate_text` on `POST /devices`. |
| **Textract** | Optional / unused by default | Not used (free-tier / subscription limits). Kept out of InvokeDetection IAM. |
| **KMS** | Sign / verify passports | Tamper-evident reuse credentials |
| **SNS** | Job complete notification | Hook for ITAD ERP / Slack |
| **CloudWatch** | Logs + custom metrics | Components recovered, CO₂e avoided |
| **CloudFront** | Static UI CDN | Fast demo URL |

Optional stretch (not in MVP stack): Cognito, OpenSearch, EventBridge rules beyond SNS.
