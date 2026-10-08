import json
from typing import Any, Dict


def strip_signature(passport: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in passport.items() if k != "signature"}


def canonical_passport_bytes(passport: Dict[str, Any]) -> bytes:
    body = strip_signature(passport)
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
