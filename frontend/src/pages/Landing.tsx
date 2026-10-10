import React from "react";
import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <span className="badge-pulse"></span>
          <span>AWS Environmental Hacks · Waste &amp; Energy Track</span>
        </div>
        <h1 className="hero-title">
          Autonomous Electronics Recovery &amp;{" "}
          <span className="gradient-text">Second-Life Passports</span>
        </h1>
        <p className="hero-subtitle">
          Over 50 million metric tons of e-waste are shredded each year because manual triage
          is too slow and component provenance is untrusted. RE:GENESIS automates optical
          inspection, BOM completeness auditing, prioritized RVS disassembly, and KMS-signed
          Digital Product Passports on AWS serverless.
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
            <span>Explore AWS Architecture</span>
          </Link>
        </div>

        {/* Live Metric Highlights */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">524.2 <span className="stat-unit">kg</span></div>
            <div className="stat-label">CO₂e Avoided per R740</div>
            <div className="stat-sub">Based on Dell Server LCA empirical factors</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">98.4 <span className="stat-unit">%</span></div>
            <div className="stat-label">Component Recovery Yield</div>
            <div className="stat-sub">High-value GPUs &amp; CPUs prioritized first</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">100 <span className="stat-unit">%</span></div>
            <div className="stat-label">Cryptographic Lineage</div>
            <div className="stat-sub">KMS ECDSA asymmetric signatures</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">&lt; 0.8 <span className="stat-unit">s</span></div>
            <div className="stat-label">Autonomous Triage Latency</div>
            <div className="stat-sub">SageMaker YOLOv8 + fallback engine</div>
          </div>
        </div>
      </section>

      {/* Interactive Demonstration Devices */}
      <section className="devices-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Pre-Configured Enterprise Hardware Targets</h2>
            <p className="section-subtitle">
              Select any validated hardware profile to inspect its disassembly graph, BOM audit, and live passport records:
            </p>
          </div>
        </div>

        <div className="device-cards-grid">
          {/* Device 1: Dell PowerEdge R740 */}
          <div className="device-preview-card">
            <div className="device-card-header">
              <span className="device-type-tag">Enterprise 2U Rack Server</span>
              <span className="device-status-tag ready">Production Ready</span>
            </div>
            <h3 className="device-card-title">Dell PowerEdge R740</h3>
            <p className="device-card-desc">
              High-density compute node with dual Xeon sockets, 8× DDR4 ECC RAM, 4× NVMe SSDs, 2× redundant PSUs, and dual PCIe GPU accelerators.
            </p>
            <div className="device-card-metrics">
              <div className="metric-pill"><span>19</span> Detected Parts</div>
              <div className="metric-pill"><span>RVS 412.5</span> Priority Score</div>
              <div className="metric-pill highlight"><span>524 kg</span> CO₂e Avoided</div>
            </div>
            <div className="device-card-actions">
              <Link to="/devices/sample-r740" className="btn btn-sm btn-primary">
                View Golden Run Dashboard →
              </Link>
              <Link to="/recovery?model=poweredge_r740" className="btn btn-sm btn-outline">
                Run New Intake
              </Link>
            </div>
          </div>

          {/* Device 2: Lenovo ThinkPad T14 */}
          <div className="device-preview-card">
            <div className="device-card-header">
              <span className="device-type-tag">Commercial Laptop</span>
              <span className="device-status-tag ready">Stretch Target</span>
            </div>
            <h3 className="device-card-title">Lenovo ThinkPad T14 Gen 2</h3>
            <p className="device-card-desc">
              Enterprise laptop with modular 50Wh Li-Ion internal battery, M.2 2280 NVMe SSD, DDR4 SO-DIMM RAM, and Wi-Fi 6 wireless module.
            </p>
            <div className="device-card-metrics">
              <div className="metric-pill"><span>5</span> Detected Parts</div>
              <div className="metric-pill"><span>RVS 88.5</span> Priority Score</div>
              <div className="metric-pill highlight"><span>84.6 kg</span> CO₂e Avoided</div>
            </div>
            <div className="device-card-actions">
              <Link to="/devices/sample-t14" className="btn btn-sm btn-primary">
                View Golden Run Dashboard →
              </Link>
              <Link to="/recovery?model=thinkpad_t14" className="btn btn-sm btn-outline">
                Run New Intake
              </Link>
            </div>
          </div>

          {/* Device 3: Cisco Catalyst 9300 */}
          <div className="device-preview-card">
            <div className="device-card-header">
              <span className="device-type-tag">Enterprise Network Switch</span>
              <span className="device-status-tag ready">Stretch Target</span>
            </div>
            <h3 className="device-card-title">Cisco Catalyst 9300 Series</h3>
            <p className="device-card-desc">
              Modular 48-port core switch featuring dual hot-plug Platinum power supplies, 3× variable-speed fan trays, storage SSD, and uplink NIC.
            </p>
            <div className="device-card-metrics">
              <div className="metric-pill"><span>9</span> Detected Parts</div>
              <div className="metric-pill"><span>RVS 142.0</span> Priority Score</div>
              <div className="metric-pill highlight"><span>182.4 kg</span> CO₂e Avoided</div>
            </div>
            <div className="device-card-actions">
              <Link to="/devices/sample-c9300" className="btn btn-sm btn-primary">
                View Golden Run Dashboard →
              </Link>
              <Link to="/recovery?model=cisco_catalyst_9300" className="btn btn-sm btn-outline">
                Run New Intake
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 4-Step Pipeline Architecture Overview */}
      <section className="workflow-section">
        <h2 className="section-title text-center">Autonomous Recovery Lifecycle</h2>
        <p className="section-subtitle text-center">
          From unclassified server chassis to cryptographically authenticated secondary marketplace components:
        </p>

        <div className="workflow-steps-grid">
          <div className="workflow-step-card">
            <div className="step-number">01</div>
            <h4 className="step-title">Optical Intake &amp; OCR</h4>
            <p className="step-desc">
              Mobile or bench photo ingestion into Amazon S3. Amazon Textract detects serial badges and model plates to lock device catalog profiles.
            </p>
            <div className="step-badge">Amazon S3 · Textract</div>
          </div>

          <div className="workflow-step-card">
            <div className="step-number">02</div>
            <h4 className="step-title">AI Hybrid Vision &amp; Audit</h4>
            <p className="step-desc">
              SageMaker YOLOv8 models component bounding boxes. Completeness auditing flags missing hardware gaps vs empirical BOM specifications.
            </p>
            <div className="step-badge">SageMaker · Python Layer</div>
          </div>

          <div className="workflow-step-card">
            <div className="step-number">03</div>
            <h4 className="step-title">RVS Disassembly Planning</h4>
            <p className="step-desc">
              Recovery Value Score (RVS) algorithms schedule high-value components (GPUs, PSUs) first, minimizing labor while respecting safety prerequisites.
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
    </div>
  );
}
