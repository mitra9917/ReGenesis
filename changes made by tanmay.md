# Changes made by Tanmay — handoff for tomorrow (M3 · M4 · M5)

This note is **from the code in the repo**, not from the hackathon checklist doc. Use it to deploy, demo, fix gaps, and submit.

---

## 1. Tomorrow morning — minimum path (30–60 min)

### A. Confirm AWS stack

```bash
cd infrastructure/sam
sam build
sam deploy   # needs samconfig.toml or --guided once
```

Stack name default in scripts: **`regenesis-dev`**. After deploy, note CloudFormation outputs:

| Output | Used for |
|--------|----------|
| `ApiUrl` | Frontend + all smokes |
| `UiBucketName` / `UiWebsiteUrl` | Hosted React UI |
| `AssetsBucketName` | Images, logs, passports, ML tarball |
| `RecoveryStateMachineArn` | Step Functions |
| `PassportKmsKeyId` | Passport sign/verify (Lambdas get this via env) |

### B. Run tests locally (no AWS bill)

```bash
python -m pytest tests/unit -q
```

### C. Point the UI at the API

**Local dev (Vite):**

```bash
cd frontend
cp env.example .env
# Edit .env:
#   VITE_API_URL=/api
#   VITE_API_PROXY_TARGET=<ApiUrl from stack, no trailing slash issues>
npm install
npm run dev
```

Open `http://localhost:5173` → upload form → results page.

**Hosted UI (S3 website bucket from stack):**

```bash
export AWS_PROFILE=your-profile   # deploy_ui.sh requires this
./scripts/deploy_ui.sh
```

Script sets `VITE_API_URL` to stack `ApiUrl`, builds, syncs to `UiBucketName`.

### D. Optional live smokes (uses AWS)

```bash
python scripts/smoke_get_device.py
python scripts/smoke_get_job_status.py
python scripts/smoke_image_upload.py
python scripts/smoke_catalog_fallback.py
python scripts/smoke_tamper_passport.py --e2e
```

Vision / SageMaker (costs money while endpoint is InService):

```bash
./scripts/sagemaker_endpoint.sh on    # needs SAGEMAKER_ROLE_ARN + model in S3
python scripts/smoke_vision_auto.py --image scripts/.smoke-fixtures/vision-smoke.jpg --e2e
./scripts/sagemaker_endpoint.sh off
```

### E. Demo without SageMaker

Deploy or override with **`DetectionMode=mock`** or **`catalog`** (SAM parameter). Pipeline still completes; UI shows **Mock** or **Catalog-assisted** badge.

---

## 2. End-to-end backend flow (what actually runs)

### API surface (`infrastructure/sam/template.yaml`)

| Method | Path | Lambda | Role |
|--------|------|--------|------|
| POST | `/devices` | `IngestFunction` | Create device, optional S3 image, start Step Functions |
| GET | `/devices/{device_id}` | `GetDeviceFunction` | Device + components + passports for UI |
| GET | `/jobs?execution_arn=...` | `GetJobStatusFunction` | Poll Step Functions status |
| GET | `/passports/{passport_id}` | `GetPassportFunction` | Raw passport JSON from S3 |
| GET | `/passports/{passport_id}/verify` | `VerifyPassportFunction` | KMS signature check |

CORS: `*` on API responses (browser can call API from S3-hosted UI or Vite proxy).

### Step Functions (`infrastructure/sam/statemachines/recovery_flow.asl.json`)

Linear pipeline (no Map state in ASL — diagnostics loop inside one Lambda):

1. **InvokeDetection** → `backend/functions/invoke_detection/app.py`
2. **ParseDetections** → `parse_detections/app.py`
3. **PlanDisassembly** → `plan_disassembly/app.py`
4. **RunDiagnostics** → `run_diagnostics/app.py`
5. **GeneratePassports** → `generate_passport/app.py`
6. **ImpactSummary** → `impact_summary/app.py`
7. **NotifyComplete** → SNS publish to `regenesis-recovery-complete-${Environment}`

### Ingest (`backend/functions/ingest/app.py`)

- Parses JSON body: `device_model_key`, optional `image_base64`, `content_type`, `serial_hint`.
- If image present: writes `s3://{ASSETS_BUCKET}/images/{device_id}/original.{jpg|png}`.
- DynamoDB **Devices** row: `status=RECOVERING`, `image_s3_key` empty string if no image uploaded.
- Starts execution on `RECOVERY_STATE_MACHINE_ARN`; stores `execution_arn` on device.
- Returns **202** with `device_id`, `execution_arn`.

**Note for demos:** Step Functions input always includes an `image_s3_key` path even when no file was uploaded (key is still computed). Detection treats missing/invalid S3 object as no image.

### Detection (`invoke_detection/app.py`) — M3 core

Controlled by env (from SAM):

- `DETECTION_MODE`: `mock` | `catalog` | `auto` (default in template: **auto**)
- `SAGEMAKER_ENDPOINT_NAME`: empty = skip SageMaker
- `DETECTION_MIN_CONFIDENCE`: default `0.45`

**`auto` logic (simplified):**

1. Optional **Textract** on plate image: scans text for catalog `ocr_hints`; may confirm model key (`get_device_spec` in `shared/catalog/devices.json`).
2. If endpoint + `image_s3_key`: **SageMaker** invoke (`application/x-image`); parse YOLO JSON detections.
3. If vision usable (mean confidence): **merge** vision + catalog gap fillers (`shared/python/regenesis_common/detection.py` → `merge_vision_with_catalog_gaps`). Source may be `vision`, `hybrid`, or fallback.
4. Else: **catalog_assisted_detections** — synthetic grid bboxes from BOM counts.
5. Always runs **`completeness_audit`** (expected vs detected counts, `gaps`, `score`).

Also logs to **PipelineEvents** table via `log_pipeline_event`.

**IAM today:** SageMaker invoke + **Textract** `DetectDocumentText` on `InvokeDetectionFunction` (see template).

**Extra scripts (not fully wired in Lambda in current `invoke_detection/app.py`):**

- `scripts/smoke_plate_ocr.py`, `scripts/fetch_tesseract_layer.py` — Tesseract/OCR path prepared for issue I-3.1.3; shared `ocr.py` may exist in some branches/layers. **Deployed Lambda path is still Textract in `app.py`.**

### Parse → plan → test → passport → impact (M3 + M4)

| Step | Persists | Shared logic |
|------|----------|--------------|
| Parse | Components table; device `detection_source`, `completeness_audit` | — |
| Plan | Device `disassembly_plan`; component `extraction_step` | `regenesis_common.planner.build_disassembly_plan` + **RVS** (`rvs.reuse_value_score`) |
| Diagnostics | S3 `logs/{device_id}/tests/{component_id}.json`; component status | `regenesis_common.diagnostics.run_component_diagnostics` — **deterministic per `component_id`** (seeded RNG) |
| Passports | S3 `passports/{passport_id}.json`; Passports table; KMS **Sign** | `regenesis_common.passport.canonical_passport_bytes` |
| Impact | Device `status=COMPLETED`, `impact_summary`; CloudWatch metrics | `regenesis_common.impact.compute_impact_summary` — catalog masses + CO₂e + **range** |

CloudWatch custom metrics (`impact_summary/app.py`): `ComponentsRecovered`, `CO2eAvoidedKg`, optionally `DetectionFallbackUsed`.

### Security demo (M3)

- **Verify API:** `verify_passport/app.py` loads passport from S3, `kms.verify` RSASSA_PSS_SHA_256.
- **Tamper smoke:** `scripts/smoke_tamper_passport.py --e2e` mutates S3 JSON → verify fails.

### Data catalog (M4 — drives everything)

- Devices BOM + disassembly rules: `shared/catalog/devices.json` (and copies under `shared/layer/catalog/` for Lambda layer).
- Component specs, test profiles, mass/CO₂e: `shared/catalog/components_specs.json`.
- Three device keys in UI: `poweredge_r740`, `thinkpad_t14`, `cisco_catalyst_9300`.

### Pipeline events (M4)

- `PIPELINE_EVENTS_TABLE` + `aws_helpers.log_pipeline_event` — stages: ingest, detect, parse, plan, test, passport, impact.
- Smoke: `scripts/smoke_pipeline_events.py`.

---

## 3. Milestone map (what Tanmay’s code covers)

### M3 — AWS integration & hardening

| Issue theme | Where in code |
|-------------|----------------|
| Vision / auto detection | `invoke_detection/app.py`, `detection.py`, `smoke_vision_auto.py`, `test_detection_auto_vision.py` |
| Catalog fallback | `catalog_assisted_detections`, `smoke_catalog_fallback.py`, `test_detection_catalog_fallback.py` |
| Plate OCR | Textract in Lambda; smokes: `smoke_textract_plate.py`, `smoke_plate_ocr.py` (Tesseract-oriented) |
| Step Functions | `recovery_flow.asl.json`, screenshot under `docs/screenshots/` |
| S3 prefixes | `verify_s3_prefixes.py`, `test_s3_key_prefixes.py` |
| Tamper passports | `verify_passport`, `smoke_tamper_passport.py`, `test_passport_tamper.py` |
| SNS complete | ASL `NotifyComplete`, `sns_subscribe_notifications.py`, `test_sns_notifications.py` |
| CloudWatch metrics | `impact_summary/app.py` |
| GET device / jobs / upload | `get_device`, `get_job_status`, `ingest`, smokes + unit tests |

### M4 — Product completeness

| Issue theme | Where in code |
|-------------|----------------|
| RVS plan timeline | `planner.py`, `PlanTimeline.tsx`, `smoke_plan_rvs_timeline.py`, `test_planner_rvs.py` |
| Completeness audit | `detection.completeness_audit`, UI on `JobResults`, `test_completeness_audit.py` |
| Deterministic diagnostics | `diagnostics.py`, `test_deterministic_diagnostics.py`, `smoke_deterministic_diagnostics.py` |
| Impact panel | `impact.py`, `ImpactPanel.tsx`, `test_impact_calc.py`, `smoke_impact_factors.py` |
| Pipeline events | `aws_helpers.log_pipeline_event`, `test_pipeline_events.py` |
| Second device types | Extra entries in `devices.json` + Upload dropdown |

### M5 — Frontend (current scope in repo)

**Routes** (`frontend/src/main.tsx`):

- `/` → **Upload** (`pages/Upload.tsx`) — pick model, optional photo, POST `/devices`, navigate to results.
- `/devices/:deviceId` → **JobResults** (`pages/JobResults.tsx`) — poll API every 3s.

**Layout:** `App.tsx` header/footer only (no separate landing/passports/impact pages — those are **sections on JobResults**).

**API client:** `frontend/src/api.ts` — `createDevice`, `getDevice`, `getJob`, `verifyPassport`, `fileToBase64`.

**Components:**

- `DetectionOverlay` — normalized bbox overlay from component list.
- `PlanTimeline` — RVS-ordered steps.
- `ImpactPanel` — qualified count, mass, CO₂e point + range vs shred baseline.
- `PassportCard` — “Verify (KMS)” → `GET /passports/{id}/verify`.

**Deploy:** `scripts/deploy_ui.sh` (bash; PowerShell variant may exist as `deploy_ui.ps1`).

**Not in code yet (M5 checklist items your friend could add):** dedicated landing page, extra routes, CloudFront (commented out in SAM — UI is **S3 static website**), loading skeletons beyond “Loading…”, global error boundary.

---

## 4. Website flow (for demo script)

```text
User opens UI (localhost:5173 or UiWebsiteUrl)
    │
    ▼
[Upload page] Choose device model (R740 / T14 / Catalyst)
    │  Optional: interior photo → base64 in POST body
    ▼
POST /devices  (Ingest Lambda)
    │  Creates device_id, starts Step Functions
    │  Returns execution_arn → stored in sessionStorage
    ▼
Navigate to /devices/{device_id}
    │
    ▼
[Job Results] Poll every 3s:
    │  GET /devices/{id}  → device, components, passports, plan, audit, impact
    │  GET /jobs?execution_arn=...  → RUNNING / SUCCEEDED / FAILED
    ▼
While RUNNING: partial data may appear (components fill in after parse)
When COMPLETED: status COMPLETED, passports listed, impact panel full
    │
    ▼
User clicks "Verify (KMS)" on a passport → GET /passports/{id}/verify
    → "Signature valid" (green) or "Invalid" (red)
```

**Badges on results page:**

- `detection_source === "vision"` → “SageMaker vision”
- `"mock"` → “Mock”
- else → “Catalog-assisted”

(hybrid from backend may show as catalog-assisted in UI — only exact `vision` gets vision pill.)

---

## 5. Important files (edit here tomorrow)

| Area | Path |
|------|------|
| SAM infra | `infrastructure/sam/template.yaml` |
| State machine | `infrastructure/sam/statemachines/recovery_flow.asl.json` |
| Shared business logic | `shared/python/regenesis_common/*.py` (also copied in `shared/layer/` for deploy) |
| Ingest / API Lambdas | `backend/functions/*/app.py` |
| React UI | `frontend/src/pages/*`, `frontend/src/components/*`, `frontend/src/api.ts` |
| Catalog data | `shared/catalog/devices.json`, `components_specs.json` |
| Smokes | `scripts/smoke_*.py` |
| Unit tests | `tests/unit/test_*.py` |
| SageMaker on/off | `scripts/sagemaker_endpoint.sh` |
| ML artifact | `ml/packaging/README.md`, tarball in S3 (not in git — `*.pt`, `model.tar.gz` gitignored) |

---

## 6. Gaps / watch-outs before submit

1. **SageMaker costs** — endpoint ON = billing. Default hackathon-safe: `DetectionMode=mock` or empty endpoint + catalog fallback.
2. **Textract** — Lambda IAM allows it; account may need Textract enabled (subscription). If it fails, detection still falls back to catalog in `auto`.
3. **Tesseract smokes vs Lambda** — `smoke_plate_ocr.py` expects a Tesseract layer deploy; **`invoke_detection/app.py` still uses Textract**, not `ocr.py`. Align these if judges need plate OCR on free tier.
4. **Ingest `image_s3_key` in SFN input** — always passes a key path; harmless if S3 object missing but can confuse debugging.
5. **GET /jobs** — on missing execution, Step Functions client may throw (502) unless Lambda maps to 404; check `smoke_get_job_status.py` expectations before demo.
6. **Uncommitted / local-only** — `samconfig.toml`, `frontend/.env`, AWS credentials, Tesseract layer zip under `shared/tesseract_layer/` (if fetched), smoke fixture images under `scripts/.smoke-fixtures/`.
7. **M6 video** — not code; use `docs/DEMO_SCRIPT.md` + live UI or recording.

---

## 7. Suggested split for your friend tomorrow

| Priority | Task |
|----------|------|
| P0 | `sam deploy` + `./scripts/deploy_ui.sh` + one full UI run (mock mode OK) |
| P0 | `pytest tests/unit -q` green |
| P1 | Polish copy on Upload/Results, fix any API errors, record demo |
| P1 | Submission checklist (`docs/SUBMISSION.md`, Builder Center) |
| P2 | Optional: second device demo (ThinkPad), SNS email subscribe script |
| P2 | Optional: turn SageMaker ON briefly for vision badge + turn OFF |
| P3 | M5 extras: landing page, CloudFront if account verified |

---

*Generated from repository structure and source as of handoff. Re-run smokes after any deploy.*
