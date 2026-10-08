type Plan = {
  steps?: Array<{
    action: string;
    risk: number;
    components?: Array<{ comp_type: string; rvs?: number }>;
  }>;
};

export function PlanTimeline({ plan }: { plan?: Plan }) {
  if (!plan?.steps?.length) {
    return <p style={{ color: "var(--muted)" }}>Plan will appear after detection…</p>;
  }

  return (
    <div>
      {plan.steps.map((step, idx) => (
        <div key={idx} className="timeline-step">
          <strong>Step {idx + 1}</strong> — {step.action}
          <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            Risk {step.risk} · {step.components?.length || 0} component(s)
            {step.components?.map((c) => ` · ${c.comp_type} (RVS ${c.rvs})`).join("")}
          </div>
        </div>
      ))}
    </div>
  );
}
