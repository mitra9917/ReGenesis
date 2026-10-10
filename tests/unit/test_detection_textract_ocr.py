from regenesis_common.detection import match_device_from_ocr_text


def test_ocr_confirms_preferred_r740_plate():
    text = "Service Tag ABC123 Dell PowerEdge R740 Rack Server"
    out = match_device_from_ocr_text(text, preferred_key="poweredge_r740")
    assert out["confirmed"] is True
    assert out["influenced"] is False
    assert out["device_model_key"] == "poweredge_r740"
    assert "R740" in out["matched_hints"] or "PowerEdge" in out["matched_hints"]


def test_ocr_influences_wrong_preferred_to_thinkpad():
    text = "Lenovo ThinkPad T14 Gen 2"
    out = match_device_from_ocr_text(text, preferred_key="poweredge_r740")
    assert out["confirmed"] is True
    assert out["influenced"] is True
    assert out["device_model_key"] == "thinkpad_t14"
    assert any(h in out["matched_hints"] for h in ("ThinkPad", "T14", "Lenovo"))


def test_ocr_no_match_leaves_preferred():
    text = "RANDOM NOISE WITHOUT MODEL TOKENS"
    out = match_device_from_ocr_text(text, preferred_key="poweredge_r740")
    assert out["confirmed"] is False
    assert out["influenced"] is False
    assert out["device_model_key"] == "poweredge_r740"
    assert out["matched_hints"] == []


def test_ocr_matches_catalyst_switch():
    text = "Cisco Catalyst 9300 Series Switch"
    out = match_device_from_ocr_text(text, preferred_key=None)
    assert out["confirmed"] is True
    assert out["device_model_key"] == "cisco_catalyst_9300"
