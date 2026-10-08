type Impact = {
  components_qualified?: number;
  components_total?: number;
  mass_diverted_kg?: number;
  co2e_avoided_kg?: number;
  co2e_avoided_kg_range?: { low: number; high: number };
  improvement_vs_shred?: number;
};

export function ImpactPanel({ impact }: { impact: Impact }) {
  return (
    <div className="grid-2">
      <div>
        <div className="impact-stat">{impact.components_qualified ?? 0}</div>
        <div className="impact-label">components qualified for reuse</div>
      </div>
      <div>
        <div className="impact-stat">{impact.mass_diverted_kg ?? 0} kg</div>
        <div className="impact-label">mass diverted from shred path</div>
      </div>
      <div>
        <div className="impact-stat">{impact.co2e_avoided_kg ?? 0} kg</div>
        <div className="impact-label">CO₂e avoided (point estimate)</div>
      </div>
      <div>
        <div className="impact-stat">
          {impact.co2e_avoided_kg_range
            ? `${impact.co2e_avoided_kg_range.low}–${impact.co2e_avoided_kg_range.high}`
            : "—"}
        </div>
        <div className="impact-label">CO₂e range · vs shred baseline +{impact.improvement_vs_shred ?? 0} parts</div>
      </div>
    </div>
  );
}
