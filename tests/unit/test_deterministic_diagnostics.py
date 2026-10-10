"""Unit tests for deterministic diagnostics per component_id (I-4.3)."""

from regenesis_common.catalog import load_catalog
from regenesis_common.detection import catalog_assisted_detections
from regenesis_common.diagnostics import run_component_diagnostics


def test_diagnostics_identical_across_multiple_invocations():
    """Verify that same component_id produces 100% identical diagnostic results."""
    comp = {"component_id": "r740-golden-gpu-01", "comp_type": "GPU"}

    first = run_component_diagnostics(comp)
    second = run_component_diagnostics(comp)
    third = run_component_diagnostics(comp)

    assert first == second == third
    assert first["component_id"] == "r740-golden-gpu-01"
    assert first["comp_type"] == "GPU"
    assert "status" in first
    assert "test_results" in first
    assert "health_score" in first
    assert "diagnostics_grade" in first
    assert "deterministic_seed" in first


def test_different_component_ids_produce_distinct_seeds_and_results():
    """Verify that different component IDs produce independent deterministic outputs."""
    comp1 = {"component_id": "r740-ram-slot-A1", "comp_type": "RAM"}
    comp2 = {"component_id": "r740-ram-slot-B1", "comp_type": "RAM"}

    r1 = run_component_diagnostics(comp1)
    r2 = run_component_diagnostics(comp2)

    assert r1["deterministic_seed"] != r2["deterministic_seed"]
    # Repeatability check for each individual ID
    assert r1 == run_component_diagnostics(comp1)
    assert r2 == run_component_diagnostics(comp2)


def test_all_catalog_profiles_execute_cleanly():
    """Verify all component types from catalog execute their profiles deterministically."""
    specs = load_catalog()["component_specs"]

    for comp_type in specs.keys():
        comp = {"component_id": f"test-{comp_type.lower()}-001", "comp_type": comp_type}
        res = run_component_diagnostics(comp)

        assert res["comp_type"] == comp_type
        assert res["status"] in ("qualified_for_reuse", "failed")
        assert len(res["test_results"]) > 0
        assert 0.0 <= res["health_score"] <= 1.0
        assert "Grade" in res["diagnostics_grade"]

        # Determinism check
        again = run_component_diagnostics(comp)
        assert res == again


def test_deterministic_catalog_assisted_detections_with_device_id():
    """Verify catalog_assisted_detections produces stable component IDs when device_id is provided."""
    dev_id = "r740-golden-run-001"
    dets1 = catalog_assisted_detections("poweredge_r740", device_id=dev_id)
    dets2 = catalog_assisted_detections("poweredge_r740", device_id=dev_id)

    ids1 = [d["detection_id"] for d in dets1]
    ids2 = [d["detection_id"] for d in dets2]
    assert ids1 == ids2

    # Entire diagnostics run across all 19 components is identical
    diag1 = [run_component_diagnostics({"component_id": d["detection_id"], "comp_type": d["comp_type"]}) for d in dets1]
    diag2 = [run_component_diagnostics({"component_id": d["detection_id"], "comp_type": d["comp_type"]}) for d in dets2]
    assert diag1 == diag2


def test_custom_health_score_respected_deterministically():
    """Verify explicit health score overrides default range while remaining deterministic."""
    comp = {
        "component_id": "r740-custom-cpu",
        "comp_type": "CPU",
        "health_score": 0.95,
    }
    res = run_component_diagnostics(comp)
    assert res["health_score"] == 0.95
    assert res["diagnostics_grade"] == "Grade A (Prime)"
    assert res["status"] == "qualified_for_reuse"
