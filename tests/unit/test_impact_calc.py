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
