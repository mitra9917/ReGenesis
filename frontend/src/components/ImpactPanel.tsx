type FactorCitation = {
  count: number;
  embodied_co2e_factor_kg: number;
  embodied_co2e_range_kg?: { low: number; high: number };
  subtotal_co2e_kg: number;
  subtotal_co2e_range_kg?: { low: number; high: number };
  avg_mass_kg: number;
  subtotal_mass_kg: number;
  lca_source: string;
};

type Impact = {
  components_qualified?: number;
  components_total?: number;
  mass_diverted_kg?: number;
  mass_diverted_kg_range?: { low: number; high: number };
  co2e_avoided_kg?: number;
  co2e_avoided_kg_range?: { low: number; high: number };
  improvement_vs_shred?: number;
  qualified_by_type?: Record<string, number>;
  factor_citations?: Record<string, FactorCitation>;
  methodology?: string;
};

export function ImpactPanel({ impact }: { impact: Impact }) {
  const citations = impact.factor_citations;
  const citationEntries = citations ? Object.entries(citations) : [];

  return (
    <div>
      <div className="grid-2">
        <div>
          <div className="impact-stat">{impact.components_qualified ?? 0}</div>
          <div className="impact-label">
            components qualified for reuse ({impact.components_total ? `${impact.components_total} total evaluated` : "reuse path"})
          </div>
        </div>
        <div>
          <div className="impact-stat">
            {impact.mass_diverted_kg ?? 0} kg
            {impact.mass_diverted_kg_range && (
              <span style={{ fontSize: "0.85rem", color: "var(--muted)", fontWeight: 400, marginLeft: "0.4rem" }}>
                ({impact.mass_diverted_kg_range.low}–{impact.mass_diverted_kg_range.high} kg)
              </span>
            )}
          </div>
          <div className="impact-label">mass diverted from shred path</div>
        </div>
        <div>
          <div className="impact-stat">{impact.co2e_avoided_kg ?? 0} kg</div>
          <div className="impact-label">CO₂e avoided (point estimate)</div>
        </div>
        <div>
          <div className="impact-stat" style={{ color: "var(--accent)" }}>
            {impact.co2e_avoided_kg_range
              ? `${impact.co2e_avoided_kg_range.low} – ${impact.co2e_avoided_kg_range.high} kg`
              : "—"}
          </div>
          <div className="impact-label">
            honest CO₂e range · vs shred baseline +{impact.improvement_vs_shred ?? impact.components_qualified ?? 0} parts
          </div>
        </div>
      </div>

      <div className="impact-citation-banner">
        <span>🌱</span>
        <div>
          <strong>Empirical Catalog Factors:</strong> Cites component lifecycle assessments (Dell PowerEdge R740 LCA & academic hardware carbon studies). Honest ranges reflect silicon die size, binning, and capacity variance.
        </div>
      </div>

      {citationEntries.length > 0 && (
        <div className="impact-breakdown-wrap">
          <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text)", marginBottom: "0.3rem" }}>
            Component Factor Citations & Impact Breakdown
          </div>
          <table className="impact-table">
            <thead>
              <tr>
                <th>Component</th>
                <th>Qty</th>
                <th>Factor (kg CO₂e/unit)</th>
                <th>Avoided Subtotal</th>
                <th>Mass (kg)</th>
                <th>LCA Source</th>
              </tr>
            </thead>
            <tbody>
              {citationEntries.map(([type, c]) => (
                <tr key={type}>
                  <td style={{ fontWeight: 600 }}>{type}</td>
                  <td>{c.count}×</td>
                  <td>
                    {c.embodied_co2e_factor_kg} kg
                    {c.embodied_co2e_range_kg && (
                      <span style={{ color: "var(--muted)", fontSize: "0.75rem", marginLeft: "0.25rem" }}>
                        ({c.embodied_co2e_range_kg.low}–{c.embodied_co2e_range_kg.high})
                      </span>
                    )}
                  </td>
                  <td style={{ fontWeight: 600, color: "var(--accent)" }}>
                    {c.subtotal_co2e_kg} kg
                    {c.subtotal_co2e_range_kg && (
                      <span style={{ color: "var(--muted)", fontWeight: 400, fontSize: "0.75rem", marginLeft: "0.25rem" }}>
                        ({c.subtotal_co2e_range_kg.low}–{c.subtotal_co2e_range_kg.high})
                      </span>
                    )}
                  </td>
                  <td>{c.subtotal_mass_kg} kg</td>
                  <td style={{ color: "var(--muted)", fontSize: "0.75rem" }}>{c.lca_source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
