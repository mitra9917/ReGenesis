from regenesis_common.detection import match_device_from_ocr_text
from regenesis_common.ocr import resolve_plate_text


def test_resolve_prefers_explicit_plate_text():
    out = resolve_plate_text(
        plate_text="Dell PowerEdge R740",
        bucket="b",
        image_key="images/x/original.jpg",
    )
    assert out["engine"] == "plate_text"
    assert "PowerEdge" in out["text"]
    assert out["error"] == ""


def test_resolve_without_image_or_text():
    out = resolve_plate_text(plate_text="", bucket="b", image_key="")
    assert out["engine"] == "none"
    assert out["text"] == ""


def test_plate_text_confirms_r740():
    resolved = resolve_plate_text(plate_text="Service Tag X Dell PowerEdge R740")
    match = match_device_from_ocr_text(resolved["text"], preferred_key="poweredge_r740")
    assert match["confirmed"] is True
    assert match["device_model_key"] == "poweredge_r740"
