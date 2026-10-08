"""Shared logic for RE:GENESIS Lambdas."""

from regenesis_common.catalog import load_catalog, get_device_spec
from regenesis_common.impact import compute_impact_summary
from regenesis_common.planner import build_disassembly_plan
from regenesis_common.passport import canonical_passport_bytes, strip_signature
from regenesis_common.diagnostics import run_component_diagnostics
from regenesis_common.detection import completeness_audit, catalog_assisted_detections
from regenesis_common.rvs import reuse_value_score

__all__ = [
    "load_catalog",
    "get_device_spec",
    "compute_impact_summary",
    "build_disassembly_plan",
    "canonical_passport_bytes",
    "strip_signature",
    "run_component_diagnostics",
    "completeness_audit",
    "catalog_assisted_detections",
    "reuse_value_score",
]
