from regenesis_common.catalog import load_catalog
from regenesis_common.planner import build_disassembly_plan
from regenesis_common.rvs import reuse_value_score


def test_rvs_gpu_higher_than_fan():
    specs = {
        "GPU": {"embodied_co2e_kg_per_unit": 180, "recoverability": 0.9, "risk_penalty": 0.3},
        "Fan": {"embodied_co2e_kg_per_unit": 5, "recoverability": 0.8, "risk_penalty": 0.1},
    }
    assert reuse_value_score("GPU", specs) > reuse_value_score("Fan", specs)


def test_rvs_hierarchy_from_catalog():
    specs = load_catalog()["component_specs"]
    rvs_gpu = reuse_value_score("GPU", specs)
    rvs_psu = reuse_value_score("PSU", specs)
    rvs_cpu = reuse_value_score("CPU", specs)
    rvs_nic = reuse_value_score("NIC", specs)
    rvs_ssd = reuse_value_score("SSD", specs)
    rvs_ram = reuse_value_score("RAM", specs)
    rvs_fan = reuse_value_score("Fan", specs)

    # High-value components strictly exceed lower-value ones
    assert rvs_gpu > rvs_psu > rvs_cpu > rvs_nic > rvs_ssd > rvs_ram > rvs_fan


def test_plan_orders_components():
    components = [
        {"component_id": "a", "comp_type": "GPU"},
        {"component_id": "b", "comp_type": "RAM"},
        {"component_id": "c", "comp_type": "SSD"},
    ]
    plan = build_disassembly_plan("poweredge_r740", components)
    assert plan["steps"]
    assert plan["total_extraction_steps"] >= len(components)
    assert plan["total_plan_rvs"] > 0
    assert plan["highest_rvs_component"] == "GPU"
    assert "strategy" in plan


def test_high_value_parts_prioritized_in_timeline():
    """Verify high-value GPU and PSU are scheduled earlier in extraction than RAM/SSD."""
    components = [
        {"component_id": "ram-1", "comp_type": "RAM"},
        {"component_id": "ram-2", "comp_type": "RAM"},
        {"component_id": "ssd-1", "comp_type": "SSD"},
        {"component_id": "gpu-1", "comp_type": "GPU"},
        {"component_id": "psu-1", "comp_type": "PSU"},
        {"component_id": "cpu-1", "comp_type": "CPU"},
    ]
    plan = build_disassembly_plan("poweredge_r740", components)

    # Flatten planned components in chronological extraction order
    extraction_order = []
    for step in plan["steps"]:
        for comp in step["components"]:
            extraction_order.append(comp)

    comp_steps = {c["comp_type"]: c["extraction_step"] for c in extraction_order}

    # GPU should be extracted before CPU, SSD, and RAM
    assert comp_steps["GPU"] < comp_steps["CPU"]
    assert comp_steps["GPU"] < comp_steps["SSD"]
    assert comp_steps["GPU"] < comp_steps["RAM"]
    assert comp_steps["PSU"] < comp_steps["SSD"]
    assert comp_steps["PSU"] < comp_steps["RAM"]

    # Verify priority tiers
    gpu_comp = next(c for c in extraction_order if c["comp_type"] == "GPU")
    assert gpu_comp["priority_tier"] == "Critical"
    assert gpu_comp["rvs"] > 100.0


def test_plan_unmatched_components_rvs_ordering():
    """Verify components not matching catalog rules are also sorted by RVS descending."""
    components = [
        {"component_id": "fan-1", "comp_type": "Fan"},
        {"component_id": "unknown-high", "comp_type": "GPU"},
    ]
    plan = build_disassembly_plan("poweredge_r740", components)
    # Both are matched or fallback, with GPU having higher RVS than Fan
    all_comps = [c for s in plan["steps"] for c in s["components"]]
    gpu_c = next(c for c in all_comps if c["comp_type"] == "GPU")
    fan_c = next(c for c in all_comps if c["comp_type"] == "Fan")
    assert gpu_c["extraction_step"] < fan_c["extraction_step"]
    assert gpu_c["rvs"] > fan_c["rvs"]

