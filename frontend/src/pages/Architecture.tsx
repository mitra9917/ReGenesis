import React from "react";

export function ArchitecturePage() {
  const pipelineStages = [
    {
      step: "01",
      name: "Ingest",
      lambda: "IngestFunction",
      aws: "Amazon S3 + API Gateway",
      purpose: "Accepts base64 chassis intake photos or device models, stores raw image in S3 images/ prefix, creates DynamoDB device row.",
      latency: "~120ms",
    },
    {
      step: "02",
      name: "Invoke Detection",
      lambda: "InvokeDetectionFunction",
      aws: "SageMaker (YOLOv8) + Tesseract OCR layer",
      purpose: "Detects internal subassemblies (CPU, GPU, RAM, SSD, PSU) via SageMaker endpoint or runs catalog-assisted fallback with Tesseract plate OCR.",
      latency: "~380ms",
    },
    {
      step: "03",
      name: "Parse & Audit",
      lambda: "ParseDetectionsFunction",
      aws: "AWS Lambda + Python Layer",
      purpose: "Performs BOM completeness audit against catalog specs. Flags under-detection gaps, deficit percentages, and remediation advice.",
      latency: "~45ms",
    },
    {
      step: "04",
      name: "Plan Disassembly",
      lambda: "PlanDisassemblyFunction",
      aws: "AWS Lambda + Attachment Graph",
      purpose: "Generates prioritized disassembly sequences based on Recovery Value Score (RVS). High-value GPUs & PSUs scheduled immediately after prerequisites.",
      latency: "~60ms",
    },
    {
      step: "05",
      name: "Run Diagnostics",
      lambda: "RunDiagnosticsFunction",
      aws: "AWS Lambda + Deterministic Tests",
      purpose: "Runs seeded diagnostic test profiles per component ID (e.g. SHA-256 seeding). Evaluates health scores and assigns letter grades (Grade A/B/C/F).",
      latency: "~85ms",
    },
    {
      step: "06",
      name: "Mint Passports",
      lambda: "MintPassportsFunction",
      aws: "AWS KMS + DynamoDB + S3",
      purpose: "Signs Digital Product Passports using KMS asymmetric ECC_NIST_P256 private key. Stores tamper-evident records in DynamoDB and S3 passports/ prefix.",
      latency: "~150ms",
    },
    {
      step: "07",
      name: "Calculate Impact",
      lambda: "CalculateImpactFunction",
      aws: "CloudWatch Custom Metrics + SNS",
      purpose: "Aggregates embodied carbon avoided ranges and mass diverted citing empirical LCA factors. Emits custom CloudWatch metrics and publishes SNS alerts.",
      latency: "~90ms",
    },
  ];

  const servicesList = [
    {
      name: "AWS Step Functions",
      role: "Workflow Orchestrator",
      desc: "Manages state transitions, retries, and error handling across all 7 asynchronous pipeline stages without server overhead.",
      badge: "Core Orchestrator",
    },
    {
      name: "Amazon SageMaker",
      role: "Computer Vision Inference",
      desc: "Hosts YOLOv8 object detection model for identifying server components from high-resolution chassis images.",
      badge: "AI / ML",
    },
    {
      name: "Tesseract OCR (Lambda layer)",
      role: "Model Plate OCR",
      desc: "Extracts manufacturer labels, serial numbers, and regulatory plates via AL2023 Tesseract binaries on Lambda (no Textract).",
      badge: "OCR / Layer",
    },
    {
      name: "AWS KMS",
      role: "Cryptographic DPP Signer",
      desc: "Asymmetric ECC_NIST_P256 key pair signs Digital Product Passports. Enables tamper-proof verification via public key.",
      badge: "Security & Trust",
    },
    {
      name: "Amazon DynamoDB",
      role: "Single-Table Data Store",
      desc: "Sub-millisecond access to Devices, Components, Passports, and chronological PipelineEvents audit records.",
      badge: "Database",
    },
    {
      name: "Amazon S3",
      role: "Object Storage",
      desc: "Partitioned storage with strict prefixes: images/ for intake photos, passports/ for signed certificates, logs/ for telemetry.",
      badge: "Storage",
    },
    {
      name: "Amazon CloudWatch",
      role: "Telemetry & Custom Metrics",
      desc: "Logs structured execution logs and publishes custom metrics: ComponentsRecovered, CO2eAvoidedKg, and DisassemblyLatency.",
      badge: "Observability",
    },
    {
      name: "Amazon SNS",
      role: "Job Completion Alerts",
      desc: "Dispatches automated notification messages to refurbishment technicians upon recovery completion.",
      badge: "Messaging",
    },
  ];

  return (
    <div className="architecture-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">AWS Serverless Architecture &amp; System Flow</h1>
          <p className="page-subtitle">
            Engineered exclusively with native AWS managed services for the AWS Environmental Hacks Hackathon.
            Demonstrates zero-idle-cost serverless execution, deterministic ML fallbacks, and cryptographic provenance.
          </p>
        </div>
      </div>

      {/* Step Functions Interactive Flow */}
      <div className="card">
        <div className="card-header-flex">
          <div>
            <h2 className="card-heading">AWS Step Functions Recovery State Machine</h2>
            <p className="card-subtext">
              The 7 discrete serverless Lambda stages orchestrated by Step Functions (RecoveryFlowStateMachine):
            </p>
          </div>
          <span className="badge-aws">Step Functions · Native Orchestration</span>
        </div>

        <div className="pipeline-flow-list">
          {pipelineStages.map((stage, idx) => (
            <div key={stage.step} className="pipeline-stage-item">
              <div className="stage-left">
                <div className="stage-step-num">{stage.step}</div>
                <div>
                  <h4 className="stage-name">{stage.name}</h4>
                  <span className="stage-lambda font-mono">{stage.lambda}</span>
                </div>
              </div>

              <div className="stage-middle">
                <p className="stage-purpose">{stage.purpose}</p>
                <div className="stage-aws-badge">{stage.aws}</div>
              </div>

              <div className="stage-right">
                <span className="stage-latency font-mono">{stage.latency}</span>
                <span className="stage-status-dot"></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AWS Cloud Services Matrix */}
      <div className="card">
        <h2 className="card-heading">AWS Services Implementation Matrix</h2>
        <p className="card-subtext">
          Enterprise cloud primitives deployed via AWS Serverless Application Model (SAM):
        </p>

        <div className="services-grid">
          {servicesList.map((svc) => (
            <div key={svc.name} className="service-card">
              <div className="service-card-top">
                <h4 className="service-name">{svc.name}</h4>
                <span className="service-badge">{svc.badge}</span>
              </div>
              <div className="service-role">{svc.role}</div>
              <p className="service-desc">{svc.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Hackathon Rubric Alignment */}
      <div className="card">
        <h2 className="card-heading">Hackathon Rubric &amp; Architectural Highlights</h2>
        <div className="rubric-grid">
          <div className="rubric-box">
            <h4 className="rubric-title">Waste &amp; Energy Impact</h4>
            <p className="rubric-text">
              Directly addresses the 50M+ metric ton global e-waste challenge. Captures 92–96% of embodied semiconductor energy by keeping functional enterprise chips out of scrap smelters.
            </p>
          </div>
          <div className="rubric-box">
            <h4 className="rubric-title">Resilience &amp; Fail-Safe Design</h4>
            <p className="rubric-text">
              Dual-mode optical detection: utilizes SageMaker YOLOv8 if deployed, with seamless fallback to Tesseract plate OCR + catalog specs. Cost guards prevent endpoint sprawl.
            </p>
          </div>
          <div className="rubric-box">
            <h4 className="rubric-title">Cryptographic Integrity</h4>
            <p className="rubric-text">
              Hardware passports are digitally signed with AWS KMS asymmetric ECC keys. Any alteration of component grade, health score, or serial number results in instant signature rejection.
            </p>
          </div>
          <div className="rubric-box">
            <h4 className="rubric-title">Full Multi-Device Catalog</h4>
            <p className="rubric-text">
              Supports Dell PowerEdge R740 (servers), Lenovo ThinkPad T14 (laptops), and Cisco Catalyst 9300 (switches) through generic JSON catalog schemas and attachment DAGs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
