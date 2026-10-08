from regenesis_common.passport import canonical_passport_bytes, strip_signature


def test_canonical_stable_and_excludes_signature():
    doc = {
        "passport_id": "p1",
        "component_id": "c1",
        "device_id": "d1",
        "timestamp": "2026-01-01T00:00:00Z",
        "component_type": "GPU",
        "status": "qualified_for_reuse",
        "tests": {"a": 1},
        "signature": "SHOULD_NOT_APPEAR",
    }
    b1 = canonical_passport_bytes(doc)
    b2 = canonical_passport_bytes({**doc, "signature": "OTHER"})
    assert b1 == b2
    assert b"signature" not in b1
    stripped = strip_signature(doc)
    assert "signature" not in stripped
