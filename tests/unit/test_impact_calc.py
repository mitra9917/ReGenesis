from regenesis_common.impact import compute_impact_summary


def test_impact_counts_qualified_only():
    components = [
        {"comp_type": "GPU", "status": "qualified"},
        {"comp_type": "RAM", "status": "failed"},
    ]
    impact = compute_impact_summary(components)
    assert impact["components_qualified"] == 1
    assert impact["co2e_avoided_kg"] > 0
    assert impact["improvement_vs_shred"] == 1
    assert "co2e_avoided_kg_range" in impact
    assert impact["co2e_avoided_kg_range"]["low"] <= impact["co2e_avoided_kg"] <= impact["co2e_avoided_kg_range"]["high"]
    assert "factor_citations" in impact
    assert "GPU" in impact["factor_citations"]
    gpu_cit = impact["factor_citations"]["GPU"]
    assert gpu_cit["count"] == 1
    assert "lca_source" in gpu_cit
    assert gpu_cit["subtotal_co2e_kg"] > 0


def test_impact_empirical_ranges_sum_correctly():
    components = [
        {"comp_type": "CPU", "status": "qualified"},
        {"comp_type": "GPU", "status": "qualified"},
        {"comp_type": "RAM", "status": "qualified"},
    ]
    impact = compute_impact_summary(components)
    assert impact["components_qualified"] == 3
    co2e_range = impact["co2e_avoided_kg_range"]
    assert co2e_range["low"] < co2e_range["high"]
    # Verify range spans expected sum of catalog ranges (CPU 18-35, GPU 140-230, RAM 4.5-9)
    assert co2e_range["low"] >= 160.0
    assert co2e_range["high"] <= 300.0
    # Mass ranges
    mass_range = impact["mass_diverted_kg_range"]
    assert mass_range["low"] <= impact["mass_diverted_kg"] <= mass_range["high"]
    # Citations
    assert set(impact["factor_citations"].keys()) == {"CPU", "GPU", "RAM"}
    for comp_type, cit in impact["factor_citations"].items():
        assert cit["lca_source"]
        assert cit["embodied_co2e_range_kg"]["low"] <= cit["embodied_co2e_factor_kg"] <= cit["embodied_co2e_range_kg"]["high"]


