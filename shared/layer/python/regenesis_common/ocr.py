"""Local Tesseract OCR helpers (Lambda layer or host install).

Lambda expects the bweigel AL2023 layer layout under /opt:
  /opt/bin/tesseract
  /opt/lib/...
  /opt/tesseract/share/tessdata/eng.traineddata
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional


def _configure_tesseract_env() -> str:
    """Return path to the tesseract binary and set tessdata / library paths."""
    explicit = os.environ.get("TESSERACT_CMD", "").strip()
    candidates = [
        explicit,
        "/opt/bin/tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        "tesseract",
    ]
    binary = next((c for c in candidates if c and (c == "tesseract" or Path(c).exists())), "tesseract")

    tessdata = os.environ.get("TESSDATA_PREFIX", "").strip()
    if not tessdata:
        for prefix in (
            "/opt/tesseract/share/tessdata",
            "/opt/share/tessdata",
            r"C:\Program Files\Tesseract-OCR\tessdata",
        ):
            if Path(prefix).exists():
                tessdata = prefix
                break
    if tessdata:
        # Tesseract wants the parent of tessdata/ OR the tessdata dir depending on version;
        # AL2023 layer uses TESSDATA_PREFIX pointing at the tessdata directory itself.
        os.environ["TESSDATA_PREFIX"] = tessdata

    lib_dir = "/opt/lib"
    if Path(lib_dir).exists():
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        if lib_dir not in existing.split(":"):
            os.environ["LD_LIBRARY_PATH"] = f"{lib_dir}:{existing}" if existing else lib_dir

    path = os.environ.get("PATH", "")
    opt_bin = "/opt/bin"
    if Path(opt_bin).exists() and opt_bin not in path.split(os.pathsep):
        os.environ["PATH"] = f"{opt_bin}{os.pathsep}{path}"

    return binary


def extract_text_from_image_bytes(image_bytes: bytes, lang: str = "eng") -> str:
    """OCR image bytes with Tesseract; return plain text (may be empty)."""
    if not image_bytes:
        return ""

    import pytesseract
    from PIL import Image

    binary = _configure_tesseract_env()
    pytesseract.pytesseract.tesseract_cmd = binary

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    text = pytesseract.image_to_string(img, lang=lang) or ""
    return " ".join(text.split())


def extract_text_from_s3(bucket: str, key: str, s3_client=None) -> str:
    """Download an S3 object and OCR it."""
    if not bucket or not key:
        return ""
    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    return extract_text_from_image_bytes(obj["Body"].read())


def resolve_plate_text(
    *,
    plate_text: Optional[str] = None,
    bucket: str = "",
    image_key: str = "",
    s3_client=None,
) -> dict:
    """Prefer explicit plate_text; otherwise OCR the uploaded image with Tesseract."""
    provided = (plate_text or "").strip()
    if provided:
        return {"text": provided, "engine": "plate_text", "error": ""}
    if not image_key:
        return {"text": "", "engine": "none", "error": ""}
    try:
        text = extract_text_from_s3(bucket, image_key, s3_client=s3_client)
        return {"text": text, "engine": "tesseract", "error": ""}
    except Exception as exc:
        return {"text": "", "engine": "tesseract", "error": f"{type(exc).__name__}: {exc}"}
