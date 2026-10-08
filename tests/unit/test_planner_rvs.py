from regenesis_common.planner import build_disassembly_plan
from regenesis_common.rvs import reuse_value_score


def test_rvs_gpu_higher_than_fan():
    specs = {
        "GPU": {"embodied_co2e_kg_per_unit": 180, "recoverability": 0.9, "risk_penalty": 0.3},
        "Fan": {"embodied_co2e_kg_per_unit": 5, "recoverability": 0.8, "risk_penalty": 0.1},
    }
    assert reuse_value_score("GPU", specs) > reuse_value_score("Fan", specs)


def test_plan_orders_components():
    components = [
        {"component_id": "a", "comp_type": "GPU"},
        {"component_id": "b", "comp_type": "RAM"},
        {"component_id": "c", "comp_type": "SSD"},
    ]
    plan = build_disassembly_plan("poweredge_r740", components)
    assert plan["steps"]
    assert plan["total_extraction_steps"] >= len(components)
