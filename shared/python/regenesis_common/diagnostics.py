import hashlib
import random
from typing import Any, Dict

from regenesis_common.catalog import load_catalog


def _rng_for_component(component_id: str) -> tuple[random.Random, int]:
    clean_id = str(component_id or "comp-default").strip()
    seed = int(hashlib.sha256(clean_id.encode("utf-8")).hexdigest()[:8], 16)
    return random.Random(seed), seed


def run_component_diagnostics(component: Dict[str, Any]) -> Dict[str, Any]:
    """Execute deterministic simulated diagnostics seeded strictly by component_id.

    Guarantee: Same component_id + comp_type ALWAYS produces the exact same
    test_results, health_score, status, and diagnostics_grade across all environments.
    """
    catalog = load_catalog()
    specs = catalog["component_specs"]
    comp_id = str(component.get("component_id") or "comp-default").strip()
    comp_type = component.get("comp_type", "RAM")
    profile = specs.get(comp_type, {}).get("test_profile", "memory_pattern")
    rng, seed = _rng_for_component(comp_id)

    health = component.get("health_score")
    if health is None:
        health = rng.uniform(0.55, 0.99)

    passed = health >= 0.45 and rng.random() > 0.12

    tests: Dict[str, Any] = {}
    if profile == "smart_health":
        tests = {
            "SMART_health_pct": round(rng.uniform(85, 100) if passed else rng.uniform(20, 60), 1),
            "bad_sectors": 0 if passed else rng.randint(1, 50),
            "read_mb_s": round(rng.uniform(400, 550), 1),
        }
    elif profile == "gpu_memory_compute":
        tests = {
            "MemoryTest": "Pass" if passed else "Fail",
            "ComputeStress": "Pass" if passed else "Fail",
            "TemperatureMax": round(rng.uniform(55, 78) if passed else rng.uniform(85, 95), 1),
        }
    elif profile == "compute_stress":
        tests = {
            "ComputeStress": "Pass" if passed else "Fail",
            "ThermalThrottle": False if passed else True,
        }
    elif profile == "voltage_regulation":
        tests = {
            "VoltageRegulation": "Pass" if passed else "Fail",
            "EfficiencyPct": round(rng.uniform(88, 94) if passed else rng.uniform(60, 75), 1),
        }
    elif profile == "loopback":
        tests = {
            "Loopback": "Pass" if passed else "Fail",
            "PacketLossPct": 0 if passed else rng.uniform(1, 5),
        }
    elif profile == "capacity_check":
        tests = {
            "CapacityPct": round(rng.uniform(75, 95) if passed else rng.uniform(40, 60), 1),
            "CycleCount": rng.randint(200, 800),
        }
    elif profile == "rpm_stability":
        tests = {
            "RPMStability": "Pass" if passed else "Fail",
            "MaxRPM": rng.randint(3000, 6000),
        }
    elif profile == "signal_test":
        tests = {
            "SignalStrengthDbm": round(rng.uniform(-45, -60) if passed else rng.uniform(-75, -90), 1),
            "ThroughputMbps": round(rng.uniform(650, 900) if passed else rng.uniform(50, 200), 1),
        }
    else:
        tests = {
            "MemoryTest": "Pass" if passed else "Fail",
            "BadWords": 0 if passed else rng.randint(1, 3),
            "Errors": 0 if passed else rng.randint(1, 5),
        }

    status = "qualified_for_reuse" if passed else "failed"

    if status == "qualified_for_reuse":
        if health >= 0.85:
            grade = "Grade A (Prime)"
        elif health >= 0.65:
            grade = "Grade B (Standard)"
        else:
            grade = "Grade C (Functional)"
    else:
        grade = "Grade F (Recycle Only)"

    return {
        "component_id": comp_id,
        "comp_type": comp_type,
        "status": status,
        "test_results": tests,
        "health_score": round(health, 3),
        "test_profile": profile,
        "diagnostics_grade": grade,
        "deterministic_seed": hex(seed)[2:],
    }
