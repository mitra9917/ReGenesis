type ComponentItem = {
  component_id?: string;
  comp_type: string;
  rvs?: number;
  priority_tier?: string;
  action?: string;
  risk?: number;
  extraction_step?: number;
};

type Step = {
  catalog_step?: number;
  action: string;
  risk: number;
  step_rvs?: number;
  priority_tier?: string;
  components?: ComponentItem[];
};

type Plan = {
  plan_id?: string;
  device_model_key?: string;
  steps?: Step[];
  total_plan_rvs?: number;
  highest_rvs_component?: string;
  strategy?: string;
  total_extraction_steps?: number;
};

function getRvsClass(rvs?: number): string {
  if (rvs === undefined) return "rvs-badge-std";
  if (rvs >= 50) return "rvs-badge-critical";
  if (rvs >= 15) return "rvs-badge-high";
  if (rvs >= 8) return "rvs-badge-med";
  return "rvs-badge-std";
}

function getTierClass(tier?: string): string {
  switch (tier?.toLowerCase()) {
    case "critical":
      return "tier-critical";
    case "high":
      return "tier-high";
    case "medium":
      return "tier-medium";
    case "prerequisite":
      return "tier-prep";
    default:
      return "tier-standard";
  }
}

function getMarkerClass(tier?: string): string {
  switch (tier?.toLowerCase()) {
    case "critical":
      return "marker-critical";
    case "high":
      return "marker-high";
    case "prerequisite":
      return "marker-prep";
    default:
      return "";
  }
}

function getRiskColor(risk: number): string {
  if (risk <= 0.15) return "var(--accent)";
  if (risk <= 0.3) return "var(--warn)";
  return "var(--danger)";
}

export function PlanTimeline({ plan }: { plan?: Plan }) {
  if (!plan?.steps?.length) {
    return <p style={{ color: "var(--muted)" }}>Plan will appear after detection…</p>;
  }

  const totalRvs =
    plan.total_plan_rvs ??
    roundToTwo(
      plan.steps.reduce(
        (sum, s) => sum + (s.components?.reduce((cSum, c) => cSum + (c.rvs || 0), 0) || 0),
        0
      )
    );

  const highestComp =
    plan.highest_rvs_component ||
    plan.steps
      .flatMap((s) => s.components || [])
      .sort((a, b) => (b.rvs || 0) - (a.rvs || 0))[0]?.comp_type;

  return (
    <div>
      <div className="timeline-header-bar">
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text)" }}>
            ⚡ Reuse Value Score (RVS) Prioritization
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
            High-yield components and low-risk steps prioritized first
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
          {highestComp && (
            <span className="pill pill-vision" style={{ fontSize: "0.7rem" }}>
              Top: {highestComp}
            </span>
          )}
          <span className="pill pill-catalog" style={{ fontSize: "0.7rem", fontWeight: 700 }}>
            Total RVS: {totalRvs}
          </span>
        </div>
      </div>

      <div style={{ position: "relative", paddingLeft: "4px" }}>
        {plan.steps.map((step, idx) => {
          const compCount = step.components?.length || 0;
          const stepRvs =
            step.step_rvs ??
            roundToTwo(step.components?.reduce((sum, c) => sum + (c.rvs || 0), 0) || 0);
          const tier =
            step.priority_tier || (compCount === 0 ? "Prerequisite" : stepRvs >= 15 ? "High" : "Medium");

          return (
            <div key={idx} className="timeline-step">
              <div className={`timeline-step-marker ${getMarkerClass(tier)}`} />

              <div className="timeline-title-row">
                <span style={{ fontWeight: 700, color: "var(--text)", fontSize: "0.9rem" }}>
                  Step {idx + 1}
                </span>
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>—</span>
                <span style={{ fontWeight: 600, color: "var(--text)", fontSize: "0.9rem" }}>
                  {step.action}
                </span>

                <span className={`tier-pill ${getTierClass(tier)}`}>
                  {tier}
                </span>

                <span
                  style={{
                    fontSize: "0.72rem",
                    color: getRiskColor(step.risk),
                    marginLeft: "auto",
                    fontWeight: 600,
                  }}
                >
                  Risk: {step.risk}
                </span>
              </div>

              {compCount > 0 ? (
                <div className="timeline-components-grid">
                  {step.components?.map((c, cIdx) => {
                    const isHigh = (c.rvs || 0) >= 15;
                    const isCritical = (c.rvs || 0) >= 50;
                    return (
                      <span
                        key={cIdx}
                        className={`comp-chip ${
                          isCritical
                            ? "comp-chip-critical"
                            : isHigh
                            ? "comp-chip-high"
                            : ""
                        }`}
                      >
                        <span style={{ fontWeight: 600 }}>{c.comp_type}</span>
                        {c.rvs !== undefined && (
                          <span className={`rvs-badge ${getRvsClass(c.rvs)}`}>
                            RVS {c.rvs}
                          </span>
                        )}
                        {c.extraction_step !== undefined && (
                          <span style={{ color: "var(--muted)", fontSize: "0.68rem" }}>
                            #{c.extraction_step}
                          </span>
                        )}
                      </span>
                    );
                  })}
                </div>
              ) : (
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", fontStyle: "italic", marginTop: "0.2rem" }}>
                  Enclosure preparation · Required before component extraction
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function roundToTwo(num: number): number {
  return Math.round(num * 100) / 100;
}
