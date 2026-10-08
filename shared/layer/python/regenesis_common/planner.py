import uuid
from typing import Any, Dict, List

from regenesis_common.catalog import load_catalog
from regenesis_common.rvs import reuse_value_score


def build_disassembly_plan(
    device_model_key: str,
    components: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build ordered extraction steps using catalog rules + RVS ranking within each step.
    """
    catalog = load_catalog()
    device = catalog["devices"][device_model_key]
    specs = catalog["component_specs"]
    rules = device["attachment_graph"]["removal_rules"]

    comp_by_type: Dict[str, List[Dict[str, Any]]] = {}
    for c in components:
        comp_by_type.setdefault(c["comp_type"], []).append(c)

    steps: List[Dict[str, Any]] = []
    step_order = 0
    for rule in sorted(rules, key=lambda r: r["step"]):
        targets = rule.get("targets", [])
        assigned: List[Dict[str, Any]] = []
        for t in targets:
            if t in comp_by_type:
                pool = sorted(
                    comp_by_type[t],
                    key=lambda c: reuse_value_score(t, specs),
                    reverse=True,
                )
                for comp in pool:
                    step_order += 1
                    assigned.append(
                        {
                            "component_id": comp["component_id"],
                            "comp_type": comp["comp_type"],
                            "extraction_step": step_order,
                            "rvs": round(reuse_value_score(t, specs), 2),
                            "action": rule["action"],
                            "risk": rule.get("risk", 0.2),
                        }
                    )
        if assigned or not targets or targets[0] in ("cover", "bottom_panel", "chassis"):
            steps.append(
                {
                    "catalog_step": rule["step"],
                    "action": rule["action"],
                    "risk": rule.get("risk", 0.2),
                    "components": assigned,
                }
            )

    # Components not matched to rules
    planned_ids = {a["component_id"] for s in steps for a in s["components"]}
    for c in components:
        if c["component_id"] not in planned_ids:
            step_order += 1
            t = c["comp_type"]
            steps.append(
                {
                    "catalog_step": 99,
                    "action": f"Extract {t}",
                    "risk": 0.2,
                    "components": [
                        {
                            "component_id": c["component_id"],
                            "comp_type": t,
                            "extraction_step": step_order,
                            "rvs": round(reuse_value_score(t, specs), 2),
                            "action": f"Extract {t}",
                            "risk": 0.2,
                        }
                    ],
                }
            )

    graph_nodes = device["attachment_graph"].get("nodes", [])
    return {
        "plan_id": str(uuid.uuid4()),
        "device_model_key": device_model_key,
        "steps": steps,
        "graph_nodes": graph_nodes,
        "total_extraction_steps": step_order,
    }
