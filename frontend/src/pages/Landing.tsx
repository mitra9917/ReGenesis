import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="pl-landing">
      <section className="pl-hero">
        <p className="pl-eyebrow">Adaptive electronics recovery</p>
        <h1 className="pl-hero-title">
          Recover the component, not just the <em>metal</em>.
        </h1>
        <p className="pl-hero-lede">
          Vision, BOM completeness, and KMS-signed Second-Life Passports for
          enterprise hardware that still has value — before the shredder.
        </p>
        <div className="pl-hero-actions">
          <Link to="/recovery" className="pl-btn pl-btn-primary">
            Start a recovery →
          </Link>
          <Link to="/devices/sample-r740" className="pl-btn pl-btn-secondary">
            Watch the pipeline
          </Link>
        </div>
        <ul className="pl-hero-points">
          <li>Evidence-first vision</li>
          <li>BOM audit by design</li>
          <li>Human verifies passports</li>
        </ul>
      </section>

      <section className="pl-compare" aria-label="Shredding versus RE:GENESIS">
        <div className="pl-dark-card">
          <div className="pl-dark-head">
            <span>Industrial shredding</span>
            <span className="pl-pill-mute">Destroys value</span>
          </div>
          <div className="pl-dark-row">
            <span className="pl-dark-label">R740 teardown</span>
            <span className="pl-dark-bad">Shredded</span>
          </div>
          <div className="pl-dark-row">
            <span>0 reuse credentials · 0 lineage</span>
            <span className="pl-dark-faint">still not circular</span>
          </div>
        </div>

        <div className="pl-dark-card pl-dark-card-active">
          <div className="pl-dark-head">
            <span>RE:GENESIS room</span>
            <span className="pl-pill-live">Recovering</span>
          </div>
          <div className="pl-dark-row">
            <span className="pl-dark-label">Same chassis · vision must agree with BOM</span>
            <span className="pl-pill-live">Live</span>
          </div>
          <div className="pl-agent-row">
            <span className="pl-agent"><b>Cv</b> Vision</span>
            <span className="pl-agent"><b>Bm</b> BOM</span>
            <span className="pl-agent"><b>Rv</b> RVS</span>
            <span className="pl-agent"><b>Km</b> KMS</span>
          </div>
          <div className="pl-dark-foot">
            Detect → audit → plan → passport · human verifies
          </div>
        </div>
      </section>

      <section className="pl-stats" aria-label="Product facts">
        <div>
          <strong>7</strong>
          <span>Trained part classes on YOLO v3</span>
        </div>
        <div>
          <strong>9</strong>
          <span>Schema slots — PSU &amp; Fan reserved</span>
        </div>
        <div>
          <strong>100%</strong>
          <span>Passport verify via AWS KMS</span>
        </div>
      </section>

      <section className="pl-section">
        <p className="pl-section-index">01 / Pipeline</p>
        <h2 className="pl-section-title">Make recovery visible.</h2>
        <p className="pl-section-lede">
          The product signature is the Step Functions trail — detect, audit,
          plan, test, sign — not a black-box score.
        </p>

        <div className="pl-white-card">
          <div className="pl-white-card-top">
            <span className="pl-tag">Vision</span>
            <h3>Claim</h3>
          </div>
          <p>
            SageMaker YOLO returns class, confidence, and normalized boxes.
            Completeness audit compares detections to the catalog BOM before any
            part is pulled.
          </p>
          <div className="pl-metric-strip">
            <div>
              <span className="pl-metric-k">BOM score</span>
              <span className="pl-metric-v">percent, not vibes</span>
            </div>
            <div>
              <span className="pl-metric-k">Fallback</span>
              <span className="pl-metric-v">catalog-assisted</span>
            </div>
            <div>
              <span className="pl-metric-k">Passport</span>
              <span className="pl-metric-v">ECDSA_SHA_256</span>
            </div>
          </div>
        </div>
      </section>

      <section className="pl-section">
        <p className="pl-section-index">02 / Workflow</p>
        <h2 className="pl-section-title">Sense. Plan. Prove.</h2>
        <p className="pl-section-lede">
          Three modes, one visual system. No separate mini-products competing
          for attention.
        </p>

        <div className="pl-workflow">
          <article>
            <span className="pl-wf-num">01</span>
            <h3>Sense</h3>
            <p>
              Intake photo + model key. YOLO detects parts; OCR can confirm the
              plate; gaps surface in the completeness audit.
            </p>
            <Link to="/recovery">Open intake →</Link>
          </article>
          <article>
            <span className="pl-wf-num">02</span>
            <h3>Plan</h3>
            <p>
              Reuse Value Score orders disassembly so high-embodied parts come
              out first, with prerequisites respected.
            </p>
            <Link to="/devices/sample-r740">See R740 plan →</Link>
          </article>
          <article>
            <span className="pl-wf-num">03</span>
            <h3>Prove</h3>
            <p>
              Diagnostics qualify components. KMS signs Second-Life Passports
              buyers can verify in one click.
            </p>
            <Link to="/passports">Verify passports →</Link>
          </article>
        </div>
      </section>

      <section className="pl-section pl-about">
        <p className="pl-section-index">03 / About</p>
        <h2 className="pl-section-title">A recovery lab, not a shredder UI.</h2>
        <p className="pl-section-lede">
          RE:GENESIS is built for ITAD and circular hardware — optical triage on
          AWS, honest LCA ranges, and cryptographic lineage instead of a single
          greenwashed score.
        </p>
        <div className="pl-about-grid">
          <article>
            <h3>No shred-first default</h3>
            <p>
              We preserve whole-component utility whenever vision and catalog
              agree — GPUs and SSDs are not “feedstock” by default.
            </p>
          </article>
          <article>
            <h3>Grounded detection</h3>
            <p>
              Hybrid path: SageMaker when the endpoint is up; catalog-assisted
              when confidence or BOM coverage is weak.
            </p>
          </article>
          <article>
            <h3>Human authority</h3>
            <p>
              Passports are signed for reuse markets, but verify stays a human
              action — the system does not auto-approve resale.
            </p>
          </article>
        </div>
        <div className="pl-hero-actions pl-about-cta">
          <Link to="/recovery" className="pl-btn pl-btn-primary">
            Start a recovery →
          </Link>
          <Link to="/architecture" className="pl-btn pl-btn-secondary">
            AWS architecture
          </Link>
        </div>
      </section>
    </div>
  );
}
