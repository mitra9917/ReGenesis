from typing import Any, Dict, List

from regenesis_common.catalog import load_catalog


def compute_impact_summary(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    catalog = load_catalog()
    specs = catalog["component_specs"]
    qualified = [c for c in components if c.get("status") in ("qualified", "qualified_for_reuse")]
    failed = [c for c in components if c.get("status") in ("failed", "recycle_only")]

    mass_kg = 0.0
    co2e_kg = 0.0
    by_type: Dict[str, int] = {}

    for c in qualified:
        t = c.get("comp_type", "RAM")
        meta = specs.get(t, {})
        mass_kg += float(meta.get("avg_mass_kg", 0.1))
        co2e_kg += float(meta.get("embodied_co2e_kg_per_unit", 10))
        by_type[t] = by_type.get(t, 0) + 1

    # Baseline: shred scenario — 0 parts reused
    regenesis_reuse_count = len(qualified)
    total_parts = len(components)

    return {
        "components_total": total_parts,
        "components_qualified": regenesis_reuse_count,
        "components_failed": len(failed),
        "mass_diverted_kg": round(mass_kg, 2),
        "co2e_avoided_kg": round(co2e_kg, 2),
        "co2e_avoided_kg_range": {
            "low": round(co2e_kg * 0.85, 2),
            "high": round(co2e_kg * 1.15, 2),
        },
        "qualified_by_type": by_type,
        "baseline_shred_reuse_count": 0,
        "improvement_vs_shred": regenesis_reuse_count,
    }
