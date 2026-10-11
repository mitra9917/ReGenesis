import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

/* Interactive RecoveryFlow explorer — CSS transitions only (no motion lib). */

type Stage = {
  step: string;
  name: string;
  lambda: string;
  aws: string;
  purpose: string;
  latency: string;
  io: string;
};

const PIPELINE: Stage[] = [
  {
    step: "01",
    name: "Ingest",
    lambda: "IngestFunction",
    aws: "API Gateway · S3 · DynamoDB",
    purpose:
      "Accepts chassis photo + model key, stores the image under images/, creates the Devices row, and starts RecoveryFlow.",
    latency: "~120ms",
    io: "POST /devices → execution_arn",
  },
  {
    step: "02",
    name: "Detect",
    lambda: "InvokeDetectionFunction",
    aws: "SageMaker YOLO · Tesseract OCR",
    purpose:
      "Runs vision when the endpoint is InService; otherwise catalog-assisted layout. Plate OCR can confirm the device model.",
    latency: "~380ms",
    io: "detections[] · detection_source",
  },
  {
    step: "03",
    name: "Audit",
    lambda: "ParseDetectionsFunction",
    aws: "Lambda · BOM catalog",
    purpose:
      "Compares detections to the engineering BOM, scores completeness, and surfaces under-detection gaps before teardown.",
    latency: "~45ms",
    io: "completeness_audit · Components",
  },
  {
    step: "04",
    name: "Plan",
    lambda: "PlanDisassemblyFunction",
    aws: "Lambda · attachment graph",
    purpose:
      "Orders extraction by Reuse Value Score so high-embodied parts (GPUs, PSUs) come first with prerequisites respected.",
    latency: "~60ms",
    io: "disassembly_plan · RVS",
  },
  {
    step: "05",
    name: "Test",
    lambda: "RunDiagnosticsFunction",
    aws: "Lambda Map · seeded RNG",
    purpose:
      "Deterministic diagnostics per component_id (SHA-256 seed) produce health scores and letter grades for reuse qualification.",
    latency: "~85ms",
    io: "test_results · grades",
  },
  {
    step: "06",
    name: "Passport",
    lambda: "MintPassportsFunction",
    aws: "KMS · DynamoDB · S3",
    purpose:
      "Signs Second-Life Passports with asymmetric KMS (ECDSA_SHA_256). Tampering the JSON fails verify.",
    latency: "~150ms",
    io: "passports/{id}.json",
  },
  {
    step: "07",
    name: "Impact",
    lambda: "CalculateImpactFunction",
    aws: "CloudWatch · SNS",
    purpose:
      "Aggregates honest LCA ranges for CO₂e avoided and mass diverted, emits custom metrics, and can notify via SNS.",
    latency: "~90ms",
    io: "impact_summary · metrics",
  },
];

const SERVICES = [
  {
    name: "Step Functions",
    role: "Orchestrator",
    badge: "Core",
    desc: "RecoveryFlow owns retries, Map diagnostics, and a visible console trail for every job.",
  },
  {
    name: "SageMaker",
    role: "Vision",
    badge: "ML",
    desc: "YOLO v3 endpoint for chassis parts — delete when idle so credits stay intact.",
  },
  {
    name: "Tesseract layer",
    role: "OCR",
    badge: "Layer",
    desc: "Nameplate text confirms catalog model keys without Textract spend.",
  },
  {
    name: "KMS",
    role: "Trust",
    badge: "Security",
    desc: "Asymmetric Sign / Verify for Digital Product Passports buyers can check.",
  },
  {
    name: "DynamoDB",
    role: "State",
    badge: "Data",
    desc: "Devices, Components, Passports, and PipelineEvents for live UI polling.",
  },
  {
    name: "S3",
    role: "Artifacts",
    badge: "Storage",
    desc: "images/, logs/, and passports/ prefixes keep evidence durable and auditable.",
  },
  {
    name: "CloudWatch",
    role: "Telemetry",
    badge: "Ops",
    desc: "ComponentsRecovered, CO2eAvoidedKg, DetectionFallbackUsed custom metrics.",
  },
  {
    name: "SNS",
    role: "Notify",
    badge: "Hook",
    desc: "Optional job-complete signal for technicians or ERP integrations.",
  },
];

const HIGHLIGHTS = [
  {
    title: "Waste & Energy",
    text: "Reuse before shred — preserve embodied semiconductor carbon instead of smelting functional parts.",
  },
  {
    title: "Fail-safe vision",
    text: "SageMaker when live; catalog-assisted when confidence or the endpoint is down.",
  },
  {
    title: "Cryptographic DPPs",
    text: "KMS signatures make health scores and serials tamper-evident for secondary markets.",
  },
  {
    title: "Multi-device catalog",
    text: "PowerEdge R740, ThinkPad T14, and Catalyst 9300 share one schema and planner.",
  },
];

export function ArchitecturePage() {
  const [active, setActive] = useState(0);
  const stage = PIPELINE[active];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setActive((i) => Math.min(PIPELINE.length - 1, i + 1));
      if (e.key === "ArrowLeft") setActive((i) => Math.max(0, i - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="arch-page">
      <header className="arch-hero">
        <p className="dpp-section-index">System · AWS SAM</p>
        <h1 className="arch-hero-title">
          One RecoveryFlow. <em>Seven</em> Lambda stages.
        </h1>
        <p className="arch-hero-lede">
          Serverless orchestration on Step Functions — vision, BOM audit, RVS planning,
          diagnostics, KMS passports, and impact — with a path that still works when
          SageMaker is off.
        </p>
        <div className="arch-hero-actions">
          <Link to="/recovery" className="pl-btn pl-btn-primary">
            Run a recovery →
          </Link>
          <Link to="/devices/sample-r740" className="pl-btn pl-btn-secondary">
            Open R740 demo
          </Link>
        </div>
      </header>

      <section className="arch-panel arch-flow-panel" aria-labelledby="flow-heading">
        <div className="arch-panel-head">
          <div>
            <p className="dpp-section-index">01 / Orchestration</p>
            <h2 id="flow-heading" className="arch-panel-title">
              RecoveryFlow state machine
            </h2>
            <p className="arch-panel-lede">
              Click a stage (or use ← →). The active step expands — same order as the live
              Step Functions console.
            </p>
          </div>
          <span className="arch-chip">Native Step Functions</span>
        </div>

        <div className="arch-flow-track" role="tablist" aria-label="Pipeline stages">
          {PIPELINE.map((s, idx) => (
            <button
              key={s.step}
              type="button"
              role="tab"
              aria-selected={idx === active}
              className={`arch-flow-node ${idx === active ? "is-active" : ""} ${idx < active ? "is-done" : ""}`}
              onClick={() => setActive(idx)}
              style={{ transitionDelay: `${idx * 40}ms` }}
            >
              <span className="arch-flow-num">{s.step}</span>
              <span className="arch-flow-label">{s.name}</span>
              {idx < PIPELINE.length - 1 && <span className="arch-flow-connector" aria-hidden="true" />}
            </button>
          ))}
        </div>

        <article
          key={stage.step}
          className="arch-stage-detail"
          role="tabpanel"
          aria-label={stage.name}
        >
          <div className="arch-stage-detail-top">
            <div>
              <p className="arch-stage-kicker">
                Stage {stage.step} · <span className="font-mono">{stage.lambda}</span>
              </p>
              <h3 className="arch-stage-title">{stage.name}</h3>
            </div>
            <div className="arch-stage-meta">
              <span className="arch-meta-pill">{stage.latency}</span>
              <span className="arch-meta-pill arch-meta-pill-lime">{stage.io}</span>
            </div>
          </div>
          <p className="arch-stage-purpose">{stage.purpose}</p>
          <p className="arch-stage-aws">
            <span>AWS</span> {stage.aws}
          </p>
          <div className="arch-stage-nav">
            <button
              type="button"
              className="pl-btn pl-btn-secondary"
              disabled={active === 0}
              onClick={() => setActive((i) => i - 1)}
            >
              ← Previous
            </button>
            <button
              type="button"
              className="pl-btn pl-btn-primary"
              disabled={active === PIPELINE.length - 1}
              onClick={() => setActive((i) => i + 1)}
            >
              Next stage →
            </button>
          </div>
        </article>
      </section>

      <section className="arch-panel" aria-labelledby="services-heading">
        <div className="arch-panel-head">
          <div>
            <p className="dpp-section-index">02 / Services</p>
            <h2 id="services-heading" className="arch-panel-title">
              AWS implementation matrix
            </h2>
            <p className="arch-panel-lede">
              Every service has a job — no ornamental cloud logos.
            </p>
          </div>
        </div>
        <div className="arch-services">
          {SERVICES.map((svc, idx) => (
            <article
              key={svc.name}
              className="arch-service"
              style={{ transitionDelay: `${80 + idx * 35}ms` }}
            >
              <div className="arch-service-top">
                <h3>{svc.name}</h3>
                <span className="arch-service-badge">{svc.badge}</span>
              </div>
              <p className="arch-service-role">{svc.role}</p>
              <p className="arch-service-desc">{svc.desc}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="arch-panel" aria-labelledby="rubric-heading">
        <div className="arch-panel-head">
          <div>
            <p className="dpp-section-index">03 / Why it scores</p>
            <h2 id="rubric-heading" className="arch-panel-title">
              Rubric highlights
            </h2>
          </div>
        </div>
        <div className="arch-rubric">
          {HIGHLIGHTS.map((h, idx) => (
            <article
              key={h.title}
              className="arch-rubric-item"
              style={{ transitionDelay: `${120 + idx * 40}ms` }}
            >
              <span className="arch-rubric-num">0{idx + 1}</span>
              <div>
                <h3>{h.title}</h3>
                <p>{h.text}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
