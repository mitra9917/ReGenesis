# RE:GENESIS — Frontend Information Architecture & Route Map

**Milestone:** M5 Frontend Multipage UX  
**Issue:** I-5.1 (Issue #47)  
**Status:** Agreed & Implemented  

---

## 1. Objectives & Principles

The RE:GENESIS web application provides an autonomous electronics recovery dashboard and Second-Life Hardware Passport explorer for enterprise e-waste triage. The information architecture is designed for:
1. **Recycling Operators & Technicians:** Rapid optical intake, automatic BOM completeness auditing, and step-by-step prioritized disassembly instructions.
2. **Secondary Hardware Buyers & Refurbishers:** Cryptographically verifiable digital product passports (DPPs) with hardware health grades and component lineage.
3. **Sustainability Auditors & Judges:** Empirical lifecycle analysis (LCA) impact reports, avoided embodied carbon metrics, and transparent AWS cloud architectural proofs.

---

## 2. Route Hierarchy & Navigation Map

```text
/ (Landing / Problem & Overview)
├── /recovery (Device Intake & Optical Ingest)
│    └── [Alias: /upload]
├── /devices/:deviceId (Device Recovery Dashboard & Workflow Monitor)
│    ├── Live Step Functions Polling
│    ├── Optical Detection Visualizer & YOLO Bounding Boxes
│    ├── BOM Completeness Audit & Under-Detection Gaps
│    ├── RVS-Prioritized Disassembly Plan Timeline
│    ├── Minted Hardware Passports (KMS Asymmetric Signed)
│    └── Chronological Pipeline Events Audit Log
├── /passports (Digital Product Passport Registry & Verification)
│    ├── One-Click Cryptographic KMS Signature Verification
│    ├── Tamper Detection Demonstrator (Hash Mismatch Simulation)
│    └── Component Lineage & Health Grading
├── /impact (Macro Carbon & Material Recovery Report)
│    ├── Embodied CO2e Avoidance vs Industrial Shredding
│    ├── Landfill Diverted Mass & Critical Minerals (Nd, Au, Cu, Co)
│    └── Scientific LCA Benchmark Factor Citations
└── /architecture (AWS Architecture & How It Works)
     ├── [Alias: /how-it-works]
     ├── Interactive 7-Stage Step Functions Pipeline
     └── Serverless Services Map (Lambda, SageMaker, Textract, KMS, DynamoDB, S3)
```

---

## 3. Page Specifications & Backend Integrations

| Route | View Component | Target Audience | Key Capabilities & Backend API Integrations |
|---|---|---|---|
| `/` | `Landing.tsx` | All / Hackathon Judges | Executive problem statement, real-time recovery metrics counter, quick intake CTA, one-click golden demo previews (`poweredge_r740`, `thinkpad_t14`, `cisco_catalyst_9300`). |
| `/recovery` | `Upload.tsx` | Operators | Multi-device intake selection, plate OCR preview, photo dropzone with base64 compression. Connects to `POST /devices`. |
| `/devices/:deviceId` | `JobResults.tsx` | Operators / Engineers | Live job status (`GET /jobs?execution_arn=...`), BOM completeness score & gaps (`GET /devices/{id}`), RVS disassembly timeline, KMS signed passports, pipeline audit log (`GET /devices/{id}/events`). Fallback support for instant offline demos. |
| `/passports` | `Passports.tsx` | Refurbishers / Buyers | Digital Product Passport explorer. Calls `GET /passports/{id}/verify` to validate KMS ECDSA_SHA_256 signatures against the KMS public key. Includes tamper simulator (`I-3.2.3`). |
| `/impact` | `ImpactReport.tsx` | ESG Auditors / Judges | Macro environmental metrics, empirical carbon avoided ranges (`co2e_avoided_kg_range`), diverted mass, and peer-reviewed Dell Server LCA factor citations (`I-4.4`). |
| `/architecture` | `Architecture.tsx` | Judges / Engineers | Interactive system diagram showcasing Step Functions state machine, hybrid ML (SageMaker YOLOv8 + fallback), KMS asymmetric key signing, and DynamoDB single-table design. |

---

## 4. Design System & Tokens

- **Aesthetic:** High-contrast cyber-industrial dark theme with glassmorphic cards and subtle neon accents.
- **Color Tokens:**
  - Primary Background: `#0a0f16` / `#0e141f`
  - Card Surface: `rgba(18, 26, 38, 0.75)` with `backdrop-filter: blur(12px)`
  - Accent / ReGenesis Emerald: `#3dd6a5` (Eco-recovery highlight)
  - Secondary / Vision Cyan: `#6eb6ff` (AI detection & vision tokens)
  - Warning / Deficit Amber: `#f5b942` (Completeness gap warnings)
  - Danger / Tamper Coral: `#f07178` (Cryptographic verification failure)
  - Border: `rgba(45, 62, 88, 0.65)`
- **Typography:** Modern clean sans-serif (`Outfit`, `DM Sans`, `system-ui`) with monospace data tags for component hashes and serial numbers.
