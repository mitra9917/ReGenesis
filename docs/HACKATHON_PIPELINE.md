# RE:GENESIS — Hackathon pipeline (milestones → phases → issues)

Shared plan for **you + collaborator**. Use this to know what comes next, what you can **skip / run in parallel**, and what is **blocked** until the other person finishes.

**Final stretch (planned last):** multipage frontend polish → 3‑minute demo video → Builder Center / submission.

---

## How to read this board

| Field | Meaning |
|-------|---------|
| **Owner** | Who usually owns it (`You` = AWS/backend/deploy, `Friend` = ML/vision, `Both`) |
| **Labels** | Tags for filtering (GitHub Issues / Linear / Notion) |
| **Parallel?** | Can the other person start the next issue without this being done? |
| **Skip?** | Safe to leave unfinished for MVP demo if time is short? |

### Label vocabulary (use consistently)

| Label | Use for |
|-------|---------|
| `milestone` | Big checkpoint |
| `phase` | Sub-stage inside a milestone |
| `ml-model` | Dataset, YOLO, SageMaker packaging |
| `aws-integration` | Wiring Lambdas / IAM / Textract / KMS / SNS / CloudWatch |
| `infra-sam` | SAM template, Stack deploy, resources |
| `backend` | Lambda logic, Step Functions, APIs |
| `frontend` | React UI, routes, UX |
| `devops-deploy` | Deploy scripts, CloudFront/S3, env vars |
| `data-catalog` | Device BOM, CO₂e factors, synthetic data |
| `security-kms` | Passport sign / verify |
| `demo-video` | Screencast, script, submission |
| `docs` | Architecture, blog, judging notes |
| `priority-p0` | Must work for demo |
| `priority-p1` | Strongly wanted |
| `priority-p2` | Stretch / polish |
| `blocker` | Stops next milestone |
| `parallel-ok` | Other person can proceed |
| `blocked-by-ml` | Needs Friend’s model/endpoint |
| `blocked-by-aws` | Needs You’s deploy / API URL |

### Parallel work rule (default)

```
Friend (ML)  ──► dataset → train → package → endpoint  (can start Day 0)
You (AWS)    ──► SAM deploy → mock/catalog E2E → UI API URL  (can start Day 0)
Merge point  ──► set SageMakerEndpointName + DetectionMode=auto
Then         ──► frontend multipage polish → video → submit
```

**You do not wait for the ML model to deploy or demo.** Catalog/mock detection keeps the full pipeline functional.

---

## Milestone 0 — Tooling & Cursor AWS MCP

**Goal:** Both machines can talk to AWS from CLI; Cursor can use AWS MCP for inspect/deploy help.  
**Labels:** `milestone` `devops-deploy` `docs` `priority-p0`

### Phase 0.1 — AWS account & CLI

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-0.1.1** | Create / verify AWS account + Free Tier / credits; set billing alarm ($25 / $50) | You | `devops-deploy` `priority-p0` | Yes for Friend | No | Alarm exists; region chosen (e.g. `ap-south-1`) |
| **I-0.1.2** | Install AWS CLI v2; `aws configure` (profile e.g. `regenesis`) | Both | `devops-deploy` | Yes | No | `aws sts get-caller-identity` works |
| **I-0.1.3** | Install SAM CLI + Docker (for `sam local` if needed) | You | `infra-sam` `devops-deploy` | Yes | Local SAM is skippable if cloud deploy works | `sam --version` works |
| **I-0.1.4** | Install Node 20+, Python 3.12+, git; clone repo | Both | `devops-deploy` | Yes | No | `npm` / `python3` available |

### Phase 0.2 — Connect AWS MCP to Cursor (so the agent can help with AWS)

You do **not** add one MCP per service (Lambda, S3, DynamoDB…). One (or a few) **AWS MCP servers** expose many AWS APIs through Cursor.

#### Recommended setup (official AWS Labs MCP)

1. **Prereqs on your machine**
   - [uv](https://github.com/astral-sh/uv) (for `uvx`) *or* Python 3.10+
   - AWS credentials already configured (`aws configure`)
2. **Open Cursor MCP config**
   - **Cursor Settings → MCP → Add server**, or edit:
     - Project (share with teammate): `.cursor/mcp.json`
     - Personal (all projects): `~/.cursor/mcp.json`
3. **Add this server** (read-only recommended for safety):

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "env": {
        "AWS_REGION": "ap-south-1",
        "AWS_API_MCP_PROFILE_NAME": "regenesis",
        "READ_OPERATIONS_ONLY": "true"
      }
    }
  }
}
```

4. **Restart Cursor** → MCP panel should show `aws-api` green / connected.
5. **Optional later (write-capable):** set `READ_OPERATIONS_ONLY` to `false` only when you trust write actions; prefer CLI/`sam deploy` for destructive changes.

#### What MCP is for vs what it is not

| Use MCP for | Do not rely on MCP alone for |
|-------------|------------------------------|
| Inspecting stacks, logs, tables, endpoints | Full SAM first deploy (use `./scripts/deploy.sh`) |
| Debugging “why is Step Functions stuck?” | Training YOLO / packaging `model.tar.gz` |
| Listing S3 keys, DynamoDB items (read) | Frontend polish / video recording |
| Confirming KMS key / IAM gaps | Replacing your AWS console judgment under credit pressure |

#### Docs reference

- Cursor MCP help: https://cursor.com/help/customization/mcp  
- AWS Labs MCP monorepo: https://github.com/awslabs/mcp  
- Prefer the **current official AWS MCP** if Cursor Marketplace lists it; the `awslabs.aws-api-mcp-server` pattern above is the common Cursor setup.

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-0.2.1** | Add AWS MCP to Cursor (`mcp.json`) + restart | Both | `devops-deploy` `docs` | Yes | Yes (nice-to-have) | Tools appear in Cursor MCP list |
| **I-0.2.2** | Smoke-test MCP: ask agent to list regions / verify caller identity | You | `aws-integration` | Yes | Yes | Agent returns correct account/region |

---

## Milestone 1 — Foundation green (no SageMaker required)

**Goal:** Deployed API + one successful recovery job using **mock or catalog-assisted** detection. UI can call API.  
**Labels:** `milestone` `infra-sam` `backend` `devops-deploy` `priority-p0` `blocker`  
**Blocks:** Real demo URL. **Does not block:** Friend’s ML training.

### Phase 1.1 — Shared data & local proof

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-1.1.1** | Review `shared/catalog/devices.json` + `components_specs.json`; tweak R740 BOM if needed | Both | `data-catalog` `priority-p0` | Yes | No | Catalog matches demo story |
| **I-1.1.2** | Run unit tests: `pytest tests/unit` | Both | `backend` `data-catalog` | Yes | No | All tests green |
| **I-1.1.3** | Generate sample synthetic devices (`scripts/generate_synthetic_devices.py`) | Friend | `data-catalog` `parallel-ok` | Yes | Yes | JSONL exists for demos |

### Phase 1.2 — First AWS deploy (Ship It)

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-1.2.1** | Copy `samconfig.toml.example` → `samconfig.toml`; set region + `DetectionMode=mock` | You | `infra-sam` `priority-p0` | Friend trains ML in parallel | No | Config committed *without secrets* or kept local |
| **I-1.2.2** | `./scripts/deploy.sh` (or `sam build && sam deploy`) | You | `infra-sam` `devops-deploy` `priority-p0` `blocker` | Friend: **parallel-ok** | No | Stack `CREATE_COMPLETE` |
| **I-1.2.3** | Note outputs: `ApiUrl`, `AssetsBucketName`, `UiBucketName`, `CloudFrontUrl`, KMS key | You | `devops-deploy` `docs` | Yes | No | Shared in team chat / Notion |
| **I-1.2.4** | Smoke: `POST /devices` with `{"device_model_key":"poweredge_r740"}` | You | `backend` `aws-integration` `priority-p0` | Yes | No | `202` + `execution_arn` |
| **I-1.2.5** | Confirm Step Functions `RecoveryFlow` → SUCCEEDED | You | `aws-integration` `backend` `priority-p0` | Yes | No | Execution green in console |
| **I-1.2.6** | Confirm DynamoDB Devices/Components/Passports + S3 passport objects | You | `aws-integration` `security-kms` | Yes | No | Rows + JSON in S3 |
| **I-1.2.7** | Confirm `GET /passports/{id}/verify` returns `valid: true` | You | `security-kms` `priority-p0` | Yes | No | Signature verifies |

### Phase 1.3 — Wire frontend to cloud API

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-1.3.1** | Set `frontend/.env` → `VITE_API_URL=<ApiUrl>` (no trailing slash issues) | You | `frontend` `devops-deploy` `priority-p0` | Yes | No | Run button enabled |
| **I-1.3.2** | `npm install && npm run dev` — complete one UI recovery | You | `frontend` `priority-p0` | Friend: ML | No | Results page shows plan + impact + passports |
| **I-1.3.3** | Deploy static UI to S3 + CloudFront (`npm run build` + sync) | You | `devops-deploy` `frontend` `priority-p1` | Yes | Can wait until Milestone 5 | Public URL works |

**Milestone 1 exit criteria:** One live E2E path without ML. Demo is already “working.”

---

## Milestone 2 — ML model (Friend’s track)

**Goal:** YOLO (or compatible) detector that returns the JSON schema our Lambda expects; optional SageMaker endpoint.  
**Labels:** `milestone` `ml-model` `priority-p1` `parallel-ok`  
**You can skip ahead to Milestone 3 with catalog mode if Friend is late.**

### Phase 2.1 — Dataset

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-2.1.1** | Collect / download PCB + server interior images (CC / Roboflow / TU Wien) | Friend | `ml-model` `data-catalog` | Yes vs M1 | Soft-skip: use catalog | ≥50 labeled images or clear plan |
| **I-2.1.2** | Label classes: CPU GPU RAM SSD HDD PSU NIC Fan Other | Friend | `ml-model` | Yes | Soft-skip | YOLO labels ready |
| **I-2.1.3** | Write `ml/training/data/data.yaml` | Friend | `ml-model` | Yes | Soft-skip | Train script finds data |

### Phase 2.2 — Train & evaluate

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-2.2.1** | Train via `train_yolo.py` or notebook | Friend | `ml-model` `priority-p1` | Yes | Soft-skip | `best.pt` exists |
| **I-2.2.2** | Record mAP / precision-recall for blog | Friend | `ml-model` `docs` | Yes | Soft-skip | Numbers ready for slides |
| **I-2.2.3** | Verify local inference output matches API schema (`detections[]` + normalized bbox) | Friend | `ml-model` `backend` | Yes | Soft-skip | ✅ `verify_inference_schema.py` + `data/sample_inference_output.json`; 9-class map reserved for later |

### Phase 2.3 — Package & SageMaker endpoint

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-2.3.1** | Build `model.tar.gz` (`model.pt` + `code/inference.py`) | Friend | `ml-model` `aws-integration` | Needs AWS account access | Soft-skip | ✅ `s3://regenesis-dev-assetsbucket-xp9zjtzuwy50/models/regenesis-yolo/model.tar.gz` |
| **I-2.3.2** | Create SageMaker model + endpoint (smallest / serverless if possible) | Friend + You | `ml-model` `aws-integration` `devops-deploy` | After M1 stack | Soft-skip | ✅ `regenesis-yolo-dev` (`ml.m5.large`) — delete when idle |
| **I-2.3.3** | Cost guard: document “delete endpoint when idle” | Both | `devops-deploy` `docs` `priority-p0` | Yes | No | ✅ `docs/SAGEMAKER_COST_GUARD.md` + `scripts/sagemaker_endpoint.sh` |
| **I-2.3.4** | Redeploy SAM: `SageMakerEndpointName=...` `DetectionMode=auto` | You | `infra-sam` `blocked-by-ml` | Blocked until 2.3.2 | Soft-skip | ✅ `DetectionMode=auto` + `SageMakerEndpointName=regenesis-yolo-dev`; vision smoke OK |

**Milestone 2 exit criteria:** Either (A) vision path works on a sample image, or (B) team agrees to demo catalog-assisted with clear UI badge (still valid).

---

## Milestone 3 — AWS services integration hardening

**Goal:** Every planned AWS service is used for a real reason; fallbacks documented; metrics/notifications work.  
**Labels:** `milestone` `aws-integration` `backend` `priority-p0`

### Phase 3.1 — Detection path (vision + fallback)

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-3.1.1** | Test `DETECTION_MODE=auto` with real endpoint | You + Friend | `aws-integration` `ml-model` | After 2.3.4 | Soft-skip | `detection_source=vision` — code maps usable SageMaker (incl. hybrid mix) → `vision`; live proof: endpoint ON + `scripts/smoke_vision_auto.py` |
| **I-3.1.2** | Force low-confidence / missing endpoint → catalog-assisted path | You | `aws-integration` `backend` `priority-p0` | Yes | No | ✅ Fallback badge + audit verified (`tests/unit/test_detection_catalog_fallback.py` + `scripts/smoke_catalog_fallback.py --e2e`) |
| **I-3.1.3** | Exercise model-plate OCR on a photo with readable text | You | `aws-integration` `priority-p1` | Yes | Soft-skip | **Tesseract in Lambda** (no Textract). Fetch layer + redeploy, then `python scripts/smoke_plate_ocr.py --e2e` (or `--text-only-e2e`) |

### Phase 3.2 — Orchestration, storage, security

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-3.2.1** | Walk Step Functions console for demo screenshots | You | `aws-integration` `demo-video` | Yes | No | ✅ Clean success screenshot captured (`docs/screenshots/step_functions_recovery_flow_success.png` for execution `rec-05e0a8f8-a9d640`) |
| **I-3.2.2** | Verify S3 prefixes: images / logs / passports | You | `aws-integration` | Yes | No | ✅ Verified: 100% of keys match `docs/ARCHITECTURE.md` (`tests/unit/test_s3_key_prefixes.py` + `scripts/verify_s3_prefixes.py`) |
| **I-3.2.3** | Tamper test: edit passport JSON → verify fails | You | `security-kms` `priority-p1` | Yes | Soft-skip | ✅ Verified: KMS detects tampering & returns valid: false (`tests/unit/test_passport_tamper.py` + `scripts/smoke_tamper_passport.py --e2e`) |
| **I-3.2.4** | SNS job-complete notification (email/subscription) | You | `aws-integration` `priority-p2` | Yes | Yes | ✅ Topic active & Step Functions wired; optional subscription management via `scripts/sns_subscribe_notifications.py` |
| **I-3.2.5** | CloudWatch metrics: ComponentsRecovered, CO2eAvoidedKg, DetectionFallbackUsed | You | `aws-integration` `priority-p1` | Yes | No | ✅ All 3 metrics active in `ReGenesis` namespace (ap-south-1); real data: ComponentsRecovered=243, CO2eAvoidedKg=7,786, DetectionFallbackUsed=5 over Oct 09–10. Dashboard screenshot: `docs/screenshots/cloudwatch_custom_metrics_dashboard.png`. Emitted by `ImpactSummaryFunction` via `put_metric_data`. |

### Phase 3.3 — API completeness

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-3.3.1** | `GET /devices/{id}` returns plan + audit + impact | You | `backend` `priority-p0` | Yes | No | ✅ Matches UI needs: returns full device snapshot including plan, audit, and impact (both root convenience keys and nested in `device`), components, and passports. Verified live on API Gateway (`https://roz4wu5br7.execute-api.ap-south-1.amazonaws.com/Prod/devices/{id}`) via `scripts/smoke_get_device.py` & unit tests (`tests/unit/test_get_device.py`). |
| **I-3.3.2** | `GET /jobs?execution_arn=` polling stable | You | `backend` `frontend` | Yes | No | ✅ UI status updates: Lambda handles unquoted/encoded ARNs, catches 404 ExecutionDoesNotExist without 502 crash, exposes execution errors/causes, and includes CORS. Frontend polling stops on terminal states (`SUCCEEDED`/`FAILED`) and avoids unmounting on transient glitches. Verified live on API Gateway + Step Functions (`scripts/smoke_get_job_status.py`) & unit tests (`tests/unit/test_get_job_status.py`). |
| **I-3.3.3** | Image upload base64 path stores in S3 and is used by detection | You | `backend` `aws-integration` | Yes | Soft-skip if model-only demo | ✅ Image key non-empty: `POST /devices` decodes base64 (including data URI prefixes), persists image to `s3://{bucket}/images/{device_id}/original.{ext}`, records `image_s3_key` in DynamoDB `DevicesTable`, and passes it to Step Functions & `InvokeDetectionFunction` for OCR & model detection. Verified live against AWS (`scripts/smoke_image_upload.py`) & unit tests (`tests/unit/test_image_upload_detection.py`). |

**Milestone 3 exit criteria:** Service map in `docs/AWS_SERVICES.md` matches what judges can see in console.

---

## Milestone 4 — Product completeness (logic, not pretty UI)

**Goal:** RVS plan, completeness audit, diagnostics, impact numbers are coherent for the R740 story.  
**Labels:** `milestone` `backend` `data-catalog` `priority-p0`

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-4.1** | RVS ordering readable in plan timeline | Both | `backend` `data-catalog` | Yes | No | ✅ High-value parts prioritized: PowerEdge R740 removal rules & fallback planner order parts by RVS descending (GPUs [RVS 132.30] and PSUs [RVS 26.89] scheduled immediately after top cover prerequisite). Enhanced plan model outputs `total_plan_rvs`, `step_rvs`, and `priority_tier`. Frontend `PlanTimeline` component displays RVS score badges, priority pills, and risk coding. Verified via unit tests (`tests/unit/test_planner_rvs.py`) and smoke test (`scripts/smoke_plan_rvs_timeline.py`). |
| **I-4.2** | Completeness audit flags under-detection | You | `backend` `ml-model` | Yes | Soft-skip | ✅ Meaningful gaps array: `completeness_audit` compares raw vision against device BOM to identify under-detected components with missing counts, deficit percentages, severity tiers (`critical`, `high`, `medium`), human-readable explanations, and catalog fallback remediation notes. Surplus detections outside BOM are tracked. Frontend `JobResults.tsx` renders an audit card with score, gap tags, and deficit badges. Verified via unit tests (`tests/unit/test_completeness_audit.py`) and smoke test (`scripts/smoke_completeness_audit.py`). |
| **I-4.3** | Deterministic diagnostics (same `component_id` → same results) | You | `backend` | Yes | No | ✅ 100% Deterministic & repeatable demo: `run_component_diagnostics` strictly seeds Python's RNG from `SHA-256(component_id)`, ensuring byte-for-byte identical status, health scores, test profile metrics, and letter grades (`Grade A/B/C/F`) across repeated runs. Device-seeded component generation ensures golden R740 runs are completely reproducible before video recording. Verified via unit tests (`tests/unit/test_deterministic_diagnostics.py`) and smoke test (`scripts/smoke_deterministic_diagnostics.py`). |
| **I-4.4** | Impact panel numbers cite catalog factors; ranges shown | Both | `data-catalog` `docs` | Yes | No | ✅ Honest ranges citing catalog factors: `components_specs.json` expanded with empirical ranges (`embodied_co2e_range_kg`, `mass_range_kg`) and LCA citations across all 9 component classes. `compute_impact_summary` computes bottom-up empirical ranges (`co2e_avoided_kg_range`, `mass_diverted_kg_range`) and structured `factor_citations` instead of fake multipliers. Frontend `ImpactPanel.tsx` presents honest carbon ranges vs shred baseline, factor citation banner, and an audit table citing Dell Server LCA & academic hardware carbon benchmarks. Verified via unit tests (`tests/unit/test_impact_calc.py`) and smoke test (`scripts/smoke_impact_factors.py`). |

| **I-4.5** | PipelineEvents table usable for debugging | You | `aws-integration` `backend` | Yes | Soft-skip | ✅ Events per pipeline stage: New `get_events` Lambda at `GET /devices/{device_id}/events` queries `PipelineEventsTable` returning chronologically sorted audit events for all stages (`ingest`, `detect`, `parse`, `plan`, `test`, `passport`, `impact`). `log_pipeline_event` hardened with try/except + returns `event_id`. `get_device` now includes `pipeline_events` in its response. `get_pipeline_events` helper added to `aws_helpers.py`. Frontend `JobResults.tsx` adds "Pipeline Audit Log" card with stage completion indicators and detail rows per event. Filtering (`?event_type=detect`) and `stage_summary` aggregation supported. IAM policy for `GetEventsFunction` added to SAM template. Verified via 8 unit tests (`tests/unit/test_pipeline_events.py`) and smoke test (`scripts/smoke_pipeline_events.py`). |

| **I-4.6** | Add 2nd device type path (laptop or switch) for stretch | Friend/You | `data-catalog` `priority-p2` | Yes | Yes | Optional |

**Milestone 4 exit criteria:** One “golden” R740 run you can repeat before the video.

---

## Milestone 5 — Frontend multipage UX (after functional)

**Goal:** Sleek minimal multipage site. Do **after** Milestones 1–4 are green enough.  
**Labels:** `milestone` `frontend` `priority-p1`

### Suggested pages

1. Landing / problem & impact  
2. New recovery (upload + model)  
3. Device dashboard (job status, detections, plan)  
4. Passports list + detail + verify  
5. Impact report  
6. How it works / AWS (for judges)

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-5.1** | Information architecture + route map | Both | `frontend` `docs` | After M1 | Soft-skip: keep 2 pages | Routes agreed |
| **I-5.2** | Shared layout, nav, design tokens (minimal sleek) | You or Friend | `frontend` `priority-p1` | After M1 | Soft-skip | Consistent look |
| **I-5.3** | Landing page (problem + CTA) | Either | `frontend` | After M1 | Soft-skip | First viewport strong |
| **I-5.4** | Recovery + live dashboard polish (loading, empty, errors) | Either | `frontend` `priority-p0` | After M1 | No | Demo path frictionless |
| **I-5.5** | Passports + verify UX | Either | `frontend` `security-kms` | After M1 | Soft-skip | One-click verify |
| **I-5.6** | Impact page / section | Either | `frontend` | After M1 | Soft-skip | Numbers clear for judges |
| **I-5.7** | Redeploy UI to CloudFront | You | `devops-deploy` `frontend` | After I-5.x | Soft-skip local-only | Prod URL |

**Parallel note:** Frontend polish can start as soon as **I-1.3.1** works; do not wait for SageMaker.

---

## Milestone 6 — Demo video & submission

**Goal:** 3‑minute recorded demo + Builder Center write-up + repo link.  
**Labels:** `milestone` `demo-video` `docs` `priority-p0`

| ID | Issue | Owner | Labels | Parallel? | Skip? | Done when |
|----|-------|-------|--------|-----------|-------|-----------|
| **I-6.1** | Rehearse `docs/DEMO_SCRIPT.md` timed to ≤3:00 | Both | `demo-video` | After golden run | No | Timing fits |
| **I-6.2** | Record screencast (upload → detect → plan → test → passport verify → impact → AWS callout) | Both | `demo-video` `priority-p0` | After M1+ | No | Video file / YouTube |
| **I-6.3** | Capture Step Functions + architecture screenshots | You | `demo-video` `aws-integration` | Yes | Soft-skip | Assets ready |
| **I-6.4** | Builder Center blog (`docs/SUBMISSION.md`) | Both | `docs` `priority-p0` | Parallel with polish | No | Published + linked |
| **I-6.5** | Submit track **Waste and Energy**; links: repo, demo URL, video | Both | `docs` `priority-p0` | Last | No | Submitted |
| **I-6.6** | Delete SageMaker endpoint / idle costly resources | You | `devops-deploy` `priority-p0` | After video | No | Credits protected |

---

## Swimlanes — what you can skip while Friend works

```text
TIME →
YOU:     [M0 CLI]──[M1 SAM deploy E2E mock]──[M3 harden]──[M4 golden]──[M5 UI]──[M6 video]
FRIEND:  [M0 setup]──[M2 dataset]──[M2 train]──[M2 endpoint]──┐
                                                              └─ merge into You at I-2.3.4 / I-3.1.1
```

| If Friend is late… | You still do |
|--------------------|--------------|
| No dataset | Keep `DetectionMode=mock` / catalog |
| No endpoint | Demo catalog-assisted + explain design |
| No mAP numbers | Cite architecture + impact KPIs |

| If You are late on deploy… | Friend still does |
|----------------------------|-------------------|
| No ApiUrl | Train + package model offline |
| No stack | Unit tests + local JSON fixtures |

---

## GitHub Issues (auto-create)

Issues, **milestones**, and **labels** (phase, `ml-model`, `aws-integration`, `service-*`, owners, priorities) are created by:

```bash
gh auth login          # one-time, in your terminal
python3 scripts/github_bootstrap_issues.py
```

### SAM CLI on macOS (pyexpat error)

If `sam build` fails with `ImportError: pyexpat` / `XML_SetAllocTrackerActivationThreshold`, run once per terminal:

```bash
source scripts/sam-env.sh
```

Or use `./scripts/deploy.sh` (includes the fix). Permanent fix: add the `DYLD_LIBRARY_PATH` line from `scripts/sam-env.sh` to your `~/.zshrc`.

Options: `--repo mitra9917/ReGenesis` · `--dry-run` (preview commands)

Re-run is safe: existing issue titles are skipped. Assign teammates manually using labels `owner-you` / `owner-friend` / `owner-both`.

Milestone names on GitHub:

1. `M0 Tooling & MCP`  
2. `M1 Foundation green`  
3. `M2 ML model`  
4. `M3 AWS integration`  
5. `M4 Product completeness`  
6. `M5 Frontend multipage`  
7. `M6 Demo & submit`

---

## Definition of Done (whole project)

- [ ] Deployed API + UI URL  
- [ ] E2E recovery on R740 (vision **or** catalog-assisted)  
- [ ] Passports mint + KMS verify works  
- [ ] Impact numbers shown  
- [ ] AWS services visible in demo (Step Functions + KMS at minimum)  
- [ ] Multipage UI polished enough for judges (or strong 2-page if time)  
- [ ] ≤3 min video + Builder Center post + submission form  

---

## Quick start today (both)

1. **Both:** Finish Milestone 0 (CLI + optional MCP).  
2. **You:** Start **I-1.2.x** (deploy).  
3. **Friend:** Start **I-2.1.x** (dataset) immediately — do not wait for deploy.  
4. Meet when **I-1.2.5** and **I-2.2.1** are done to schedule endpoint merge (**I-2.3.4**).  
5. **Only then** deep multipage UI (**M5**) and video (**M6**).
