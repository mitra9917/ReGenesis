#!/usr/bin/env python3
"""Download the AL2023 Tesseract Lambda layer into shared/tesseract_layer/content.

Source: https://github.com/bweigel/aws-lambda-tesseract-layer (v5.4.0)
Run before `sam build` / `sam deploy` if content/ is missing.

  python scripts/fetch_tesseract_layer.py
"""

from __future__ import annotations

import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYER_DIR = ROOT / "shared" / "tesseract_layer"
CONTENT = LAYER_DIR / "content"
ZIP_PATH = LAYER_DIR / "tesseract-al2023-x86.zip"
URL = (
    "https://github.com/bweigel/aws-lambda-tesseract-layer/releases/download/"
    "v5.4.0/tesseract-al2023-x86.zip"
)


def main() -> int:
    LAYER_DIR.mkdir(parents=True, exist_ok=True)
    marker = CONTENT / "bin" / "tesseract"
    if marker.exists() and not ("--force" in sys.argv):
        print(f"Already present: {marker}")
        return 0

    print(f"Downloading {URL} …")
    urllib.request.urlretrieve(URL, ZIP_PATH)
    print(f"Extracting to {CONTENT} …")
    if CONTENT.exists():
        shutil.rmtree(CONTENT)
    CONTENT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(CONTENT)
    if not marker.exists():
        print("ERROR: bin/tesseract missing after extract", file=sys.stderr)
        return 1
    print("OK: Tesseract layer ready for SAM ContentUri shared/tesseract_layer/content/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
