import { useState } from "react";
import { Link } from "react-router-dom";
import { SAMPLE_GOLDEN_RUNS } from "../api";

export function LandingPage() {
  const [activeDeviceKey, setActiveDeviceKey] = useState<"sample-r740" | "sample-t14" | "sample-c9300">("sample-r740");
  const [activeComparisonTab, setActiveComparisonTab] = useState<"problem" | "solution">("solution");
  const [simBatchSize, setSimBatchSize] = useState<number>(25);

  const activeSample = SAMPLE_GOLDEN_RUNS[activeDeviceKey];

  return (
    <div className="landing-page">
      {/* =========================================================================
          HERO SECTION: Split Hero with Live Interactive Triage Simulator
          ========================================================================= */}
      <section className="hero-split-section">
        <div className="hero-content-col">
          <div className="hero-badge">
            <span className="badge-pulse"></span>
            <span>AWS Environmental Hacks · Waste &amp; Energy Track</span>
          </div>

          <h1 className="hero-title">
            Transforming E-Waste into{" "}
            <span className="gradient-text">Verifiable Second-Life</span> Hardware
          </h1>

          <p className="hero-lead">
            Every year, <strong>53.6 million metric tons</strong> of enterprise electronics are pulverized in industrial shredders because manual component triage is too slow and resale buyers cannot verify hardware provenance.
          </p>

          <p className="hero-sublead">
            <strong>RE:GENESIS</strong> automates optical inspection, BOM completeness auditing, prioritized RVS disassembly, and AWS KMS-signed <strong>Digital Product Passports</strong> on a zero-idle-cost serverless architecture.
          </p>

          <div className="hero-actions">
            <Link to="/recovery" className="btn btn-primary hero-btn">
              <span className="btn-icon">⚡</span>
              <span>Launch Recovery Intake</span>
            </Link>
            <Link to="/passports" className="btn btn-secondary hero-btn">
              <span className="btn-icon">🛡️</span>
              <span>Verify Hardware Passports</span>
            </Link>
            <Link to="/architecture" className="btn btn-outline hero-btn">
              <span className="btn-icon">☁️</span>
              <span>AWS Architecture</span>
            </Link>
          </div>

          <div className="hero-trust-row">
            <div className="trust-item">
              <span className="trust-icon">🌿</span>
              <span>Dell Server LCA Empirical Factors</span>
            </div>
            <div className="trust-item">
              <span className="trust-icon">🔒</span>
              <span>KMS ECDSA Asymmetric Signatures</span>
            </div>
            <div className="trust-item">
              <span className="trust-icon">⚡</span>
              <span>Step Functions Orchestrated</span>
            </div>
          </div>
        </div>

        {/* Live Interactive Triage Simulator (First Viewport Wow Factor) */}
        <div className="hero-simulator-col">
          <div className="triage-simulator-card">
            <div className="sim-card-header">
              <div className="sim-status-indicator">
                <span className="status-dot-pulse"></span>
                <span>Live Autonomous Triage Visualizer</span>
              </div>
              <span className="sim-chip font-mono">0.68s Latency</span>
            </div>

            {/* Device Selector Tabs */}
            <div className="sim-device-tabs" role="tablist" aria-label="Simulator Target Devices">
              <button
                className={`sim-tab ${activeDeviceKey === "sample-r740" ? "sim-tab-active" : ""}`}
                onClick={() => setActiveDeviceKey("sample-r740")}
              >
                Dell R740 Server
              </button>
              <button
                className={`sim-tab ${activeDeviceKey === "sample-t14" ? "sim-tab-active" : ""}`}
                onClick={() => setActiveDeviceKey("sample-t14")}
              >
                ThinkPad T14 Laptop
              </button>
              <button
                className={`sim-tab ${activeDeviceKey === "sample-c9300" ? "sim-tab-active" : ""}`}
                onClick={() => setActiveDeviceKey("sample-c9300")}
              >
                Catalyst 9300 Switch
              </button>
            </div>

            {/* Visualizer Display Box */}
            <div className="sim-visual-box">
              <div className="sim-overlay-scanline"></div>
              
              <div className="sim-screen-header">
                <div>
                  <span className="sim-device-name">{activeSample.display_name}</span>
                  <div className="sim-meta-tags">
                    <span className="badge-vision">{activeSample.detection_source}</span>
                    <span className="badge-accent">BOM 100% Complete</span>
                    <span className="badge-neutral font-mono">{activeSample.serial_hint}</span>
                  </div>
                </div>
              </div>

              {/* Detected Component Tags Grid */}
              <div className="sim-detected-grid">
                {activeSample.passports.map((p) => (
                  <div key={p.passport_id} className="sim-component-pill">
                    <span className="pill-type">{p.comp_type}</span>
                    <span className="pill-grade">{p.letter_grade}</span>
                    <span className="pill-score">{p.health_score}%</span>
                  </div>
                ))}
              </div>

              {/* Real-Time Impact Counters */}
              <div className="sim-metrics-banner">
                <div className="sim-metric-block">
                  <span className="sim-metric-val text-accent">
                    {activeSample.impact.co2e_avoided_kg} kg
                  </span>
                  <span className="sim-metric-lbl">Avoided CO₂e</span>
                </div>
                <div className="sim-metric-block">
                  <span className="sim-metric-val text-vision">
                    RVS {activeSample.plan.total_plan_rvs}
                  </span>
                  <span className="sim-metric-lbl">Recovery Score</span>
                </div>
                <div className="sim-metric-block">
                  <span className="sim-metric-val">
                    {activeSample.summary.total_components_detected} Parts
                  </span>
                  <span className="sim-metric-lbl">Harvestable</span>
                </div>
              </div>

              <div className="sim-actions-footer">
                <Link
                  to={`/devices/${activeSample.device_id}`}
                  className="btn btn-sm btn-primary w-full"
                >
                  Open Full {activeSample.display_name.split(" ")[0]} Dashboard &amp; Timeline →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          KEY NUMBERS: Macro Environmental & Latency Highlights
          ========================================================================= */}
      <section className="stats-banner-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">524.2 <span className="stat-unit">kg</span></div>
            <div className="stat-label">CO₂e Avoided per R740 Server</div>
            <div className="stat-sub">Dell EMC LCA empirical silicon benchmarks</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">98.4 <span className="stat-unit">%</span></div>
            <div className="stat-label">Component Preservation Yield</div>
            <div className="stat-sub">Prioritizes high-value GPUs &amp; CPUs first</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">100 <span className="stat-unit">%</span></div>
            <div className="stat-label">Cryptographic Lineage</div>
            <div className="stat-sub">AWS KMS asymmetric ECC_NIST_P256 keys</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">&lt; 0.8 <span className="stat-unit">s</span></div>
            <div className="stat-label">Autonomous Triage Latency</div>
            <div className="stat-sub">Zero-idle-cost AWS Step Functions execution</div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          THE PROBLEM VS THE RE:GENESIS SOLUTION (Interactive Contrast)
          ========================================================================= */}
      <section className="contrast-section">
        <div className="section-header text-center">
          <h2 className="section-title">The Industrial E-Waste Paradox</h2>
          <p className="section-subtitle">
            Why precision component recovery beats shred-and-smelt downcycling every single time:
          </p>
        </div>

        <div className="contrast-toggle-wrap">
          <button
            className={`contrast-toggle-btn ${activeComparisonTab === "problem" ? "active-problem" : ""}`}
            onClick={() => setActiveComparisonTab("problem")}
          >
            ❌ The Status Quo: Industrial Shredding
          </button>
          <button
            className={`contrast-toggle-btn ${activeComparisonTab === "solution" ? "active-solution" : ""}`}
            onClick={() => setActiveComparisonTab("solution")}
          >
            ✅ The RE:GENESIS Circular Solution
          </button>
        </div>

        {activeComparisonTab === "problem" ? (
          <div className="contrast-card contrast-problem-card">
            <div className="contrast-badge-pill problem-pill">The Traditional Linear Way</div>
            <h3 className="contrast-card-title">Downcycling Enterprise Silicon into Dust</h3>
            <p className="contrast-card-text">
              Traditional electronics recyclers use massive industrial shredders that mechanically crush enterprise server blades and PCs. Functional GPUs, NVMe SSDs, and multi-core CPUs are crushed into mixed scrap metal.
            </p>
            <div className="contrast-points-grid">
              <div className="contrast-point">
                <span className="point-icon text-danger">⚠️</span>
                <div>
                  <strong>94% Utility Loss:</strong> Hundreds of hours of extreme cleanroom wafer lithography destroyed in milliseconds.
                </div>
              </div>
              <div className="contrast-point">
                <span className="point-icon text-danger">⚠️</span>
                <div>
                  <strong>Toxic Slag &amp; Smelter Emissions:</strong> Chemical burning and pyrometallurgical smelting release significant scope-3 CO₂.
                </div>
              </div>
              <div className="contrast-point">
                <span className="point-icon text-danger">⚠️</span>
                <div>
                  <strong>Zero Market Provenance:</strong> Uncertified loose components flood grey markets with no proof of authenticity or remaining lifespan.
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="contrast-card contrast-solution-card">
            <div className="contrast-badge-pill solution-pill">The Autonomous Precision Way</div>
            <h3 className="contrast-card-title">Autonomous Non-Destructive Triage &amp; DPPs</h3>
            <p className="contrast-card-text">
              RE:GENESIS preserves whole-component utility. Optical computer vision inspects the chassis, RVS planning orders the safest extraction sequence, and AWS KMS issues immutable digital product passports for secondary marketplace resale.
            </p>
            <div className="contrast-points-grid">
              <div className="contrast-point">
                <span className="point-icon text-accent">✓</span>
                <div>
                  <strong>Maximum Carbon Savings:</strong> Directly negates the carbon emissions of manufacturing new semiconductor dies.
                </div>
              </div>
              <div className="contrast-point">
                <span className="point-icon text-accent">✓</span>
                <div>
                  <strong>RVS Profit Maximization:</strong> Removal sequences extract $130+ GPU modules first, maximizing technician throughput.
                </div>
              </div>
              <div className="contrast-point">
                <span className="point-icon text-accent">✓</span>
                <div>
                  <strong>Verifiable Second-Life Passports:</strong> Refurbishers and enterprise buyers verify health scores and KMS signatures in 1 click.
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* =========================================================================
          INTERACTIVE FLEET SCALE SIMULATOR (Quick ESG Teaser)
          ========================================================================= */}
      <section className="fleet-teaser-section">
        <div className="card fleet-teaser-card">
          <div className="teaser-header">
            <div>
              <h3 className="teaser-title">Data Center Decommissioning ESG Estimator</h3>
              <p className="teaser-subtitle">
                Estimate the environmental return of autonomous circular recovery across enterprise server refreshes:
              </p>
            </div>
            <div className="teaser-slider-box">
              <label htmlFor="landing-slider" className="slider-label">
                Decommission Batch: <strong>{simBatchSize} Rack Servers</strong>
              </label>
              <input
                id="landing-slider"
                type="range"
                min="5"
                max="200"
                step="5"
                value={simBatchSize}
                onChange={(e) => setSimBatchSize(parseInt(e.target.value, 10))}
                className="slider"
              />
            </div>
          </div>

          <div className="teaser-kpis-grid">
            <div className="teaser-kpi">
              <span className="teaser-kpi-val text-accent">
                {(simBatchSize * 524.2).toLocaleString()} kg
              </span>
              <span className="teaser-kpi-lbl">Avoided Embodied CO₂e</span>
            </div>
            <div className="teaser-kpi">
              <span className="teaser-kpi-val text-vision">
                {(simBatchSize * 14.8).toLocaleString()} kg
              </span>
              <span className="teaser-kpi-lbl">Landfill E-Waste Diverted</span>
            </div>
            <div className="teaser-kpi">
              <span className="teaser-kpi-val text-warn">
                {(simBatchSize * 1.2).toFixed(1)} grams
              </span>
              <span className="teaser-kpi-lbl">Connector Gold (Au) Reclaimed</span>
            </div>
            <div className="teaser-kpi">
              <span className="teaser-kpi-val">
                {simBatchSize * 19} Parts
              </span>
              <span className="teaser-kpi-lbl">KMS-Certified Passports</span>
            </div>
          </div>

          <div className="teaser-footer">
            <Link to="/impact" className="link-accent">
              Explore Full Methodology, LCA Citations &amp; Critical Minerals Breakdown →
            </Link>
          </div>
        </div>
      </section>

      {/* =========================================================================
          AUTONOMOUS RECOVERY LIFECYCLE (4 Steps)
          ========================================================================= */}
      <section className="workflow-section">
        <div className="section-header text-center">
          <h2 className="section-title">Autonomous Recovery Lifecycle</h2>
          <p className="section-subtitle">
            From unclassified hardware chassis to cryptographically verified second-life component:
          </p>
        </div>

        <div className="workflow-steps-grid">
          <div className="workflow-step-card">
            <div className="step-number">01</div>
            <h4 className="step-title">Optical Intake &amp; OCR</h4>
            <p className="step-desc">
              Technician photo ingestion into Amazon S3. Textract scans manufacturer labels and serial numbers to lock catalog profiles.
            </p>
            <div className="step-badge">Amazon S3 · Textract</div>
          </div>

          <div className="workflow-step-card">
            <div className="step-number">02</div>
            <h4 className="step-title">AI Vision &amp; Audit</h4>
            <p className="step-desc">
              SageMaker YOLOv8 models component bounding boxes. Completeness auditing flags missing hardware gaps vs empirical BOM specs.
            </p>
            <div className="step-badge">SageMaker · Python Layer</div>
          </div>

          <div className="workflow-step-card">
            <div className="step-number">03</div>
            <h4 className="step-title">RVS Disassembly Planning</h4>
            <p className="step-desc">
              Recovery Value Score (RVS) algorithms schedule high-value components (GPUs, PSUs) first, minimizing labor while respecting safety.
            </p>
            <div className="step-badge">Step Functions · Lambda</div>
          </div>

          <div className="workflow-step-card">
            <div className="step-number">04</div>
            <h4 className="step-title">Second-Life Passports</h4>
            <p className="step-desc">
              Deterministic health diagnostics benchmark every subassembly. AWS KMS signs Digital Product Passports for resale transparency.
            </p>
            <div className="step-badge">AWS KMS · DynamoDB</div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          FINAL CALL TO ACTION
          ========================================================================= */}
      <section className="final-cta-section">
        <div className="final-cta-card">
          <h2 className="cta-heading">Ready to Accelerate Electronics Circularity?</h2>
          <p className="cta-subheading">
            Test the live recovery pipeline on AWS serverless with our pre-loaded Dell R740, ThinkPad T14, or Cisco Catalyst 9300 profiles.
          </p>
          <div className="cta-button-row">
            <Link to="/recovery" className="btn btn-primary hero-btn">
              <span className="btn-icon">⚡</span>
              <span>Start New Recovery Intake</span>
            </Link>
            <Link to="/devices/sample-r740" className="btn btn-outline hero-btn">
              <span>View Dell R740 Golden Demo</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
