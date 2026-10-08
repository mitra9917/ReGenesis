from typing import Any, Dict


def reuse_value_score(
    comp_type: str,
    specs: Dict[str, Any],
    test_pass_probability: float = 0.85,
) -> float:
    """Reuse Value Score: embodied CO2e × recoverability × pass_prob − risk."""
    meta = specs.get(comp_type, specs.get("RAM", {}))
    co2 = float(meta.get("embodied_co2e_kg_per_unit", 10))
    recoverability = float(meta.get("recoverability", 0.8))
    risk = float(meta.get("risk_penalty", 0.2))
    return co2 * recoverability * test_pass_probability - (risk * co2 * 0.1)
