import uuid
from typing import Any, Dict, List

from regenesis_common.catalog import load_catalog
from regenesis_common.rvs import reuse_value_score


def _priority_tier(rvs: float) -> str:
    if rvs >= 50.0:
        return "Critical"
    if rvs >= 15.0:
        return "High"
    if rvs >= 8.0:
        return "Medium"
    return "Standard"


def _step_priority_tier(step_rvs: float, has_components: bool) -> str:
    if not has_components:
        return "Prerequisite"
    return _priority_tier(step_rvs)


def build_disassembly_plan(
    device_model_key: str,
    components: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build ordered extraction steps using catalog rules + RVS ranking within each step.
    High-value parts (e.g. GPUs, PSUs) are prioritized sensibly.
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
                    rvs_val = round(reuse_value_score(t, specs), 2)
                    assigned.append(
                        {
                            "component_id": comp["component_id"],
                            "comp_type": comp["comp_type"],
                            "extraction_step": step_order,
                            "rvs": rvs_val,
                            "priority_tier": _priority_tier(rvs_val),
                            "action": rule["action"],
                            "risk": rule.get("risk", 0.2),
                        }
                    )
        # Sort assigned within step by RVS descending
        assigned.sort(key=lambda c: c["rvs"], reverse=True)

        if assigned or not targets or targets[0] in ("cover", "bottom_panel", "chassis"):
            step_rvs = round(sum(c["rvs"] for c in assigned), 2)
            steps.append(
                {
                    "catalog_step": rule["step"],
                    "action": rule["action"],
                    "risk": rule.get("risk", 0.2),
                    "step_rvs": step_rvs,
                    "priority_tier": _step_priority_tier(step_rvs, bool(assigned)),
                    "components": assigned,
                }
            )

    # Components not matched to catalog rules — prioritize by RVS descending
    planned_ids = {a["component_id"] for s in steps for a in s["components"]}
    unmatched = [c for c in components if c["component_id"] not in planned_ids]
    unmatched.sort(
        key=lambda c: reuse_value_score(c["comp_type"], specs),
        reverse=True,
    )
    for c in unmatched:
        step_order += 1
        t = c["comp_type"]
        rvs_val = round(reuse_value_score(t, specs), 2)
        assigned_comp = {
            "component_id": c["component_id"],
            "comp_type": t,
            "extraction_step": step_order,
            "rvs": rvs_val,
            "priority_tier": _priority_tier(rvs_val),
            "action": f"Extract {t}",
            "risk": 0.2,
        }
        steps.append(
            {
                "catalog_step": 99,
                "action": f"Extract {t}",
                "risk": 0.2,
                "step_rvs": rvs_val,
                "priority_tier": _priority_tier(rvs_val),
                "components": [assigned_comp],
            }
        )

    all_planned = [c for s in steps for c in s["components"]]
    total_plan_rvs = round(sum(c["rvs"] for c in all_planned), 2)
    highest_comp = max(all_planned, key=lambda c: c["rvs"]) if all_planned else None

    # Summary of unique component types ordered by RVS descending
    rvs_ranking = []
    seen_types = set()
    for c in sorted(all_planned, key=lambda x: x["rvs"], reverse=True):
        if c["comp_type"] not in seen_types:
            seen_types.add(c["comp_type"])
            rvs_ranking.append(
                {
                    "comp_type": c["comp_type"],
                    "rvs": c["rvs"],
                    "priority_tier": c["priority_tier"],
                }
            )

    graph_nodes = device["attachment_graph"].get("nodes", [])
    return {
        "plan_id": str(uuid.uuid4()),
        "device_model_key": device_model_key,
        "steps": steps,
        "graph_nodes": graph_nodes,
        "total_extraction_steps": step_order,
        "total_plan_rvs": total_plan_rvs,
        "highest_rvs_component": highest_comp["comp_type"] if highest_comp else None,
        "rvs_ranking": rvs_ranking,
        "strategy": "RVS-prioritized extraction (highest reuse value and lowest risk first)",
    }
