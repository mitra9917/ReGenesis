import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


def _catalog_dir() -> Path:
    env = os.environ.get("CATALOG_DIR")
    if env:
        return Path(env)
    # Lambda layer: /opt/python/regenesis_common/../../catalog won't work — pack catalog in layer
    here = Path(__file__).resolve().parent
    candidates = [
        here / "catalog",
        here.parent.parent.parent / "catalog",
        Path("/opt/catalog"),
    ]
    for p in candidates:
        if (p / "devices.json").exists():
            return p
    return here.parent.parent.parent / "catalog"


@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, Any]:
    base = _catalog_dir()
    with open(base / "devices.json", encoding="utf-8") as f:
        devices = json.load(f)
    with open(base / "components_specs.json", encoding="utf-8") as f:
        specs = json.load(f)
    return {"devices": devices, "component_specs": specs["component_types"]}


def get_device_spec(device_model_key: str) -> Dict[str, Any]:
    catalog = load_catalog()
    if device_model_key not in catalog["devices"]:
        raise KeyError(f"Unknown device model: {device_model_key}")
    return catalog["devices"][device_model_key]
